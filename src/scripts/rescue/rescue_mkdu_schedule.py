# -*- coding: utf-8 -*-
"""
Script rescue untuk memperbaiki jadwal MKDU khususnya AL ISLAM KEMUHAMMADIYAHAN III
yang salah dijadwalkan sebagai semester 1, padahal seharusnya semester 3.

Fungsi:
1. Load jadwal yang sudah ada dari jadwal.py
2. Identifikasi dan perbaiki semester untuk mata kuliah MKDU
3. Re-schedule ulang MKDU dengan semester yang benar
4. Pastikan tidak ada bentrok dengan jadwal lain
5. Generate jadwal baru yang sudah diperbaiki
"""

import pandas as pd
import numpy as np
import re
from collections import defaultdict
from pathlib import Path

# Import fungsi dari jadwal.py yang dibutuhkan
import sys
sys.path.append('.')
from jadwal import (
    norm, extract_semester, combine_dosen, sessions_for_day,
    allowed_days, build_maps, place_one, resolve_all, detect_conflicts,
    load_informatika, load_pengairan, load_elektro, load_arsitektur_source,
    parse_pwk_asli, BASE_DIR, FILE_MKDU, SHEET_MKDU,
    SESS_MON_THU, SESS_FRI, SESS_WE, DAYS_MON_THU, DAY_FRI, DAYS_WE, ALL_ROOMS
)

def load_mkdu_corrected():
    """
    Load MKDU dengan perbaikan semester berdasarkan nama mata kuliah
    """
    df = pd.read_excel(FILE_MKDU, sheet_name=SHEET_MKDU)
    out = []

    for _, r in df.iterrows():
        kode = norm(r.get("Kode Mata kuliah", r.get("Kode Mata Kuliah", "")))
        mk = norm(r.get("Nama Mata Kuliah", ""))
        if not (kode and mk):
            continue

        kelas = norm(r.get("Kelas", ""))
        sks = r.get("SKS", "")
        dos = norm(r.get("Dosen", ""))

        # Default semester extraction from class name
        sem = extract_semester(kelas)

        # Override semester based on course name
        mk_upper = mk.upper()
        if "AL ISLAM KEMUHAMMADIYAHAN III" in mk_upper or "AIK III" in mk_upper:
            sem = 3  # AL ISLAM KEMUHAMMADIYAHAN III is for semester 3
            # Update kelas to reflect correct semester
            if kelas and "-" in kelas:
                letter_part = kelas.split("-")[1]  # Get the letter part (A, B, C, etc.)
                kelas = f"3-{letter_part}"  # Change to semester 3
        elif "AL ISLAM KEMUHAMMADIYAHAN I" in mk_upper or "AIK I" in mk_upper:
            sem = 1
        elif "AL ISLAM KEMUHAMMADIYAHAN II" in mk_upper or "AIK II" in mk_upper:
            sem = 2
        elif "AL ISLAM KEMUHAMMADIYAHAN IV" in mk_upper or "AIK IV" in mk_upper:
            sem = 4
        elif "PENDIDIKAN AGAMA ISLAM" in mk_upper:
            sem = 1  # Semester 1
        elif "PANCASILA" in mk_upper:
            sem = 1  # Semester 1 (diperbaiki dari semester 2)
        elif "BAHASA INDONESIA" in mk_upper:
            sem = 1  # Semester 1
        elif "BAHASA INGGRIS" in mk_upper:
            sem = 1  # Semester 1 (diperbaiki dari semester 2)
        elif "BAHASA ARAB" in mk_upper:
            sem = 1  # Semester 1

        # Update kelas format for non-AIK III courses if needed
        if sem != extract_semester(kelas) and kelas and "-" in kelas:
            letter_part = kelas.split("-")[1]
            kelas = f"{sem}-{letter_part}"

        out.append(dict(
            Prodi="MKDU",
            Semester=sem,
            Kelas=kelas,
            Kode_MK=kode,
            Mata_Kuliah=mk,
            SKS=sks if pd.notna(sks) else "",
            Dosen=dos,
            D1=dos,
            D2="",
            NR=False
        ))

    return pd.DataFrame(out)

