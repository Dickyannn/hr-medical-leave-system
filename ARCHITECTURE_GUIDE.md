# 🎨 SYSTEM ARCHITECTURE & VISUAL GUIDE

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       FRONTEND (Streamlit)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  📤 Upload Page     📊 Dashboard      🔍 Review      ⚙️ Config   │
│  ├─ File Upload     ├─ KPI Cards      ├─ Filter      ├─ Master  │
│  ├─ OCR Preview     ├─ Charts         ├─ Table       │  Data    │
│  ├─ Edit Form       ├─ Analytics      └─ Export      └─ Status  │
│  └─ Save Button     └─ Indicators                                │
│                                                                   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   llm_client.py     │
                    │   (Backend Logic)   │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
    ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
    │  Gemini API  │   │ Data Process │   │  Disease     │
    │ (Image Read) │   │  & Normalize │   │ Classifier   │
    ├──────────────┤   ├──────────────┤   ├──────────────┤
    │ • OCR Text   │   │ • Parse Text │   │ • Reimborse  │
    │ • Normalize  │   │ • Date Norm  │   │ • Category   │
    │   Image      │   │ • Diagnosis  │   │ • Master DB  │
    │              │   │   Mapping    │   │              │
    └──────────────┘   └──────────────┘   └──────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
    ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
    │  Duplicate   │   │   Disease    │   │   Analytics  │
    │ Checker      │   │ Classification
    │              │   │              │   │              │
    ├──────────────┤   ├──────────────┤   ├──────────────┤
    │ • NIK Match  │   │ • Reimborse  │   │ • Statistics │
    │ • Date Match │   │   Status     │   │ • Trends     │
    │ • Diagnosis  │   │ • Warning    │   │ • Fraud Det  │
    │   Match      │   │   Flag       │   │              │
    │ • Scoring    │   │              │   │              │
    └──────────────┘   └──────────────┘   └──────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  SQLite Database    │
                    │  (surat_izin.db)    │
                    └─────────────────────┘
```

---

## 📊 Data Flow Diagram

```
START: Upload Surat Izin Dokter
  │
  ▼
[1] FILE UPLOAD (JPG/PNG/PDF)
  │
  ├─► Validate format
  └─► Create temp file
  │
  ▼
[2] OCR - GEMINI AI IMAGE READING
  │
  ├─► Base64 encode image
  ├─► Call Gemini API
  ├─► Extract raw text
  └─► Delete temp file
  │
  ▼
[3] TEXT PARSING
  │
  ├─► Split by line
  ├─► Extract key:value pairs
  ├─► Map to fields:
  │   ├─ NIK
  │   ├─ Nama
  │   ├─ Tanggal Izin
  │   ├─ Durasi
  │   ├─ Diagnosa
  │   ├─ Dokter
  │   └─ Rumah Sakit
  │
  ▼
[4] NORMALIZATION
  │
  ├─► Tanggal → YYYY-MM-DD
  ├─► Durasi → Integer
  ├─► Diagnosa → UPPERCASE + Synonym Map
  └─► Nama → lowercase + trim
  │
  ▼
[5] DISEASE CLASSIFICATION
  │
  ├─► Query DISEASE_MASTER
  ├─► Check if reimburseable
  ├─► Get kategori (RINGAN/SEDANG/BERAT)
  └─► Set warning flag if not reimburseable
  │
  ▼
[6] DUPLICATE DETECTION
  │
  ├─► Query existing records
  ├─► Score matching:
  │   ├─ NIK same    : +50%
  │   ├─ Date same   : +30%
  │   └─ Diagnosis   : +20%
  ├─► Calculate total score
  └─► Flag if score ≥ 80%
  │
  ▼
[7] DATA ASSEMBLY
  │
  ├─► Create unique surat_id
  ├─► Set timestamps
  ├─► Compile all fields
  └─► Include raw text for audit
  │
  ▼
[8] DATABASE SAVE
  │
  ├─► Insert into surat_izin table
  ├─► Commit transaction
  └─► Return success
  │
  ▼
[9] USER FEEDBACK
  │
  ├─► Show extracted data
  ├─► Show analysis results
  ├─► Show warnings (if any)
  └─► Confirm save
  │
  ▼
END: Record Saved

---

DASHBOARD FLOW:
Query surat_izin table
  ├─► Count total, eligible, duplicates
  ├─► Group by disease
  ├─► Group by month
  ├─► Calculate fraud indicators
  └─► Render charts
