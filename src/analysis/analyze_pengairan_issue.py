import pandas as pd

file = 'jadwal_gabungan_SATU_TABEL_FINAL_PWK_ARS.xlsx'
df = pd.read_excel(file, sheet_name='Jadwal Induk (Gabungan)')

print('🔍 ANALISIS MASALAH PENGAIRAN')
print('=' * 50)

# Focus on Pengairan
pengairan_data = df[df['Prodi'] == 'Pengairan']
unplaced_pengairan = pengairan_data[(pengairan_data['Hari'].isna()) | (pengairan_data['Hari'] == '')]

print(f'📊 PENGAIRAN OVERVIEW:')
print(f'   Total courses: {len(pengairan_data)}')
print(f'   Scheduled   : {len(pengairan_data) - len(unplaced_pengairan)}')
print(f'   Unplaced    : {len(unplaced_pengairan)}')
print()

if len(unplaced_pengairan) > 0:
    print('❌ UNPLACED PENGAIRAN COURSES:')
    for i, (_, row) in enumerate(unplaced_pengairan.iterrows(), 1):
        mk = str(row['Mata Kuliah'])[:40]
        semester = row['Semester']
        kelas = row['Kelas']
        dosen = str(row['Dosen 1'])[:25] if pd.notna(row['Dosen 1']) else 'N/A'
        mode = row['Mode'] if pd.notna(row['Mode']) else 'N/A'
        print(f'   {i}. {mk:40} | S{semester} {kelas:10} | {dosen:25} | {mode}')
    print()

# Analyze why they're unplaced
print('🔍 ROOT CAUSE ANALYSIS:')

# Check if it's weekend-only issue
weekend_courses = pengairan_data[pengairan_data['Kelas'].str.contains('NR', na=False)]
print(f'   Non-Reguler courses: {len(weekend_courses)} (should go to weekend)')

# Check semester distribution
sem_dist = pengairan_data['Semester'].value_counts().sort_index()
print(f'   Semester distribution:')
for sem, count in sem_dist.items():
    sem_scheduled = len(pengairan_data[(pengairan_data['Semester'] == sem) &
                                      (pengairan_data['Hari'].notna()) &
                                      (pengairan_data['Hari'] != '')])
    sem_unplaced = count - sem_scheduled
    print(f'     Semester {sem}: {count} total | {sem_scheduled} scheduled | {sem_unplaced} unplaced')

# Check class distribution
print(f'   Class distribution:')
class_dist = pengairan_data['Kelas'].value_counts()
for kelas, count in class_dist.head(10).items():
    kelas_scheduled = len(pengairan_data[(pengairan_data['Kelas'] == kelas) &
                                        (pengairan_data['Hari'].notna()) &
                                        (pengairan_data['Hari'] != '')])
    kelas_unplaced = count - kelas_scheduled
    status = '❌' if kelas_unplaced > 0 else '✅'
    print(f'     {kelas:15}: {count} total | {kelas_scheduled} scheduled | {kelas_unplaced} unplaced {status}')

# Check if weekend slots are full
weekend_data = df[df['Hari'].isin(['Sabtu', 'Minggu'])]
print(f'\n📅 WEEKEND UTILIZATION:')
print(f'   Total weekend courses: {len(weekend_data)}')
weekend_by_prodi = weekend_data['Prodi'].value_counts()
for prodi, count in weekend_by_prodi.items():
    print(f'     {prodi}: {count} courses')

# Check weekend capacity
print(f'\n📊 WEEKEND CAPACITY ANALYSIS:')
weekend_schedule = weekend_data.groupby(['Hari', 'Sesi']).size()
print(f'   Weekend time slots used:')
for (hari, sesi), count in weekend_schedule.items():
    print(f'     {hari} Sesi {sesi}: {count} courses')

# Check specific unplaced courses for conflicts
if len(unplaced_pengairan) > 0:
    print(f'\n🔍 WHY THESE COURSES ARE UNPLACED:')
    for i, (_, row) in enumerate(unplaced_pengairan.iterrows(), 1):
        mk = str(row['Mata Kuliah'])
        semester = row['Semester']
        kelas = row['Kelas']
        is_nr = 'NR' in str(kelas)

        print(f'   {i}. {mk[:30]:30} | S{semester} {kelas}')
        print(f'      Non-Reguler: {"Yes" if is_nr else "No"} (weekend required: {"Yes" if is_nr else "No"})')

        # Check if same student group has other courses
        same_students = pengairan_data[
            (pengairan_data['Semester'] == semester) &
            (pengairan_data['Kelas'] == kelas) &
            (pengairan_data['Hari'].notna()) &
            (pengairan_data['Hari'] != '')
        ]
        if len(same_students) > 0:
            print(f'      Same student group has {len(same_students)} other scheduled courses')
            time_slots_used = same_students[['Hari', 'Sesi']].drop_duplicates()
            print(f'      Time slots occupied by same students:')
            for _, slot in time_slots_used.iterrows():
                print(f'        {slot["Hari"]} Sesi {slot["Sesi"]}')
        print()