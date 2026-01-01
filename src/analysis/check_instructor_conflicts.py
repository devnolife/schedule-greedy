import pandas as pd
from collections import defaultdict

file = 'jadwal_gabungan_SATU_TABEL_FINAL_PWK_ARS.xlsx'
df = pd.read_excel(file, sheet_name='Jadwal Induk (Gabungan)')

print('🔍 ANALISIS INSTRUCTOR CONFLICTS DETAIL')
print('=' * 50)

# Filter scheduled courses only
scheduled_df = df[(df['Hari'].notna()) & (df['Hari'] != '') & (df['Sesi'].notna()) & (df['Sesi'] != '')]

print(f'📊 CHECKING {len(scheduled_df)} SCHEDULED COURSES')
print()

# Check instructor conflicts based on D1 only (new logic)
instructor_map = defaultdict(list)

for i, row in scheduled_df.iterrows():
    hari = row['Hari']
    sesi = row['Sesi']
    if pd.notna(hari) and pd.notna(sesi):
        key = (hari, sesi)

        # Only check D1 for conflicts - D2 is backup
        dosen1 = str(row['Dosen 1']).strip() if pd.notna(row['Dosen 1']) else ''

        if dosen1 and dosen1.lower() not in ['nan', 'n/a', '']:
            instructor_map[(key, dosen1)].append(i)

conflicts = [(key_dosen, idxs) for key_dosen, idxs in instructor_map.items() if len(idxs) > 1]

print(f'👨‍🏫 INSTRUCTOR CONFLICTS FOUND: {len(conflicts)}')

if len(conflicts) > 0:
    print('\n❌ CONFLICT DETAILS:')
    for i, ((time_key, dosen), course_idxs) in enumerate(conflicts[:10], 1):
        hari, sesi = time_key
        print(f'\n{i:2}. CONFLICT: {hari} Sesi {sesi} - {dosen}')

        for j, idx in enumerate(course_idxs, 1):
            course_row = scheduled_df.loc[idx]
            prodi = course_row['Prodi']
            mk = str(course_row['Mata Kuliah'])[:40]
            kelas = course_row['Kelas']
            ruang = course_row['Ruang']
            dosen2 = str(course_row['Dosen 2']).strip() if pd.notna(course_row['Dosen 2']) else ''

            print(f'      {j}. {prodi:12} | {mk:40} | {kelas:8} | R:{ruang:8} | D2:{dosen2[:15]:15}')

    if len(conflicts) > 10:
        print(f'       ... and {len(conflicts)-10} more conflicts')

print(f'\n🔍 ROOT CAUSE ANALYSIS:')
print(f'   These conflicts mean the same D1 (primary instructor) is teaching')
print(f'   multiple courses at the same time, which is impossible.')
print(f'   D2 is correctly ignored as backup/replacement.')

print(f'\n💡 POSSIBLE CAUSES:')
print(f'   1. Same instructor really assigned to multiple courses at same time')
print(f'   2. Data inconsistency in instructor names')
print(f'   3. Scheduling algorithm needs further refinement')

# Check if these are legitimate conflicts or data issues
if len(conflicts) > 0:
    print(f'\n📋 SAMPLE CONFLICT ANALYSIS:')
    (time_key, dosen), course_idxs = conflicts[0]
    hari, sesi = time_key

    print(f'   Example: {dosen} at {hari} Sesi {sesi}')
    print(f'   Teaching {len(course_idxs)} courses simultaneously:')

    for idx in course_idxs:
        course_row = scheduled_df.loc[idx]
        print(f'     - {course_row["Prodi"]} {course_row["Semester"]} {course_row["Kelas"]}: {course_row["Mata Kuliah"]}')

    print(f'   This appears to be a genuine conflict that needs resolution.')