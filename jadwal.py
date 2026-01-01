# -*- coding: utf-8 -*-
"""
Gabung jadwal 5 prodi + MKDU ke SATU TABEL tanpa bentrok.
- PWK: pakai jadwal asli (hari–jam–ruang).
- Arsitektur: auto-schedule (Senin–Jumat) tanpa bentrok.
Aturan:
- NR (Non-Reguler) & MKDU => Sabtu/Minggu (MKDU dipaksa Sabtu).
- Semester 1 => Zoom (tanpa ruangan).
- Tidak boleh bentrok dosen & ruangan.
- Jangan geser PWK saat menyelesaikan konflik.
"""

import pandas as pd
import numpy as np
import re
from collections import defaultdict
from pathlib import Path

# =========================
# KONFIGURASI (ubah kalau perlu)
# =========================

# MKDU keywords to filter out from other prodi
MKDU_KEYWORDS = [
    'pancasila', 'bahasa indonesia', 'pendidikan agama', 'bahasa inggris',
    'bahasa arab', 'aik', 'aqidah islam', 'komprehensif aik'
]

def is_mkdu_course(mata_kuliah):
    """Check if a course is MKDU based on keywords"""
    if not mata_kuliah:
        return False
    mk_lower = str(mata_kuliah).lower()
    return any(keyword in mk_lower for keyword in MKDU_KEYWORDS)
BASE_DIR = Path(".")  # current directory
FILE_INF = BASE_DIR / "JADWAL SEMESTER.xlsx"
FILE_PENG = BASE_DIR / "Struktur Mata Kuliah Final ok.xlsx"  # Reg & NR
FILE_EL   = BASE_DIR / "Pengampuh MK T. Elektro.xlsx"        # Reg & NR
FILE_PWK  = BASE_DIR / "jadwal pwk ganjil 2025 2026.xlsx"    # jadwal asli
FILE_ARS  = BASE_DIR / "JADWAL GANJIL 25-26_ARSITEKTUR.xlsx"
FILE_MKDU = BASE_DIR / "MKDU 20251.xlsx"

SHEET_INF = "Sheet1"
SHEET_PENG_REG = "Jadwal Reguler"
SHEET_PENG_NR  = "Jadwal Non Reg"
SHEET_EL_REG   = "Pengampuh MK 2025(1) REG "
SHEET_EL_NR    = "Pengampuh MK 2025(1) NR "
SHEET_PWK      = "Sheet1"
SHEET_ARS      = "Pengampuh GANJIL"
SHEET_MKDU     = "Sheet1"

# Kolom-kolom kemungkinan (Arsitektur kadang beda nama header)
ARS_COL_KODE   = ("Kode MK", "KODE MK", "kode mk")
ARS_COL_MK     = ("Mata Kuliah", "MATA KULIAH", "NAMA MATA KULIAH")
ARS_COL_KELAS  = ("Kls", "Kelas", "KELAS")
ARS_COL_SEM    = ("SMT", "Semester", "SEMESTER")
ARS_COL_SKS    = ("SKS",)
ARS_COL_DOSEN  = ("Nama Dosen", "Dosen", "DOSEN")

# =========================
# UTIL & STRUKTUR WAKTU
# =========================
ROMAN_MAP = {"I":1,"II":2,"III":3,"IV":4,"V":5,"VI":6,"VII":7,"VIII":8}

def norm(x): return "" if pd.isna(x) else str(x).strip()

def extract_semester(x):
    s = norm(x).upper()
    if not s: return ""
    m = re.match(r'^(VIII|VII|VI|IV|V|III|II|I)', s)
    if m: return ROMAN_MAP[m.group(1)]
    m = re.match(r'^(\d+)', s)
    if m:
        try: return int(m.group(1))
        except: return ""
    return ""

def combine_dosen(*vals):
    flat = [norm(v) for v in vals if norm(v)]
    seen = set(); out = []
    for v in flat:
        if v not in seen:
            out.append(v); seen.add(v)
    if not out: return "", "", ""
    d1 = out[0]; d2 = out[1] if len(out)>1 else ""
    return "; ".join(out), d1, d2