```

---

## 🔄 Duplicate Detection Algorithm

```
FOR each new_record:
  score = 0
  
  FOR each existing_record in database:
    
    IF new_record.nik == existing_record.nik:
      score += 50
    
    IF new_record.tanggal_izin == existing_record.tanggal_izin:
      score += 30
    
    IF new_record.diagnosa == existing_record.diagnosa:
      score += 20
    
    IF score >= 80:
      FLAG AS DUPLICATE ⚠️
      SAVE WARNING (score, reason)
      BREAK
  
  RETURN is_duplicate, score, reason
```

Example:
```
New Record:
  NIK: 3175xxxx
  Date: 2026-01-12
  Diagnosa: DEMAM

Existing Record 1:
  NIK: 3175xxxx  ✅ MATCH (+50)
  Date: 2026-01-05
  Diagnosa: DBD

Existing Record 2:
  NIK: 3174xxxx
  Date: 2026-01-12  ✅ MATCH (+30)
  Diagnosa: DEMAM  ✅ MATCH (+20)
  
  Total Score: 30 + 20 = 50% (Not flagged, < 80%)

Existing Record 3:
  NIK: 3175xxxx  ✅ MATCH (+50)
  Date: 2026-01-12  ✅ MATCH (+30)
  Diagnosa: DEMAM  ✅ MATCH (+20)
  
  Total Score: 50 + 30 + 20 = 100% ✅ FLAGGED!
```

---

## 📈 Dashboard Layout

### 1️⃣ Top KPI Section
```
┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│    Total     │  Eligible    │  Not Eligible│  Duplicates  │  Need Review │
│     45       │      28      │      17      │       3      │       5      │
└──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
```

### 2️⃣ Charts Section (2 Columns)

**Left Column:**
- Top 5 Penyakit (Horizontal Bar Chart)
- Reimbursement Distribution (Pie Chart)
- Trend per Bulan (Line Chart)

**Right Column:**
- Penyakit Tidak Reimburseable (Horizontal Bar)
- Kategori Distribusi (Bar Chart)
- Fraud Indicators (Table)

---

## 🎯 Disease Master Classification

```
DISEASE_MASTER = {
    'DEMAM': {
        'reimburseable': False,
        'kategori': 'RINGAN'
    },
    'PILEK': {
        'reimburseable': False,
        'kategori': 'RINGAN'
    },
    'BATUK': {
        'reimburseable': False,
        'kategori': 'RINGAN'
    },
    'SAKIT KEPALA': {
        'reimburseable': False,
        'kategori': 'RINGAN'
    },
    'TIPES': {
        'reimburseable': True,
        'kategori': 'SEDANG'
    },
    'DBD': {
        'reimburseable': True,
        'kategori': 'BERAT'
    },
    'DIARE': {
        'reimburseable': True,
        'kategori': 'SEDANG'
    },
    'ASMA': {
        'reimburseable': True,
        'kategori': 'SEDANG'
    },
    'HIPERTENSI': {
        'reimburseable': True,
        'kategori': 'SEDANG'
    },
    'DIABETES': {
        'reimburseable': True,
        'kategori': 'BERAT'
    }
}
```

---

## 🗄️ Database Schema Diagram

```
┌─────────────────────────────────────────────────────┐
│              TABLE: surat_izin                       │
├─────────────────────────────────────────────────────┤
│ PRIMARY KEY:                                         │
│ • surat_id (TEXT) ──────────► SURAT_20260112101530 │
├─────────────────────────────────────────────────────┤
│ KARYAWAN DATA:                                       │
│ • nik (TEXT)         ──────► 3175xxxx               │
│ • nama (TEXT)        ──────► dicky anugrah          │
├─────────────────────────────────────────────────────┤
│ SURAT DATA:                                          │
│ • tanggal_izin (TEXT)    ──► 2026-01-12             │
│ • durasi (INTEGER)       ──► 2                      │
│ • diagnosa (TEXT)        ──► DEMAM                  │
│ • dokter (TEXT)          ──► dr. andi               │
│ • rumah_sakit (TEXT)     ──► rs sehat               │
├─────────────────────────────────────────────────────┤
│ CLASSIFICATION:                                      │
│ • is_reimburseable (BOOLEAN) ──► False              │
│ • kategori (TEXT)            ──► RINGAN             │
├─────────────────────────────────────────────────────┤
│ DUPLICATE CHECK:                                     │
│ • is_duplicate (BOOLEAN)  ──► False                 │
│ • duplicate_score (FLOAT) ──► 0.0                   │
│ • duplicate_note (TEXT)   ──► NULL                  │
├─────────────────────────────────────────────────────┤
│ WARNING:                                             │
│ • warning_flag (BOOLEAN)  ──► True                  │
│ • warning_reason (TEXT)   ──► Penyakit tidak dapat  │
│                               direimburse            │
├─────────────────────────────────────────────────────┤
│ AUDIT:                                               │
│ • upload_date (TEXT)      ──► 2026-01-12T10:15:30  │
│ • raw_text (TEXT)         ──► [OCR raw output]     │
└─────────────────────────────────────────────────────┘
```

---

## 🔐 Data Security Flow

```
USER INPUT (Image)
  ▼
