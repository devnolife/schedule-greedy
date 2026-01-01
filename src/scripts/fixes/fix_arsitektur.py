#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script khusus untuk menyesuaikan jadwal Arsitektur:
1. Hapus mata kuliah skripsi dari Arsitektur
2. Pindahkan semua mata kuliah Arsitektur dari hari Sabtu ke hari lain (Senin-Jumat)
"""

import pandas as pd
from pathlib import Path
from jadwal_finetune import (
    remove_courses_by_keyword,
    find_available_slots,
    add_course_to_schedule,
    reschedule_course,
    print_schedule_summary,
    get_col_name
)
from jadwal import resolve_all

def move_arsitektur_from_saturday(df):
    """
    Pindahkan semua mata kuliah Arsitektur dari hari Sabtu ke hari lain (Senin-Jumat)
    """
    print("Mencari mata kuliah Arsitektur yang dijadwalkan di hari Sabtu...")

    # Cari mata kuliah Arsitektur yang di Sabtu
    arsitektur_sabtu = df[
        (df["Prodi"].str.upper() == "ARSITEKTUR") &
        (df["Hari"].str.upper() == "SABTU")
    ].copy()

    if len(arsitektur_sabtu) == 0:
        print("Tidak ada mata kuliah Arsitektur yang dijadwalkan di hari Sabtu")
        return df

    mk_col = get_col_name(df, ["Mata Kuliah", "Mata_Kuliah"])
    print(f"Ditemukan {len(arsitektur_sabtu)} mata kuliah Arsitektur di hari Sabtu:")
    for _, row in arsitektur_sabtu.iterrows():
        ruang_info = f"({row['Ruang']})" if row['Ruang'] else "(Zoom)"
        print(f"  - {row['Semester']}{row['Kelas']}: {row[mk_col]} (Sesi {row['Sesi']}) {ruang_info}")

    # Hapus mata kuliah Arsitektur dari Sabtu
    df_updated = df[~(
        (df["Prodi"].str.upper() == "ARSITEKTUR") &
        (df["Hari"].str.upper() == "SABTU")
    )].copy()

    print(f"\nMata kuliah Arsitektur di Sabtu telah dihapus dari jadwal")
    print("Mencari slot alternatif di hari Senin-Jumat...")

    # Cari slot kosong di hari Senin-Jumat untuk setiap mata kuliah
    weekdays = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat"]
    moved_count = 0
    failed_courses = []

    for _, course in arsitektur_sabtu.iterrows():
        course_dict = course.to_dict()
        course_name = course[mk_col]

        # Cari slot kosong di hari kerja
        slot_found = False
        for day in weekdays:
            available_slots = find_available_slots(df_updated, day=day)

            # Filter slot yang cocok untuk mata kuliah ini
            suitable_slots = []
            for slot in available_slots:
                # Periksa apakah ada ruang tersedia atau bisa zoom
                if slot['Room_Count'] > 0 or str(course['Semester']) == "1":
                    suitable_slots.append(slot)

            if suitable_slots:
                # Pilih slot terbaik (yang paling sedikit konfliknya)
                best_slot = min(suitable_slots, key=lambda x: x['Total_Conflicts'])

                # Tambahkan mata kuliah ke slot yang dipilih
                try:
                    df_updated = add_course_to_schedule(
                        df_updated,
                        course_dict,
                        target_day=best_slot["Hari"],
                        target_session=best_slot["Sesi"]
                    )
                    moved_count += 1
                    slot_found = True
                    print(f"  ✓ {course['Semester']}{course['Kelas']}: {course_name} → {best_slot['Hari']} Sesi {best_slot['Sesi']}")
                    break
                except Exception as e:
                    continue

        if not slot_found:
            failed_courses.append(course_name)
            print(f"  ✗ Tidak dapat memindahkan: {course['Semester']}{course['Kelas']}: {course_name}")

    print(f"\nHasil pemindahan:")
    print(f"  - Berhasil dipindahkan: {moved_count} mata kuliah")
    print(f"  - Gagal dipindahkan: {len(failed_courses)} mata kuliah")

    if failed_courses:
        print("Mata kuliah yang gagal dipindahkan:")
        for course in failed_courses:
            print(f"    - {course}")

    return df_updated

def main():
    # Cek apakah file jadwal sudah ada
    jadwal_file = Path("jadwal_gabungan_SATU_TABEL_FINAL_PWK_ARS.xlsx")

    if not jadwal_file.exists():
        print("File jadwal tidak ditemukan. Jalankan jadwal.py terlebih dahulu untuk membuat jadwal.")
        print("Contoh: python jadwal.py")
        return

    print("=== PENYESUAIAN KHUSUS JADWAL ARSITEKTUR ===")
    print()

    # 1. Baca jadwal yang sudah ada
    print("1. Membaca jadwal yang sudah ada...")
    df = pd.read_excel(jadwal_file, sheet_name="Jadwal Induk (Gabungan)")
    print(f"   Total mata kuliah: {len(df)}")

    # Lihat jadwal Arsitektur saat ini
    print("\n2. Jadwal Arsitektur saat ini:")
    arsitektur_before = df[df["Prodi"].str.upper() == "ARSITEKTUR"]
    sabtu_arsitektur_before = len(arsitektur_before[arsitektur_before["Hari"] == "Sabtu"])
    print(f"   Total mata kuliah Arsitektur: {len(arsitektur_before)}")
    print(f"   Mata kuliah Arsitektur di Sabtu: {sabtu_arsitektur_before}")

    # 3. Hapus mata kuliah skripsi dari Arsitektur
    print("\n3. Menghapus mata kuliah 'skripsi' dari Arsitektur...")
    df_updated, removed_skripsi = remove_courses_by_keyword(df, "skripsi", prodi="Arsitektur")

    # 4. Pindahkan semua mata kuliah Arsitektur dari Sabtu ke hari lain
    print("\n4. Memindahkan mata kuliah Arsitektur dari hari Sabtu...")
    df_updated = move_arsitektur_from_saturday(df_updated)

    # 5. Selesaikan konflik yang mungkin terjadi
    print("\n5. Menyelesaikan konflik yang mungkin terjadi...")
    df_final = resolve_all(df_updated)

    # 6. Verifikasi hasil
    print("\n6. Verifikasi hasil...")
    arsitektur_after = df_final[df_final["Prodi"].str.upper() == "ARSITEKTUR"]
    sabtu_arsitektur_after = len(arsitektur_after[arsitektur_after["Hari"] == "Sabtu"])

    print(f"   Total mata kuliah Arsitektur: {len(arsitektur_after)}")
    print(f"   Mata kuliah Arsitektur di Sabtu: {sabtu_arsitektur_after}")

    if sabtu_arsitektur_after == 0:
        print("   ✓ Berhasil! Tidak ada lagi mata kuliah Arsitektur di hari Sabtu")
    else:
        print(f"   ⚠ Masih ada {sabtu_arsitektur_after} mata kuliah Arsitektur di hari Sabtu")

    # 7. Lihat sebaran jadwal Arsitektur per hari
    print("\n7. Sebaran jadwal Arsitektur per hari setelah penyesuaian:")
    for day in ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]:
        count = len(arsitektur_after[arsitektur_after["Hari"] == day])
        if count > 0:
            print(f"   {day}: {count} mata kuliah")

    # 8. Simpan hasil
    output_file = "jadwal_arsitektur_disesuaikan.xlsx"
    print(f"\n8. Menyimpan jadwal yang sudah disesuaikan ke: {output_file}")

    # Simpan dengan format yang sama seperti aslinya
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        # Sheet utama
        df_final.to_excel(writer, sheet_name="Jadwal Disesuaikan", index=False)

        # Sheet per prodi
        for prodi in ["Informatika", "PWK", "Elektro", "Pengairan", "Arsitektur", "MKDU"]:
            df_prodi = df_final[df_final["Prodi"].str.upper() == prodi.upper()]
            if not df_prodi.empty:
                df_prodi.to_excel(writer, sheet_name=f"Jadwal {prodi}", index=False)

        # Sheet khusus Arsitektur yang telah disesuaikan
        arsitektur_final = df_final[df_final["Prodi"].str.upper() == "ARSITEKTUR"]
        arsitektur_final.to_excel(writer, sheet_name="Arsitektur Fixed", index=False)

    print(f"   Selesai! File tersimpan: {output_file}")

    # 9. Ringkasan perubahan
    print("\n=== RINGKASAN PERUBAHAN ===")
    print(f"Total mata kuliah sebelum: {len(df)}")
    print(f"Total mata kuliah sesudah: {len(df_final)}")

    if len(removed_skripsi) > 0:
        mk_col = get_col_name(removed_skripsi, ["Mata Kuliah", "Mata_Kuliah"])
        print(f"Mata kuliah skripsi yang dihapus: {len(removed_skripsi)}")
        for _, course in removed_skripsi.iterrows():
            print(f"  - {course[mk_col]} ({course['Semester']}{course['Kelas']})")

    print(f"Mata kuliah Arsitektur di Sabtu:")
    print(f"  - Sebelum: {sabtu_arsitektur_before}")
    print(f"  - Sesudah: {sabtu_arsitektur_after}")

    print(f"\n✓ Penyesuaian selesai! Arsitektur tidak lagi dijadwalkan di hari Sabtu")

if __name__ == "__main__":
    main()