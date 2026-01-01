# -*- coding: utf-8 -*-
"""
Script untuk menambahkan mata kuliah Pemrograman Berbasis Objek
untuk semester 5, kelas A sampai F di program studi Informatika.

Perubahan yang dilakukan:
1. Menambahkan mata kuliah "Pemrograman Berbasis Objek" untuk semester 5, kelas A-F
2. Menggunakan dosen yang sudah ada di data Informatika
3. Generate jadwal untuk Informatika saja tanpa mempengaruhi jadwal lain
"""

import pandas as pd
import numpy as np
import re
from collections import defaultdict
from pathlib import Path

# Import fungsi dari jadwal.py dan rescue_informatika_update.py
import sys
sys.path.append('.')
from jadwal import (
    norm, extract_semester, combine_dosen, sessions_for_day,
    allowed_days, build_maps, place_one, resolve_all, detect_conflicts,
    load_pengairan, load_elektro, load_arsitektur_source,
    parse_pwk_asli, BASE_DIR,
    SESS_MON_THU, SESS_FRI, SESS_WE, DAYS_MON_THU, DAY_FRI, DAYS_WE, ALL_ROOMS
)
from rescue_informatika_update import (
    extract_semester_num, parse_informatika_sheet, load_informatika_updated
)
from parse_jadwal_semester import parse_jadwal_semester

def create_lecturer_mapping_from_jadwal_semester():
    """
    Create lecturer mapping directly from JADWAL SEMESTER.xlsx using correct columns
    """
    print("Creating lecturer mapping from JADWAL SEMESTER.xlsx...")

    # Parse JADWAL SEMESTER.xlsx with updated parser
    jadwal_semester_df, all_lecturers = parse_jadwal_semester()

    # Create mapping by mata kuliah from JADWAL SEMESTER.xlsx
    mk_lecturer_map = {}
    matched_count = 0

    for _, row in jadwal_semester_df.iterrows():
        mk = str(row['Mata_Kuliah']).strip().upper()
        smt = str(row['SMT']).strip().upper()

        # Get dosen information (now correctly from columns 7 and 8)
        dosen1 = str(row['Dosen1']).strip() if row['Dosen1'] else ''
        dosen2 = str(row['Dosen2']).strip() if row['Dosen2'] else ''

        # Create mapping entry
        if mk not in mk_lecturer_map:
            mk_lecturer_map[mk] = {
                'D1': dosen1 if dosen1 else dosen2,  # Primary lecturer
                'D2': dosen2 if dosen1 and dosen2 != dosen1 else '',  # Secondary if different
                'Dosen': dosen1 if dosen1 else dosen2,  # For compatibility
                'entries': [(smt, dosen1, dosen2)]
            }
            matched_count += 1
        else:
            # If mata kuliah already exists, try to find different lecturers
            existing = mk_lecturer_map[mk]

            # If we don't have D2 yet and found different lecturer
            if not existing['D2'] and dosen1 and dosen1 != existing['D1']:
                mk_lecturer_map[mk]['D2'] = dosen1
            elif not existing['D2'] and dosen2 and dosen2 != existing['D1']:
                mk_lecturer_map[mk]['D2'] = dosen2

            # Add entry for tracking
            existing['entries'].append((smt, dosen1, dosen2))

    print(f"Found {len(mk_lecturer_map)} unique mata kuliah with lecturer assignments")
    print(f"Successfully mapped {matched_count} courses from JADWAL SEMESTER.xlsx")

    # Show sample mappings
    print("\nSample lecturer mappings from JADWAL SEMESTER.xlsx:")
    count = 0
    for mk, info in mk_lecturer_map.items():
        if info['D1']:
            print(f"  {mk} -> D1: {info['D1']} | D2: {info['D2'] if info['D2'] else '(kosong)'}")
            count += 1
            if count >= 5:
                break

    # Show statistics
    courses_with_both_lecturers = sum(1 for info in mk_lecturer_map.values() if info['D1'] and info['D2'])
    print(f"\nMata kuliah dengan kedua dosen: {courses_with_both_lecturers}/{len(mk_lecturer_map)}")

    return mk_lecturer_map

