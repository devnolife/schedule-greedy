import pandas as pd

file = 'jadwal_gabungan_SATU_TABEL_FINAL_PWK_ARS.xlsx'
xl = pd.ExcelFile(file)

print('📅 JADWAL KULIAH SEMESTER GANJIL 2025-2026')
print('=' * 50)

print(f'\n📊 SUMMARY OUTPUT FILE:')
print(f'File: {file}')
print(f'Total Sheets: {len(xl.sheet_names)}')

print(f'\n📋 AVAILABLE SHEETS:')
for i, sheet in enumerate(xl.sheet_names, 1):
    print(f'{i:2}. {sheet}')

# Main schedule verification
df = pd.read_excel(file, sheet_name='Jadwal Induk (Gabungan)')
print(f'\n📈 PROGRAM STUDI DISTRIBUTION:')
prodi_counts = df['Prodi'].value_counts()
total = len(df)

for prodi, count in prodi_counts.items():
    percentage = (count/total)*100
    print(f'   {prodi:15}: {count:3} courses ({percentage:5.1f}%)')

print(f'\n   TOTAL COURSES   : {total:3} courses')

# Detailed verification for each prodi
print(f'\n📚 DETAILED PRODI VERIFICATION:')

for prodi in ['Informatika', 'PWK', 'Elektro', 'Pengairan', 'Arsitektur', 'MKDU']:
    prodi_data = df[df['Prodi'] == prodi]
    if len(prodi_data) > 0:
        sheet_name = f'Jadwal {prodi.upper()}'
        if sheet_name in xl.sheet_names:
            sheet_data = pd.read_excel(file, sheet_name=sheet_name, header=None, skiprows=12)
            print(f'   ✅ {prodi:15}: {len(prodi_data):3} courses (Sheet: {len(sheet_data)} rows)')
        else:
            print(f'   ❌ {prodi:15}: {len(prodi_data):3} courses (Sheet: MISSING)')
    else:
        print(f'   ❌ {prodi:15}:   0 courses (NOT FOUND)')

# Conflict verification
conflicts = pd.read_excel(file, sheet_name='Ringkasan Konflik')
print(f'\n⚡ CONFLICT STATUS:')
for _, row in conflicts.iterrows():
    status = '✅ CLEAR' if row['Value'] == 0 else f'❌ {row["Value"]} FOUND'
    print(f'   {row["Metric"]:25}: {status}')

# Arsitektur detail check
print(f'\n🏛️  ARSITEKTUR COURSE SAMPLES:')
ars_data = df[df['Prodi'] == 'Arsitektur']
for i, (_, row) in enumerate(ars_data.head(5).iterrows(), 1):
    day = row['Hari'] if pd.notna(row['Hari']) else 'TBD'
    time = row['Jam'] if pd.notna(row['Jam']) else 'TBD'
    room = row['Ruang'] if pd.notna(row['Ruang']) and row['Ruang'] != '' else 'Zoom'
    print(f'   {i}. {row["Mata Kuliah"]:35} | {day:8} {time:12} | {room}')

if len(ars_data) > 5:
    print(f'   ... and {len(ars_data)-5} more courses')

print(f'\n🎯 STATUS: SCHEDULE GENERATION COMPLETE!')
print(f'📁 Output saved to: {file}')