def create_corrected_schedule():
    """
    Buat jadwal lengkap dengan MKDU yang sudah diperbaiki
    """
    print("=== RESCUE MKDU SCHEDULE ===")
    print("Loading all course data...")

    # 1) Load semua data prodi (kecuali MKDU, akan di-load dengan versi yang diperbaiki)
    inf = load_informatika()
    peng = load_pengairan()
    el = load_elektro()
    ars_src = load_arsitektur_source()
    mkdu_corrected = load_mkdu_corrected()  # Gunakan versi yang diperbaiki

    print(f"Loaded courses: Informatika={len(inf)}, Pengairan={len(peng)}, Elektro={len(el)}, Arsitektur={len(ars_src)}, MKDU={len(mkdu_corrected)}")

    # Check MKDU corrected data
    print("\n=== MKDU Corrected Data ===")
    aik3_corrected = mkdu_corrected[mkdu_corrected['Mata_Kuliah'].str.contains('AL ISLAM KEMUHAMMADIYAHAN III', case=False, na=False)]
    if not aik3_corrected.empty:
        print("AL ISLAM KEMUHAMMADIYAHAN III courses:")
        print(aik3_corrected[['Mata_Kuliah', 'Semester', 'Kelas']])

    print("\nAll MKDU courses by semester:")
    mkdu_by_sem = mkdu_corrected.groupby('Semester')['Mata_Kuliah'].unique()
    for sem, courses in mkdu_by_sem.items():
        print(f"Semester {sem}: {courses}")

    # Hapus artefak MK numerik
    for df in (inf, peng, el, ars_src, mkdu_corrected):
        if not df.empty:
            mask_bad = df["Mata_Kuliah"].astype(str).str.fullmatch(r"\d+(\.\d+)?", na=False)
            df.drop(df[mask_bad].index, inplace=True)

    # 2) Penempatan awal semua kecuali PWK
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

            # Aturan khusus
            weekend_only = (row["Prodi"].upper() == "MKDU") or row["NR"]
            zoom = str(row["Semester"]) == "1"

            # Cari slot
            if row["Prodi"].upper() == "MKDU":
                days = ["Sabtu"]  # MKDU dipaksa Sabtu
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

    place_block(inf, "Informatika")
    place_block(peng, "Pengairan")
    place_block(el, None)  # Elektro sudah punya "Prodi" di frame-nya
    place_block(ars_src, None)  # Arsitektur auto-schedule
    place_block(mkdu_corrected, "MKDU")  # Gunakan MKDU yang sudah diperbaiki

    master = pd.DataFrame(rows)

    # 3) Masukkan PWK dari jadwal asli
    print("\nLoading PWK schedule...")
    pwk = parse_pwk_asli()
    for c in ("Semester", "Kelas", "Kode_MK", "SKS", "Dosen", "D1", "D2"):
        if c not in pwk.columns:
            pwk[c] = ""
    pwk.rename(columns={"Mode": "Mode"}, inplace=True)
    pwk = pwk[["Hari", "Sesi", "Jam", "Ruang", "Prodi", "Semester", "Kelas", "Kode_MK", "Mata_Kuliah", "SKS", "Dosen", "Mode", "D1", "D2"]]

    # Hapus PWK lama jika ada lalu tempel PWK asli
    master = master[master["Prodi"].str.lower() != "pwk"].reset_index(drop=True)
    master = pd.concat([master, pwk], ignore_index=True)

    # 4) Normalisasi aturan
    master.loc[master["Prodi"].str.upper() == "MKDU", "Hari"] = "Sabtu"
    master.loc[master["Semester"].astype(str) == "1", "Mode"] = "Zoom"
    master.loc[master["Mode"].str.lower().str.contains("zoom", na=False), "Ruang"] = ""

    # 5) Selesaikan konflik
    print("\nResolving conflicts...")
    master = resolve_all(master)

    # 6) Analysis and summary
    def count_conflicts(df):
        # ruang
        luring = df[~df["Mode"].str.lower().str.contains("zoom", na=False)]
        room_conf = luring[luring["Ruang"] != ""].groupby(["Hari", "Sesi", "Ruang"]).size()
        room_conflicts = int((room_conf > 1).sum())

        # dosen - hanya check D1 untuk konflik
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

    # Check MKDU final result
    print("\n=== MKDU Final Schedule Analysis ===")
    mkdu_final = master[master["Prodi"].str.upper() == "MKDU"]
    aik3_final = mkdu_final[mkdu_final['Mata_Kuliah'].str.contains('AL ISLAM KEMUHAMMADIYAHAN III', case=False, na=False)]

    if not aik3_final.empty:
        print("AL ISLAM KEMUHAMMADIYAHAN III final schedule:")
        print(aik3_final[['Hari', 'Sesi', 'Jam', 'Mata_Kuliah', 'Semester', 'Kelas', 'Ruang']])

    print(f"\nMKDU courses by semester (final):")
    mkdu_final_by_sem = mkdu_final.groupby('Semester')['Mata_Kuliah'].unique()
    for sem, courses in mkdu_final_by_sem.items():
        print(f"Semester {sem}: {courses}")

    return master, rc, ic, em