def clean_specialization_classes(informatika_courses):
    """
    Clean up specialization classes - remove regular classes C,D,E,F from specialization courses
    """
    print("Cleaning specialization classes...")

    # Define specialization courses (these should only be in AI-A/B, JK-A/B, RPL-A/B)
    specialization_courses = {
        'AI': ['APPLIED MACHINE LEARNING', 'DATA ENGINEERING AND BIG DATA SYSTEM', 'MATHEMATIC FOR AI'],
        'JK': ['ETHICAL HACKING AND PENETRATION', 'ADVANCE NETWORK SECURITY AND PROTOCOLS', 'Security Governance, Risk, and Compliance (GRC)'],
        'RPL': ['CLOUD NATIVE APPLICATION DEVELOPMENT', 'ADVANCED SOFTWARE DESIGN AND ARCHITECTURE', 'DEVOPS AND CI/CD PIPELINES']
    }

    # Convert to uppercase for matching
    all_specialization_courses = []
    for courses in specialization_courses.values():
        all_specialization_courses.extend([c.upper() for c in courses])

    cleaned_courses = []
    removed_count = 0

    for _, course in informatika_courses.iterrows():
        course_dict = course.to_dict()
        mk = str(course['Mata_Kuliah']).strip().upper()
        kelas = str(course['Kelas']).strip().upper()

        # Check if this is a specialization course in a regular class
        if (mk in all_specialization_courses and
            kelas in ['C', 'D', 'E', 'F'] and
            course['Semester'] == 5):
            # Remove this course - specialization courses should not be in regular classes
            removed_count += 1
            print(f"  Removed: {mk} from class {kelas}")
            continue

        cleaned_courses.append(course_dict)

    print(f"Removed {removed_count} specialization courses from regular classes C,D,E,F")
    return pd.DataFrame(cleaned_courses)

def update_informatika_with_lecturers():
    """
    Update Informatika courses with D1 and D2 lecturer names from JADWAL SEMESTER.xlsx
    """
    print("Updating Informatika courses with lecturer information from JADWAL SEMESTER.xlsx...")

    # Load existing Informatika data
    informatika_courses = load_informatika_updated()

    # Clean specialization classes first
    informatika_courses = clean_specialization_classes(informatika_courses)

    # Create lecturer mapping from JADWAL SEMESTER.xlsx
    lecturer_mapping = create_lecturer_mapping_from_jadwal_semester()

    print(f"Using lecturer mappings for {len(lecturer_mapping)} mata kuliah from JADWAL SEMESTER.xlsx")

    # Update Informatika courses with lecturer information
    updated_courses = []
    matched_count = 0
    unmatched_courses = []

    for _, course in informatika_courses.iterrows():
        course_dict = course.to_dict()

        # Try to find lecturer mapping by mata kuliah
        mk = str(course['Mata_Kuliah']).strip().upper()

        if mk in lecturer_mapping:
            lecturer_info = lecturer_mapping[mk]
            course_dict['D1'] = lecturer_info['D1']
            course_dict['D2'] = lecturer_info['D2']
            course_dict['Dosen'] = lecturer_info['Dosen']
            matched_count += 1
        else:
            # Keep existing lecturer info from informatika file
            existing_dosen = course_dict.get('Dosen', '').strip()
            if existing_dosen and existing_dosen != '8':
                course_dict['D1'] = existing_dosen
                course_dict['D2'] = ""  # No second lecturer found in JADWAL SEMESTER
                course_dict['Dosen'] = existing_dosen
            else:
                course_dict['D1'] = ""
                course_dict['D2'] = ""
                course_dict['Dosen'] = ""

            unmatched_courses.append(mk)

        updated_courses.append(course_dict)

    print(f"Successfully matched {matched_count} courses with JADWAL SEMESTER.xlsx")
    print(f"Courses not found in JADWAL SEMESTER.xlsx: {len(unmatched_courses)}")

    if unmatched_courses:
        print("Sample unmatched courses:")
        for course in unmatched_courses[:5]:
            print(f"  - {course}")

    return pd.DataFrame(updated_courses)

