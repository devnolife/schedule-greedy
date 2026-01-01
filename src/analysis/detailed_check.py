import pandas as pd
from collections import defaultdict

file = 'jadwal_gabungan_SATU_TABEL_FINAL_PWK_ARS.xlsx'
df = pd.read_excel(file, sheet_name='Jadwal Induk (Gabungan)')

print('🔍 DETAILED CONFLICT ANALYSIS')
print('=' * 50)

# 1. Room conflicts check
print('\n🏠 ROOM CONFLICT CHECK:')
luring = df[~df['Mode (Zoom/Luring)'].str.lower().str.contains('zoom', na=False)]
room_conflicts = luring[luring['Ruang'] != ''].groupby(['Hari', 'Sesi', 'Ruang']).size()
room_conflicts = room_conflicts[room_conflicts > 1]

if len(room_conflicts) > 0:
    print('❌ ROOM CONFLICTS FOUND:')
    for (day, session, room), count in room_conflicts.items():
        print(f'   {day} Sesi {session} Ruang {room}: {count} courses')
        conflicted = df[(df['Hari']==day) & (df['Sesi']==session) & (df['Ruang']==room)]
        for _, row in conflicted.iterrows():
            print(f'     - {row["Prodi"]} {row["Mata Kuliah"]}')
else:
    print('✅ NO ROOM CONFLICTS')

# 2. Instructor conflicts check
print('\n👨‍🏫 INSTRUCTOR CONFLICT CHECK:')
slot_conflicts = defaultdict(lambda: defaultdict(list))

for idx, row in df.iterrows():
    day = row['Hari']
    sesi = row['Sesi']
    if not day or not sesi:
        continue
    key = (day, int(sesi))

    # Check both Dosen 1 and Dosen 2
    for col in ['Dosen 1', 'Dosen 2']:
        dosen = str(row[col]).strip() if pd.notna(row[col]) else ''
        if dosen and dosen != '' and dosen != 'nan':
            slot_conflicts[key][dosen].append({
                'idx': idx,
                'prodi': row['Prodi'],
                'mk': row['Mata Kuliah'],
                'kelas': row['Kelas']
            })

instr_conflicts_found = False
for (day, session), instructors in slot_conflicts.items():
    for instructor, classes in instructors.items():
        if len(classes) > 1:
            if not instr_conflicts_found:
                print('❌ INSTRUCTOR CONFLICTS FOUND:')
                instr_conflicts_found = True
            print(f'   {day} Sesi {session} - {instructor}:')
            for cls in classes:
                print(f'     - {cls["prodi"]} {cls["mk"]} ({cls["kelas"]})')

if not instr_conflicts_found:
    print('✅ NO INSTRUCTOR CONFLICTS')

print('\n📋 DOSEN COLUMN STATUS:')
# Check Dosen 1 and Dosen 2 filling
dosen1_filled = df['Dosen 1'].notna() & (df['Dosen 1'] != '') & (df['Dosen 1'] != 'nan')
dosen2_filled = df['Dosen 2'].notna() & (df['Dosen 2'] != '') & (df['Dosen 2'] != 'nan')

print(f'   Dosen 1 filled: {dosen1_filled.sum()}/{len(df)} ({(dosen1_filled.sum()/len(df)*100):.1f}%)')
print(f'   Dosen 2 filled: {dosen2_filled.sum()}/{len(df)} ({(dosen2_filled.sum()/len(df)*100):.1f}%)')

# Check by prodi
print('\n📊 DOSEN FILLING BY PRODI:')
for prodi in df['Prodi'].unique():
    prodi_df = df[df['Prodi'] == prodi]
    d1_filled = (prodi_df['Dosen 1'].notna() & (prodi_df['Dosen 1'] != '') & (prodi_df['Dosen 1'] != 'nan')).sum()
    d2_filled = (prodi_df['Dosen 2'].notna() & (prodi_df['Dosen 2'] != '') & (prodi_df['Dosen 2'] != 'nan')).sum()
    total = len(prodi_df)
    print(f'   {prodi:12}: D1={d1_filled:3}/{total:3} ({d1_filled/total*100:4.1f}%) | D2={d2_filled:3}/{total:3} ({d2_filled/total*100:4.1f}%)')

# Sample courses with missing instructors
print('\n❓ COURSES WITH MISSING INSTRUCTORS (first 10):')
missing_instructors = df[(~dosen1_filled) & (~dosen2_filled)]
for i, (_, row) in enumerate(missing_instructors.head(10).iterrows()):
    print(f'   {i+1:2}. {row["Prodi"]:12} | {row["Mata Kuliah"]:40}')

if len(missing_instructors) > 10:
    print(f'   ... and {len(missing_instructors)-10} more courses without instructors')

print(f'\n📈 SUMMARY:')
print(f'   Total courses: {len(df)}')
print(f'   Missing instructors: {len(missing_instructors)} courses')
print(f'   Courses with D1 only: {(dosen1_filled & ~dosen2_filled).sum()} courses')
print(f'   Courses with both D1&D2: {(dosen1_filled & dosen2_filled).sum()} courses')