# Sesi
SESS_MON_THU = [(1,"07:30–09:00"),(2,"09:00–10:30"),(3,"10:30–12:00"),(4,"13:00–14:30"),(5,"15:00–16:30")]
SESS_FRI     = [(1,"07:30–09:00"),(2,"09:00–10:30"),(3,"10:30–11:30"),(4,"13:00–14:30"),(5,"15:00–16:30")]
SESS_WE      = [(1,"07:30–09:00"),(2,"09:00–10:30"),(3,"10:30–12:00"),(4,"13:00–14:30"),(5,"15:00–16:30")]
DAYS_MON_THU = ["Senin","Selasa","Rabu","Kamis"]
DAY_FRI      = ["Jumat"]
DAYS_WE      = ["Sabtu","Minggu"]
ALL_ROOMS    = [f"3.{i}" for i in range(1,15)]
LAB_ROOMS    = []  # No lab rooms needed since practicum courses are removed

def is_praktikum(mata_kuliah):
    """Check if a course is a practicum/lab course"""
    mk_lower = str(mata_kuliah).lower()
    practicum_keywords = ['praktikum', 'praktek', 'lab ', 'laboratorium']
    return any(keyword in mk_lower for keyword in practicum_keywords)

def sessions_for_day(day):
    if day == "Jumat": return SESS_FRI
    if day in ("Sabtu","Minggu"): return SESS_WE
    return SESS_MON_THU

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
        roman_map = {1:"I", 2:"II", 3:"III", 4:"IV", 5:"V", 6:"VI", 7:"VII", 8:"VIII"}
        return roman_map.get(num, sem_str)

    return sem_str

# =========================
# LOAD & NORMALISASI DATA PRODI
# =========================
def load_informatika():
    df = pd.read_excel(FILE_INF, sheet_name=SHEET_INF)
    kode_col, mk_col, kelas_col, sks_col = "Kode MK", "Mata Kuliah", "SMT", "SKS"
    dosen_cols = [c for c in df.columns if "dosen" in c.lower()]
    out = []
    for _, r in df.iterrows():
        kode = norm(r.get(kode_col,""))
        mk   = norm(r.get(mk_col,""))
        if not (kode and mk): continue
        if mk=="4" and kode=="3": continue  # artefak header
        # Skip KOMPREHENSIF AIK, practicum, and MKDU courses for Informatika
        if "KOMPREHENSIF AIK" in mk.upper():
            continue
        if is_praktikum(mk):
            continue

        # Skip MKDU courses (will be handled in separate MKDU sheet)
        if is_mkdu_course(mk):
            continue

        kelas = norm(r.get(kelas_col,""))
        sem = extract_semester(kelas)
        sks = r.get(sks_col,"")
        dosen, d1, d2 = combine_dosen(*[r.get(c,"") for c in dosen_cols])
        out.append(dict(Prodi="Informatika", Semester=sem, Kelas=kelas, Kode_MK=kode,
                        Mata_Kuliah=mk, SKS=sks if pd.notna(sks) else "", Dosen=dosen, D1=d1, D2=d2, NR=False))
    return pd.DataFrame(out)

def load_pengairan():
    out = []
    for sh, is_nr in [(SHEET_PENG_REG, False), (SHEET_PENG_NR, True)]:
        df = pd.read_excel(FILE_PENG, sheet_name=sh)
        poss_dosen = [c for c in df.columns if "dosen" in c.lower() or "unnamed" in c.lower()]
        for _, r in df.iterrows():
            kode = norm(r.get("Kode MK",""))
            mk   = norm(r.get("Mata Kuliah",""))
            if not (kode and mk) or mk=="4": continue
            # Skip MKDU courses (they should only be in MKDU prodi)
            if is_mkdu_course(mk): continue
            kelas = norm(r.get("SMT",""))
            sem = extract_semester(kelas)
            sks = r.get("SKS","")
            dosen, d1, d2 = combine_dosen(*[r.get(c,"") for c in poss_dosen])
            kelas2 = (kelas + (" NR" if is_nr else "")).strip() or ("NR" if is_nr else "")
            out.append(dict(Prodi="Pengairan", Semester=sem, Kelas=kelas2, Kode_MK=kode,
                            Mata_Kuliah=mk, SKS=sks if pd.notna(sks) else "", Dosen=dosen, D1=d1, D2=d2, NR=is_nr))
    return pd.DataFrame(out)

