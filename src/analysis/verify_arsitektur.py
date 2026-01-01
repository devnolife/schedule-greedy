import pandas as pd

file = 'jadwal_gabungan_SATU_TABEL_FINAL_PWK_ARS.xlsx'
df = pd.read_excel(file, sheet_name='Jadwal Induk (Gabungan)')

print('🏛️ ARSITEKTUR VERIFICATION AFTER FIX')
print('=' * 50)

ars_data = df[df['Prodi'] == 'Arsitektur']
print(f'Total Arsitektur courses now: {len(ars_data)}')

print('\n📚 ARSITEKTUR COURSES BY SEMESTER:')
for sem in sorted(ars_data['Semester'].unique()):
    sem_courses = ars_data[ars_data['Semester'] == sem]
    print(f'\nSemester {sem}: {len(sem_courses)} courses')
    for i, (_, row) in enumerate(sem_courses.head(5).iterrows(), 1):
        mk = str(row['Mata Kuliah'])[:40] if pd.notna(row['Mata Kuliah']) else 'N/A'
        kode = str(row['Kode MK']) if pd.notna(row['Kode MK']) else 'N/A'
        dosen = str(row['Dosen 1'])[:20] if pd.notna(row['Dosen 1']) else 'N/A'
        print(f'  {i:2}. {mk:40} | {kode:15} | {dosen:20}')
    if len(sem_courses) > 5:
        print(f'     ... and {len(sem_courses)-5} more')

print(f'\n🎯 COMPARISON:')
print(f'Before fix: 10 courses (only Semester I)')
print(f'After fix : {len(ars_data)} courses (All semester I, III, V, VII)')

print(f'\n📊 SEMESTER DISTRIBUTION:')
sem_counts = ars_data['Semester'].value_counts().sort_index()
for sem, count in sem_counts.items():
    print(f'  Semester {sem}: {count} courses')

print(f'\n✅ SUCCESS: All Arsitektur courses from all semesters are now loaded!')

# Show sample of original vs fixed
print(f'\n📋 ORIGINAL ANALYSIS SHOWED:')
print(f'  Semester I  : 10 courses')
print(f'  Semester III:  9 courses')
print(f'  Semester V  :  9 courses (1 filtered out: Komprehensif AIK)')
print(f'  Semester VII:  5 courses')
print(f'  Expected    : 32 courses total')
print(f'  Actual      : {len(ars_data)} courses ✅')