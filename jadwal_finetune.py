# -*- coding: utf-8 -*-
"""
Fitur Fine-Tuning Jadwal - Penyesuaian jadwal tanpa rebuild lengkap
Untuk semua prodi: bisa hapus mata kuliah tertentu dan cari slot kosong untuk hari tertentu
"""

import pandas as pd
import numpy as np
from collections import defaultdict
from jadwal import (
    resolve_all, detect_conflicts, norm
)
from jadwal_wrapper import (
    build_maps_excel as build_maps, place_one_excel as place_one,
    instr_names, sessions_for_day, ALL_ROOMS
)

# Helper function to get column names consistently
def get_col_name(df, possible_names):
    """Get the actual column name from a list of possible names"""
    for name in possible_names:
        if name in df.columns:
            return name
    return possible_names[0]  # fallback to first option

# =========================
# FINE-TUNING FUNCTIONS
# =========================

def remove_courses_by_keyword(df, keyword, prodi=None):
    """
    Hapus mata kuliah yang mengandung keyword tertentu dari jadwal
    Args:
        df: DataFrame dengan jadwal saat ini
        keyword: kata kunci untuk dicari di nama mata kuliah (case-insensitive)
        prodi: filter prodi tertentu (opsional, misal "Arsitektur")
    Returns:
        df_updated: DataFrame yang sudah dihapus mata kuliahnya
        removed_courses: DataFrame mata kuliah yang dihapus
    """
    # Handle both possible column names
    mk_col = get_col_name(df, ["Mata Kuliah", "Mata_Kuliah"])
    mask = df[mk_col].str.lower().str.contains(keyword.lower(), na=False)
    if prodi:
        mask = mask & (df["Prodi"].str.upper() == prodi.upper())

    removed_courses = df[mask].copy()
    df_updated = df[~mask].copy()

    print(f"Dihapus {len(removed_courses)} mata kuliah yang mengandung '{keyword}':")
    for _, row in removed_courses.iterrows():
        ruang_info = f"({row['Ruang']})" if row['Ruang'] else "(Zoom)"
        mk_name = row[mk_col]
        print(f"  - {row['Prodi']} {row['Semester']}{row['Kelas']}: {mk_name} ({row['Hari']} {row['Jam']}) {ruang_info}")

    return df_updated, removed_courses

def find_available_slots(df, day=None, prodi=None, semester=None):
    """
    Cari slot waktu yang tersedia pada hari tertentu
    Args:
        df: DataFrame dengan jadwal saat ini
        day: hari tertentu yang dicek (misal "Sabtu"), jika None akan cek semua hari
        prodi: filter berdasarkan prodi jika diperlukan
        semester: filter berdasarkan semester jika diperlukan
    Returns:
        List slot yang tersedia dengan detail lengkap
    """
    # Build current occupancy maps
    instr_busy, room_busy, student_busy = build_maps(df)

    # Define days to check
    days_to_check = [day] if day else ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

    available_slots = []

    for check_day in days_to_check:
        sessions = sessions_for_day(check_day)

        for sess, jam in sessions:
            key = (check_day, sess)

            # Check room availability
            available_rooms = [room for room in ALL_ROOMS if room not in room_busy[key]]

            # Get busy instructors for this slot
            busy_instructors = list(instr_busy[key])

            # Get busy student groups
            busy_students = list(student_busy[key])

            slot_info = {
                "Hari": check_day,
                "Sesi": sess,
                "Jam": jam,
                "Available_Rooms": available_rooms,
                "Room_Count": len(available_rooms),
                "Busy_Instructors": busy_instructors,
                "Busy_Students": busy_students,
                "Total_Conflicts": len(busy_instructors) + len(busy_students)
            }

            # Add this slot if it has available rooms or is suitable for Zoom
            if available_rooms or check_day in ["Sabtu", "Minggu"]:  # Weekend can use Zoom
                available_slots.append(slot_info)

    # Sort by day order and session
    day_order = {"Senin": 0, "Selasa": 1, "Rabu": 2, "Kamis": 3, "Jumat": 4, "Sabtu": 5, "Minggu": 6}
    available_slots.sort(key=lambda x: (day_order.get(x["Hari"], 99), x["Sesi"]))

    return available_slots