def parse_el(df):
    # cari baris header yang memuat 'Kelas'
    header = None
    for i, row in df.iterrows():
        if any(norm(v).lower()=="kelas" for v in row.values if pd.notna(v)): header = i; break
    if header is None: return pd.DataFrame()
    df2 = df.iloc[header:]
    df2.columns = df2.iloc[0]
    df2 = df2[1:]
    out = []
    for _, r in df2.iterrows():
        kode = norm(r.get("Kode MK",""))
        mk   = norm(r.get("Mata Kuliah",""))
        kelas= norm(r.get("Kelas",""))
        if not (kode and mk and kelas): continue
        # Skip MKDU courses (they should only be in MKDU prodi)
        if is_mkdu_course(mk): continue
        sem = extract_semester(kelas)
        sks = r.get("SKS","")
        dos  = norm(r.get("Nama Dosen",""))
        out.append((kode,mk,kelas,sem,sks if pd.notna(sks) else "",dos))
    cols = ["Kode_MK","Mata_Kuliah","Kelas","Semester","SKS","Dosen"]
    return pd.DataFrame(out, columns=cols)

def load_elektro():
    reg = parse_el(pd.read_excel(FILE_EL, sheet_name=SHEET_EL_REG))
    nr  = parse_el(pd.read_excel(FILE_EL, sheet_name=SHEET_EL_NR))
    reg["Prodi"]="Elektro"; reg["NR"]=False; reg["D1"]=reg["Dosen"]; reg["D2"]=""
    nr["Prodi"]="Elektro";  nr["NR"]=True;  nr["Kelas"]=nr["Kelas"]+" NR"; nr["D1"]=nr["Dosen"]; nr["D2"]=""
    return pd.concat([reg, nr], ignore_index=True)

def resolve_first_present(row, keys):
    for k in keys:
        if k in row and norm(row[k]): return norm(row[k])
    return ""

def load_arsitektur_source():
    # Read raw data without header to handle multiple semester sections
    df_raw = pd.read_excel(FILE_ARS, sheet_name=SHEET_ARS, header=None)

    out = []
    current_semester = 1

    # Find all semester sections and their courses
    i = 0
    while i < len(df_raw):
        row = df_raw.iloc[i]
        row_str = ' '.join([str(val) for val in row if pd.notna(val)]).lower()

        # Check if this row indicates a semester
        if 'semester' in row_str:
            if 'semester vii' in row_str:
                current_semester = 7
            elif 'semester v' in row_str:
                current_semester = 5
            elif 'semester iii' in row_str:
                current_semester = 3
            elif 'semester i' in row_str:
                current_semester = 1

            # Skip to next row to look for header
            i += 1
            continue

        # Check if this is a header row (NO, Kode MK, NAMA MATA KULIAH, etc.)
        if any('kode mk' in str(val).lower() for val in row if pd.notna(val)):
            # This is a header row, skip it
            i += 1
            continue

        # Check if this is a course data row
        if (pd.notna(row.iloc[1]) and pd.notna(row.iloc[2]) and pd.notna(row.iloc[3])):
            no = str(row.iloc[1]).strip()
            kode = str(row.iloc[2]).strip()
            mk = str(row.iloc[3]).strip()
            sks = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else ""
            dosen1 = str(row.iloc[5]).strip() if pd.notna(row.iloc[5]) and str(row.iloc[5]).strip() != 'nan' else ""
            dosen2 = str(row.iloc[6]).strip() if pd.notna(row.iloc[6]) and str(row.iloc[6]).strip() != 'nan' else ""

            # Validate this is a course row (has number, valid code, meaningful name)
            if (no.isdigit() and len(kode) > 5 and len(mk) > 3):
                # Skip MKDU courses (they should only be in MKDU prodi)
                if is_mkdu_course(mk):
                    i += 1
                    continue

                # Skip KKP and seminar usul
                mk_lower = mk.lower()
                if 'kkp' in mk_lower or 'seminar usul' in mk_lower:
                    i += 1
                    continue

                # Combine both dosen if available
                dosen_combined = dosen1
                if dosen2:
                    dosen_combined = f"{dosen1}, {dosen2}" if dosen1 else dosen2

                # Arsitektur: 2 kelas (A dan B) untuk semester 1,3,5,7 dengan dosen yang sama
                if current_semester in [1, 3, 5, 7]:
                    # Buat untuk kelas A
                    out.append(dict(
                        Prodi="Arsitektur",
                        Semester=current_semester,
                        Kelas="A",
                        Kode_MK=kode,
                        Mata_Kuliah=mk,
                        SKS=sks,
                        Dosen=dosen_combined,
                        D1=dosen1,
                        D2=dosen2,
                        NR=False
                    ))
                    # Buat untuk kelas B dengan dosen yang sama
                    out.append(dict(
                        Prodi="Arsitektur",
                        Semester=current_semester,
                        Kelas="B",
                        Kode_MK=kode,
                        Mata_Kuliah=mk,
                        SKS=sks,
                        Dosen=dosen_combined,
                        D1=dosen1,
                        D2=dosen2,
                        NR=False
                    ))
                else:
                    # Semester lain tetap satu kelas
                    out.append(dict(
                        Prodi="Arsitektur",
                        Semester=current_semester,
                        Kelas="A",
                        Kode_MK=kode,
                        Mata_Kuliah=mk,
                        SKS=sks,
                        Dosen=dosen_combined,
                        D1=dosen1,
                        D2=dosen2,
                        NR=False
                    ))

        i += 1

    return pd.DataFrame(out)

