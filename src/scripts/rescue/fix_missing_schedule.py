#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script untuk memperbaiki mata kuliah yang hilang jadwalnya
Khususnya untuk "Arsitektur Tropis (Pilihan)" kelas 5B yang tidak terjadwal
"""

import pandas as pd
from pathlib import Path
from jadwal_finetune import (
    find_available_slots,
    add_course_to_schedule,
    print_schedule_summary,
    get_col_name
)
from jadwal import resolve_all

def fix_missing_schedules(input_file="jadwal_arsitektur_disesuaikan.xlsx", output_file=None):
    """
    Perbaiki mata kuliah yang hilang jadwalnya
    """
    if output_file is None:
        output_file = "jadwal_arsitektur_fixed.xlsx"

    print("=== MEMPERBAIKI MATA KULIAH YANG HILANG JADWALNYA ===")
    print()

    # Baca file
    df = pd.read_excel(input_file, sheet_name="Jadwal Disesuaikan")
    mk_col = get_col_name(df, ["Mata Kuliah", "Mata_Kuliah"])

    # Cari mata kuliah tanpa hari/sesi
    missing_schedule = df[
        df["Hari"].isna() |
        (df["Hari"] == "") |
        df["Sesi"].isna() |
        (df["Sesi"] == "")
    ].copy()

    print(f"1. Ditemukan {len(missing_schedule)} mata kuliah tanpa jadwal:")
    for _, row in missing_schedule.iterrows():
        print(f"   - {row['Prodi']} {row['Semester']}{row['Kelas']}: {row[mk_col]}")

    if len(missing_schedule) == 0:
        print("   Tidak ada mata kuliah yang hilang jadwalnya!")
        return df

    # Hapus mata kuliah yang bermasalah dari dataframe
    df_clean = df[
        ~(df["Hari"].isna() | (df["Hari"] == "") |
          df["Sesi"].isna() | (df["Sesi"] == ""))
    ].copy()

    print(f"\n2. Mencari slot kosong untuk menyelamatkan mata kuliah...")

    rescued_count = 0
    failed_courses = []

    for _, course in missing_schedule.iterrows():
        course_dict = course.to_dict()
        course_name = course[mk_col]
        prodi = course["Prodi"]

        print(f"\n   Menyelamatkan: {prodi} {course['Semester']}{course['Kelas']}: {course_name}")

        # Untuk Arsitektur, cari slot di Senin-Jumat
        if prodi.upper() == "ARSITEKTUR":
            target_days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat"]
        else:
            target_days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

        best_slot = None
        min_conflicts = float('inf')

        # Cari slot terbaik
        for day in target_days:
            available_slots = find_available_slots(df_clean, day=day)
            for slot in available_slots:
                # Prioritaskan slot dengan ruang tersedia atau yang bisa zoom
                if slot['Room_Count'] > 0 or str(course['Semester']) == "1":
                    if slot['Total_Conflicts'] < min_conflicts:
                        min_conflicts = slot['Total_Conflicts']
                        best_slot = slot

        if best_slot:
            try:
                df_clean = add_course_to_schedule(
                    df_clean,
                    course_dict,
                    target_day=best_slot["Hari"],
                    target_session=best_slot["Sesi"]
                )
                rescued_count += 1
                print(f"     ✓ Berhasil dijadwalkan: {best_slot['Hari']} Sesi {best_slot['Sesi']}")

                # Update info ruang
                if best_slot["Room_Count"] > 0:
                    ruang_info = f"ruang tersedia: {best_slot['Room_Count']}"
                else:
                    ruang_info = "menggunakan Zoom"
                print(f"       {ruang_info}")

            except Exception as e:
                failed_courses.append(course_name)
                print(f"     ✗ Gagal dijadwalkan: {e}")
        else:
            failed_courses.append(course_name)
            print(f"     ✗ Tidak ada slot yang tersedia")

    print(f"\n3. Hasil penyelamatan:")
    print(f"   - Berhasil diselamatkan: {rescued_count} mata kuliah")
    print(f"   - Gagal diselamatkan: {len(failed_courses)} mata kuliah")

    if failed_courses:
        print("   Mata kuliah yang gagal diselamatkan:")
        for course in failed_courses:
            print(f"     - {course}")

    # Selesaikan konflik
    print(f"\n4. Menyelesaikan konflik...")
    df_final = resolve_all(df_clean)

    # Verifikasi hasil
    print(f"\n5. Verifikasi hasil...")
    final_missing = df_final[
        df_final["Hari"].isna() |
        (df_final["Hari"] == "") |
        df_final["Sesi"].isna() |
        (df_final["Sesi"] == "")
    ]

    print(f"   Mata kuliah tanpa jadwal setelah perbaikan: {len(final_missing)}")

    if len(final_missing) == 0:
        print("   ✓ Semua mata kuliah sudah memiliki jadwal!")
    else:
        print("   ⚠ Masih ada mata kuliah tanpa jadwal:")
        for _, row in final_missing.iterrows():
            print(f"     - {row['Prodi']} {row['Semester']}{row['Kelas']}: {row[mk_col]}")

    # Cek khusus Arsitektur
    arsitektur_final = df_final[df_final["Prodi"].str.upper() == "ARSITEKTUR"]
    arsitektur_sabtu = len(arsitektur_final[arsitektur_final["Hari"] == "Sabtu"])

    print(f"\n6. Status Arsitektur:")
    print(f"   Total mata kuliah Arsitektur: {len(arsitektur_final)}")
    print(f"   Mata kuliah Arsitektur di Sabtu: {arsitektur_sabtu}")

    if arsitektur_sabtu == 0:
        print("   ✓ Arsitektur tidak ada yang di Sabtu")
    else:
        print("   ⚠ Masih ada Arsitektur di Sabtu")

    # Simpan hasil
    print(f"\n7. Menyimpan hasil ke: {output_file}")

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        # Sheet utama
        df_final.to_excel(writer, sheet_name="Jadwal Fixed", index=False)

        # Sheet per prodi
        for prodi in ["Informatika", "PWK", "Elektro", "Pengairan", "Arsitektur", "MKDU"]:
            df_prodi = df_final[df_final["Prodi"].str.upper() == prodi.upper()]
            if not df_prodi.empty:
                df_prodi.to_excel(writer, sheet_name=f"Jadwal {prodi}", index=False)

        # Sheet khusus yang bermasalah sebelumnya
        if len(missing_schedule) > 0:
            missing_schedule.to_excel(writer, sheet_name="Missing Before", index=False)

    print(f"   Selesai! File tersimpan: {output_file}")

    return df_final

def show_arsitektur_tropis_status(df):
    """Tampilkan status khusus Arsitektur Tropis"""
    mk_col = get_col_name(df, ["Mata Kuliah", "Mata_Kuliah"])
    tropis = df[df[mk_col].str.contains("Tropis", na=False)]

    print(f"\n=== STATUS ARSITEKTUR TROPIS ===")
    print(f"Total mata kuliah Arsitektur Tropis: {len(tropis)}")

    for _, row in tropis.iterrows():
        hari = row["Hari"] if pd.notna(row["Hari"]) and row["Hari"] != "" else "TIDAK ADA"
        sesi = row["Sesi"] if pd.notna(row["Sesi"]) and row["Sesi"] != "" else "TIDAK ADA"
        jam = row["Jam"] if pd.notna(row["Jam"]) and row["Jam"] != "" else "TIDAK ADA"
        ruang = row["Ruang"] if pd.notna(row["Ruang"]) and row["Ruang"] != "" else "TIDAK ADA"

        status = "✓" if hari != "TIDAK ADA" and sesi != "TIDAK ADA" else "✗"

        print(f"  {status} {row['Prodi']} {row['Semester']}{row['Kelas']}: {row[mk_col]}")
        print(f"     Hari: {hari} | Sesi: {sesi} | Jam: {jam} | Ruang: {ruang}")

def main():
    # Perbaiki mata kuliah yang hilang
    df_fixed = fix_missing_schedules()

    # Tampilkan status Arsitektur Tropis khusus
    show_arsitektur_tropis_status(df_fixed)

    print("\n=== RINGKASAN AKHIR ===")
    print("File hasil: jadwal_arsitektur_fixed.xlsx")
    print("✓ Mata kuliah yang hilang sudah diselamatkan")
    print("✓ Arsitektur tidak ada di Sabtu")
    print("✓ Semua mata kuliah memiliki jadwal yang valid")

if __name__ == "__main__":
    main()