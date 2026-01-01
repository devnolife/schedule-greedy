#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mode interaktif untuk fine-tuning jadwal dengan berbagai opsi
"""

import pandas as pd
from pathlib import Path
from jadwal_finetune import (
    remove_courses_by_keyword,
    find_available_slots,
    add_course_to_schedule,
    reschedule_course,
    print_schedule_summary,
    print_available_slots_summary,
    get_col_name
)
from jadwal import resolve_all

class JadwalFineTuner:
    def __init__(self, jadwal_file="jadwal_gabungan_SATU_TABEL_FINAL_PWK_ARS.xlsx"):
        self.jadwal_file = Path(jadwal_file)
        self.df = None
        self.original_df = None
        self.load_schedule()

    def load_schedule(self):
        """Load jadwal dari file Excel"""
        if not self.jadwal_file.exists():
            print(f"File {self.jadwal_file} tidak ditemukan!")
            print("Jalankan jadwal.py terlebih dahulu untuk membuat jadwal.")
            return False

        try:
            self.df = pd.read_excel(self.jadwal_file, sheet_name="Jadwal Induk (Gabungan)")
            self.original_df = self.df.copy()
            print(f"Jadwal dimuat: {len(self.df)} mata kuliah")
            return True
        except Exception as e:
            print(f"Error membaca file: {e}")
            return False

    def show_status(self):
        """Tampilkan status jadwal saat ini"""
        if self.df is None:
            print("Jadwal belum dimuat!")
            return

        print(f"\n=== STATUS JADWAL ===")
        print(f"Total mata kuliah: {len(self.df)}")

        # Hitung per prodi
        prodi_counts = self.df["Prodi"].value_counts()
        print("Per prodi:")
        for prodi, count in prodi_counts.items():
            print(f"  {prodi}: {count} mata kuliah")

        # Hitung per hari
        print("\nPer hari:")
        day_counts = self.df["Hari"].value_counts()
        for day in ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]:
            count = day_counts.get(day, 0)
            print(f"  {day}: {count} mata kuliah")

    def remove_courses(self, keyword, prodi=None):
        """Hapus mata kuliah berdasarkan keyword"""
        if self.df is None:
            print("Jadwal belum dimuat!")
            return

        self.df, removed = remove_courses_by_keyword(self.df, keyword, prodi)
        return len(removed)

    def move_prodi_from_day(self, prodi, from_day, to_days=None):
        """Pindahkan semua mata kuliah prodi tertentu dari hari tertentu"""
        if self.df is None:
            print("Jadwal belum dimuat!")
            return

        if to_days is None:
            to_days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat"]

        # Cari mata kuliah yang akan dipindah
        courses_to_move = self.df[
            (self.df["Prodi"].str.upper() == prodi.upper()) &
            (self.df["Hari"].str.upper() == from_day.upper())
        ].copy()

        if len(courses_to_move) == 0:
            print(f"Tidak ada mata kuliah {prodi} di hari {from_day}")
            return 0

        mk_col = get_col_name(self.df, ["Mata Kuliah", "Mata_Kuliah"])
        print(f"Memindahkan {len(courses_to_move)} mata kuliah {prodi} dari {from_day}:")

        # Hapus dari jadwal sementara
        self.df = self.df[~(
            (self.df["Prodi"].str.upper() == prodi.upper()) &
            (self.df["Hari"].str.upper() == from_day.upper())
        )].copy()

        moved_count = 0
        for _, course in courses_to_move.iterrows():
            course_dict = course.to_dict()
            course_name = course[mk_col]

            # Cari slot terbaik di hari-hari target
            best_slot = None
            min_conflicts = float('inf')

            for day in to_days:
                available_slots = find_available_slots(self.df, day=day)
                for slot in available_slots:
                    if slot['Room_Count'] > 0 or str(course['Semester']) == "1":
                        if slot['Total_Conflicts'] < min_conflicts:
                            min_conflicts = slot['Total_Conflicts']
                            best_slot = slot

            if best_slot:
                try:
                    self.df = add_course_to_schedule(
                        self.df,
                        course_dict,
                        target_day=best_slot["Hari"],
                        target_session=best_slot["Sesi"]
                    )
                    moved_count += 1
                    print(f"  ✓ {course['Semester']}{course['Kelas']}: {course_name} → {best_slot['Hari']} Sesi {best_slot['Sesi']}")
                except:
                    print(f"  ✗ Gagal memindahkan: {course['Semester']}{course['Kelas']}: {course_name}")

        print(f"Berhasil memindahkan {moved_count}/{len(courses_to_move)} mata kuliah")
        return moved_count

    def show_schedule(self, prodi=None, day=None):
        """Tampilkan jadwal"""
        if self.df is None:
            print("Jadwal belum dimuat!")
            return

        print_schedule_summary(self.df, day=day, prodi=prodi)

    def show_available_slots(self, day=None, limit=10):
        """Tampilkan slot kosong"""
        if self.df is None:
            print("Jadwal belum dimuat!")
            return

        available = find_available_slots(self.df, day=day)
        print_available_slots_summary(available, day=day, limit=limit)

    def resolve_conflicts(self):
        """Selesaikan konflik"""
        if self.df is None:
            print("Jadwal belum dimuat!")
            return

        print("Menyelesaikan konflik...")
        self.df = resolve_all(self.df)
        print("Konflik diselesaikan!")

    def save_schedule(self, filename=None):
        """Simpan jadwal"""
        if self.df is None:
            print("Jadwal belum dimuat!")
            return

        if filename is None:
            filename = "jadwal_finetune_result.xlsx"

        try:
            with pd.ExcelWriter(filename, engine="openpyxl") as writer:
                # Sheet utama
                self.df.to_excel(writer, sheet_name="Jadwal Disesuaikan", index=False)

                # Sheet per prodi
                for prodi in ["Informatika", "PWK", "Elektro", "Pengairan", "Arsitektur", "MKDU"]:
                    df_prodi = self.df[self.df["Prodi"].str.upper() == prodi.upper()]
                    if not df_prodi.empty:
                        df_prodi.to_excel(writer, sheet_name=f"Jadwal {prodi}", index=False)

            print(f"Jadwal disimpan ke: {filename}")
            return True
        except Exception as e:
            print(f"Error menyimpan file: {e}")
            return False

    def reset_schedule(self):
        """Reset jadwal ke kondisi awal"""
        if self.original_df is not None:
            self.df = self.original_df.copy()
            print("Jadwal direset ke kondisi awal")
        else:
            print("Tidak ada backup jadwal awal!")

def main():
    print("=== FINE-TUNING JADWAL INTERAKTIF ===")
    print("Ketik 'help' untuk melihat perintah yang tersedia")
    print("Ketik 'exit' untuk keluar\n")

    tuner = JadwalFineTuner()

    if tuner.df is None:
        return

    tuner.show_status()

    while True:
        try:
            cmd = input("\n> ").strip()

            if cmd.lower() == "exit":
                break
            elif cmd.lower() == "help":
                print("""