def load_mkdu():
    df = pd.read_excel(FILE_MKDU, sheet_name=SHEET_MKDU)
    out=[]
    for _, r in df.iterrows():
        kode = norm(r.get("Kode Mata kuliah", r.get("Kode Mata Kuliah","")))
        mk   = norm(r.get("Nama Mata Kuliah",""))
        if not (kode and mk): continue
        kelas= norm(r.get("Kelas","")); sks = r.get("SKS",""); dos = norm(r.get("Dosen",""))
        sem  = extract_semester(kelas)
        out.append(dict(Prodi="MKDU", Semester=sem, Kelas=kelas, Kode_MK=kode,
                        Mata_Kuliah=mk, SKS=sks if pd.notna(sks) else "", Dosen=dos, D1=dos, D2="", NR=False))
    return pd.DataFrame(out)

# =========================
# PARSE PWK (pakai jadwal asli)
# =========================
DAY_NAMES = ["SENIN","SELASA","RABU","KAMIS","JUMAT","SABTU","MINGGU"]
DAY_MAP   = {"SENIN":"Senin","SELASA":"Selasa","RABU":"Rabu","KAMIS":"Kamis","JUMAT":"Jumat","SABTU":"Sabtu","MINGGU":"Minggu"}
TIME_PAT  = re.compile(r'^\s*\d{1,2}[:\.]\d{2}\s*-\s*\d{1,2}[:\.]\d{2}\s*$')
ROOM_PAT  = re.compile(r'(?:IQRA|B-?3\.\d+|3\.\d+|B3\.\d+)', re.IGNORECASE)

def normalize_time(s):
    s = s.replace('.', ':')
    s = re.sub(r'\s*-\s*', '–', s)
    return s

def jam_to_sesi(day, jam):
    jam = jam.replace('.',':').replace('-', '–').replace(' - ', '–')
    if day == "Jumat":
        mapping = {"07:30–09:00":1,"09:00–10:30":2,"10:30–11:30":3,"13:00–14:30":4,"15:00–16:30":5}
    else:
        mapping = {"07:30–09:00":1,"09:00–10:30":2,"10:30–12:00":3,"13:00–14:30":4,"15:00–16:30":5}
    return mapping.get(jam, None)