def add_course_to_schedule(df, course_info, target_day=None, target_session=None, target_room=None):
    """
    Tambahkan mata kuliah kembali ke jadwal pada slot yang ditentukan atau slot terbaik yang tersedia
    Args:
        df: DataFrame dengan jadwal saat ini
        course_info: dictionary dengan detail mata kuliah (dari removed_courses)
        target_day: hari yang diinginkan (opsional)
        target_session: sesi yang diinginkan (opsional)
        target_room: ruang yang diinginkan (opsional)
    Returns:
        DataFrame yang sudah ditambah mata kuliahnya
    """
    # Build current occupancy maps
    instr_busy, room_busy, student_busy = build_maps(df)

    # Create a row from course_info
    row = course_info.copy()

    # If specific slot is requested, try that first
    if target_day and target_session:
        key = (target_day, target_session)
        names = instr_names(row)
        student_id = (norm(row["Prodi"]), str(row["Semester"]), norm(row["Kelas"]))

        # Check conflicts
        instructor_conflict = any(n in instr_busy[key] for n in names if n)
        student_conflict = student_id in student_busy[key]

        if not instructor_conflict and not student_conflict:
            # Find available room or use Zoom
            if target_room and target_room not in room_busy[key]:
                room = target_room
            elif str(row["Semester"]) == "1":  # Semester 1 uses Zoom
                room = ""
            else:
                available_rooms = [r for r in ALL_ROOMS if r not in room_busy[key]]
                room = available_rooms[0] if available_rooms else ""

            if room or str(row["Semester"]) == "1":
                # Add to specific slot
                sessions = sessions_for_day(target_day)
                jam = next((j for s, j in sessions if s == target_session), "")

                new_row = {
                    **row,
                    "Hari": target_day,
                    "Sesi": target_session,
                    "Jam": jam,
                    "Ruang": room,
                    "Mode": "Zoom" if str(row["Semester"]) == "1" or room == "" else "Luring"
                }

                df_new = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                ruang_info = f"ruang {room}" if room else "Zoom"
                mk_col = get_col_name(df, ["Mata Kuliah", "Mata_Kuliah"])
                mk_name = row.get(mk_col, row.get("Mata Kuliah", row.get("Mata_Kuliah", "Unknown")))
                print(f"Berhasil menambahkan: {mk_name} ke {target_day} sesi {target_session} ({ruang_info})")
                return df_new

    # If specific slot failed or not specified, find best available slot
    slot = place_one(row, instr_busy, room_busy, student_busy)

    if slot["Hari"]:
        new_row = {
            **row,
            **slot,
            "Mode": "Zoom" if str(row["Semester"]) == "1" or slot["Ruang"] == "" else "Luring"
        }
        df_new = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        ruang_info = f"ruang {slot['Ruang']}" if slot['Ruang'] else "Zoom"
        mk_col = get_col_name(df, ["Mata Kuliah", "Mata_Kuliah"])
        mk_name = row.get(mk_col, row.get("Mata Kuliah", row.get("Mata_Kuliah", "Unknown")))
        print(f"Berhasil menambahkan: {mk_name} ke {slot['Hari']} sesi {slot['Sesi']} ({ruang_info})")
        return df_new
    else:
        mk_col = get_col_name(df, ["Mata Kuliah", "Mata_Kuliah"])
        mk_name = row.get(mk_col, row.get("Mata Kuliah", row.get("Mata_Kuliah", "Unknown")))
        print(f"Tidak dapat menemukan slot kosong untuk: {mk_name}")
        # Add as unplaced
        new_row = {
            **row,
            "Hari": "",
            "Sesi": "",
            "Jam": "",
            "Ruang": "",
            "Mode": "UNPLACED"
        }
        df_new = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        return df_new

def reschedule_course(df, course_filter, new_day=None, new_session=None, new_room=None):
    """
    Pindahkan mata kuliah yang sudah ada ke slot waktu baru
    Args:
        df: DataFrame dengan jadwal saat ini
        course_filter: dict untuk identifikasi mata kuliah (misal {"Mata_Kuliah": "skripsi", "Prodi": "Arsitektur"})
        new_day: hari target
        new_session: sesi target
        new_room: ruang target (opsional)
    Returns:
        DataFrame yang sudah dipindah mata kuliahnya
    """
    # Find matching courses
    mask = pd.Series([True] * len(df))
    for key, value in course_filter.items():
        if key in df.columns:
            mask = mask & (df[key].str.lower().str.contains(value.lower(), na=False))

    matching_courses = df[mask]

    if len(matching_courses) == 0:
        print("Tidak ditemukan mata kuliah yang sesuai dengan kriteria filter")
        return df

    mk_col = get_col_name(df, ["Mata Kuliah", "Mata_Kuliah"])
    print(f"Ditemukan {len(matching_courses)} mata kuliah yang cocok:")
    for _, row in matching_courses.iterrows():
        ruang_info = f"({row['Ruang']})" if row['Ruang'] else "(Zoom)"
        print(f"  - {row['Prodi']} {row['Semester']}{row['Kelas']}: {row[mk_col]} ({row['Hari']} {row['Jam']}) {ruang_info}")

    # Remove the courses and try to add them back to new slots
    df_updated = df[~mask].copy()

    for _, course in matching_courses.iterrows():
        df_updated = add_course_to_schedule(df_updated, course.to_dict(), new_day, new_session, new_room)

    return df_updated

