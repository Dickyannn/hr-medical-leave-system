# 🚀 QUICK START GUIDE

## Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

## Step 2: Verify .env
Check that `.env` file has:
```
GEMINI_API_KEY=AIzaSyB-H5Dx2fqxLcSQKnhg6gstsQFSpHNl_ms
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent
```

## Step 3: Run App
```bash
streamlit run app.py
```

## Step 4: Open in Browser
```
http://localhost:8501
```

---

## 📱 Menu Utama

### 📤 Upload Surat
- Upload surat izin dokter (JPG/PNG)
- Sistem OCR dengan Gemini AI
- Edit data jika perlu
- Simpan & analisis otomatis

### 📊 Dashboard Analytics
- Lihat statistik keseluruhan
- Top 5 penyakit paling sering
- Trend izin sakit per bulan
- Fraud indicator & duplikat

### 🔍 Review Data
- Filter data berdasarkan status
- Lihat detail setiap surat
- Export data jika perlu

### ⚙️ Konfigurasi
- Master data penyakit
- Status reimburseable
- Kategori penyakit

---

## 🎯 Contoh Workflow

1. **Upload Surat** → Scan/foto surat izin dokter
2. **OCR Ekstrak** → Gemini AI membaca gambar
3. **Review Data** → Edit jika ada error OCR
4. **Simpan** → Sistem cek duplikasi & reimbursability
5. **Dashboard** → Lihat trend & analisis

---

## 🆘 Butuh Bantuan?

Baca file `README.md` untuk dokumentasi lengkap