def add_semester_7_courses():
    """
    Menambahkan mata kuliah semester 7 sesuai dengan jumlah kelas yang ada
    """
    print("Adding semester 7 courses...")

    # Define semester 7 courses
    semester_7_courses = [
        {
            'Kode_MK': 'CP6552022544',
            'Mata_Kuliah': 'Standarisasi Keselamatan Kerja',
            'SKS': '2'
        },
        {
            'Kode_MK': 'BW6042502',
            'Mata_Kuliah': 'Etika Profesi',
            'SKS': '2'
        },
        {
            'Kode_MK': 'BW6042503',
            'Mata_Kuliah': 'Technopreneurship (Kepemimpinan dan kewirausahaan)',
            'SKS': '2'
        },
        {
            'Kode_MK': 'BW6042504',
            'Mata_Kuliah': 'Metodologi Penelitian dan Publikasi Ilmiah',
            'SKS': '2'
        }
    ]

    # Semester 7 courses are general courses for regular classes only (A, B, C, D, E)
    # NOT for class F and NOT for specialization classes (AI-A, AI-B, JK-A, JK-B, RPL-A, RPL-B)
    available_classes = ['A', 'B', 'C', 'D', 'E']

    print(f"Creating semester 7 courses for classes: {', '.join(available_classes)}")

    # Create semester 7 courses for each class
    sem7_courses = []
    for course_info in semester_7_courses:
        for kelas in available_classes:
            sem7_course = {
                'Prodi': 'Informatika',
                'Semester': 7,
                'Kelas': kelas,
                'Kode_MK': course_info['Kode_MK'],
                'Mata_Kuliah': course_info['Mata_Kuliah'],
                'SKS': course_info['SKS'],
                'Dosen': '',  # No lecturer assigned yet
                'D1': '',     # No Dosen 1
                'D2': '',     # No Dosen 2
                'NR': False
            }
            sem7_courses.append(sem7_course)

    # Convert to DataFrame
    sem7_df = pd.DataFrame(sem7_courses)

    print(f"Created {len(sem7_df)} semester 7 courses:")
    for course_info in semester_7_courses:
        course_count = len(available_classes)
        print(f"  {course_info['Mata_Kuliah']} ({course_info['Kode_MK']}) - {course_count} kelas")

    return sem7_df

