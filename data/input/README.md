# 📥 Input Data Directory

Direktori ini berisi semua data input (data awal) untuk ChronoSync.

## Struktur

```
input/
└── program_studies/        # Data per program studi
    ├── informatika/       # Program Studi Informatika
    ├── pengairan/         # Program Studi Pengairan (Irrigation)
    ├── elektro/           # Program Studi Teknik Elektro
    ├── pwk/               # Program Studi PWK (Urban Planning)
    ├── arsitektur/        # Program Studi Arsitektur
    └── mkdu/              # Mata Kuliah Dasar Umum
```

## File yang Dibutuhkan

### Informatika
- `JADWAL SEMESTER.xlsx` - Struktur mata kuliah Informatika
- `informatika.xlsx` - Data Informatika updated (opsional)

### Pengairan
- `Struktur Mata Kuliah Final ok.xlsx` - Struktur mata kuliah Pengairan (regular & non-regular)

### Elektro
- `Pengampuh MK T. Elektro.xlsx` - Data mata kuliah dan pengampu Teknik Elektro

### PWK (Urban Planning)
- `jadwal pwk ganjil 2025 2026.xlsx` - **JADWAL TETAP PWK** (tidak boleh diubah oleh ChronoSync)

### Arsitektur
- `JADWAL GANJIL 25-26_ARSITEKTUR.xlsx` - Struktur mata kuliah Arsitektur

### MKDU (General Education)
- `MKDU 20251.xlsx` - Mata Kuliah Dasar Umum untuk semua program

## Format File Excel

Setiap file Excel harus memiliki kolom-kolom berikut (dapat bervariasi):

### Kolom Wajib
- **Mata Kuliah** / **MK** - Nama mata kuliah
- **SKS** - Jumlah SKS
- **Semester** / **Smt** - Semester (1-8 atau I-VIII)
- **Kelas** - Kelas (A, B, C, dll)
- **Dosen** / **Pengampu** - Nama dosen pengampu

### Kolom Opsional
- **Kode MK** - Kode mata kuliah
- **Reguler/Non-Reguler** - Tipe kelas
- **Praktikum** - Penanda praktikum
- **Ruangan** - Ruangan (untuk jadwal tetap)
- **Hari** - Hari (untuk jadwal tetap)
- **Jam** / **Sesi** - Waktu (untuk jadwal tetap)

## Catatan Penting

1. **PWK memiliki jadwal tetap** - File PWK berisi jadwal yang sudah ditetapkan dan tidak akan diubah oleh ChronoSync
2. **MKDU hanya Sabtu** - Semua mata kuliah MKDU akan dijadwalkan pada hari Sabtu
3. **Non-Reguler weekend** - Kelas non-reguler akan dijadwalkan di weekend (Sabtu/Minggu)
4. **Semester 1 = Zoom** - Semua kelas semester 1 menggunakan Zoom (tidak perlu ruangan fisik)

## Cara Menambah Program Studi Baru

1. Buat folder baru di `program_studies/<nama_prodi>/`
2. Tambahkan file Excel dengan format yang sesuai
3. Update `config/settings.py` - tambahkan path ke `INPUT_PATHS`
4. Update `config/constraints.yaml` - tambahkan rules untuk prodi baru
5. Jalankan scheduling engine

## Troubleshooting

### File tidak ditemukan
- Pastikan nama file dan path sesuai dengan yang ada di `config/settings.py`
- Periksa case sensitivity (huruf besar/kecil)

### Error saat membaca Excel
- Pastikan file dalam format `.xlsx` (bukan `.xls`)
- Buka file dan pastikan tidak ada password protection
- Periksa apakah kolom-kolom wajib ada

### Data tidak lengkap
- Pastikan semua kolom wajib terisi
- Periksa format semester (angka atau roman numerals)
- Periksa format SKS (angka, bukan teks)
