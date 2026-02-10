# 🏥 HR Digitalisasi Surat Izin Dokter

Sistem otomatis untuk mengekstrak, menganalisis, dan mengelola surat izin dokter karyawan.

## 📋 Fitur Utama

### 1. **📤 Upload & OCR**
- Upload surat izin dokter (JPG, PNG, PDF)
- Ekstrak teks otomatis menggunakan **Gemini AI Vision**
- Tampilkan data terekstrak untuk review/edit sebelum disimpan

### 2. **🔍 Deteksi Duplikasi**
Rule-based scoring dengan kriteria:
- NIK sama: **50%**
- Tanggal izin sama: **30%**
- Diagnosa sama: **20%**
- **Threshold: ≥ 80%** = Potensi Duplikat (warning only, tidak auto-reject)

### 3. **💰 Klasifikasi Penyakit & Reimbursement**
Master data penyakit dengan status reimburseable:
- ✅ **ELIGIBLE**: Tipes, DBD, Diare, Asma, Hipertensi, Diabetes
- ❌ **TIDAK ELIGIBLE**: Demam, Pilek, Batuk, Sakit Kepala

### 4. **📊 Dashboard Analytics**
- Statistik keseluruhan (Total, Eligible, Duplikat)
- Top 5 penyakit paling sering
- Penyakit tidak reimburseable
- Reimbursement insight (pie chart)
- Trend izin sakit per bulan
- Fraud indicator (pola izin berulang)

### 5. **🔍 Review Data**
- Filter berdasarkan status reimbursement
- Filter duplikat & warning
- Sorting & export data

### 6. **⚙️ Konfigurasi**
- Master data penyakit dapat dikonfigurasi
- Tambah/ubah status reimburseable

---

## 🚀 Setup & Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Environment Variables
File `.env` sudah tersedia dengan:
```
GEMINI_API_KEY=<your-api-key>
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent
```

### 3. Run Streamlit App
```bash
streamlit run app.py
```

App akan buka di `http://localhost:8501`

---

## 📂 File Structure
```
.
├── llm_client.py          # LLM integration & data processing
├── app.py                 # Streamlit UI
├── requirements.txt       # Dependencies
├── .env                   # API Keys
└── surat_izin.db         # SQLite Database (auto-created)
```

---

## 🗄️ Database Schema

### Table: `surat_izin`
| Field | Type | Deskripsi |
|-------|------|-----------|
| surat_id | TEXT (PK) | Unique ID surat |
| nik | TEXT | NIK karyawan |
| nama | TEXT | Nama karyawan |
| tanggal_izin | TEXT | Tanggal izin (YYYY-MM-DD) |
| durasi | INTEGER | Durasi izin (hari) |
| diagnosa | TEXT | Diagnosis (normalized) |
| dokter | TEXT | Nama dokter |
| rumah_sakit | TEXT | Nama RS |
| is_reimburseable | BOOLEAN | Status reimbursement |
| kategori | TEXT | Kategori penyakit (RINGAN/SEDANG/BERAT) |
| is_duplicate | BOOLEAN | Flag duplikat |
| duplicate_score | FLOAT | Score duplikasi (0-100) |
| duplicate_note | TEXT | Catatan duplikasi |
| warning_flag | BOOLEAN | Ada warning |
| warning_reason | TEXT | Alasan warning |
| upload_date | TEXT | Waktu upload |
| raw_text | TEXT | Raw OCR text |

---

## 🔧 Konfigurasi Penyakit

Edit `llm_client.py` di bagian `DISEASE_MASTER`:
```python
DISEASE_MASTER = {
    'DEMAM': {'reimburseable': False, 'kategori': 'RINGAN'},
    'TIPES': {'reimburseable': True, 'kategori': 'SEDANG'},
    # ... tambah penyakit sesuai kebutuhan
}
```

---

## 📊 Workflow Sistem

```
1. INPUT DATA
   ↓ Upload surat izin dokter (JPG/PNG/PDF)
   
2. OCR - TEXT EXTRACTION
   ↓ Gemini AI membaca isi surat
   
3. INFORMATION EXTRACTION & NORMALIZATION
   ↓ Parse field: NIK, Nama, Tanggal, Durasi, Diagnosa, dll
   ↓ Normalisasi: Tanggal → YYYY-MM-DD, Diagnosa → UPPERCASE
   
4. DISEASE CLASSIFICATION
   ↓ Cek master data penyakit
   ↓ Tentukan is_reimburseable
   
5. DUPLICATE DETECTION
   ↓ Rule-based scoring (NIK + Tanggal + Diagnosa)
   ↓ Threshold ≥ 80% → Flag sebagai duplikat
   
6. DATA STORAGE
   ↓ Simpan ke SQLite database
   ↓ Semua surat disimpan untuk audit trail
   
7. HR REVIEW PANEL
   ↓ Filter: Eligible, Need Review, Not Reimburseable
   ↓ Lihat duplikat & riwayat izin karyawan
   
8. DASHBOARD ANALYTICS
   ↓ Statistik penyakit
   ↓ Trend waktu
   ↓ Reimbursement insight
   ↓ Fraud indicator

9. OUTPUT AKHIR
   ✅ Proses manual → otomatis
   ✅ Risiko klaim palsu berkurang
   ✅ HR bisa sorting cepat
   ✅ Data siap dianalisis
   ✅ Aman secara kebijakan
```

---

## 🎯 Use Cases

### Use Case 1: Upload Surat Baru
1. HR klik "Upload Surat"
2. Pilih file surat izin dokter
3. Sistem OCR & ekstrak data otomatis
4. Review data yang terekstrak
5. Klik "Simpan & Analisis"
6. Sistem cek: Duplikasi? Reimburseable?
7. Simpan ke database

### Use Case 2: Review Data Duplikat
1. Buka Dashboard
2. Lihat "Duplicate Indicator"
3. Klik link ke "Review Data"
4. Filter "Hanya Duplikat"
5. HR decide: Keep/Delete/Mark as Exception

### Use Case 3: Analisis Trend Penyakit
1. Buka Dashboard
2. Lihat "Top 5 Penyakit"
3. Lihat "Trend per Bulan"
4. Identifikasi peak season
5. Buat policy & intervention

---

## 💡 Contoh Output

### OCR Hasil
```
NIK: 3175xxxx
Nama: Dicky Anugrah
Tanggal Izin: 12 Januari 2026
Durasi: 2 hari
Diagnosa: Demam
Dokter: dr. Andi
Rumah Sakit: RS Sehat
```

### Analisis Output
```
✅ Extracted Data
❌ NOT REIMBURSEABLE (Demam = penyakit ringan)
⚠️ NO DUPLICATE
```

---

## 🔐 Security & Privacy

- ✅ Data disimpan lokal (SQLite)
- ✅ API key di `.env` (tidak hardcoded)
- ✅ Audit trail lengkap (semua surat disimpan)
- ✅ No sensitive data di logs
- ✅ GDPR-ready (bisa delete records)

---

## 🐛 Troubleshooting

### Error: API Key Invalid
```
Pastikan GEMINI_API_KEY di .env sudah benar
```

### Error: Image Format Not Supported
```
Gunakan format: JPG, PNG, atau PDF
```

### Database Locked
```
Tutup terminal yang lain
Restart streamlit: streamlit run app.py
```

---