def add_pbo_and_semester_7_courses():
    """
    Menambahkan mata kuliah Pemrograman Berbasis Objek untuk semester 5, kelas A-F
    dan mata kuliah semester 7 sesuai dengan jumlah kelas yang ada
    """
    print("Adding Pemrograman Berbasis Objek courses for semester 5, classes A-F...")
    print("Adding semester 7 courses for all available classes...")

    # Load Informatika data with updated lecturer information
    informatika_courses = update_informatika_with_lecturers()

    # Get lecturer mapping to find suitable lecturers for PBO
    lecturer_mapping = create_lecturer_mapping_from_jadwal_semester()

    # Find programming-related lecturers for PBO
    programming_lecturers = []
    for mk, info in lecturer_mapping.items():
        if any(keyword in mk.lower() for keyword in ['program', 'algoritma', 'software']):
            if info['D1'] and info['D1'] not in programming_lecturers:
                programming_lecturers.append(info['D1'])
            if info['D2'] and info['D2'] not in programming_lecturers:
                programming_lecturers.append(info['D2'])

    # If not enough from programming, add other computer science lecturers
    if len(programming_lecturers) < 2:
        for mk, info in lecturer_mapping.items():
            if any(keyword in mk.lower() for keyword in ['informatika', 'komputer', 'sistem']):
                if info['D1'] and info['D1'] not in programming_lecturers:
                    programming_lecturers.append(info['D1'])
                if info['D2'] and info['D2'] not in programming_lecturers:
                    programming_lecturers.append(info['D2'])

    # PBO courses should not have lecturer names assigned yet
    print(f"Creating PBO courses without lecturer assignments (belum ditentukan)")

    # Create PBO courses for classes A-F without lecturers
    pbo_courses = []
    for kelas in ['A', 'B', 'C', 'D', 'E', 'F']:
        pbo_course = {
            'Prodi': 'Informatika',
            'Semester': 5,
            'Kelas': kelas,
            'Kode_MK': f'INF5{kelas}PBO',  # Generate unique course code
            'Mata_Kuliah': 'Pemrograman Berbasis Objek',
            'SKS': '3',
            'Dosen': '',  # No lecturer assigned yet
            'D1': '',     # No Dosen 1
            'D2': '',     # No Dosen 2
            'NR': False
        }
        pbo_courses.append(pbo_course)

    # Convert to DataFrame
    pbo_df = pd.DataFrame(pbo_courses)

    print(f"Created {len(pbo_df)} PBO courses:")
    for _, course in pbo_df.iterrows():
        print(f"  {course['Semester']}{course['Kelas']} - {course['Mata_Kuliah']} | Dosen: (belum ditentukan)")

    # Add semester 7 courses
    sem7_df = add_semester_7_courses()

    # Combine with existing Informatika courses
    updated_informatika = pd.concat([informatika_courses, pbo_df, sem7_df], ignore_index=True)

    print(f"\nTotal Informatika courses after adding PBO and Semester 7: {len(updated_informatika)}")

    # Show semester 5 distribution
    sem5_courses = updated_informatika[updated_informatika['Semester'] == 5]
    print(f"Semester 5 courses: {len(sem5_courses)}")
    print("Semester 5 class distribution:")
    print(sem5_courses['Kelas'].value_counts().sort_index())

    # Show semester 7 distribution
    sem7_courses = updated_informatika[updated_informatika['Semester'] == 7]
    print(f"\nSemester 7 courses: {len(sem7_courses)}")
    print("Semester 7 class distribution:")
    print(sem7_courses['Kelas'].value_counts().sort_index())

    return updated_informatika, "", ""