def save_corrected_schedule(master, rc, ic, em, output_path=None):
    """
    Simpan jadwal yang sudah diperbaiki ke Excel
    """
    if output_path is None:
        output_path = BASE_DIR / "jadwal_gabungan_MKDU_FIXED.xlsx"

    def format_class_name(kelas, semester):
        """Convert class format from IA to 1A, etc."""
        if not kelas:
            return "A"

        kelas = str(kelas).strip()

        # If already in correct format (like 1A, 2B), return as is
        if len(kelas) >= 2 and kelas[0].isdigit():
            return kelas

        # Convert roman/letter format to number format
        if semester and str(semester).isdigit():
            sem_num = str(semester)
            if kelas.startswith(('I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII')):
                # Extract letter part (A, B, C, etc.)
                letter_part = ""
                for char in kelas:
                    if char.isalpha() and char not in ['I', 'V', 'X']:
                        letter_part += char
                if not letter_part:
                    letter_part = "A"
                return f"{sem_num}{letter_part}"
            elif len(kelas) == 2 and kelas[0] in ['I', 'V'] and kelas[1].isalpha():
                # Cases like IA, IB, VA, VB
                if kelas[0] == 'I':
                    return f"1{kelas[1]}"
                elif kelas[0] == 'V':
                    return f"5{kelas[1]}"

        return kelas

    def format_semester_display(semester):
        """Convert semester to display format with both number and roman"""
        if not semester:
            return "I"

        sem_str = str(semester).strip()

        # If it's already a number, convert to roman for display
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

        # Sort schedule data by day and session
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

            # Format semester and class
            semester_display = format_semester_display(row["Semester"])
            class_formatted = format_class_name(row["Kelas"], row["Semester"])

            data_row = [
                str(i),                           # No
                row["Hari"],                      # HARI
                row["Jam"],                       # Jam
                semester_display,                 # SMT (Semester in Roman)
                class_formatted,                  # Kelas (formatted like 1A, 2B)
                row["Kode_MK"],                   # Kode MK
                row["Mata_Kuliah"],               # Mata Kuliah
                str(row["SKS"]) if pd.notna(row["SKS"]) else "",  # SKS
                dosen1,                           # Nama Dosen (Dosen 1)
                ruang,                            # Ruang
                dosen2                            # Dosen 2 (additional column)
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

    # Urut master
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

        # Keep the original combined sheet as well
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

    print(f"\n=== RESCUE COMPLETED ===")
    print(f"Jadwal yang diperbaiki tersimpan di: {output_path}")
    print(f"Ringkasan: Room={rc}, Dosen={ic}, Kosong={em}")
    return output_path

def main():
    """
    Main function untuk menjalankan rescue schedule MKDU
    """
    try:
        # Buat jadwal yang diperbaiki
        master, rc, ic, em = create_corrected_schedule()

        # Simpan hasil
        output_file = save_corrected_schedule(master, rc, ic, em)

        print(f"\n✅ MKDU Schedule rescue completed successfully!")
        print(f"📁 Output file: {output_file}")

        return True

    except Exception as e:
        print(f"❌ Error during MKDU schedule rescue: {str(e)}")
        return False

if __name__ == "__main__":
    main()