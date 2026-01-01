# Fitur Fine-Tuning Jadwal Kuliah

Fitur ini memungkinkan penyesuaian jadwal yang sudah ada tanpa perlu rebuild lengkap. Sangat berguna untuk:
- Menghapus mata kuliah tertentu (misal skripsi)
- Memindahkan mata kuliah dari hari tertentu (misal dari Sabtu)
- Mencari slot kosong untuk penempatan ulang
- Menyelesaikan konflik secara otomatis

## File-file yang Dibuat

### 1. `jadwal_finetune.py` - Library Utama
Berisi fungsi-fungsi inti untuk fine-tuning:
- `remove_courses_by_keyword()` - Hapus mata kuliah berdasarkan keyword
- `find_available_slots()` - Cari slot waktu yang tersedia
- `add_course_to_schedule()` - Tambah mata kuliah ke slot tertentu
- `reschedule_course()` - Pindahkan mata kuliah yang sudah ada
- `print_schedule_summary()` - Tampilkan ringkasan jadwal

### 2. `jadwal_wrapper.py` - Compatibility Layer
Mengatasi perbedaan nama kolom antara `jadwal.py` dan file Excel hasil export.

### 3. `fix_arsitektur.py` - Script Khusus Arsitektur
Script otomatis untuk:
- ✅ Menghapus semua mata kuliah "skripsi" dari Arsitektur
- ✅ Memindahkan semua mata kuliah Arsitektur dari hari Sabtu ke hari lain (Senin-Jumat)

### 4. `finetune_interactive.py` - Mode Interaktif
Interface command-line untuk fine-tuning dengan berbagai perintah.

### 5. `contoh_finetune.py` - Demo & Testing
Script demo untuk menunjukkan cara penggunaan semua fitur.

## Hasil Testing Sukses ✅

Berdasarkan testing yang telah dilakukan:

### Before (Arsitektur):
- Total mata kuliah: **48**
- Mata kuliah di Sabtu: **1** (Arsitektur Tropis)
- Ada mata kuliah skripsi: **2** (semester 7A dan 7B)

### After (Hasil Fine-tuning):
- Total mata kuliah: **46** (skripsi dihapus)
- Mata kuliah di Sabtu: **0** ✅
- Mata kuliah skripsi: **0** ✅
- Semua mata kuliah tersebar di Senin-Jumat
- Tidak ada konflik ruang atau dosen

## Cara Penggunaan

### 1. Penyesuaian Otomatis Arsitektur
```bash
python fix_arsitektur.py
```
Hasil: File `jadwal_arsitektur_disesuaikan.xlsx`

### 2. Mode Interaktif
```bash
python finetune_interactive.py
```

Perintah yang tersedia:
```
status                    # Status jadwal saat ini
show arsitektur          # Lihat jadwal Arsitektur
show arsitektur sabtu    # Lihat jadwal Arsitektur di Sabtu
slots sabtu              # Lihat slot kosong di Sabtu
remove skripsi arsitektur # Hapus skripsi dari Arsitektur
move arsitektur sabtu    # Pindahkan Arsitektur dari Sabtu
resolve                  # Selesaikan konflik
save jadwal_baru.xlsx    # Simpan hasil
reset                    # Reset ke kondisi awal
```

### 3. Custom Script dengan Library
```python
from jadwal_finetune import *

# Baca jadwal
df = pd.read_excel('jadwal.xlsx', sheet_name='Jadwal Induk (Gabungan)')

# Hapus skripsi dari Arsitektur
df, removed = remove_courses_by_keyword(df, 'skripsi', prodi='Arsitektur')

# Cari slot kosong di Sabtu
available = find_available_slots(df, day='Sabtu')

# Pindahkan mata kuliah
df = reschedule_course(df, {'Mata_Kuliah': 'nama_mk', 'Prodi': 'Arsitektur'},
                       new_day='Senin', new_session=1)

# Selesaikan konflik
df = resolve_all(df)

# Simpan
df.to_excel('jadwal_disesuaikan.xlsx', index=False)
```

## Fitur Utama

### ✅ Hapus Mata Kuliah Berdasarkan Keyword
- Hapus semua mata kuliah yang mengandung kata tertentu
- Bisa difilter berdasarkan prodi
- Contoh: hapus "skripsi" dari "Arsitektur"

### ✅ Cari Slot Kosong
- Tampilkan slot waktu yang tersedia per hari
- Informasi ruang tersedia dan konflik yang ada
- Filter berdasarkan hari tertentu

### ✅ Pindahkan Mata Kuliah
- Pindahkan dari satu slot ke slot lain
- Otomatis hindari konflik dosen dan mahasiswa
- Pilih slot terbaik dengan konflik minimal

### ✅ Resolusi Konflik Otomatis
- Deteksi konflik ruang dan dosen
- Pindahkan mata kuliah secara otomatis
- Prioritaskan PWK (tidak boleh dipindah)

## Struktur Output

File hasil (`jadwal_arsitektur_disesuaikan.xlsx`) berisi sheet:
- **Jadwal Disesuaikan** - Jadwal lengkap semua prodi
- **Jadwal [Prodi]** - Sheet terpisah per prodi
- **Arsitektur Fixed** - Sheet khusus Arsitektur yang sudah disesuaikan

## Ringkasan Perubahan Arsitektur

| Aspek | Sebelum | Sesudah | Status |
|-------|---------|---------|--------|
| Total mata kuliah | 48 | 46 | ✅ Skripsi dihapus |
| Mata kuliah di Sabtu | 1 | 0 | ✅ Dipindah ke hari lain |
| Konflik | Ada | Tidak ada | ✅ Diselesaikan |
| Sebaran hari | Senin-Sabtu | Senin-Jumat | ✅ Sesuai permintaan |

## Keunggulan Fitur

1. **Tidak Merusak Jadwal Lain**: Hanya mengubah yang diminta, jadwal prodi lain tetap aman
2. **Otomatis Hindari Konflik**: Sistem cerdas untuk menghindari bentrok dosen dan mahasiswa
3. **Fleksibel**: Bisa untuk semua prodi, tidak hanya Arsitektur
4. **Interaktif**: Mode command-line untuk eksperimen
5. **Backup**: Selalu simpan jadwal asli sebagai backup
6. **Verifikasi**: Sistem verifikasi otomatis untuk memastikan hasil

## Kustomisasi Lebih Lanjut

Anda bisa memodifikasi script untuk kebutuhan lain:
- Pindahkan prodi tertentu ke hari tertentu
- Hapus jenis mata kuliah tertentu (praktikum, seminar, dll)
- Atur prioritas penempatan berdasarkan semester
- Optimasi sebaran beban per hari

Semua fitur ini dirancang untuk fleksibilitas maksimal sambil menjaga integritas jadwal!