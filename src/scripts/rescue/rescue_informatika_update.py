# -*- coding: utf-8 -*-
"""
Script rescue untuk update struktur mata kuliah Informatika.

Perubahan yang dilakukan:
1. Mata kuliah peminatan semester 5 dari 6 kelas (VA-VF) menjadi 2 kelas saja
2. Menggunakan struktur kelas baru dari informatika.xlsx:
   - 5A: Kelas umum
   - 5AI-A: Peminatan AI
   - 5JK-A: Peminatan Jaringan Komputer/Security

Fungsi:
1. Load data Informatika baru dari informatika.xlsx
2. Update struktur dengan kelas peminatan yang lebih efisien
3. Generate jadwal ulang dengan data Informatika yang sudah diperbarui
4. Pastikan tidak ada bentrok dengan prodi lain
"""

import pandas as pd
import numpy as np
import re
from collections import defaultdict
from pathlib import Path

# Import fungsi dari jadwal.py dan rescue_mkdu_schedule.py
import sys
sys.path.append('.')
from jadwal import (
    norm, extract_semester, combine_dosen, sessions_for_day,
    allowed_days, build_maps, place_one, resolve_all, detect_conflicts,
    load_pengairan, load_elektro, load_arsitektur_source,
    parse_pwk_asli, BASE_DIR,
    SESS_MON_THU, SESS_FRI, SESS_WE, DAYS_MON_THU, DAY_FRI, DAYS_WE, ALL_ROOMS
)
from rescue_mkdu_schedule import load_mkdu_corrected

def extract_semester_num(smt_str):
    """Extract semester number from SMT column"""
    if pd.isna(smt_str):
        return None
    s = str(smt_str).strip().upper()
    if not s:
        return None
    # Extract first digit from string like '1A', '3B', etc.
    m = re.match(r'^(\d+)', s)
    if m:
        return int(m.group(1))
    return None

def parse_informatika_sheet(sheet_name):
    """Parse informatika course data from Excel sheet"""
    df = pd.read_excel(BASE_DIR / "informatika.xlsx", sheet_name=sheet_name, header=None)
    courses = []

    # Find header row (contains 'KODE MK', 'MATA KULIAH', etc.)
    header_row = None
    for i in range(min(15, len(df))):
        row_str = ' '.join([str(val) for val in df.iloc[i] if pd.notna(val)]).upper()
        if 'KODE' in row_str and 'MATA' in row_str:
            header_row = i
            break

    if header_row is None:
        return courses

    # Skip header row and number row, start from actual data
    data_start = header_row + 2  # Skip header and number row

    for i in range(data_start, len(df)):
        row = df.iloc[i]
        # Skip rows that are clearly not course data
        if pd.isna(row.iloc[1]) or str(row.iloc[1]).strip() == '':  # HARI column empty
            continue

        try:
            smt = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ''
            kode = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else ''
            mk = str(row.iloc[5]).strip() if pd.notna(row.iloc[5]) else ''
            sks = str(row.iloc[6]).strip() if pd.notna(row.iloc[6]) else ''
            dosen = str(row.iloc[7]).strip() if pd.notna(row.iloc[7]) else ''

            if kode and mk and smt:  # Valid course data
                sem_num = extract_semester_num(smt)
                courses.append({
                    'Kode_MK': kode,
                    'Mata_Kuliah': mk,
                    'SMT': smt,
                    'Semester': sem_num,
                    'SKS': sks,
                    'Dosen': dosen
                })
        except:
            continue

    return courses