def generate_informatika_schedule_with_pbo():
    """
    Generate schedule for Informatika only with the new PBO courses and semester 7
    """
    print("=== GENERATING INFORMATIKA SCHEDULE WITH PBO AND SEMESTER 7 ===")

    # Get Informatika courses with PBO and semester 7
    informatika_with_pbo, pbo_dosen1, pbo_dosen2 = add_pbo_and_semester_7_courses()

    # Initialize scheduling variables
    rows = []
    instr_busy = defaultdict(set)
    room_busy = defaultdict(set)
    student_busy = defaultdict(set)

    # Place PBO courses first to ensure they get scheduled
    pbo_courses = informatika_with_pbo[informatika_with_pbo['Mata_Kuliah'] == 'Pemrograman Berbasis Objek']
    sem7_courses = informatika_with_pbo[informatika_with_pbo['Semester'] == 7]
    other_courses = informatika_with_pbo[
        (informatika_with_pbo['Mata_Kuliah'] != 'Pemrograman Berbasis Objek') &
        (informatika_with_pbo['Semester'] != 7)
    ]

    placed_count = 0
    unplaced_count = 0

    print(f"Scheduling PBO courses first ({len(pbo_courses)} courses)...")
    print(f"Then scheduling Semester 7 courses ({len(sem7_courses)} courses)...")

    # Schedule PBO courses first
    for _, course in pbo_courses.iterrows():
        row = {
            "Prodi": course["Prodi"],
            "Semester": course["Semester"],
            "Kelas": course["Kelas"],
            "Kode_MK": course["Kode_MK"],
            "Mata_Kuliah": course["Mata_Kuliah"],
            "SKS": course["SKS"],
            "Dosen": course["Dosen"],
            "D1": course["D1"],
            "D2": course["D2"],
            "NR": bool(course["NR"])
        }

        # PBO specific scheduling - weekdays only
        days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat"]
        placed = False
        student_id = (norm(row["Prodi"]), str(row["Semester"]), norm(row["Kelas"]))

        for day in days:
            for sess, jam in sessions_for_day(day):
                key = (day, sess)
                names = [row["D1"]] if row["D1"] else ([row["Dosen"]] if row["Dosen"] else [])

                # Check instructor conflicts
                if any(n in instr_busy[key] for n in names if n):
                    continue

                # Check student conflicts
                if student_id in student_busy[key]:
                    continue

                # Find available room
                room = next((rm for rm in ALL_ROOMS if rm not in room_busy[key]), "")
                if not room:
                    continue

                slot = dict(Hari=day, Sesi=sess, Jam=jam, Ruang=room)
                room_busy[key].add(room)
                placed = True

                # Add instructor to busy list
                for n in names:
                    if n:
                        instr_busy[key].add(n)

                # Add student to busy list
                student_busy[key].add(student_id)

                rows.append({**slot, **row, "Mode": "Luring"})
                placed_count += 1
                print(f"  Placed PBO {row['Kelas']}: {day} Sesi {sess} - {room}")
                break
            if placed:
                break

        if not placed:
            rows.append(dict(Hari="", Sesi="", Jam="", Ruang="", **row, Mode="Luring (UNPLACED)"))
            unplaced_count += 1
            print(f"  Failed to place PBO {row['Kelas']}")

    pbo_placed = placed_count
    pbo_unplaced = unplaced_count
    print(f"PBO scheduling: Placed={pbo_placed}, Unplaced={pbo_unplaced}")

    # Now schedule semester 7 courses
    print(f"Scheduling semester 7 courses ({len(sem7_courses)} courses)...")

    for _, course in sem7_courses.iterrows():
        row = {
            "Prodi": course["Prodi"],
            "Semester": course["Semester"],
            "Kelas": course["Kelas"],
            "Kode_MK": course["Kode_MK"],
            "Mata_Kuliah": course["Mata_Kuliah"],
            "SKS": course["SKS"],
            "Dosen": course["Dosen"],
            "D1": course["D1"],
            "D2": course["D2"],
            "NR": bool(course["NR"])
        }

        # Semester 7 scheduling - weekdays preferred
        days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat"]
        placed = False
        student_id = (norm(row["Prodi"]), str(row["Semester"]), norm(row["Kelas"]))

        for day in days:
            for sess, jam in sessions_for_day(day):
                key = (day, sess)
                names = [row["D1"]] if row["D1"] else ([row["Dosen"]] if row["Dosen"] else [])

                # Check instructor conflicts (skip if no instructor assigned)
                if names and names[0] and any(n in instr_busy[key] for n in names if n):
                    continue

                # Check student conflicts
                if student_id in student_busy[key]:
                    continue

                # Find available room
                room = next((rm for rm in ALL_ROOMS if rm not in room_busy[key]), "")
                if not room:
                    continue

                slot = dict(Hari=day, Sesi=sess, Jam=jam, Ruang=room)
                room_busy[key].add(room)
                placed = True

                # Add instructor to busy list (only if instructor exists)
                for n in names:
                    if n:
                        instr_busy[key].add(n)

                # Add student to busy list
                student_busy[key].add(student_id)

                rows.append({**slot, **row, "Mode": "Luring"})
                placed_count += 1
                print(f"  Placed Sem7 {row['Kelas']} {row['Mata_Kuliah']}: {day} Sesi {sess} - {room}")
                break
            if placed:
                break

        if not placed:
            rows.append(dict(Hari="", Sesi="", Jam="", Ruang="", **row, Mode="Luring (UNPLACED)"))
            unplaced_count += 1
            print(f"  Failed to place Sem7 {row['Kelas']} {row['Mata_Kuliah']}")

    sem7_placed = placed_count - pbo_placed
    sem7_unplaced = unplaced_count - pbo_unplaced
    print(f"Semester 7 scheduling: Placed={sem7_placed}, Unplaced={sem7_unplaced}")

    # Now schedule other courses
    print(f"Scheduling other courses ({len(other_courses)} courses)...")

    for _, course in other_courses.iterrows():
        row = {
            "Prodi": course["Prodi"],
            "Semester": course["Semester"],
            "Kelas": course["Kelas"],
            "Kode_MK": course["Kode_MK"],
            "Mata_Kuliah": course["Mata_Kuliah"],
            "SKS": course["SKS"],
            "Dosen": course["Dosen"],
            "D1": course["D1"],
            "D2": course["D2"],
            "NR": bool(course["NR"])
        }

        # Scheduling rules
        weekend_only = row["NR"]
        zoom = str(row["Semester"]) == "1"
        is_pbo = "Pemrograman Berbasis Objek" in str(row["Mata_Kuliah"])

        # Determine allowed days
        if weekend_only:
            days = ["Sabtu", "Minggu"]
        elif is_pbo:
            # PBO should be scheduled on weekdays, not weekend
            days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat"]  # Monday-Friday only
        else:
            days = DAYS_MON_THU + DAY_FRI + DAYS_WE

        placed = False
        student_id = (norm(row["Prodi"]), str(row["Semester"]), norm(row["Kelas"]))

        for day in days:
            for sess, jam in sessions_for_day(day):
                key = (day, sess)
                names = [row["D1"]] if row["D1"] else ([row["Dosen"]] if row["Dosen"] else [])

                # Check instructor conflicts
                if any(n in instr_busy[key] for n in names if n):
                    continue

                # Check student conflicts
                if student_id in student_busy[key]:
                    continue

                if zoom:
                    slot = dict(Hari=day, Sesi=sess, Jam=jam, Ruang="")
                    placed = True
                else:
                    room = next((rm for rm in ALL_ROOMS if rm not in room_busy[key]), "")
                    if not room:
                        continue
                    slot = dict(Hari=day, Sesi=sess, Jam=jam, Ruang=room)
                    room_busy[key].add(room)
                    placed = True

                # Add instructor to busy list
                for n in names:
                    instr_busy[key].add(n)

                # Add student to busy list
                student_busy[key].add(student_id)

                rows.append({**slot, **row, "Mode": "Zoom" if zoom else "Luring"})
                placed_count += 1
                break
            if placed:
                break

        if not placed:
            rows.append(dict(Hari="", Sesi="", Jam="", Ruang="", **row, Mode="Zoom" if zoom else "Luring (UNPLACED)"))
            unplaced_count += 1

    total_placed = placed_count
    total_unplaced = unplaced_count
    other_placed = total_placed - pbo_placed - sem7_placed
    other_unplaced = total_unplaced - pbo_unplaced - sem7_unplaced
    print(f"Other courses scheduling: Placed={other_placed}, Unplaced={other_unplaced}")
    print(f"Total Informatika scheduling: Placed={total_placed}, Unplaced={total_unplaced}")

    # Convert to DataFrame
    informatika_schedule = pd.DataFrame(rows)

    # Apply rules
    informatika_schedule.loc[informatika_schedule["Semester"].astype(str) == "1", "Mode"] = "Zoom"
    informatika_schedule.loc[informatika_schedule["Mode"].str.lower().str.contains("zoom", na=False), "Ruang"] = ""

    return informatika_schedule, pbo_dosen1, pbo_dosen2