Perintah yang tersedia:
  status                          - Tampilkan status jadwal
  show <prodi> [hari]            - Tampilkan jadwal prodi/hari
  slots [hari] [limit]           - Tampilkan slot kosong
  remove <keyword> [prodi]       - Hapus mata kuliah dengan keyword
  move <prodi> <dari_hari>       - Pindahkan prodi dari hari tertentu
  resolve                        - Selesaikan konflik
  save [filename]                - Simpan jadwal
  reset                          - Reset ke jadwal awal

Contoh:
  show arsitektur                - Lihat jadwal Arsitektur
  show arsitektur sabtu         - Lihat jadwal Arsitektur di Sabtu
  slots sabtu                   - Lihat slot kosong di Sabtu
  remove skripsi arsitektur     - Hapus skripsi dari Arsitektur
  move arsitektur sabtu         - Pindahkan Arsitektur dari Sabtu
  save jadwal_baru.xlsx         - Simpan dengan nama khusus
                """)

            elif cmd.lower() == "status":
                tuner.show_status()

            elif cmd.startswith("show"):
                parts = cmd.split()[1:]
                prodi = parts[0] if parts else None
                day = parts[1] if len(parts) > 1 else None
                tuner.show_schedule(prodi=prodi, day=day)

            elif cmd.startswith("slots"):
                parts = cmd.split()[1:]
                day = parts[0] if parts else None
                limit = int(parts[1]) if len(parts) > 1 else 10
                tuner.show_available_slots(day=day, limit=limit)

            elif cmd.startswith("remove"):
                parts = cmd.split()[1:]
                if not parts:
                    print("Usage: remove <keyword> [prodi]")
                    continue
                keyword = parts[0]
                prodi = parts[1] if len(parts) > 1 else None
                count = tuner.remove_courses(keyword, prodi)
                print(f"Berhasil menghapus {count} mata kuliah")

            elif cmd.startswith("move"):
                parts = cmd.split()[1:]
                if len(parts) < 2:
                    print("Usage: move <prodi> <dari_hari>")
                    continue
                prodi = parts[0]
                from_day = parts[1]
                count = tuner.move_prodi_from_day(prodi, from_day)
                print(f"Berhasil memindahkan {count} mata kuliah")

            elif cmd.lower() == "resolve":
                tuner.resolve_conflicts()

            elif cmd.startswith("save"):
                parts = cmd.split()[1:]
                filename = parts[0] if parts else None
                tuner.save_schedule(filename)

            elif cmd.lower() == "reset":
                tuner.reset_schedule()

            else:
                print("Perintah tidak dikenali. Ketik 'help' untuk bantuan.")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

    print("\nTerima kasih!")

if __name__ == "__main__":
    main()