def load_informatika_updated():
    """
    Load updated Informatika course structure from informatika.xlsx
    """
    print("Loading updated Informatika data from informatika.xlsx...")

    # Parse both sheets
    sheet1_courses = parse_informatika_sheet('Jadwal INFORMATIKA (simak)')
    sheet2_courses = parse_informatika_sheet('jadwal informatika1')

    # Combine and deduplicate
    all_courses = []
    seen_keys = set()  # Use (kode, smt) as key to allow different specialization classes

    for course in sheet1_courses + sheet2_courses:
        key = (course['Kode_MK'], course['SMT'])
        if key not in seen_keys:
            all_courses.append(course)
            seen_keys.add(key)

    # Convert to proper format for scheduling
    out = []
    for course in all_courses:
        # Extract class from SMT (like 5A, 5AI-A, 5JK-A)
        smt = course['SMT']
        semester = course['Semester']

        # Parse class name from SMT
        if len(smt) > 1:
            kelas = smt[1:]  # Remove semester digit
            if kelas.startswith('-'):
                kelas = kelas[1:]  # Remove leading dash
        else:
            kelas = 'A'

        out.append(dict(
            Prodi="Informatika",
            Semester=semester,
            Kelas=kelas,
            Kode_MK=course['Kode_MK'],
            Mata_Kuliah=course['Mata_Kuliah'],
            SKS=course['SKS'],
            Dosen=course['Dosen'],
            D1=course['Dosen'],
            D2="",
            NR=False
        ))

    df = pd.DataFrame(out)
    print(f"Loaded {len(df)} Informatika courses")

    # Show semester distribution
    if not df.empty:
        print("Semester distribution:")
        print(df['Semester'].value_counts().sort_index())

        # Show semester 5 specialization classes
        sem5 = df[df['Semester'] == 5]
        if not sem5.empty:
            print(f"\nSemester 5 courses: {len(sem5)}")
            print("Specialization classes:")
            print(sem5['Kelas'].value_counts())

    return df

