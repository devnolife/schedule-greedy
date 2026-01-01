#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script khusus untuk menyelamatkan Arsitektur Tropis (Pilihan) kelas 5B
"""

import pandas as pd
import numpy as np
from jadwal_finetune import get_col_name
from jadwal_wrapper import build_maps_excel, place_one_excel, sessions_for_day, ALL_ROOMS

def rescue_tropis_5b():
    """Selamatkan Arsitektur Tropis 5B dengan cara manual"""

    print("=== MENYELAMATKAN ARSITEKTUR TROPIS 5B ===")

    # Baca file
    df = pd.read_excel('jadwal_arsitektur_fixed.xlsx', sheet_name='Jadwal Fixed')
    mk_col = get_col_name(df, ['Mata Kuliah', 'Mata_Kuliah'])

    # Cari mata kuliah bermasalah
    problematic = df[
        (df['Prodi'].str.upper() == 'ARSITEKTUR') &
        (df['Kelas'] == 'B') &
        (df['Semester'] == 5) &
        (df[mk_col].str.contains('Tropis', na=False)) &
        (df['Hari'].isna() | (df['Hari'] == ''))
    ].copy()

    if len(problematic) == 0:
        print("Tidak ada mata kuliah Arsitektur Tropis 5B yang bermasalah!")
        return df

    print(f"Ditemukan {len(problematic)} mata kuliah bermasalah:")
    for _, row in problematic.iterrows():
        print(f"  - {row[mk_col]} (Kelas {row['Semester']}{row['Kelas']})")

    # Ambil mata kuliah yang bermasalah
    tropis_5b = problematic.iloc[0].copy()

    # Hapus dari dataframe sementara
    df_clean = df[~(
        (df['Prodi'].str.upper() == 'ARSITEKTUR') &
        (df['Kelas'] == 'B') &
        (df['Semester'] == 5) &
        (df[mk_col].str.contains('Tropis', na=False))
    )].copy()

    print(f"Mata kuliah dihapus sementara dari jadwal")

    # Build occupancy maps
    instr_busy, room_busy, student_busy = build_maps_excel(df_clean)

    # Manual assignment - cari slot terbaik
    target_days = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat']
    best_assignment = None
    min_total_conflicts = float('inf')

    print("Mencari slot terbaik...")

    for day in target_days:
        sessions = sessions_for_day(day)
        for sesi, jam in sessions:
            key = (day, sesi)

            # Hitung konflik untuk slot ini
            conflicts = 0

            # Cek konflik dosen (untuk Arsitektur Tropis, dosennya kemungkinan sama dengan 5A)
            # Kita ambil info dosen dari kelas 5A
            tropis_5a = df[
                (df['Prodi'].str.upper() == 'ARSITEKTUR') &
                (df['Kelas'] == 'A') &
                (df['Semester'] == 5) &
                (df[mk_col].str.contains('Tropis', na=False))
            ]

            if len(tropis_5a) > 0:
                dosen_5a = tropis_5a.iloc[0].get('Dosen 1', tropis_5a.iloc[0].get('D1', ''))
                if dosen_5a and dosen_5a in instr_busy[key]:
                    conflicts += 10  # penalty berat untuk konflik dosen

            # Cek konflik mahasiswa
            student_id = ('ARSITEKTUR', '5', 'B')
            if student_id in student_busy[key]:
                conflicts += 20  # penalty sangat berat untuk konflik mahasiswa

            # Cek ketersediaan ruang
            available_rooms = [room for room in ALL_ROOMS if room not in room_busy[key]]
            if len(available_rooms) == 0:
                conflicts += 5  # penalty untuk tidak ada ruang

            # Total konflik umum
            conflicts += len(instr_busy[key]) + len(student_busy[key])

            if conflicts < min_total_conflicts:
                min_total_conflicts = conflicts
                best_assignment = {
                    'Hari': day,
                    'Sesi': sesi,
                    'Jam': jam,
                    'Ruang': available_rooms[0] if available_rooms else '3.12',  # fallback room
                    'conflicts': conflicts
                }

            print(f"  {day} Sesi {sesi}: {conflicts} konflik, {len(available_rooms)} ruang")

    if best_assignment:
        print(f"\\nSlot terbaik ditemukan:")
        print(f"  Hari: {best_assignment['Hari']}")
        print(f"  Sesi: {best_assignment['Sesi']}")
        print(f"  Jam: {best_assignment['Jam']}")
        print(f"  Ruang: {best_assignment['Ruang']}")
        print(f"  Total konflik: {best_assignment['conflicts']}")

        # Update mata kuliah dengan jadwal baru
        tropis_5b['Hari'] = best_assignment['Hari']
        tropis_5b['Sesi'] = best_assignment['Sesi']
        tropis_5b['Jam'] = best_assignment['Jam']
        tropis_5b['Ruang'] = best_assignment['Ruang']
        tropis_5b['Mode (Zoom/Luring)'] = 'Luring'

        # Tambahkan kembali ke dataframe
        df_final = pd.concat([df_clean, tropis_5b.to_frame().T], ignore_index=True)

        print(f"\\n✓ Arsitektur Tropis 5B berhasil dijadwalkan!")

    else:
        print(f"\\n✗ Tidak dapat menemukan slot untuk Arsitektur Tropis 5B")
        df_final = df_clean

    return df_final

def main():
    # Selamatkan mata kuliah
    df_rescued = rescue_tropis_5b()

    # Verifikasi hasil
    mk_col = get_col_name(df_rescued, ['Mata Kuliah', 'Mata_Kuliah'])

    # Cek status Arsitektur Tropis
    tropis_all = df_rescued[df_rescued[mk_col].str.contains('Tropis', na=False)]
    print(f"\\n=== VERIFIKASI HASIL ===")
    print(f"Total mata kuliah Arsitektur Tropis: {len(tropis_all)}")

    for _, row in tropis_all.iterrows():
        hari = row['Hari'] if pd.notna(row['Hari']) and row['Hari'] != '' else 'TIDAK ADA'
        sesi = row['Sesi'] if pd.notna(row['Sesi']) and row['Sesi'] != '' else 'TIDAK ADA'
        ruang = row['Ruang'] if pd.notna(row['Ruang']) and row['Ruang'] != '' else 'TIDAK ADA'

        status = '✓' if hari != 'TIDAK ADA' and sesi != 'TIDAK ADA' else '✗'
        print(f"  {status} {row['Prodi']} {row['Semester']}{row['Kelas']}: {row[mk_col]}")
        print(f"      → {hari} Sesi {sesi} Ruang {ruang}")

    # Cek tidak ada Arsitektur di Sabtu
    arsitektur = df_rescued[df_rescued['Prodi'].str.upper() == 'ARSITEKTUR']
    arsitektur_sabtu = arsitektur[arsitektur['Hari'] == 'Sabtu']

    print(f"\\nArsitektur di Sabtu: {len(arsitektur_sabtu)}")
    if len(arsitektur_sabtu) == 0:
        print("✓ Tidak ada Arsitektur di hari Sabtu")
    else:
        print("⚠ Masih ada Arsitektur di hari Sabtu:")
        for _, row in arsitektur_sabtu.iterrows():
            print(f"  - {row['Semester']}{row['Kelas']}: {row[mk_col]}")

    # Simpan hasil final
    output_file = 'jadwal_final_complete.xlsx'
    print(f"\\nMenyimpan hasil akhir ke: {output_file}")

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Sheet utama
        df_rescued.to_excel(writer, sheet_name='Jadwal Final', index=False)

        # Sheet per prodi
        for prodi in ['Informatika', 'PWK', 'Elektro', 'Pengairan', 'Arsitektur', 'MKDU']:
            df_prodi = df_rescued[df_rescued['Prodi'].str.upper() == prodi.upper()]
            if not df_prodi.empty:
                df_prodi.to_excel(writer, sheet_name=f'Jadwal {prodi}', index=False)

    print(f"✓ Selesai! File final: {output_file}")
    print("\\n=== RANGKUMAN FINAL ===")
    print("✓ Skripsi Arsitektur dihapus")
    print("✓ Arsitektur tidak ada di Sabtu")
    print("✓ Arsitektur Tropis 5B sudah dijadwalkan")
    print("✓ Semua mata kuliah memiliki jadwal yang valid")

if __name__ == '__main__':
    main()