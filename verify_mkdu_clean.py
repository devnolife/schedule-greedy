import pandas as pd

file = 'jadwal_gabungan_SATU_TABEL_FINAL_PWK_ARS.xlsx'
df = pd.read_excel(file, sheet_name='Jadwal Induk (Gabungan)')

print('🧹 VERIFIKASI PEMBERSIHAN MKDU DARI SEMUA PRODI')
print('=' * 60)

# Define MKDU keywords to identify MKDU courses
mkdu_keywords = [
    'pancasila', 'bahasa indonesia', 'pendidikan agama', 'bahasa inggris',
    'bahasa arab', 'aik', 'aqidah islam', 'komprehensif aik'
]

print('📊 MKDU COURSES ANALYSIS AFTER CLEANUP:')
print()

total_before = 490  # Before cleanup
total_after = len(df)
mkdu_removed = total_before - total_after

print(f'📈 TOTAL COURSES:')
print(f'   Before cleanup: {total_before} courses')
print(f'   After cleanup : {total_after} courses')
print(f'   MKDU removed  : {mkdu_removed} courses')
print()

for prodi in ['Informatika', 'PWK', 'Elektro', 'Pengairan', 'Arsitektur', 'MKDU']:
    prodi_data = df[df['Prodi'] == prodi]
    mkdu_in_prodi = []

    for _, row in prodi_data.iterrows():
        mk = str(row['Mata Kuliah']).lower()
        if any(keyword in mk for keyword in mkdu_keywords):
            mkdu_in_prodi.append({
                'mk': row['Mata Kuliah'],
                'kode': row['Kode MK'],
                'semester': row['Semester']
            })

    status = '✅ CLEAN' if len(mkdu_in_prodi) == 0 else '❌ HAS MKDU'

    print(f'🎓 {prodi.upper()}:')
    print(f'   Total courses: {len(prodi_data):3}')
    print(f'   MKDU courses : {len(mkdu_in_prodi):3} {status}')

    if len(mkdu_in_prodi) > 0:
        print(f'   Remaining MKDU courses:')
        for i, course in enumerate(mkdu_in_prodi[:5], 1):
            print(f'     {i}. {course["mk"][:35]:35} | Sem {course["semester"]} | {course["kode"]}')
        if len(mkdu_in_prodi) > 5:
            print(f'     ... and {len(mkdu_in_prodi)-5} more')
    print()

# Summary
non_mkdu_prodi = ['Informatika', 'PWK', 'Elektro', 'Pengairan', 'Arsitektur']
clean_count = 0
for prodi in non_mkdu_prodi:
    prodi_data = df[df['Prodi'] == prodi]
    has_mkdu = any(any(keyword in str(row['Mata Kuliah']).lower() for keyword in mkdu_keywords)
                   for _, row in prodi_data.iterrows())
    if not has_mkdu:
        clean_count += 1

print(f'🎯 CLEANUP SUMMARY:')
print(f'   Non-MKDU prodi cleaned: {clean_count}/5 ✅')
print(f'   MKDU courses only in MKDU prodi: {"✅ SUCCESS" if clean_count == 5 else "❌ FAILED"}')

# Check MKDU prodi has courses
mkdu_data = df[df['Prodi'] == 'MKDU']
mkdu_course_count = len(mkdu_data)
print(f'   MKDU prodi has {mkdu_course_count} courses: {"✅ GOOD" if mkdu_course_count > 0 else "❌ EMPTY"}')

if clean_count == 5 and mkdu_course_count > 0:
    print(f'\n🎉 ✅ SUCCESS: MKDU separation complete!')
    print(f'   All non-MKDU prodi are clean, MKDU courses only in MKDU sheet')
else:
    print(f'\n⚠️  ❌ Issues detected, cleanup incomplete')