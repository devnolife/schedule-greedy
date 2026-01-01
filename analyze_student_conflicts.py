import pandas as pd

file = 'jadwal_gabungan_SATU_TABEL_FINAL_PWK_ARS.xlsx'
df = pd.read_excel(file, sheet_name='Jadwal Induk (Gabungan)')

print('🔍 ANALISIS KONFLIK MAHASISWA (STUDENT CONFLICTS)')
print('=' * 60)

# Group by Prodi, Semester, Kelas, Hari, Sesi to find conflicts
conflicts = []

for (prodi, semester, kelas), group in df.groupby(['Prodi', 'Semester', 'Kelas']):
    for (hari, sesi), time_group in group.groupby(['Hari', 'Sesi']):
        if len(time_group) > 1:
            course_list = []
            for _, row in time_group.iterrows():
                mk = str(row['Mata Kuliah']) if pd.notna(row['Mata Kuliah']) else 'N/A'
                ruang = str(row['Ruang']) if pd.notna(row['Ruang']) else 'N/A'
                dosen = str(row['Dosen 1']) if pd.notna(row['Dosen 1']) else 'N/A'
                course_list.append([mk, ruang, dosen])

            conflicts.append({
                'prodi': prodi,
                'semester': semester,
                'kelas': kelas,
                'hari': hari,
                'sesi': sesi,
                'courses': course_list
            })

print(f'📊 TOTAL STUDENT CONFLICTS FOUND: {len(conflicts)}')
print()

if len(conflicts) > 0:
    print('❌ STUDENT CONFLICTS DETECTED:')
    print()
    for i, conflict in enumerate(conflicts[:15], 1):
        print(f'{i:2}. CONFLICT: {conflict["prodi"]} Semester {conflict["semester"]} Kelas {conflict["kelas"]}')
        print(f'    Time: {conflict["hari"]} Sesi {conflict["sesi"]}')
        for j, course in enumerate(conflict['courses'], 1):
            mk, ruang, dosen = course
            print(f'      {j}. {mk[:40]:40} | R:{ruang:10} | {dosen[:20]:20}')
        print()

    if len(conflicts) > 15:
        print(f'    ... and {len(conflicts)-15} more conflicts')

    print(f'🎯 ROOT CAUSE:')
    print(f'   Same students (Prodi + Semester + Kelas) scheduled at same time')
    print(f'   Students cannot be in multiple places simultaneously')
    print(f'   Current algorithm only checks room+instructor conflicts, not student conflicts')
    print(f'   Need to add student conflict prevention to scheduling algorithm')
else:
    print('✅ NO STUDENT CONFLICTS - Schedule is valid for students')

print(f'\n📈 CONFLICT STATISTICS BY PRODI:')
prodi_conflicts = {}
for conflict in conflicts:
    prodi = conflict['prodi']
    prodi_conflicts[prodi] = prodi_conflicts.get(prodi, 0) + 1

for prodi in ['Informatika', 'PWK', 'Elektro', 'Pengairan', 'Arsitektur', 'MKDU']:
    count = prodi_conflicts.get(prodi, 0)
    status = '❌' if count > 0 else '✅'
    print(f'  {prodi:12}: {count:3} conflicts {status}')

print(f'\n💡 SOLUTION NEEDED:')
print(f'   1. Add student conflict detection to place_one() function')
print(f'   2. Check if (prodi, semester, kelas) already has course at (hari, sesi)')
print(f'   3. Skip time slots that would create student conflicts')
print(f'   4. This will ensure no student is double-booked')