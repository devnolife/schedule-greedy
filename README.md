# Sistem Penjadwalan Kuliah Terintegrasi

## Algoritma yang Digunakan

### 1. **Greedy Scheduling Algorithm**
Program menggunakan algoritma greedy untuk penempatan mata kuliah dengan prioritas sebagai berikut:
- **Priority-based placement**: PWK (menggunakan jadwal asli) > Prodi lain (auto-schedule)
- **Time slot allocation**: Mengalokasikan slot waktu berdasarkan hari dan sesi yang tersedia
- **Resource constraint satisfaction**: Memastikan tidak ada konflik dosen, ruangan, dan mahasiswa

### 2. **Conflict Resolution Algorithm**
- **Iterative conflict detection**: Mendeteksi konflik ruangan dan dosen dalam setiap iterasi
- **Priority-based conflict resolution**: PWK tidak dipindahkan, prodi lain disesuaikan
- **Student conflict prevention**: Mencegah mahasiswa mengambil 2 mata kuliah bersamaan

### 3. **Constraint Satisfaction**
- **Hard constraints**: Dosen tidak boleh mengajar 2 mata kuliah bersamaan
- **Resource constraints**: Ruangan tidak boleh digunakan 2 mata kuliah bersamaan
- **Time constraints**: Semester 1 = Zoom, NR & MKDU = Weekend, MKDU = Sabtu

## Kapan Sebaiknya Menggunakan Program Ini

### **Cocok Digunakan Untuk:**
1. **Penjadwalan multi-prodi** dengan aturan berbeda per prodi
2. **Institusi dengan jadwal tetap** (seperti PWK) yang tidak boleh diubah
3. **Sistem dengan pembagian kelas reguler/non-reguler**
4. **Penjadwalan hybrid** (online/offline) berdasarkan semester
5. **Fakultas teknik** dengan banyak mata kuliah praktikum

### **Tidak Cocok Untuk:**
1. Sistem dengan fleksibilitas tinggi dalam perubahan jadwal
2. Penjadwalan single-prodi sederhana
3. Sistem tanpa pembagian reguler/non-reguler
4. Institusi tanpa mata kuliah wajib umum (MKDU)

## Alur Program

### **Phase 1: Data Loading & Preprocessing**
```
1. Load data dari 6 file Excel:
   - Informatika (JADWAL SEMESTER.xlsx)
   - Pengairan (Struktur Mata Kuliah Final ok.xlsx)
   - Elektro (Pengampuh MK T. Elektro.xlsx)
   - PWK (jadwal pwk ganjil 2025 2026.xlsx)
   - Arsitektur (JADWAL GANJIL 25-26_ARSITEKTUR.xlsx)
   - MKDU (MKDU 20251.xlsx)

2. Data normalization:
   - Extract semester dari format roman/angka
   - Combine multiple dosen columns
   - Filter praktikum courses
   - Skip MKDU dari prodi lain
```

### **Phase 2: Initial Placement**
```
1. Setup time slots:
   - Senin-Kamis: 5 sesi (07:30-16:30)
   - Jumat: 5 sesi (termasuk istirahat Jumatan)
   - Sabtu-Minggu: 5 sesi

2. Setup ruangan: 3.1 sampai 3.14

3. Apply placement rules:
   - MKDU → Sabtu only
   - Non-Reguler → Weekend (Sabtu/Minggu)
   - Semester 1 → Zoom (tanpa ruangan)
   - Reguler → Weekdays (Senin-Jumat)

4. Greedy placement dengan conflict checking:
   - Check instructor availability
   - Check room availability
   - Check student schedule conflicts
```

### **Phase 3: PWK Integration**
```
1. Parse jadwal PWK asli dari Excel
2. Hapus PWK yang sudah di-auto-schedule
3. Insert jadwal PWK asli (TIDAK BOLEH DIUBAH)
4. Deteksi internal conflict dalam PWK
```

### **Phase 4: Conflict Resolution**
```
Iterative process (max 120 iterations):

1. Detect conflicts:
   - Room conflicts: 2+ mata kuliah di ruangan sama
   - Instructor conflicts: dosen mengajar 2+ mata kuliah bersamaan

2. Resolve conflicts:
   - Prioritas PWK (tidak dipindahkan)
   - Pindahkan mata kuliah lain ke slot kosong
   - Cek constraint satisfaction setiap pemindahan

3. Convergence check:
   - Stop jika tidak ada perubahan dalam 1 iterasi
   - Output conflict summary
```

### **Phase 5: Output Generation**
```
1. Sort by: Hari → Sesi → Ruangan → Prodi → Semester → Kelas

2. Generate multiple Excel sheets:
   - Sheet per prodi dengan format standard
   - Sheet gabungan (master schedule)
   - Sheet ringkasan konflik

3. Format output:
   - Header institusional per prodi
   - Roman numeral untuk semester
   - Format kelas (1A, 2B, dst)
   - Zoom indication untuk semester 1
```

## Keunggulan Algoritma

1. **Preserve existing schedules**: PWK jadwal tidak berubah
2. **Multi-constraint satisfaction**: Dosen, ruangan, mahasiswa
3. **Scalable conflict resolution**: Iterative improvement
4. **Rule-based scheduling**: Aturan berbeda per kategori mata kuliah
5. **Comprehensive output**: Multiple format untuk berbagai kebutuhan

## Kompleksitas

- **Time Complexity**: O(n × m × r) dimana n=mata kuliah, m=slot waktu, r=ruangan
- **Space Complexity**: O(n) untuk tracking conflicts
- **Iteration Complexity**: Maksimal 120 iterasi untuk konvergensi