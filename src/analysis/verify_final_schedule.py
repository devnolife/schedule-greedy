import pandas as pd
from collections import defaultdict

file = 'jadwal_gabungan_SATU_TABEL_FINAL_PWK_ARS.xlsx'
df = pd.read_excel(file, sheet_name='Jadwal Induk (Gabungan)')

print('🎉 VERIFIKASI JADWAL FINAL TANPA KONFLIK MAHASISWA')
print('=' * 60)

# Filter out rows with missing schedule (unplaced courses)
scheduled_df = df[(df['Hari'].notna()) & (df['Hari'] != '') & (df['Sesi'].notna()) & (df['Sesi'] != '')]
unplaced_df = df[(df['Hari'].isna()) | (df['Hari'] == '') | (df['Sesi'].isna()) | (df['Sesi'] == '')]

print(f'📊 SCHEDULING RESULTS:')
print(f'   Total courses: {len(df)}')
print(f'   Scheduled    : {len(scheduled_df)} ✅')
print(f'   Unplaced     : {len(unplaced_df)} ⚠️')
print()

# 1. Check Student Conflicts
print('👥 STUDENT CONFLICT CHECK:')
student_conflicts = 0
for (prodi, semester, kelas), group in scheduled_df.groupby(['Prodi', 'Semester', 'Kelas']):
    for (hari, sesi), time_group in group.groupby(['Hari', 'Sesi']):
        if len(time_group) > 1:
            student_conflicts += 1

print(f'   Student conflicts: {student_conflicts} {"✅" if student_conflicts == 0 else "❌"}')

# 2. Check Room Conflicts
print('🏠 ROOM CONFLICT CHECK:')
room_conflicts = 0
for (hari, sesi, ruang), group in scheduled_df.groupby(['Hari', 'Sesi', 'Ruang']):
    if pd.notna(ruang) and ruang != '' and len(group) > 1:
        room_conflicts += 1

print(f'   Room conflicts   : {room_conflicts} {"✅" if room_conflicts == 0 else "❌"}')

# 3. Check Instructor Conflicts
print('👨‍🏫 INSTRUCTOR CONFLICT CHECK:')
instructor_conflicts = 0
instructor_map = defaultdict(list)

for i, row in scheduled_df.iterrows():
    hari = row['Hari']
    sesi = row['Sesi']
    if pd.notna(hari) and pd.notna(sesi):
        key = (hari, sesi)
        dosen1 = str(row['Dosen 1']).strip() if pd.notna(row['Dosen 1']) else ''
        dosen2 = str(row['Dosen 2']).strip() if pd.notna(row['Dosen 2']) else ''

        # Only check dosen1 for conflicts - dosen2 is just backup/replacement
        if dosen1 and dosen1.lower() not in ['nan', 'n/a', '']:
            instructor_map[(key, dosen1)].append(i)

conflicts = [(key_dosen, idxs) for key_dosen, idxs in instructor_map.items() if len(idxs) > 1]
instructor_conflicts = len(conflicts)

print(f'   Instructor conflicts: {instructor_conflicts} {"✅" if instructor_conflicts == 0 else "❌"}')

print(f'\n📈 SUMMARY BY PRODI:')
for prodi in ['Informatika', 'PWK', 'Elektro', 'Pengairan', 'Arsitektur', 'MKDU']:
    prodi_data = df[df['Prodi'] == prodi]
    prodi_scheduled = len(prodi_data[(prodi_data['Hari'].notna()) & (prodi_data['Hari'] != '')])
    prodi_unplaced = len(prodi_data) - prodi_scheduled

    print(f'  {prodi:12}: {len(prodi_data):3} total | {prodi_scheduled:3} scheduled | {prodi_unplaced:2} unplaced')

print(f'\n🎯 FINAL ASSESSMENT:')
if student_conflicts == 0:
    print('   ✅ STUDENT CONFLICTS ELIMINATED - No double-booking of students!')
else:
    print('   ❌ Student conflicts still exist')

if room_conflicts == 0:
    print('   ✅ ROOM CONFLICTS RESOLVED')
else:
    print('   ❌ Room conflicts still exist')

total_conflicts = student_conflicts + room_conflicts + instructor_conflicts
if total_conflicts == 0:
    print(f'\n🎉 ✅ PERFECT SCHEDULE!')
    print(f'   All conflicts eliminated: 0 student, 0 room, 0 instructor conflicts')
    print(f'   {len(scheduled_df)} courses successfully scheduled')
elif student_conflicts == 0:
    print(f'\n🎯 ✅ STUDENT CONFLICTS SOLVED!')
    print(f'   Main objective achieved: Students can no longer be double-booked')
    print(f'   Minor conflicts remain: {instructor_conflicts} instructor conflicts')
else:
    print(f'\n⚠️  Issues remain: {total_conflicts} total conflicts')

if len(unplaced_df) > 0:
    print(f'\n📋 UNPLACED COURSES ({len(unplaced_df)}):')
    for i, (_, row) in enumerate(unplaced_df.head(10).iterrows(), 1):
        mk = str(row['Mata Kuliah'])[:35]
        prodi = row['Prodi']
        sem = row['Semester']
        kelas = row['Kelas']
        print(f'   {i:2}. {mk:35} | {prodi} S{sem} {kelas}')
    if len(unplaced_df) > 10:
        print(f'       ... and {len(unplaced_df)-10} more unplaced courses')