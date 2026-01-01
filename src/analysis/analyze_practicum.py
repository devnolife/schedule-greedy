import pandas as pd

file = 'jadwal_gabungan_SATU_TABEL_FINAL_PWK_ARS.xlsx'
df = pd.read_excel(file, sheet_name='Jadwal Induk (Satu Tabel)')

print('=== DETAILED INFORMATIKA PRACTICUM ANALYSIS ===')
informatika_df = df[df['Prodi'] == 'Informatika']
practicum_keywords = ['praktikum', 'praktek', 'lab ', 'laboratorium']

practicum_courses = []
for _, row in informatika_df.iterrows():
    mk = str(row['Mata Kuliah']).lower()
    if any(keyword in mk for keyword in practicum_keywords):
        practicum_courses.append(row)

# Separate by semester and mode
sem1_zoom = [c for c in practicum_courses if str(c['Semester']) == '1']
others = [c for c in practicum_courses if str(c['Semester']) != '1']

print(f'Semester 1 (Zoom): {len(sem1_zoom)}')
print(f'Other semesters: {len(others)}')

print(f'\n=== SEMESTER 1 PRACTICUM (should be Zoom) ===')
for course in sem1_zoom[:5]:
    print(f'{course["Mata Kuliah"]:50} | Mode: {course["Mode (Zoom/Luring)"]:10} | Room: {course["Ruang"]}')

print(f'\n=== OTHER SEMESTER PRACTICUM (should use labs) ===')
for course in others[:5]:
    room = course['Ruang'] if pd.notna(course['Ruang']) else 'EMPTY'
    dosen = course['Dosen 1'] if pd.notna(course['Dosen 1']) else 'NO DOSEN'
    print(f'{course["Mata Kuliah"]:50} | Room: {room:15} | Dosen: {dosen}')

print(f'\n=== ROOM USAGE SUMMARY ===')
all_rooms = [c['Ruang'] for c in others if pd.notna(c['Ruang'])]
from collections import Counter
room_counts = Counter(all_rooms)
for room, count in room_counts.items():
    print(f'{room:20}: {count}')

print(f'\n=== SUCCESS METRICS ===')
no_dosen_count = sum(1 for c in practicum_courses if pd.isna(c['Dosen 1']) or str(c['Dosen 1']).strip() == '')
lab_only_count = sum(1 for c in others if pd.notna(c['Ruang']) and c['Ruang'] in ['Lab Pemrograman', 'Lab Jaringan'])
print(f'Practicum courses without instructor: {no_dosen_count}/{len(practicum_courses)}')
print(f'Non-semester-1 practicum in labs only: {lab_only_count}/{len(others)}')