def save_informatika_pbo_schedule(schedule_df, pbo_dosen1, pbo_dosen2, output_path=None):
    """
    Save Informatika schedule with PBO and Semester 7 to Excel file
    """
    if output_path is None:
        output_path = BASE_DIR / "jadwal_informatika_pbo_semester7_lengkap.xlsx"

    def format_class_name(kelas, semester):
        """Convert class format"""
        if not kelas:
            return "A"
        return str(kelas).strip()

    def format_semester_display(semester):
        """Convert semester to display format"""
        if not semester:
            return "I"
        sem_str = str(semester).strip()
        if sem_str.isdigit():
            num = int(sem_str)
            roman_map = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII"}
            return roman_map.get(num, sem_str)
        return sem_str

    # Create header section
    header_data = []
    header_data.append(["JADWAL KULIAH INFORMATIKA"])
    header_data.append(["SEMESTER GANJIL TAHUN AKADEMIK 2025 - 2026"])
    header_data.append(["DENGAN PENAMBAHAN PBO DAN MATA KULIAH SEMESTER 7"])
    header_data.append([""])
    header_data.append(["FAKULTAS ", ":", "TEKNIK"])
    header_data.append(["JURUSAN", ":", "INFORMATIKA"])
    header_data.append(["PROGRAM STUDI", ":", "INFORMATIKA"])
    header_data.append(["KELAS", ":", "REGULER"])
    header_data.append([""])

    # Column headers
    header_data.append(["No.", "HARI", "Jam", "SMT", "Kelas", "Kode MK", "Mata Kuliah", "SKS", "Dosen 1", "Ruang", "Dosen 2"])
    header_data.append(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"])

    # Sort schedule data
    order = {d: i for i, d in enumerate(["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu", ""])}
    df_sorted = schedule_df.copy()
    df_sorted["__o"] = df_sorted["Hari"].map(order).fillna(99)
    df_sorted["Sesi_num"] = pd.to_numeric(df_sorted["Sesi"], errors="coerce").fillna(99).astype(int)
    df_sorted = df_sorted.sort_values(by=["__o", "Sesi_num", "Ruang"]).drop(columns=["__o", "Sesi_num"])

    # Data rows
    data_rows = []
    for i, (_, row) in enumerate(df_sorted.iterrows(), 1):
        ruang = row["Ruang"] if pd.notna(row["Ruang"]) and row["Ruang"] != "" else "Zoom"
        dosen1 = row["D1"] if pd.notna(row["D1"]) and row["D1"] != "" else ""
        dosen2 = row["D2"] if pd.notna(row["D2"]) and row["D2"] != "" else ""

        semester_display = format_semester_display(row["Semester"])
        class_formatted = format_class_name(row["Kelas"], row["Semester"])

        data_row = [
            str(i),
            row["Hari"],
            row["Jam"],
            semester_display,
            class_formatted,
            row["Kode_MK"],
            row["Mata_Kuliah"],
            str(row["SKS"]) if pd.notna(row["SKS"]) else "",
            dosen1,
            ruang,
            dosen2
        ]
        data_rows.append(data_row)

    # Combine header and data
    all_data = header_data + data_rows

    # Create DataFrame and write to Excel
    max_cols = max(len(row) for row in all_data)
    for row in all_data:
        while len(row) < max_cols:
            row.append("")

    df_output = pd.DataFrame(all_data)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df_output.to_excel(writer, sheet_name="Jadwal Informatika PBO+Sem7", index=False, header=False)

        # Add summary sheet
        summary_data = []
        summary_data.append(["RINGKASAN PENAMBAHAN MATA KULIAH"])
        summary_data.append([""])
        summary_data.append(["PEMROGRAMAN BERBASIS OBJEK (SEMESTER 5)"])
        summary_data.append(["Mata Kuliah", ":", "Pemrograman Berbasis Objek"])
        summary_data.append(["Semester", ":", "5 (Lima)"])
        summary_data.append(["Kelas", ":", "A, B, C, D, E, F"])
        summary_data.append(["SKS", ":", "3"])
        summary_data.append(["Dosen", ":", "(belum ditentukan)"])
        summary_data.append([""])
        summary_data.append(["MATA KULIAH SEMESTER 7"])
        summary_data.append(["1. (CP6552022544) Standarisasi Keselamatan Kerja - 2 SKS"])
        summary_data.append(["2. (BW6042502) Etika Profesi - 2 SKS"])
        summary_data.append(["3. (BW6042503) Technopreneurship - 2 SKS"])
        summary_data.append(["4. (BW6042504) Metodologi Penelitian - 2 SKS"])
        summary_data.append(["Dosen", ":", "(belum ditentukan)"])
        summary_data.append([""])

        # PBO course details
        pbo_courses = df_sorted[df_sorted['Mata_Kuliah'] == 'Pemrograman Berbasis Objek']
        if not pbo_courses.empty:
            summary_data.append(["JADWAL PEMROGRAMAN BERBASIS OBJEK:"])
            summary_data.append(["Kelas", "Hari", "Sesi", "Jam", "Ruang"])
            for _, course in pbo_courses.iterrows():
                summary_data.append([
                    f"5{course['Kelas']}",
                    course['Hari'],
                    str(course['Sesi']),
                    course['Jam'],
                    course['Ruang'] if course['Ruang'] else 'Zoom'
                ])

        # Semester 7 course details
        sem7_courses = df_sorted[df_sorted['Semester'] == 7]
        if not sem7_courses.empty:
            summary_data.append([""])
            summary_data.append(["JADWAL SEMESTER 7:"])
            summary_data.append(["Mata Kuliah", "Kelas", "Hari", "Sesi", "Jam", "Ruang"])
            for _, course in sem7_courses.iterrows():
                summary_data.append([
                    course['Mata_Kuliah'],
                    f"7{course['Kelas']}",
                    course['Hari'],
                    str(course['Sesi']),
                    course['Jam'],
                    course['Ruang'] if course['Ruang'] else 'Zoom'
                ])

        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name="Ringkasan", index=False, header=False)

    print(f"\n✅ Jadwal Informatika dengan PBO dan Semester 7 berhasil disimpan ke: {output_path}")

    # Show PBO course summary
    pbo_courses = schedule_df[schedule_df['Mata_Kuliah'] == 'Pemrograman Berbasis Objek']
    print(f"\n📚 Mata kuliah Pemrograman Berbasis Objek yang ditambahkan:")
    print(f"   - Semester: 5")
    print(f"   - Kelas: A, B, C, D, E, F ({len(pbo_courses)} kelas)")
    print(f"   - SKS: 3")
    print(f"   - Dosen: (belum ditentukan)")

    if not pbo_courses.empty:
        print(f"\n📅 Jadwal PBO:")
        for _, course in pbo_courses.iterrows():
            ruang_info = course['Ruang'] if course['Ruang'] else 'Zoom'
            print(f"   - Kelas 5{course['Kelas']}: {course['Hari']} Sesi {course['Sesi']} ({course['Jam']}) - {ruang_info}")

    # Show semester 7 course summary
    sem7_courses = schedule_df[schedule_df['Semester'] == 7]
    print(f"\n📚 Mata kuliah Semester 7 yang ditambahkan:")
    print(f"   - Jumlah mata kuliah: 4")
    print(f"   - Total kelas: {len(sem7_courses)}")
    print(f"   - Dosen: (belum ditentukan)")

    if not sem7_courses.empty:
        print(f"\n📅 Jadwal Semester 7:")
        current_mk = ""
        for _, course in sem7_courses.iterrows():
            ruang_info = course['Ruang'] if course['Ruang'] else 'Zoom'
            if course['Mata_Kuliah'] != current_mk:
                current_mk = course['Mata_Kuliah']
                print(f"   {current_mk}:")
            print(f"     - Kelas 7{course['Kelas']}: {course['Hari']} Sesi {course['Sesi']} ({course['Jam']}) - {ruang_info}")

    return output_path

def main():
    """
    Main function to add PBO and semester 7 courses and generate schedule
    """
    try:
        print("=== MENAMBAHKAN MATA KULIAH BARU ===")
        print("1. Pemrograman Berbasis Objek - Semester 5, Kelas A sampai F")
        print("2. Mata Kuliah Semester 7 - 4 mata kuliah sesuai jumlah kelas")
        print("")

        # Generate schedule with PBO and semester 7
        informatika_schedule, pbo_dosen1, pbo_dosen2 = generate_informatika_schedule_with_pbo()

        # Save results
        output_file = save_informatika_pbo_schedule(informatika_schedule, pbo_dosen1, pbo_dosen2)

        print(f"\n🎉 Penambahan mata kuliah berhasil!")
        print(f"📁 File output: {output_file}")

        return True

    except Exception as e:
        print(f"❌ Error saat menambahkan mata kuliah: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()