import pandas as pd
from collections import defaultdict

file = 'jadwal_gabungan_SATU_TABEL_FINAL_PWK_ARS.xlsx'
df = pd.read_excel(file, sheet_name='Jadwal Induk (Gabungan)')

print('🔍 COMPREHENSIVE CONFLICT ANALYSIS')
print('=' * 60)
print(f'Total courses to analyze: {len(df)}')

# ============================================
# 1. ROOM CONFLICT CHECK (DETAILED)
# ============================================
print('\n🏠 ROOM CONFLICT CHECK (DETAILED):')
print('-' * 40)

room_schedule = defaultdict(list)
room_conflicts = []

for idx, row in df.iterrows():
    day = row['Hari']
    sesi = row['Sesi']
    ruang = row['Ruang']
    mode = str(row['Mode (Zoom/Luring)']).lower()

    # Skip if Zoom or empty room
    if 'zoom' in mode or not ruang or str(ruang).strip() == '':
        continue

    key = (day, int(sesi), ruang)
    room_schedule[key].append({
        'idx': idx,
        'prodi': row['Prodi'],
        'mk': row['Mata Kuliah'],
        'kelas': row['Kelas'],
        'jam': row['Jam'],
        'dosen1': row['Dosen 1'],
        'dosen2': row['Dosen 2']
    })

# Find conflicts
for key, courses in room_schedule.items():
    if len(courses) > 1:
        room_conflicts.append((key, courses))

if room_conflicts:
    print(f'❌ ROOM CONFLICTS FOUND: {len(room_conflicts)}')
    for i, ((day, sesi, ruang), courses) in enumerate(room_conflicts, 1):
        print(f'\n{i}. CONFLICT: {day} Sesi {sesi} Ruang {ruang}')
        for j, course in enumerate(courses, 1):
            print(f'   {j}. {course["prodi"]:12} | {course["mk"][:40]:40} | {course["kelas"]:8} | {course["jam"]}')
else:
    print('✅ NO ROOM CONFLICTS FOUND')

# ============================================
# 2. INSTRUCTOR CONFLICT CHECK (DETAILED)
# ============================================
print('\n👨‍🏫 INSTRUCTOR CONFLICT CHECK (DETAILED):')
print('-' * 40)

instructor_schedule = defaultdict(list)
instructor_conflicts = []

for idx, row in df.iterrows():
    day = row['Hari']
    sesi = row['Sesi']

    if not day or not sesi:
        continue

    key = (day, int(sesi))

    # Check both Dosen 1 and Dosen 2
    for col_name in ['Dosen 1', 'Dosen 2']:
        dosen = str(row[col_name]).strip() if pd.notna(row[col_name]) else ''
        if dosen and dosen != '' and dosen != 'nan':
            instructor_schedule[(key, dosen)].append({
                'idx': idx,
                'prodi': row['Prodi'],
                'mk': row['Mata Kuliah'],
                'kelas': row['Kelas'],
                'jam': row['Jam'],
                'ruang': row['Ruang'],
                'dosen_col': col_name
            })

# Find instructor conflicts
for (key, dosen), courses in instructor_schedule.items():
    if len(courses) > 1:
        instructor_conflicts.append(((key, dosen), courses))

if instructor_conflicts:
    print(f'❌ INSTRUCTOR CONFLICTS FOUND: {len(instructor_conflicts)}')
    for i, (((day, sesi), dosen), courses) in enumerate(instructor_conflicts, 1):
        print(f'\n{i}. CONFLICT: {day} Sesi {sesi} - {dosen}')
        for j, course in enumerate(courses, 1):
            print(f'   {j}. {course["prodi"]:12} | {course["mk"][:40]:40} | {course["kelas"]:8} | R:{course["ruang"]:10} | {course["dosen_col"]}')
else:
    print('✅ NO INSTRUCTOR CONFLICTS FOUND')

# ============================================
# 3. TIME SLOT UTILIZATION ANALYSIS
# ============================================
print('\n⏰ TIME SLOT UTILIZATION ANALYSIS:')
print('-' * 40)

days = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
sessions = [1, 2, 3, 4, 5]

time_utilization = defaultdict(int)
for _, row in df.iterrows():
    day = row['Hari']
    sesi = row['Sesi']
    if day and sesi:
        time_utilization[(day, int(sesi))] += 1

print('Courses per time slot:')
for day in days:
    if any(time_utilization.get((day, s), 0) > 0 for s in sessions):
        print(f'  {day:8}:', end='')
        for sesi in sessions:
            count = time_utilization.get((day, sesi), 0)
            print(f' S{sesi}:{count:2}', end='')
        print()

# ============================================
# 4. ROOM UTILIZATION ANALYSIS
# ============================================
print('\n🏫 ROOM UTILIZATION ANALYSIS:')
print('-' * 40)

room_usage = defaultdict(int)
for _, row in df.iterrows():
    ruang = row['Ruang']
    mode = str(row['Mode (Zoom/Luring)']).lower()
    if ruang and 'zoom' not in mode:
        room_usage[ruang] += 1

print('Top room usage:')
sorted_rooms = sorted(room_usage.items(), key=lambda x: x[1], reverse=True)
for i, (room, count) in enumerate(sorted_rooms[:15], 1):
    print(f'  {i:2}. {room:20}: {count:3} courses')

# ============================================
# 5. SCHEDULE COMPLETENESS CHECK
# ============================================
print('\n📋 SCHEDULE COMPLETENESS CHECK:')
print('-' * 40)

missing_schedule = df[(df['Hari'].isna() | (df['Hari'] == '')) |
                     (df['Sesi'].isna() | (df['Sesi'] == ''))]

if len(missing_schedule) > 0:
    print(f'❌ COURSES WITHOUT SCHEDULE: {len(missing_schedule)}')
    for i, (_, row) in enumerate(missing_schedule.head(10).iterrows(), 1):
        print(f'   {i:2}. {row["Prodi"]:12} | {row["Mata Kuliah"][:40]:40}')
    if len(missing_schedule) > 10:
        print(f'   ... and {len(missing_schedule)-10} more')
else:
    print('✅ ALL COURSES HAVE SCHEDULE')

# ============================================
# 6. SUMMARY REPORT
# ============================================
print('\n📊 CONFLICT SUMMARY REPORT:')
print('=' * 40)
print(f'Total courses analyzed    : {len(df)}')
print(f'Room conflicts           : {len(room_conflicts)}')
print(f'Instructor conflicts     : {len(instructor_conflicts)}')
print(f'Unscheduled courses      : {len(missing_schedule)}')
print(f'Unique rooms used        : {len(room_usage)}')
print(f'Active time slots        : {len([k for k, v in time_utilization.items() if v > 0])}')

if len(room_conflicts) == 0 and len(instructor_conflicts) == 0 and len(missing_schedule) == 0:
    print('\n🎉 ✅ SCHEDULE IS CONFLICT-FREE!')
    print('   No room conflicts, no instructor conflicts, all courses scheduled.')
else:
    print('\n⚠️  ❌ CONFLICTS DETECTED!')
    print('   Please review the conflicts above and fix them.')

print(f'\n📁 Analysis complete for: {file}')