def parse_pwk_asli():
    raw = pd.read_excel(FILE_PWK, sheet_name=SHEET_PWK, header=None)
    entries=[]; current_day=None
    seen_slots = set()  # Track (day, time, room) to avoid PWK internal conflicts

    for _, row in raw.iterrows():
        vals = [norm(v) for v in row.values if norm(v)]

        # Check if this is a day header
        if len(vals)==1 and vals[0].upper() in DAY_NAMES:
            current_day = DAY_MAP[vals[0].upper()]
            continue

        # Skip if no current day set
        if not current_day:
            continue

        # Look for structured data with columns: No, Jam, SMT, Kode MK, Mata Kuliah, SKS, Dosen, Dosen2, Ruang
        row_vals = [norm(v) for v in row.values]

        # Check if this looks like a data row (has time pattern)
        jam_col = None
        for i, val in enumerate(row_vals):
            if val and TIME_PAT.match(val):
                jam_col = i
                break

        if jam_col is not None and len(row_vals) > jam_col + 4:
            jam = normalize_time(row_vals[jam_col])
            smt = row_vals[jam_col + 1] if jam_col + 1 < len(row_vals) else ""
            kode = row_vals[jam_col + 2] if jam_col + 2 < len(row_vals) else ""
            mk = row_vals[jam_col + 3] if jam_col + 3 < len(row_vals) else ""
            sks = row_vals[jam_col + 4] if jam_col + 4 < len(row_vals) else ""
            dosen1 = row_vals[jam_col + 5] if jam_col + 5 < len(row_vals) else ""
            dosen2 = row_vals[jam_col + 6] if jam_col + 6 < len(row_vals) else ""
            ruang = row_vals[jam_col + 7] if jam_col + 7 < len(row_vals) else ""

            # Sometimes room is in the last non-empty column
            if not ruang:
                for i in range(len(row_vals)-1, jam_col+6, -1):
                    if row_vals[i] and ROOM_PAT.search(row_vals[i]):
                        ruang = row_vals[i]
                        break

            if mk and ruang:
                sesi = jam_to_sesi(current_day, jam)
                if sesi:
                    # Check for PWK internal conflicts
                    slot_key = (current_day, jam, ruang)
                    if slot_key in seen_slots:
                        print(f"WARNING: PWK internal conflict detected at {current_day} {jam} {ruang}")
                        print(f"  Skipping: {mk} (semester {smt})")
                        continue

                    seen_slots.add(slot_key)

                    # Combine dosen names
                    dosen_list = [d for d in [dosen1, dosen2] if d]
                    dosen_combined = "; ".join(dosen_list)

                    entries.append(dict(
                        Hari=current_day, Sesi=sesi, Jam=jam, Ruang=ruang,
                        Prodi="PWK", Semester=smt, Kelas="", Kode_MK=kode,
                        Mata_Kuliah=mk, SKS=sks, Dosen=dosen_combined, Mode="Luring",
                        D1=dosen1, D2=dosen2
                    ))
    return pd.DataFrame(entries)

# =========================
# SCHEDULER & CONFLICT RESOLUTION
# =========================
def is_zoom(mode): return "zoom" in norm(mode).lower()

def instr_names(row):
    # Only check D1 for conflicts - D2 is just backup/replacement for D1
    if norm(row.get("D1","")):
        return [norm(row["D1"])]
    elif norm(row.get("Dosen","")):
        return [norm(row["Dosen"])]
    else:
        return []

def allowed_days(row):
    prodi = norm(row["Prodi"]).upper()
    kelas = norm(row["Kelas"]).upper()
    if prodi == "MKDU": return ["Sabtu"]
    if " NR" in kelas or kelas=="NR" or "NON REG" in kelas or "NON-REG" in kelas or "NONREG" in kelas:
        return ["Sabtu","Minggu"]
    return ["Senin","Selasa","Rabu","Kamis","Jumat"]

def build_maps(df):
    instr_busy = defaultdict(set); room_busy = defaultdict(set); student_busy = defaultdict(set)
    for _, r in df.iterrows():
        day = norm(r["Hari"]); sesi = r["Sesi"]; mode = norm(r["Mode"])
        if not day or not sesi: continue
        key = (day, int(sesi))

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

def place_one(row, instr_busy, room_busy, student_busy=None):
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

