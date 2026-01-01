"""
Schedule-AI Configuration Settings
"""
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
INPUT_DIR = DATA_DIR / "input" / "program_studies"
OUTPUT_DIR = DATA_DIR / "output"
OUTPUT_FINAL_DIR = OUTPUT_DIR / "final"
OUTPUT_PROGRAM_DIR = OUTPUT_DIR / "program_specific"
OUTPUT_INTERMEDIATE_DIR = OUTPUT_DIR / "intermediate"

# Input data paths
INPUT_PATHS = {
    "informatika": INPUT_DIR / "informatika" / "JADWAL SEMESTER.xlsx",
    "informatika_updated": INPUT_DIR / "informatika" / "informatika.xlsx",
    "pengairan": INPUT_DIR / "pengairan" / "Struktur Mata Kuliah Final ok.xlsx",
    "elektro": INPUT_DIR / "elektro" / "Pengampuh MK T. Elektro.xlsx",
    "pwk": INPUT_DIR / "pwk" / "jadwal pwk ganjil 2025 2026.xlsx",
    "arsitektur": INPUT_DIR / "arsitektur" / "JADWAL GANJIL 25-26_ARSITEKTUR.xlsx",
    "mkdu": INPUT_DIR / "mkdu" / "MKDU 20251.xlsx",
}

# Scheduling parameters
MAX_ITERATIONS = 120
CONFLICT_RESOLUTION_MAX_ATTEMPTS = 10

# Time slots
DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
WEEKDAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat"]
WEEKEND = ["Sabtu", "Minggu"]

# Room configuration
AVAILABLE_ROOMS = [
    "3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8",
    "3.9", "3.10", "3.11", "3.12", "3.13", "3.14"
]
ZOOM_ROOM = "Zoom"

# Semester constraints
SEMESTER_1_MODE = "Zoom"  # Semester 1 uses Zoom only
NON_REGULAR_DAYS = WEEKEND  # Non-regular classes on weekends
MKDU_DAYS = ["Sabtu"]  # MKDU only on Saturday

# Program priorities (higher number = higher priority)
PROGRAM_PRIORITIES = {
    "PWK": 100,  # PWK has highest priority (pre-scheduled, cannot move)
    "Informatika": 50,
    "Arsitektur": 50,
    "Pengairan": 50,
    "Elektro": 50,
    "MKDU": 30,
}

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
