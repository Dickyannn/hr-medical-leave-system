#!/usr/bin/env python3
"""
Quick test untuk dashboard dengan sample data
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import random

DB_PATH = "surat_izin_demo.db"

def create_demo_db():
    """Create sample data untuk testing dashboard"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS surat_izin (
        surat_id TEXT PRIMARY KEY,
        nik TEXT,
        nama TEXT,
        tanggal_izin TEXT,
        durasi INTEGER,
        diagnosa TEXT,
        dokter TEXT,
        rumah_sakit TEXT,
        is_reimburseable BOOLEAN,
        kategori TEXT,
        is_duplicate BOOLEAN,
        duplicate_score FLOAT,
        duplicate_note TEXT,
        warning_flag BOOLEAN,
        warning_reason TEXT,
        upload_date TEXT,
        raw_text TEXT
    )
    ''')
    
    # Sample data
    diseases = [
        ('DEMAM', False, 'RINGAN'),
        ('FLU', False, 'RINGAN'),
        ('TIPES', True, 'SEDANG'),
        ('DBD', True, 'BERAT'),
        ('DIARE', True, 'SEDANG'),
        ('ASMA', True, 'SEDANG'),
    ]
    
    names = [
        'Dicky Anugrah', 'Sari Utami', 'Hari Santoso',
        'Budi Raharjo', 'Ani Wijaya', 'Citra Dewi',
        'Eka Putri', 'Fajar Rahman', 'Gita Kumala'
    ]
    
    doctors = ['dr. Andi', 'dr. Budi', 'dr. Citra', 'dr. Doni', 'dr. Eka']
    hospitals = ['RS Sehat', 'RS Maju', 'Klinik Medis', 'RS Bersama']
    
    # Generate 100 sample records across Jan-Feb 2026
    base_date = datetime(2026, 1, 1)
    
    for i in range(100):
        nik = f"31750{1000 + i}"
        nama = random.choice(names)
        diagnosa, is_reimburseable, kategori = random.choice(diseases)
        
        # Random dates between Jan-Feb
        days_offset = random.randint(0, 40)
        upload_date = base_date + timedelta(days=days_offset)
        
        # Create record
        record = (
            f"SURAT_{upload_date.strftime('%Y%m%d')}{i:03d}",  # surat_id
            nik,  # nik
            nama,  # nama
            upload_date.strftime('%Y-%m-%d'),  # tanggal_izin
            random.randint(1, 3),  # durasi
            diagnosa,  # diagnosa
            random.choice(doctors),  # dokter
            random.choice(hospitals),  # rumah_sakit
            is_reimburseable,  # is_reimburseable
            kategori,  # kategori
            random.random() < 0.05,  # is_duplicate (5% chance)
            random.uniform(0, 100) if random.random() < 0.05 else 0,  # duplicate_score
            "Similar NIK & Date" if random.random() < 0.05 else None,  # duplicate_note
            is_reimburseable == False or random.random() < 0.1,  # warning_flag
            None if is_reimburseable else "Penyakit tidak dapat direimburse",  # warning_reason
            upload_date.isoformat(),  # upload_date
            f"OCR text for {nama}"  # raw_text
        )
        
        cursor.execute('''
        INSERT INTO surat_izin VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', record)
    
    conn.commit()
    conn.close()
    
    print(f"✅ Demo database created: {DB_PATH}")
    print(f"✅ Created 100 sample records")
    print(f"✅ Date range: 2026-01-01 to 2026-02-10")
    print(f"\nTo test:")
    print(f"1. Move this file to your project folder")
    print(f"2. Run: python test_demo_data.py")
    print(f"3. Then run: streamlit run app.py")
    print(f"4. Dashboard will have 100 sample records to filter")

if __name__ == "__main__":
    create_demo_db()
