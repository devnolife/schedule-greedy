#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contoh Penggunaan Fitur Fine-Tuning Jadwal
Script ini mendemonstrasikan cara menggunakan fitur fine-tuning untuk:
1. Menghapus mata kuliah tertentu (misal skripsi dari Arsitektur)
2. Mencari slot kosong di hari Sabtu
3. Menambahkan mata kuliah ke slot baru
"""

import pandas as pd
from pathlib import Path
from jadwal_finetune import (
    remove_courses_by_keyword,
    find_available_slots,
    add_course_to_schedule,
    reschedule_course,
    print_schedule_summary,
    print_available_slots_summary
)
from jadwal import resolve_all

def main():
    # Cek apakah file jadwal sudah ada
    jadwal_file = Path("jadwal_gabungan_SATU_TABEL_FINAL_PWK_ARS.xlsx")

    if not jadwal_file.exists():
        print("File jadwal tidak ditemukan. Jalankan jadwal.py terlebih dahulu untuk membuat jadwal.")
        print("Contoh: python jadwal.py")
        return

    print("=== CONTOH FINE-TUNING JADWAL ===")
    print()

    # 1. Baca jadwal yang sudah ada
    print("1. Membaca jadwal yang sudah ada...")
    df = pd.read_excel(jadwal_file, sheet_name="Jadwal Induk (Gabungan)")
    print(f"   Total mata kuliah: {len(df)}")

    # Lihat jadwal Arsitektur saat ini
    print("\n2. Jadwal Arsitektur saat ini:")
    print_schedule_summary(df, prodi="Arsitektur")

    # 3. Hapus mata kuliah skripsi dari Arsitektur
    print("\n3. Menghapus mata kuliah 'skripsi' dari Arsitektur...")
    df_updated, removed_courses = remove_courses_by_keyword(df, "skripsi", prodi="Arsitektur")

    if len(removed_courses) == 0:
        print("   Tidak ada mata kuliah skripsi yang ditemukan di Arsitektur")
        print("   Mencoba mencari dengan keyword lain...")

        # Coba keyword lain yang mungkin ada
        for keyword in ["tugas akhir", "ta", "thesis", "capstone"]:
            df_updated, removed_courses = remove_courses_by_keyword(df, keyword, prodi="Arsitektur")
            if len(removed_courses) > 0:
                break

    # 4. Cari slot kosong di hari Sabtu
    print("\n4. Mencari slot kosong di hari Sabtu...")
    available_saturday = find_available_slots(df_updated, day="Sabtu")
    print_available_slots_summary(available_saturday, day="Sabtu", limit=5)

    # 5. Jika ada mata kuliah yang dihapus, coba tambahkan ke Sabtu
    if len(removed_courses) > 0:
        print("\n5. Menambahkan mata kuliah yang dihapus ke slot Sabtu...")

        for _, course in removed_courses.iterrows():
            course_dict = course.to_dict()

            # Coba tambahkan ke slot Sabtu yang tersedia
            if available_saturday:
                target_slot = available_saturday[0]  # Ambil slot pertama yang tersedia
                df_updated = add_course_to_schedule(
                    df_updated,
                    course_dict,
                    target_day="Sabtu",
                    target_session=target_slot["Sesi"]
                )
            else:
                # Jika Sabtu penuh, cari slot lain
                all_available = find_available_slots(df_updated)
                if all_available:
                    best_slot = all_available[0]
                    df_updated = add_course_to_schedule(
                        df_updated,
                        course_dict,
                        target_day=best_slot["Hari"],
                        target_session=best_slot["Sesi"]
                    )
    else:
        print("\n5. Tidak ada mata kuliah yang dihapus, mencoba contoh lain...")

        # Contoh: pindahkan mata kuliah lain ke Sabtu
        print("   Mencari mata kuliah yang bisa dipindah ke Sabtu...")

        # Cari mata kuliah dari Arsitektur yang tidak di weekend
        arsitektur_courses = df_updated[
            (df_updated["Prodi"].str.upper() == "ARSITEKTUR") &
            (~df_updated["Hari"].isin(["Sabtu", "Minggu"]))
        ]

        if len(arsitektur_courses) > 0:
            # Ambil mata kuliah pertama untuk dipindah
            course_to_move = arsitektur_courses.iloc[0]
            mk_col = "Mata Kuliah" if "Mata Kuliah" in df_updated.columns else "Mata_Kuliah"
            print(f"   Memindahkan: {course_to_move[mk_col]} ke Sabtu")

            # Filter untuk mata kuliah ini
            course_filter = {
                mk_col: course_to_move[mk_col],
                "Prodi": "Arsitektur"
            }

            if available_saturday:
                df_updated = reschedule_course(
                    df_updated,
                    course_filter,
                    new_day="Sabtu",
                    new_session=available_saturday[0]["Sesi"]
                )

    # 6. Selesaikan konflik yang mungkin terjadi
    print("\n6. Menyelesaikan konflik yang mungkin terjadi...")
    df_final = resolve_all(df_updated)

    # 7. Lihat hasil akhir
    print("\n7. Jadwal Sabtu setelah penyesuaian:")
    print_schedule_summary(df_final, day="Sabtu")

    print("\n8. Jadwal Arsitektur setelah penyesuaian:")
    print_schedule_summary(df_final, prodi="Arsitektur")

    # 8. Simpan hasil
    output_file = "jadwal_disesuaikan.xlsx"
    print(f"\n9. Menyimpan jadwal yang sudah disesuaikan ke: {output_file}")

    # Simpan dengan format yang sama seperti aslinya
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        df_final.to_excel(writer, sheet_name="Jadwal Disesuaikan", index=False)

        # Buat sheet per prodi juga
        for prodi in ["Informatika", "PWK", "Elektro", "Pengairan", "Arsitektur", "MKDU"]:
            df_prodi = df_final[df_final["Prodi"].str.upper() == prodi.upper()]
            if not df_prodi.empty:
                df_prodi.to_excel(writer, sheet_name=f"Jadwal {prodi}", index=False)

    print(f"   Selesai! File tersimpan: {output_file}")

    # 9. Ringkasan perubahan
    print("\n=== RINGKASAN PERUBAHAN ===")
    print(f"Mata kuliah sebelum: {len(df)}")
    print(f"Mata kuliah sesudah: {len(df_final)}")

    if len(removed_courses) > 0:
        mk_col = "Mata Kuliah" if "Mata Kuliah" in removed_courses.columns else "Mata_Kuliah"
        print(f"Mata kuliah yang dihapus: {len(removed_courses)}")
        for _, course in removed_courses.iterrows():
            print(f"  - {course[mk_col]} ({course['Prodi']})")

    # Bandingkan jadwal Sabtu
    sabtu_before = len(df[df["Hari"] == "Sabtu"])
    sabtu_after = len(df_final[df_final["Hari"] == "Sabtu"])
    print(f"Mata kuliah di Sabtu sebelum: {sabtu_before}")
    print(f"Mata kuliah di Sabtu sesudah: {sabtu_after}")

def demo_interactive():
    """
    Mode interaktif untuk mencoba fitur fine-tuning
    """
    print("=== MODE INTERAKTIF FINE-TUNING ===")
    print("Ketik 'help' untuk melihat perintah yang tersedia")
    print("Ketik 'exit' untuk keluar")

    # Load jadwal
    jadwal_file = Path("jadwal_gabungan_SATU_TABEL_FINAL_PWK_ARS.xlsx")
    if not jadwal_file.exists():
        print("File jadwal tidak ditemukan!")
        return

    df = pd.read_excel(jadwal_file, sheet_name="Jadwal Induk (Gabungan)")
    print(f"Jadwal dimuat: {len(df)} mata kuliah")

    while True:
        try:
            cmd = input("\n> ").strip().lower()

            if cmd == "exit":
                break
            elif cmd == "help":
                print("Perintah yang tersedia:")
                print("  remove <keyword> [prodi] - Hapus mata kuliah dengan keyword")
                print("  slots <hari>            - Lihat slot kosong di hari tertentu")
                print("  schedule <prodi> [hari] - Lihat jadwal prodi/hari")
                print("  save <filename>         - Simpan jadwal saat ini")
                print("  help                    - Tampilkan bantuan ini")
                print("  exit                    - Keluar")
            elif cmd.startswith("remove "):
                parts = cmd.split()[1:]
                keyword = parts[0] if parts else ""
                prodi = parts[1] if len(parts) > 1 else None

                if keyword:
                    df, removed = remove_courses_by_keyword(df, keyword, prodi)
                    print(f"Dihapus {len(removed)} mata kuliah")
            elif cmd.startswith("slots "):
                hari = cmd.split()[1] if len(cmd.split()) > 1 else None
                available = find_available_slots(df, day=hari)
                print_available_slots_summary(available, day=hari)
            elif cmd.startswith("schedule "):
                parts = cmd.split()[1:]
                prodi = parts[0] if parts else None
                hari = parts[1] if len(parts) > 1 else None
                print_schedule_summary(df, day=hari, prodi=prodi)
            elif cmd.startswith("save "):
                filename = cmd.split()[1] if len(cmd.split()) > 1 else "jadwal_interactive.xlsx"
                df.to_excel(filename, index=False)
                print(f"Jadwal disimpan ke: {filename}")
            else:
                print("Perintah tidak dikenali. Ketik 'help' untuk bantuan.")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

    print("Terima kasih!")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        demo_interactive()
    else:
        main()