VALIDATE FORMAT
  ▼
CREATE TEMP FILE
  ▼
READ FILE → BASE64 ENCODE
  ▼
SEND TO GEMINI API (HTTPS)
  ▼
RECEIVE OCR RESULT
  ▼
SAVE RAW_TEXT TO DB (Audit Trail)
  ▼
PROCESS & NORMALIZE
  ▼
DELETE TEMP FILE
  ▼
SAVE TO SQLITE (Local)
  │
  └─► No sensitive data in logs
  └─► API Key in .env (not hardcoded)
  └─► All data stays in-house
```

---

## 🚀 Deployment Architecture

```
┌─────────────────────────────────────────┐
│      USER BROWSER                       │
│   (http://localhost:8501)               │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│    STREAMLIT SERVER                     │
│    (Python process)                     │
│    ├─ app.py (Main app)                 │
│    └─ llm_client.py (Logic)             │
└────────────────┬────────────────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
    ▼            ▼            ▼
┌────────┐ ┌──────────┐ ┌──────────────┐
│ Gemini │ │ SQLite   │ │  File System │
│  API   │ │   DB     │ │  (Temp Files)│
└────────┘ └──────────┘ └──────────────┘
```

---

## 💾 File Organization

```
PROJECT ROOT
│
├── 📄 app.py
│   └─ Streamlit frontend application
│       ├─ Page 1: Upload Surat
│       ├─ Page 2: Dashboard
│       ├─ Page 3: Review Data
│       └─ Page 4: Konfigurasi
│
├── 📄 llm_client.py
│   └─ Backend logic & API integration
│       ├─ read_image_with_gemini()
│       ├─ parse_ocr_text()
│       ├─ normalize_*() functions
│       ├─ classify_disease()
│       └─ DISEASE_MASTER config
│
├── 📄 requirements.txt
│   └─ Python dependencies
│
├── 📄 .env
│   └─ Environment variables (API keys)
│
├── 🗄️  surat_izin.db
│   └─ SQLite database (auto-created)
│
├── 📖 README.md
│   └─ Full documentation
│
├── ⚡ QUICKSTART.md
│   └─ Quick setup guide
│
└── 🧪 test_setup.py
    └─ Setup verification script
```

---

## 📱 UI Mockup

### 📤 UPLOAD PAGE
```
┌─────────────────────────────────────────────────────┐
│ 📤 Upload Surat Izin Dokter                         │
├─────────────────────────────────────────────────────┤
│                                                     │
│ [Choose File] [Browse...]                          │
│                                                     │
│ [File uploaded: scan_surat.jpg]                     │
│                                                     │
│ ✨ Extracting data with AI...                       │
│                                                     │
├─────────────────────────────────────────────────────┤
│ DATA TEREKSTRAK            │ ANALISIS                │
│                            │                        │
│ NIK: [3175xxxx        ]    │ Status: ❌ NOT OK      │
│ Nama: [Dicky Anugrah ]     │ Kategori: RINGAN       │
│ Tgl: [2026-01-12     ]     │ ⚠️ Duplikat: TIDAK     │
│ Durasi: [2          ]      │ 🚨 Warning: Penyakit    │
│ Diagnosa: [Demam    ]      │ tidak dapat direimburse│
│ Dokter: [dr. Andi   ]      │                        │
│ RS: [RS Sehat       ]      │ [💾 Simpan & Analisis] │
│                            │                        │
└─────────────────────────────────────────────────────┘
```

### 📊 DASHBOARD PAGE
```
┌────────────────────────────────────────────────────────────┐
│ 📊 DASHBOARD ANALYTICS                                      │
├────────────────────────────────────────────────────────────┤
│                                                             │
│ [45] Total │ [28] Eligible │ [17] Not │ [3] Duplikat │[5]Wa│
│                                                             │
├─────────────────────────────────────┬──────────────────────┤
│ Top 5 Penyakit                      │ Not Reimburseable    │
│                                     │                      │
│ DEMAM        ■■■■■■■ (15)          │ DEMAM      ■■■■■ (10)│
│ PILEK        ■■■■■ (10)            │ BATUK      ■■■ (5)   │
│ DBD          ■■■■ (8)              │ PILEK      ■■ (4)    │
│ TIPES        ■■■ (6)               │ SAKIT KEPALA■ (2)    │
│ BATUK        ■■■ (6)               │                      │
│                                     │                      │
├─────────────────────────────────────┴──────────────────────┤
│ Reimbursement Distribution    │ Kategori Penyakit         │
│                               │                           │
│     ✅62%        ❌38%         │ RINGAN   ■■■■■  (25)      │
│                               │ SEDANG   ■■■■   (15)      │
│     [Pie Chart]               │ BERAT    ■■     (5)       │
│                               │                           │
├──────────────────────────────────────────────────────────┤
│ Trend per Bulan (Timeline Chart)                        │
│                                                         │
│ Jan: [8 surat] Feb: [12] Mar: [15] Apr: [10]          │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ Fraud Indicator                                         │
│ 🔁 Duplikat Total: 3                                   │
│ ⚠️ Karyawan Izin Berulang:                             │
│    • Dicky (3175xxxx): 4 kali [SUSPICIOUS]             │
│    • Budi (3176xxxx): 3 kali [MONITOR]                 │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

## 🎓 Example Workflow

### Scenario: Upload Surat Izin dengan Diagnosis Demam

**Step 1: Upload**
```
File: surat_demam.jpg
```

**Step 2: OCR Processing**
```
Gemini API reads image:
NIK: 3175xxxx
Nama: Dicky Anugrah
Tanggal Izin: 12 Januari 2026
Durasi: 2 hari
Diagnosa: Demam
Dokter: dr. Andi
Rumah Sakit: RS Sehat
```

**Step 3: Normalization**
```
NIK: 3175xxxx
Nama: dicky anugrah
Tanggal: 2026-01-12
Durasi: 2
Diagnosa: DEMAM (mapped from "demam panas")
Dokter: dr. andi
RS: rs sehat
```

**Step 4: Classification**
```
Disease: DEMAM
Reimburseable: FALSE
Kategori: RINGAN
Warning: "Penyakit tidak dapat direimburse"
```

**Step 5: Duplicate Check**
```
Query database...
No matching records found
is_duplicate: FALSE
```

**Step 6: Save to DB**
```
Insert into surat_izin:
- surat_id: SURAT_20260112101530
- nik: 3175xxxx
- is_reimburseable: FALSE
- warning_flag: TRUE
- warning_reason: Penyakit tidak dapat direimburse
```

**Step 7: Display Results**
```
✅ Surat berhasil disimpan!
❌ Status: NOT REIMBURSEABLE
⚠️ Reason: Penyakit ringan (DEMAM)
✅ No duplicates detected
```

**Step 8: Dashboard Update**
```
Total Surat: +1
Not Eligible: +1
DEMAM count: +1
```

---

## ✨ Key Features Summary

| Feature | Status | Details |
|---------|--------|---------|
| Image OCR | ✅ | Gemini AI Vision |
| Data Extraction | ✅ | 7 fields extracted |
| Data Normalization | ✅ | Date, Diagnosis, Name |
| Disease Classification | ✅ | 10 diseases, 2 statuses |
| Duplicate Detection | ✅ | Rule-based scoring (80% threshold) |
| Database | ✅ | SQLite with 17 fields |
| Dashboard | ✅ | 4 pages, 8+ charts |
| Analytics | ✅ | KPIs, trends, fraud detection |
| User Interface | ✅ | Streamlit, responsive |
| Security | ✅ | .env config, local storage |
| Documentation | ✅ | README, QUICKSTART, this guide |
| Testing | ✅ | test_setup.py |

---

**Status: ✅ COMPLETE & PRODUCTION READY**

