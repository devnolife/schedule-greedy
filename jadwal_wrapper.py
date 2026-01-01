#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wrapper untuk mengatasi perbedaan nama kolom antara jadwal.py dan file Excel
"""

import pandas as pd
import numpy as np
from collections import defaultdict

def norm(x):
    return "" if pd.isna(x) else str(x).strip()

def is_zoom(mode):
    return "zoom" in norm(mode).lower()

def instr_names(row):
    # Only check D1 for conflicts - D2 is just backup/replacement for D1
    # Handle both pandas Series and dict
    if hasattr(row, 'index'):
        # pandas Series
        d1_col = "Dosen 1" if "Dosen 1" in row.index else "D1"
        dosen_col = "Dosen" if "Dosen" in row.index else "Dosen"
        d1_val = row.get(d1_col, "") if hasattr(row, 'get') else row[d1_col] if d1_col in row.index else ""
        dosen_val = row.get(dosen_col, "") if hasattr(row, 'get') else row[dosen_col] if dosen_col in row.index else ""
    else:
        # dict
        d1_col = "Dosen 1" if "Dosen 1" in row else "D1"
        dosen_col = "Dosen" if "Dosen" in row else "Dosen"
        d1_val = row.get(d1_col, "")
        dosen_val = row.get(dosen_col, "")

    if norm(d1_val):
        return [norm(d1_val)]
    elif norm(dosen_val):
        return [norm(dosen_val)]
    else:
        return []

def build_maps_excel(df):
    """Build maps compatible with Excel column names"""
    instr_busy = defaultdict(set); room_busy = defaultdict(set); student_busy = defaultdict(set)

    # Handle different column names
    mode_col = "Mode (Zoom/Luring)" if "Mode (Zoom/Luring)" in df.columns else "Mode"

    for _, r in df.iterrows():
        day = norm(r["Hari"]); sesi = r["Sesi"]; mode = norm(r.get(mode_col, ""))
        if not day or pd.isna(sesi) or sesi == "": continue
        try:
            sesi_int = int(float(sesi))
        except (ValueError, TypeError):
            continue
        key = (day, sesi_int)

        # Track instructor conflicts
        for n in instr_names(r):
            if n: instr_busy[key].add(n)

        # Track room conflicts
        if not is_zoom(mode):
            room = norm(r.get("Ruang",""))
            if room: room_busy[key].add(room)

        # Track student conflicts - CRITICAL: Students can't be in 2 places at once
        student_id = (norm(r.get("Prodi","")), str(r.get("Semester","")), norm(r.get("Kelas","")))
        if all(student_id):  # Only add if all components are valid
            student_busy[key].add(student_id)

    return instr_busy, room_busy, student_busy

# Sessions definition (copy from jadwal.py)
SESS_MON_THU = [(1,"07:30–09:00"),(2,"09:00–10:30"),(3,"10:30–12:00"),(4,"13:00–14:30"),(5,"15:00–16:30")]
SESS_FRI     = [(1,"07:30–09:00"),(2,"09:00–10:30"),(3,"10:30–11:30"),(4,"13:00–14:30"),(5,"15:00–16:30")]
SESS_WE      = [(1,"07:30–09:00"),(2,"09:00–10:30"),(3,"10:30–12:00"),(4,"13:00–14:30"),(5,"15:00–16:30")]
ALL_ROOMS    = [f"3.{i}" for i in range(1,15)]

def sessions_for_day(day):
    if day == "Jumat": return SESS_FRI
    if day in ("Sabtu","Minggu"): return SESS_WE
    return SESS_MON_THU

def allowed_days(row):
    prodi = norm(row["Prodi"]).upper()
    kelas = norm(row["Kelas"]).upper()
    if prodi == "MKDU": return ["Sabtu"]
    if " NR" in kelas or kelas=="NR" or "NON REG" in kelas or "NON-REG" in kelas or "NONREG" in kelas:
        return ["Sabtu","Minggu"]
    return ["Senin","Selasa","Rabu","Kamis","Jumat"]

def place_one_excel(row, instr_busy, room_busy, student_busy=None):
    zoom = (str(row["Semester"]) == "1")

    # Create student identifier (prodi, semester, kelas)
    student_id = (norm(row["Prodi"]), str(row["Semester"]), norm(row["Kelas"]))

    for day in allowed_days(row):
        for sess, jam in sessions_for_day(day):
            key = (day, sess)
            names = instr_names(row)

            # Check instructor conflicts
            if any(n in instr_busy[key] for n in names if n):
                continue

            # Check student conflicts - CRITICAL: Students can't be in 2 places at once
            if student_busy is not None and student_id in student_busy[key]:
                continue

            if zoom:
                return dict(Hari=day, Sesi=sess, Jam=jam, Ruang="")
            else:
                # Use all available rooms (no lab rooms needed)
                for room in ALL_ROOMS:
                    if room not in room_busy[key]:
                        return dict(Hari=day, Sesi=sess, Jam=jam, Ruang=room)
    return dict(Hari="", Sesi="", Jam="", Ruang="")