def print_schedule_summary(df, day=None, prodi=None):
    """
    Cetak ringkasan jadwal saat ini
    Args:
        df: DataFrame dengan jadwal
        day: filter berdasarkan hari tertentu (opsional)
        prodi: filter berdasarkan prodi tertentu (opsional)
    """
    filtered_df = df.copy()

    if day:
        filtered_df = filtered_df[filtered_df["Hari"].str.upper() == day.upper()]

    if prodi:
        filtered_df = filtered_df[filtered_df["Prodi"].str.upper() == prodi.upper()]

    if len(filtered_df) == 0:
        print("Tidak ditemukan mata kuliah dengan filter yang ditentukan")
        return

    print(f"\n=== Ringkasan Jadwal ===")
    if day:
        print(f"Hari: {day}")
    if prodi:
        print(f"Prodi: {prodi}")
    print(f"Total mata kuliah: {len(filtered_df)}")

    # Group by day and session
    for day_name in ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]:
        day_courses = filtered_df[filtered_df["Hari"] == day_name]
        if len(day_courses) > 0:
            print(f"\n{day_name}:")
            for sess in sorted(day_courses["Sesi"].unique()):
                sess_courses = day_courses[day_courses["Sesi"] == sess]
                print(f"  Sesi {sess}:")
                for _, row in sess_courses.iterrows():
                    mk_col = get_col_name(filtered_df, ["Mata Kuliah", "Mata_Kuliah"])
                    room_info = f"({row['Ruang']})" if row['Ruang'] else "(Zoom)"
                    print(f"    {row['Prodi']} {row['Semester']}{row['Kelas']}: {row[mk_col]} {room_info}")

def print_available_slots_summary(available_slots, day=None, limit=10):
    """
    Cetak ringkasan slot yang tersedia
    Args:
        available_slots: list dari find_available_slots()
        day: filter berdasarkan hari (opsional)
        limit: batasi jumlah slot yang ditampilkan
    """
    if day:
        available_slots = [slot for slot in available_slots if slot["Hari"].upper() == day.upper()]

    if not available_slots:
        filter_info = f" untuk hari {day}" if day else ""
        print(f"Tidak ada slot yang tersedia{filter_info}")
        return

    print(f"\n=== Slot Tersedia ===")
    if day:
        print(f"Hari: {day}")

    for i, slot in enumerate(available_slots[:limit]):
        room_info = f"({slot['Room_Count']} ruang)" if slot['Room_Count'] > 0 else "(Zoom only)"
        print(f"{i+1}. {slot['Hari']} Sesi {slot['Sesi']} ({slot['Jam']}) {room_info}")
        if slot['Busy_Instructors']:
            print(f"    Dosen sibuk: {', '.join(slot['Busy_Instructors'][:3])}{'...' if len(slot['Busy_Instructors']) > 3 else ''}")
        if slot['Busy_Students']:
            print(f"    Mahasiswa sibuk: {len(slot['Busy_Students'])} kelompok")

    if len(available_slots) > limit:
        print(f"... dan {len(available_slots) - limit} slot lainnya")

# =========================
# CONTOH PENGGUNAAN
# =========================

def contoh_penggunaan():
    """
    Contoh cara menggunakan fitur fine-tuning
    """
    print("=== CONTOH PENGGUNAAN FITUR FINE-TUNING ===")
    print()

    print("1. Membaca jadwal yang sudah ada:")
    print("   df = pd.read_excel('jadwal_gabungan_SATU_TABEL_FINAL_PWK_ARS.xlsx', sheet_name='Jadwal Induk (Gabungan)')")
    print()

    print("2. Menghapus mata kuliah tertentu (misal skripsi dari Arsitektur):")
    print("   df_updated, removed = remove_courses_by_keyword(df, 'skripsi', prodi='Arsitektur')")
    print()

    print("3. Mencari slot kosong untuk hari Sabtu:")
    print("   available_saturday = find_available_slots(df_updated, day='Sabtu')")
    print("   print_available_slots_summary(available_saturday, day='Sabtu')")
    print()

    print("4. Menambahkan mata kuliah ke slot tertentu:")
    print("   if removed:")
    print("       course = removed.iloc[0].to_dict()  # ambil mata kuliah pertama yang dihapus")
    print("       df_final = add_course_to_schedule(df_updated, course, target_day='Sabtu', target_session=1)")
    print()

    print("5. Memindahkan mata kuliah yang sudah ada:")
    print("   df_moved = reschedule_course(df, {'Mata_Kuliah': 'algoritma', 'Prodi': 'Informatika'}, new_day='Sabtu')")
    print()

    print("6. Melihat ringkasan jadwal:")
    print("   print_schedule_summary(df_final, day='Sabtu')")
    print("   print_schedule_summary(df_final, prodi='Arsitektur')")
    print()

    print("7. Menyelesaikan konflik yang mungkin terjadi:")
    print("   df_resolved = resolve_all(df_final)")
    print()

    print("8. Menyimpan jadwal yang sudah disesuaikan:")
    print("   df_resolved.to_excel('jadwal_disesuaikan.xlsx', index=False)")

if __name__ == "__main__":
    contoh_penggunaan()