def create_updated_schedule():
    """
    Create complete schedule with updated Informatika structure
    """
    print("=== RESCUE INFORMATIKA UPDATE ===")
    print("Loading all course data with updated Informatika...")

    # 1) Load all course data (with updated Informatika)
    inf_updated = load_informatika_updated()  # Use updated version
    peng = load_pengairan()
    el = load_elektro()
    ars_src = load_arsitektur_source()
    mkdu_corrected = load_mkdu_corrected()  # Use corrected MKDU

    print(f"Loaded courses: Informatika={len(inf_updated)}, Pengairan={len(peng)}, Elektro={len(el)}, Arsitektur={len(ars_src)}, MKDU={len(mkdu_corrected)}")

    # Remove numeric artifacts
    for df in (inf_updated, peng, el, ars_src, mkdu_corrected):
        if not df.empty:
            mask_bad = df["Mata_Kuliah"].astype(str).str.fullmatch(r"\d+(\.\d+)?", na=False)
            df.drop(df[mask_bad].index, inplace=True)

    # 2) Place all courses except PWK
    rows = []
    instr_busy = defaultdict(set)
    room_busy = defaultdict(set)
    student_busy = defaultdict(set)

    def place_block(df_block, prodi_name):
        nonlocal rows, instr_busy, room_busy, student_busy
        placed_count = 0
        unplaced_count = 0

        for _, c in df_block.iterrows():
            row = {
                "Prodi": prodi_name if prodi_name else c.get("Prodi", ""),
                "Semester": c.get("Semester", ""),
                "Kelas": c.get("Kelas", ""),
                "Kode_MK": c.get("Kode_MK", ""),
                "Mata_Kuliah": c.get("Mata_Kuliah", ""),
                "SKS": c.get("SKS", ""),
                "Dosen": c.get("Dosen", ""),
                "D1": c.get("D1", ""),
                "D2": c.get("D2", ""),
                "NR": bool(c.get("NR", False))
            }

            # Scheduling rules
            weekend_only = (row["Prodi"].upper() == "MKDU") or row["NR"]
            zoom = str(row["Semester"]) == "1"

            # Determine allowed days
            if row["Prodi"].upper() == "MKDU":
                days = ["Sabtu"]  # MKDU forced to Saturday
            elif weekend_only:
                days = ["Sabtu", "Minggu"]
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

        print(f"{prodi_name or 'Unknown'}: Placed={placed_count}, Unplaced={unplaced_count}")

    # Place all courses
    place_block(inf_updated, "Informatika")  # Use updated Informatika
    place_block(peng, "Pengairan")
    place_block(el, None)
    place_block(ars_src, None)
    place_block(mkdu_corrected, "MKDU")

    master = pd.DataFrame(rows)

    # 3) Add PWK from original schedule
    print("\nLoading PWK schedule...")
    pwk = parse_pwk_asli()
    for c in ("Semester", "Kelas", "Kode_MK", "SKS", "Dosen", "D1", "D2"):
        if c not in pwk.columns:
            pwk[c] = ""
    pwk.rename(columns={"Mode": "Mode"}, inplace=True)
    pwk = pwk[["Hari", "Sesi", "Jam", "Ruang", "Prodi", "Semester", "Kelas", "Kode_MK", "Mata_Kuliah", "SKS", "Dosen", "Mode", "D1", "D2"]]

    # Remove old PWK and add original PWK
    master = master[master["Prodi"].str.lower() != "pwk"].reset_index(drop=True)
    master = pd.concat([master, pwk], ignore_index=True)

    # 4) Apply rules
    master.loc[master["Prodi"].str.upper() == "MKDU", "Hari"] = "Sabtu"
    master.loc[master["Semester"].astype(str) == "1", "Mode"] = "Zoom"
    master.loc[master["Mode"].str.lower().str.contains("zoom", na=False), "Ruang"] = ""

    # 5) Resolve conflicts
    print("\nResolving conflicts...")
    master = resolve_all(master)

    # 6) Analysis
    def count_conflicts(df):
        # Room conflicts
        luring = df[~df["Mode"].str.lower().str.contains("zoom", na=False)]
        room_conf = luring[luring["Ruang"] != ""].groupby(["Hari", "Sesi", "Ruang"]).size()
        room_conflicts = int((room_conf > 1).sum())

        # Instructor conflicts
        slot_map = defaultdict(list)
        for i, r in df.iterrows():
            day = norm(r["Hari"])
            sesi = r["Sesi"]
            if not day or not sesi:
                continue
            d1 = norm(r.get("D1", ""))
            if d1:
                slot_map[(day, int(sesi), d1)].append(i)
            elif norm(r.get("Dosen", "")):
                slot_map[(day, int(sesi), norm(r["Dosen"]))].append(i)

        instr_conflicts = sum(1 for _, idxs in slot_map.items() if len(idxs) > 1)
        empties = int(((df["Hari"] == "") | (df["Sesi"] == "")).sum())
        return room_conflicts, instr_conflicts, empties

    rc, ic, em = count_conflicts(master)

    # Show Informatika analysis
    print("\n=== Informatika Updated Analysis ===")
    inf_final = master[master["Prodi"].str.upper() == "INFORMATIKA"]

    if not inf_final.empty:
        print(f"Total Informatika courses scheduled: {len(inf_final)}")
        print("Semester distribution (final):")
        print(inf_final['Semester'].value_counts().sort_index())

        sem5_final = inf_final[inf_final['Semester'] == 5]
        if not sem5_final.empty:
            print(f"\nSemester 5 courses: {len(sem5_final)}")
            print("Specialization classes in final schedule:")
            print(sem5_final['Kelas'].value_counts())

            print("\nSample semester 5 courses:")
            print(sem5_final[['Hari', 'Sesi', 'Jam', 'Mata_Kuliah', 'Kelas', 'Ruang']].head(10))

    return master, rc, ic, em