def detect_conflicts(df):
    # ruang
    luring = df[~df["Mode"].str.lower().str.contains("zoom", na=False)]
    g = luring[luring["Ruang"]!=""].groupby(["Hari","Sesi","Ruang"]).size()
    room_conf = [(k, df[(df["Hari"]==k[0]) & (df["Sesi"]==k[1]) & (df["Ruang"]==k[2])].index.tolist())
                 for k, v in g.items() if v > 1]
    # dosen
    slot_map = defaultdict(lambda: defaultdict(list))
    for i, r in df.iterrows():
        day = norm(r["Hari"]); sesi = r["Sesi"]
        if not day or not sesi: continue
        for n in instr_names(r):
            if n: slot_map[(day, int(sesi))][n].append(i)
    instr_conf = [((name, key), idxs) for key, m in slot_map.items() for name, idxs in m.items() if len(idxs) > 1]
    return room_conf, instr_conf

def try_move(idx, df):
    """Pindahkan baris ke slot lain (tidak memindahkan PWK)."""
    row = df.loc[idx].to_dict()
    if norm(row["Prodi"]).lower() == "pwk":
        return False  # jangan pindahkan PWK
    # occupancy tanpa baris ini
    tmp = df.drop(index=[idx])
    instr_busy, room_busy, student_busy = build_maps(tmp)
    slot = place_one(row, instr_busy, room_busy, student_busy)
    if slot["Hari"]:
        df.at[idx, "Hari"] = slot["Hari"]
        df.at[idx, "Sesi"] = slot["Sesi"]
        df.at[idx, "Jam"]  = slot["Jam"]
        df.at[idx, "Ruang"]= slot["Ruang"] if not is_zoom(row["Mode"]) else ""
        return True
    return False

def resolve_all(df, max_iters=120):
    for iteration in range(max_iters):
        changed = False
        room_conf, instr_conf = detect_conflicts(df)

        # Print debug info for first few iterations
        if iteration < 3:
            print(f"Iteration {iteration}: Room conflicts: {len(room_conf)}, Instructor conflicts: {len(instr_conf)}")

        # Selesaikan konflik ruang (utamakan jaga PWK)
        for (key, idxs) in room_conf:
            # Prioritas: PWK > yang sudah terjadwal baik > lainnya
            pwk_idx = next((i for i in idxs if df.at[i,"Prodi"].strip().lower()=="pwk"), None)
            if pwk_idx is not None:
                keep = pwk_idx
            else:
                keep = idxs[0]  # keep the first one if no PWK

            for i in idxs:
                if i == keep:
                    continue
                if try_move(i, df):
                    changed = True
                    if iteration < 3:
                        print(f"  Moved row {i} ({df.at[i,'Prodi']} - {df.at[i,'Mata_Kuliah']}) to resolve room conflict")

        # Recompute conflicts setelah resolusi ruang
        room_conf, instr_conf = detect_conflicts(df)

        # Selesaikan konflik dosen
        for ((name, key), idxs) in instr_conf:
            pwk_idx = next((i for i in idxs if df.at[i,"Prodi"].strip().lower()=="pwk"), None)
            if pwk_idx is not None:
                keep = pwk_idx
            else:
                keep = idxs[0]

            for i in idxs:
                if i == keep:
                    continue
                if try_move(i, df):
                    changed = True
                    if iteration < 3:
                        print(f"  Moved row {i} ({df.at[i,'Prodi']} - {df.at[i,'Mata_Kuliah']}) to resolve instructor conflict")

        if not changed:
            print(f"Converged after {iteration + 1} iterations")
            break

    return df

