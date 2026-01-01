# 📤 Output Data Directory

Direktori ini berisi semua hasil output (jadwal yang dihasilkan) dari ChronoSync.

## Struktur

```
output/
├── final/                  # ⭐ Jadwal final utama
├── program_specific/       # Jadwal per-program studi
│   ├── arsitektur/
│   └── informatika/
└── intermediate/           # File kerja intermediate
```

## File Output Utama

### 📂 final/

Berisi jadwal final yang siap digunakan:

- **`jadwal_gabungan_SATU_TABEL_FINAL_PWK_ARS.xlsx`** ⭐
  - **JADWAL UTAMA** - Jadwal lengkap semua program studi
  - Berisi semua mata kuliah dari 6 program studi
  - Format: Multiple sheets per program + master schedule

- **`jadwal_final_complete.xlsx`**
  - Versi alternatif jadwal lengkap
  - Format komprehensif dengan semua detail

- **`jadwal_disesuaikan.xlsx`**
  - Jadwal yang sudah di-fine-tune
  - Hasil dari proses adjustment manual/otomatis

### 📂 program_specific/

Berisi jadwal khusus per-program studi:

#### `arsitektur/`
- `jadwal_arsitektur_disesuaikan.xlsx` - Jadwal Arsitektur (adjusted)
- `jadwal_arsitektur_fixed.xlsx` - Jadwal Arsitektur (fixed)

#### `informatika/`
- `jadwal_informatika_pbo_semester7_lengkap.xlsx` - IT dengan PBO semester 7
- `jadwal_informatika_pbo_dosen_lengkap.xlsx` - IT dengan PBO + dosen lengkap
- `jadwal_informatika_with_pbo.xlsx` - IT integrated dengan PBO

### 📂 intermediate/

Berisi file kerja intermediate (biasanya tidak perlu digunakan):

- `output.xlsx` - Output test/temporary
- `jadwal_gabungan_INFORMATIKA_UPDATED.xlsx` - Versi dengan IT updated
- `jadwal_gabungan_MKDU_FIXED.xlsx` - Versi dengan MKDU corrected

## Format File Output

Setiap file Excel output berisi:

### Sheets yang Ada

1. **Master Schedule** - Jadwal gabungan semua program
2. **Per-Program Sheets** - Sheet terpisah untuk setiap program studi:
   - Informatika
   - Pengairan
   - Elektro
   - PWK
   - Arsitektur
   - MKDU

### Kolom di Setiap Sheet

| Kolom | Deskripsi |
|-------|-----------|
| **Hari** | Hari kuliah (Senin-Minggu) |
| **Sesi** | Waktu kuliah (1-5) |
| **Ruangan** | Ruangan/Zoom |
| **Prodi** | Program studi |
| **Mata Kuliah** | Nama mata kuliah |
| **SKS** | Jumlah SKS |
| **Semester** | Semester (I-VIII) |
| **Kelas** | Kelas (1A, 2B, dst) |
| **Dosen** | Nama dosen pengampu |

## Cara Menggunakan Output

### 1. Untuk Administrasi

Gunakan file utama:
```
data/output/final/jadwal_gabungan_SATU_TABEL_FINAL_PWK_ARS.xlsx
```

### 2. Untuk Program Studi Tertentu

Gunakan sheet khusus atau file di `program_specific/`:
```
data/output/program_specific/informatika/jadwal_informatika_*.xlsx
```

### 3. Untuk Fine-tuning

1. Load jadwal dari `final/`
2. Jalankan fine-tuning script
3. Hasil baru tersimpan di `final/jadwal_disesuaikan.xlsx`

## Jadwal Waktu (Sesi)

| Sesi | Waktu | Keterangan |
|------|-------|------------|
| 1 | 07:30 - 09:10 | Pagi |
| 2 | 09:30 - 11:10 | Pagi |
| 3 | 11:30 - 13:10 | Siang |
| 4 | 13:30 - 15:10 | Siang |
| 5 | 15:30 - 17:10 | Sore |

**Catatan Jumat**: Ada penyesuaian untuk waktu sholat Jumat

## Verifikasi Output

Setelah generate jadwal, jalankan verification scripts:

```bash
# Cek semua konflik
python src/analysis/comprehensive_conflict_check.py

# Cek konflik mahasiswa
python src/analysis/analyze_student_conflicts.py

# Cek konflik dosen
python src/analysis/check_instructor_conflicts.py

# Verifikasi final
python src/analysis/verify_final_schedule.py
```

## Interpretasi Hasil

### Status Jadwal

- ✅ **No Conflicts** - Jadwal siap digunakan
- ⚠️ **Minor Conflicts** - Ada konflik kecil, perlu review
- ❌ **Major Conflicts** - Perlu perbaikan serius

### Jenis Konflik

1. **Room Conflict** - 2+ mata kuliah di ruangan sama, waktu sama
2. **Instructor Conflict** - Dosen mengajar 2+ mata kuliah bersamaan
3. **Student Conflict** - Mahasiswa mengambil 2+ mata kuliah bersamaan

## Backup dan Versioning

Disarankan untuk:

1. **Backup jadwal final** sebelum fine-tuning
2. **Simpan versi dengan timestamp** untuk tracking
3. **Gunakan git** untuk version control

Contoh:
```bash
cp data/output/final/jadwal_disesuaikan.xlsx \
   data/output/final/jadwal_disesuaikan_2025-01-01.xlsx
```

## Troubleshooting

### File kosong/tidak ada data
- Pastikan scheduling engine berhasil dijalankan
- Periksa console output untuk error messages
- Verifikasi input data sudah lengkap

### Banyak konflik
- Jalankan ulang dengan max iterations lebih tinggi
- Cek constraint configuration di `config/constraints.yaml`
- Review prioritas program di `config/settings.py`

### Format tidak sesuai
- Periksa wrapper configuration di `src/core/jadwal_wrapper.py`
- Verifikasi column mapping
