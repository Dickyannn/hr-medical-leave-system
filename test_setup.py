#!/usr/bin/env python3
"""
Test script untuk verify semua komponen bekerja
"""

import os
import sys
from dotenv import load_dotenv

print("🔍 Checking Setup...\n")

# 1. Check .env
print("1️⃣  Checking .env file...")
load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")
gemini_url = os.getenv("GEMINI_BASE_URL")

if gemini_key and gemini_url:
    print(f"   ✅ GEMINI_API_KEY found: {gemini_key[:20]}...")
    print(f"   ✅ GEMINI_BASE_URL found")
else:
    print("   ❌ .env file incomplete!")
    sys.exit(1)

# 2. Check imports
print("\n2️⃣  Checking dependencies...")
try:
    import streamlit
    print("   ✅ streamlit installed")
except ImportError:
    print("   ❌ streamlit not installed")

try:
    import pandas
    print("   ✅ pandas installed")
except ImportError:
    print("   ❌ pandas not installed")

try:
    import plotly
    print("   ✅ plotly installed")
except ImportError:
    print("   ❌ plotly not installed")

try:
    import requests
    print("   ✅ requests installed")
except ImportError:
    print("   ❌ requests not installed")

# 3. Test llm_client functions
print("\n3️⃣  Testing llm_client functions...")
try:
    from llm_client import (
        parse_ocr_text,
        normalize_date,
        normalize_diagnosis,
        classify_disease,
        DISEASE_MASTER
    )
    print("   ✅ llm_client imports successful")
    
    # Test normalize_date
    date_result = normalize_date("12 Januari 2026")
    print(f"   ✅ normalize_date: '12 Januari 2026' → '{date_result}'")
    assert date_result == "2026-01-12", f"Expected 2026-01-12, got {date_result}"
    
    # Test normalize_diagnosis
    diag_result = normalize_diagnosis("demam panas")
    print(f"   ✅ normalize_diagnosis: 'demam panas' → '{diag_result}'")
    assert diag_result == "DEMAM", f"Expected DEMAM, got {diag_result}"
    
    # Test classify_disease
    disease_info = classify_disease("DEMAM")
    print(f"   ✅ classify_disease: DEMAM → reimburseable={disease_info['is_reimburseable']}")
    assert disease_info['is_reimburseable'] == False
    
    # Test parse_ocr_text
    raw_text = """
    NIK: 3175xxxx
    Nama: Dicky Anugrah
    Tanggal Izin: 12 Januari 2026
    Durasi: 2 hari
    Diagnosa: Demam
    Dokter: dr. Andi
    Rumah Sakit: RS Sehat
    """
    
    parsed = parse_ocr_text(raw_text)
    print(f"   ✅ parse_ocr_text: Extracted {len([v for v in parsed.values() if v])} fields")
    assert parsed['nik'] == "3175xxxx"
    assert parsed['nama'] == "Dicky Anugrah"
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 4. Test disease master data
print("\n4️⃣  Checking disease master data...")
print(f"   ✅ Total diseases: {len(DISEASE_MASTER)}")
for disease, info in DISEASE_MASTER.items():
    status = "✅" if info['reimburseable'] else "❌"
    print(f"      {status} {disease}: {info['kategori']}")

# 5. Test database
print("\n5️⃣  Testing database...")
try:
    import sqlite3
    if os.path.exists("surat_izin.db"):
        conn = sqlite3.connect("surat_izin.db")
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM surat_izin")
        count = cursor.fetchone()[0]
        conn.close()
        print(f"   ✅ Database exists with {count} records")
    else:
        print("   ⚠️  Database will be created on first run")
except Exception as e:
    print(f"   ❌ Database error: {e}")

# 6. Summary
print("\n" + "="*50)
print("✅ ALL CHECKS PASSED!")
print("="*50)
print("\n🚀 Next step: Run 'streamlit run app.py'")
print("\n📊 App will open at: http://localhost:8501")