def save_updated_schedule(master, rc, ic, em, output_path=None):
    """
    Save updated schedule to Excel
    """
    if output_path is None:
        output_path = BASE_DIR / "jadwal_gabungan_INFORMATIKA_UPDATED.xlsx"

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

    def create_prodi_sheet(df_prodi, prodi_name, writer):
        # Create header section
        header_data = []
        header_data.append(["JADWAL KULIAH "])
        header_data.append(["SEMESTER GANJIL TAHUN AKADEMIK 2025 - 2026"])
        header_data.append([""])
        header_data.append(["FAKULTAS ", ":", "TEKNIK"])

        if prodi_name.upper() == "INFORMATIKA":
            header_data.append(["JURUSAN", ":", "INFORMATIKA"])
            header_data.append(["PROGRAM STUDI", ":", "INFORMATIKA"])
        elif prodi_name.upper() == "PWK":
            header_data.append(["JURUSAN", ":", "PENGEMBANGAN WILAYAH DAN KOTA"])
            header_data.append(["PROGRAM STUDI", ":", "PENGEMBANGAN WILAYAH DAN KOTA"])
        elif prodi_name.upper() == "ELEKTRO":
            header_data.append(["JURUSAN", ":", "TEKNIK ELEKTRO"])
            header_data.append(["PROGRAM STUDI", ":", "TEKNIK ELEKTRO"])
        elif prodi_name.upper() == "PENGAIRAN":
            header_data.append(["JURUSAN", ":", "TEKNIK SIPIL"])
            header_data.append(["PROGRAM STUDI", ":", "TEKNIK PENGAIRAN"])
        elif prodi_name.upper() == "ARSITEKTUR":
            header_data.append(["JURUSAN", ":", "ARSITEKTUR"])
            header_data.append(["PROGRAM STUDI", ":", "ARSITEKTUR"])
        elif prodi_name.upper() == "MKDU":
            header_data.append(["JURUSAN", ":", "MATA KULIAH DASAR UMUM"])
            header_data.append(["PROGRAM STUDI", ":", "MKDU"])
        else:
            header_data.append(["JURUSAN", ":", prodi_name.upper()])
            header_data.append(["PROGRAM STUDI", ":", prodi_name.upper()])

        header_data.append(["KELAS", ":", "REGULER"])
        header_data.append([""])

        # Column headers
        header_data.append(["No.", "HARI", "Jam", "SMT", "Kelas", "Kode MK", "Mata Kuliah", "SKS", "Nama Dosen", "Ruang"])
        header_data.append(["", "", "", "", "", "", "", "", "Dosen 1", "Dosen 2"])
        header_data.append(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"])

        # Sort schedule data
        order = {d: i for i, d in enumerate(["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu", ""])}
        df_sorted = df_prodi.copy()
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
        df_output.to_excel(writer, sheet_name=f"Jadwal {prodi_name.upper()}",
                          index=False, header=False)

    # Sort master
    order = {d: i for i, d in enumerate(["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu", ""])}
    master["__o"] = master["Hari"].map(order).fillna(99)
    master["Sesi_num"] = pd.to_numeric(master["Sesi"], errors="coerce").fillna(99).astype(int)
    master = master.sort_values(by=["__o", "Sesi_num", "Ruang", "Prodi", "Semester", "Kelas"]).drop(columns=["__o", "Sesi_num"])

    with pd.ExcelWriter(output_path, engine="openpyxl") as w:
        # Create sheets for each prodi
        prodis = ["Informatika", "PWK", "Elektro", "Pengairan", "Arsitektur", "MKDU"]

        for prodi in prodis:
            df_prodi = master[master["Prodi"].str.upper() == prodi.upper()]
            if not df_prodi.empty:
                create_prodi_sheet(df_prodi, prodi, w)

        # Combined sheet
        master.rename(columns={
            "Kode_MK": "Kode MK",
            "Mata_Kuliah": "Mata Kuliah",
            "D1": "Dosen 1",
            "D2": "Dosen 2",
            "Mode": "Mode (Zoom/Luring)"
        }).to_excel(w, index=False, sheet_name="Jadwal Induk (Gabungan)")

        # Conflict summary
        pd.DataFrame({
            "Metric": ["Room Conflicts", "Instructor Conflicts", "Rows w/ Empty Day/Session"],
            "Value": [rc, ic, em]
        }).to_excel(w, index=False, sheet_name="Ringkasan Konflik")

    print(f"\n=== INFORMATIKA UPDATE COMPLETED ===")
    print(f"Updated schedule saved to: {output_path}")
    print(f"Summary: Room={rc}, Instructor={ic}, Empty={em}")
    return output_path

def main():
    """
    Main function to run Informatika update
    """
    try:
        # Create updated schedule
        master, rc, ic, em = create_updated_schedule()

        # Save results
        output_file = save_updated_schedule(master, rc, ic, em)

        print(f"\n✅ Informatika schedule update completed successfully!")
        print(f"📁 Output file: {output_file}")

        return True

    except Exception as e:
        print(f"❌ Error during Informatika update: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()