# =========================
# PIPELINE UTAMA
# =========================
def main(output_path=BASE_DIR / "jadwal_gabungan_SATU_TABEL_FINAL_PWK_ARS.xlsx"):
    # 1) Muat semua daftar MK
    inf = load_informatika()
    peng = load_pengairan()
    el  = load_elektro()
    ars_src = load_arsitektur_source()
    mkdu = load_mkdu()

    # Hapus artefak MK numerik
    for df in (inf, peng, el, ars_src, mkdu):
        if not df.empty:
            mask_bad = df["Mata_Kuliah"].astype(str).str.fullmatch(r"\d+(\.\d+)?", na=False)
            df.drop(df[mask_bad].index, inplace=True)

    # 2) Penempatan awal semua kecuali PWK
    rows=[]
    # fungsi bantu untuk place awal (tanpa lihat PWK)
    instr_busy = defaultdict(set); room_busy = defaultdict(set); student_busy = defaultdict(set)

    def place_block(df_block, prodi_name):
        nonlocal rows, instr_busy, room_busy, student_busy
        for _, c in df_block.iterrows():
            row = {
                "Prodi": prodi_name if prodi_name else c.get("Prodi",""),
                "Semester": c.get("Semester",""),
                "Kelas": c.get("Kelas",""),
                "Kode_MK": c.get("Kode_MK",""),
                "Mata_Kuliah": c.get("Mata_Kuliah",""),
                "SKS": c.get("SKS",""),
                "Dosen": c.get("Dosen",""),
                "D1": c.get("D1",""),
                "D2": c.get("D2",""),
                "NR": bool(c.get("NR", False))
            }
            # aturan khusus
            weekend_only = (row["Prodi"].upper()=="MKDU") or row["NR"]
            zoom = str(row["Semester"])=="1"

            # cari slot
            days = ["Sabtu","Minggu"] if weekend_only else (DAYS_MON_THU + DAY_FRI + DAYS_WE)
            if row["Prodi"].upper()=="MKDU":
                days = ["Sabtu"]  # MKDU dipaksa Sabtu
            placed = False

            # Create student identifier for conflict detection
            student_id = (norm(row["Prodi"]), str(row["Semester"]), norm(row["Kelas"]))

            for day in days:
                for sess, jam in sessions_for_day(day):
                    key = (day, sess)
                    # Only check D1 for conflicts - D2 is just backup/replacement for D1
                    names = [row["D1"]] if row["D1"] else ([row["Dosen"]] if row["Dosen"] else [])

                    # Check instructor conflicts
                    if any(n in instr_busy[key] for n in names if n):
                        continue

                    # Check student conflicts - CRITICAL: Students can't be in 2 places at once
                    if student_id in student_busy[key]:
                        continue

                    if zoom:
                        slot = dict(Hari=day, Sesi=sess, Jam=jam, Ruang="")
                        placed = True
                    else:
                        # Use all available rooms (no lab rooms needed)
                        room = next((rm for rm in ALL_ROOMS if rm not in room_busy[key]), "")
                        if not room: continue
                        slot = dict(Hari=day, Sesi=sess, Jam=jam, Ruang=room)
                        room_busy[key].add(room)
                        placed = True

                    # Add instructor to busy list
                    for n in names: instr_busy[key].add(n)

                    # Add student to busy list - CRITICAL: Prevent student conflicts
                    student_busy[key].add(student_id)

                    rows.append({**slot, **row, "Mode": "Zoom" if zoom else "Luring"})
                    break
                if placed: break
            if not placed:
                # unplaced
                rows.append(dict(Hari="", Sesi="", Jam="", Ruang="", **row, Mode="Zoom" if zoom else "Luring (UNPLACED)"))

    place_block(inf, "Informatika")
    place_block(peng, "Pengairan")
    # Elektro sudah punya "Prodi" di frame-nya
    place_block(el, None)
    place_block(ars_src, None)  # Arsitektur auto-schedule
    place_block(mkdu, "MKDU")

    master = pd.DataFrame(rows)

    # 3) Masukkan PWK dari jadwal asli (HARUS dipakai apa adanya)
    pwk = parse_pwk_asli()
    # set struktur kolom sama
    for c in ("Semester","Kelas","Kode_MK","SKS","Dosen","D1","D2"):
        if c not in pwk.columns: pwk[c] = ""
    pwk.rename(columns={"Mode":"Mode"}, inplace=True)
    pwk = pwk[["Hari","Sesi","Jam","Ruang","Prodi","Semester","Kelas","Kode_MK","Mata_Kuliah","SKS","Dosen","Mode","D1","D2"]]

    # Hapus PWK lama jika ada lalu tempel PWK asli
    master = master[master["Prodi"].str.lower()!="pwk"].reset_index(drop=True)
    master = pd.concat([master, pwk], ignore_index=True)

    # 4) Normalisasi aturan: MKDU Sabtu, Smt1 Zoom, Zoom tanpa ruang
    master.loc[master["Prodi"].str.upper()=="MKDU","Hari"] = "Sabtu"
    master.loc[master["Semester"].astype(str)=="1","Mode"] = "Zoom"
    master.loc[master["Mode"].str.lower().str.contains("zoom", na=False),"Ruang"] = ""

    # 5) Selesaikan konflik (jangan pindahkan PWK)
    master = resolve_all(master)

    # 6) Urut & simpan
    order = {d:i for i,d in enumerate(["Senin","Selasa","Rabu","Kamis","Jumat","Sabtu","Minggu",""])}
    master["__o"] = master["Hari"].map(order).fillna(99)
    master["Sesi_num"] = pd.to_numeric(master["Sesi"], errors="coerce").fillna(99).astype(int)
    master = master.sort_values(by=["__o","Sesi_num","Ruang","Prodi","Semester","Kelas"]).drop(columns=["__o","Sesi_num"])

    # Ringkasan konflik
    def count_conflicts(df):
        # ruang
        luring = df[~df["Mode"].str.lower().str.contains("zoom", na=False)]
        room_conf = luring[luring["Ruang"]!=""].groupby(["Hari","Sesi","Ruang"]).size()
        room_conflicts = int((room_conf > 1).sum())
        # dosen
        slot_map = defaultdict(list)
        for i, r in df.iterrows():
            day = norm(r["Hari"]); sesi = r["Sesi"]
            if not day or not sesi: continue
            for n in instr_names(r):
                if n: slot_map[(day,int(sesi),n)].append(i)
        instr_conflicts = sum(1 for _, idxs in slot_map.items() if len(idxs) > 1)
        empties = int(((df["Hari"]=="") | (df["Sesi"]=="")).sum())
        return room_conflicts, instr_conflicts, empties

    rc, ic, em = count_conflicts(master)

    # Create separate sheets for each prodi
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
        order = {d:i for i,d in enumerate(["Senin","Selasa","Rabu","Kamis","Jumat","Sabtu","Minggu",""])}
        df_sorted = df_prodi.copy()
        df_sorted["__o"] = df_sorted["Hari"].map(order).fillna(99)
        df_sorted["Sesi_num"] = pd.to_numeric(df_sorted["Sesi"], errors="coerce").fillna(99).astype(int)
        df_sorted = df_sorted.sort_values(by=["__o","Sesi_num","Ruang"]).drop(columns=["__o","Sesi_num"])

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
                str(row["SKS"]) if pd.notna(row["SKS"]) else "", # SKS
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

    with pd.ExcelWriter(output_path, engine="openpyxl") as w:
        # Create sheets for each prodi
        prodis = ["Informatika", "PWK", "Elektro", "Pengairan", "Arsitektur", "MKDU"]

        for prodi in prodis:
            df_prodi = master[master["Prodi"].str.upper() == prodi.upper()]
            if not df_prodi.empty:
                create_prodi_sheet(df_prodi, prodi, w)

        # Keep the original combined sheet as well
        master.rename(columns={
            "Kode_MK":"Kode MK",
            "Mata_Kuliah":"Mata Kuliah",
            "D1":"Dosen 1",
            "D2":"Dosen 2",
            "Mode":"Mode (Zoom/Luring)"
        }).to_excel(w, index=False, sheet_name="Jadwal Induk (Gabungan)")

        # Conflict summary
        pd.DataFrame({
            "Metric":["Room Conflicts","Instructor Conflicts","Rows w/ Empty Day/Session"],
            "Value":[rc, ic, em]
        }).to_excel(w, index=False, sheet_name="Ringkasan Konflik")

    print(f"Selesai. Tersimpan di: {output_path}")
    print(f"Ringkasan: Room={rc}, Dosen={ic}, Kosong={em}")
    print(f"Sheets dibuat untuk: {', '.join([p for p in prodis if not master[master['Prodi'].str.upper() == p.upper()].empty])}")

if __name__ == "__main__":
    main()
