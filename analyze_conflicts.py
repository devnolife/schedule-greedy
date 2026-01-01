import pandas as pd

file = 'jadwal_gabungan_SATU_TABEL_FINAL_PWK_ARS.xlsx'
df = pd.read_excel(file, sheet_name='Jadwal Induk (Satu Tabel)')
conflicts = pd.read_excel(file, sheet_name='Ringkasan Konflik')

print('=== FINAL CONFLICTS ===')
print(conflicts)

print('\n=== PWK SCHEDULE ===')
pwk_df = df[df['Prodi'] == 'PWK']
print(f'PWK entries: {len(pwk_df)}')
for _, row in pwk_df.iterrows():
    print(f'{row["Hari"]:8} S{row["Sesi"]} {row["Ruang"]:15} | {row["Mata Kuliah"]}')

print('\n=== ROOM CONFLICTS ===')
luring = df[~df['Mode (Zoom/Luring)'].str.lower().str.contains('zoom', na=False)]
room_conflicts = luring[luring['Ruang'] != ''].groupby(['Hari', 'Sesi', 'Ruang']).size()
room_conflicts = room_conflicts[room_conflicts > 1]

for (day, session, room), count in room_conflicts.items():
    print(f'\nCONFLICT: {day} Sesi {session} Ruang {room}')
    conflicted = df[(df['Hari']==day) & (df['Sesi']==session) & (df['Ruang']==room)]
    for _, row in conflicted.iterrows():
        print(f'  - {row["Prodi"]} {row["Mata Kuliah"]}')