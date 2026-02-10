import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from llm_client import (
    read_image_with_gemini,
    parse_ocr_text,
    classify_disease,
    DISEASE_MASTER
)
import os
from pathlib import Path

# ==================== DATABASE SETUP ====================

DB_PATH = "surat_izin.db"

def init_db():
    """Inisialisasi database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
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
    
    conn.commit()
    conn.close()


def get_all_records():
    """Ambil semua record dari database"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM surat_izin ORDER BY upload_date DESC", conn)
    conn.close()
    return df


def check_duplicate(new_data: dict) -> tuple[bool, float, str]:
    """
    Cek duplikasi dengan rule-based scoring
    
    Kriteria bobot:
    - NIK sama: 50%
    - Tanggal izin sama: 30%
    - Diagnosa sama: 20%
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM surat_izin")
    existing_records = cursor.fetchall()
    conn.close()
    
    if not existing_records:
        return False, 0.0, ""
    
    # Get column names
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(surat_izin)")
    columns = [row[1] for row in cursor.fetchall()]
    conn.close()
    
    highest_score = 0.0
    similar_records = []
    
    for record in existing_records:
        record_dict = dict(zip(columns, record))
        score = 0.0
        
        # NIK check (50%)
        if new_data.get('nik') and record_dict.get('nik') == new_data['nik']:
            score += 50
        
        # Tanggal izin check (30%)
        if new_data.get('tanggal_izin') and record_dict.get('tanggal_izin') == new_data['tanggal_izin']:
            score += 30
        
        # Diagnosa check (20%)
        if new_data.get('diagnosa') and record_dict.get('diagnosa') == new_data['diagnosa']:
            score += 20
        
        if score >= 80:
            highest_score = max(highest_score, score)
            similar_records.append(record_dict)
    
    if highest_score >= 80:
        note_parts = []
        if any(r['nik'] == new_data.get('nik') for r in similar_records):
            note_parts.append("NIK sama")
        if any(r['tanggal_izin'] == new_data.get('tanggal_izin') for r in similar_records):
            note_parts.append("Tanggal sama")
        if any(r['diagnosa'] == new_data.get('diagnosa') for r in similar_records):
            note_parts.append("Diagnosa sama")
        
        return True, highest_score, " & ".join(note_parts)
    
    return False, highest_score, ""


def save_to_db(record: dict):
    """Simpan record ke database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO surat_izin VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        record['surat_id'],
        record['nik'],
        record['nama'],
        record['tanggal_izin'],
        record['durasi'],
        record['diagnosa'],
        record['dokter'],
        record['rumah_sakit'],
        record['is_reimburseable'],
        record['kategori'],
        record['is_duplicate'],
        record['duplicate_score'],
        record['duplicate_note'],
        record['warning_flag'],
        record['warning_reason'],
        record['upload_date'],
        record['raw_text']
    ))
    
    conn.commit()
    conn.close()


# ==================== STREAMLIT APP ====================

st.set_page_config(page_title="HR Digitalisasi Surat Izin Dokter", layout="wide")

# Initialize DB
init_db()

# Sidebar navigation
st.sidebar.title("📋 Menu Navigasi")
page = st.sidebar.radio(
    "Pilih halaman:",
    ["📤 Upload Surat", "📊 Dashboard Analytics", "🔍 Review Data", "⚙️ Konfigurasi Penyakit"]
)

# ==================== PAGE 1: UPLOAD ====================

if page == "📤 Upload Surat":
    st.title("📤 Upload Surat Izin Dokter")
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Upload surat izin dokter (JPG, PNG, PDF):",
            type=['jpg', 'jpeg', 'png', 'pdf']
        )
    
    if uploaded_file:
        with st.spinner("📖 Membaca gambar dengan AI..."):
            # Save temp file
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Read with Gemini
            raw_text = read_image_with_gemini(temp_path)
            
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        # Parse text
        extracted_data = parse_ocr_text(raw_text)
        
        # Display extracted data
        st.success("✅ Data berhasil diekstrak!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Data Terekstrak")
            with st.form("edit_form"):
                nik = st.text_input("NIK", value=extracted_data['nik'] or "")
                nama = st.text_input("Nama", value=extracted_data['nama'] or "")
                tanggal_izin = st.text_input("Tanggal Izin (YYYY-MM-DD)", value=extracted_data['tanggal_izin'] or "")
                durasi = st.number_input("Durasi (hari)", value=extracted_data['durasi'] or 1, min_value=1)
                diagnosa = st.text_input("Diagnosa", value=extracted_data['diagnosa'] or "")
                dokter = st.text_input("Dokter", value=extracted_data['dokter'] or "")
                rumah_sakit = st.text_input("Rumah Sakit", value=extracted_data['rumah_sakit'] or "")
                
                submitted = st.form_submit_button("💾 Simpan & Analisis", use_container_width=True)
        
        if submitted:
            # Validate
            if not all([nik, nama, tanggal_izin, diagnosa]):
                st.error("❌ Data NIK, Nama, Tanggal Izin, dan Diagnosa harus lengkap!")
            else:
                # Prepare record
                processed_data = {
                    'nik': nik,
                    'nama': nama.lower().strip(),
                    'tanggal_izin': tanggal_izin,
                    'durasi': int(durasi),
                    'diagnosa': diagnosa.upper().strip(),
                    'dokter': dokter,
                    'rumah_sakit': rumah_sakit,
                    'raw_text': raw_text
                }
                
                # Check duplicate
                is_dup, dup_score, dup_note = check_duplicate(processed_data)
                
                # Classify disease
                disease_info = classify_disease(processed_data['diagnosa'])
                
                # Create record
                record = {
                    'surat_id': f"SURAT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    'nik': processed_data['nik'],
                    'nama': processed_data['nama'],
                    'tanggal_izin': processed_data['tanggal_izin'],
                    'durasi': processed_data['durasi'],
                    'diagnosa': processed_data['diagnosa'],
                    'dokter': processed_data['dokter'],
                    'rumah_sakit': processed_data['rumah_sakit'],
                    'is_reimburseable': disease_info['is_reimburseable'],
                    'kategori': disease_info['kategori'],
                    'is_duplicate': is_dup,
                    'duplicate_score': dup_score,
                    'duplicate_note': dup_note if is_dup else None,
                    'warning_flag': is_dup or disease_info['warning'] is not None,
                    'warning_reason': disease_info['warning'] if disease_info['warning'] else (f"Duplikasi ({dup_score}%)" if is_dup else None),
                    'upload_date': datetime.now().isoformat(),
                    'raw_text': raw_text
                }
                
                # Save to DB
                save_to_db(record)
                st.success(f"✅ Surat {record['surat_id']} berhasil disimpan!")
        
        with col2:
            st.subheader("🔍 Analisis")
            if submitted and all([nik, nama, tanggal_izin, diagnosa]):
                st.write(f"**Status Reimbursement:** {'✅ ELIGIBLE' if disease_info['is_reimburseable'] else '❌ TIDAK ELIGIBLE'}")
                st.write(f"**Kategori:** {disease_info['kategori']}")
                
                if is_dup:
                    st.warning(f"⚠️ **POTENSI DUPLIKAT**: {dup_score}% - {dup_note}")
                else:
                    st.info("✅ Tidak ada duplikasi")
                
                if disease_info['warning']:
                    st.warning(f"⚠️ {disease_info['warning']}")


# ==================== PAGE 2: DASHBOARD ====================

elif page == "📊 Dashboard Analytics":
    st.title("📊 Dashboard Analytics HR")
    st.markdown("---")
    
    df = get_all_records()
    
    if df.empty:
        st.info("📭 Belum ada data. Mulai dengan upload surat di halaman Upload.")
    else:
        # ---- DATE FILTER ----
        st.subheader("🔍 Filter Data")
        
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        
        # Convert upload_date to datetime
        df['upload_date'] = pd.to_datetime(df['upload_date'])
        
        with filter_col1:
            filter_type = st.radio(
                "Tipe Filter:",
                ["Tanpa Filter", "By Bulan & Tahun", "By Rentang Tanggal"],
                horizontal=True
            )
        
        if filter_type == "By Bulan & Tahun":
            with filter_col2:
                selected_year = st.selectbox(
                    "Pilih Tahun:",
                    sorted(df['upload_date'].dt.year.unique(), reverse=True)
                )
            
            with filter_col3:
                months = sorted(df[df['upload_date'].dt.year == selected_year]['upload_date'].dt.month.unique())
                month_names = {1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April', 
                              5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
                              9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'}
                selected_month = st.selectbox(
                    "Pilih Bulan:",
                    months,
                    format_func=lambda x: month_names.get(x, str(x))
                )
            
            # Filter data by year and month
            df_filtered = df[(df['upload_date'].dt.year == selected_year) & 
                            (df['upload_date'].dt.month == selected_month)]
        
        elif filter_type == "By Rentang Tanggal":
            with filter_col2:
                start_date = st.date_input(
                    "Tanggal Mulai:",
                    value=df['upload_date'].min().date()
                )
            
            with filter_col3:
                end_date = st.date_input(
                    "Tanggal Akhir:",
                    value=df['upload_date'].max().date()
                )
            
            # Filter data by date range
            df_filtered = df[(df['upload_date'].dt.date >= start_date) & 
                            (df['upload_date'].dt.date <= end_date)]
        
        else:
            # No filter
            df_filtered = df.copy()
        
        st.markdown("---")
        
        # ---- STATISTIK KESELURUHAN ----
        st.subheader("📈 Statistik Keseluruhan")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("📄 Total Surat", len(df_filtered))
        
        with col2:
            eligible = df_filtered['is_reimburseable'].sum()
            st.metric("✅ Eligible", int(eligible))
        
        with col3:
            not_eligible = len(df_filtered) - int(df_filtered['is_reimburseable'].sum())
            st.metric("❌ Tidak Eligible", not_eligible)
        
        with col4:
            duplicates = int(df_filtered['is_duplicate'].sum())
            st.metric("🔁 Duplikat", duplicates)
        
        with col5:
            warnings = int(df_filtered['warning_flag'].sum())
            st.metric("⚠️ Perlu Review", warnings)
        
        st.markdown("---")
        
        # ---- TOP DISEASES ----
        st.subheader("🏥 Top 5 Penyakit Paling Sering")
        
        col1, col2 = st.columns(2)
        
        with col1:
            disease_counts = df_filtered['diagnosa'].value_counts().head(5)
            if len(disease_counts) > 0:
                fig_disease = go.Figure(data=[
                    go.Bar(x=disease_counts.values, y=disease_counts.index, orientation='h', marker_color='lightblue')
                ])
                fig_disease.update_layout(xaxis_title="Jumlah", yaxis_title="Penyakit", height=400)
                st.plotly_chart(fig_disease, use_container_width=True)
            else:
                st.info("Tidak ada data untuk periode ini")
        
        with col2:
            # Penyakit tidak reimburseable
            not_reimb = df_filtered[df_filtered['is_reimburseable'] == False]['diagnosa'].value_counts().head(5)
            if len(not_reimb) > 0:
                fig_not_reimb = go.Figure(data=[
                    go.Bar(x=not_reimb.values, y=not_reimb.index, orientation='h', marker_color='salmon')
                ])
                fig_not_reimb.update_layout(xaxis_title="Jumlah", yaxis_title="Penyakit", height=400)
                st.plotly_chart(fig_not_reimb, use_container_width=True)
            else:
                st.info("Semua penyakit dapat direimburse!")
        
        st.markdown("---")
        
        # ---- REIMBURSEMENT ANALYSIS ----
        st.subheader("💰 Reimbursement Insight")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Count reimburseable status properly
            reimb_true = int((df_filtered['is_reimburseable'] == True).sum())
            reimb_false = int((df_filtered['is_reimburseable'] == False).sum())
            
            labels = ['✅ Bisa Direimburse', '❌ Tidak Bisa Direimburse']
            values = [reimb_true, reimb_false]
            colors = ['#2ecc71', '#e74c3c']
            
            if sum(values) > 0:
                fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, marker=dict(colors=colors))])
                fig_pie.update_layout(height=400, title="Distribusi Reimbursement")
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Tidak ada data")
        
        with col2:
            category_dist = df_filtered['kategori'].value_counts()
            if len(category_dist) > 0:
                fig_cat = go.Figure(data=[
                    go.Bar(x=category_dist.index, y=category_dist.values, marker_color='mediumpurple')
                ])
                fig_cat.update_layout(xaxis_title="Kategori", yaxis_title="Jumlah", height=400, title="Distribusi Kategori Penyakit")
                st.plotly_chart(fig_cat, use_container_width=True)
            else:
                st.info("Tidak ada data")
        
        st.markdown("---")
        
        # ---- TREND TIMELINE ----
        st.subheader("📅 Trend Izin Sakit per Bulan")
        
        df_filtered['month'] = pd.to_datetime(df_filtered['tanggal_izin']).dt.to_period('M').astype(str)
        monthly_counts = df_filtered['month'].value_counts().sort_index()
        
        if len(monthly_counts) > 0:
            fig_timeline = go.Figure(data=[
                go.Bar(x=monthly_counts.index, y=monthly_counts.values, marker_color='teal')
            ])
            fig_timeline.update_layout(xaxis_title="Bulan (Tanggal Izin)", yaxis_title="Jumlah Surat", height=400)
            st.plotly_chart(fig_timeline, use_container_width=True)
        else:
            st.info("Tidak ada data untuk periode ini")
        
        st.markdown("---")
        
        # ---- DUPLICATE & FRAUD INDICATOR ----
        st.subheader("🔴 Fraud / Duplicate Indicator")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("🔁 Total Duplikat Terdeteksi", int(df_filtered['is_duplicate'].sum()))
            
            # Karyawan dengan izin berulang
            st.write("**Karyawan dengan Izin Berulang (3+ kali):**")
            employee_freq = df_filtered['nik'].value_counts()
            repeat_employees = employee_freq[employee_freq >= 3]
            
            if len(repeat_employees) > 0:
                for nik, count in repeat_employees.items():
                    emp_data = df_filtered[df_filtered['nik'] == nik].iloc[0]
                    st.warning(f"{emp_data['nama']} ({nik}): {count} kali izin")
            else:
                st.info("Tidak ada pola izin berulang yang mencurigakan")
        
        with col2:
            # Duplicate score distribution
            dup_df = df_filtered[df_filtered['is_duplicate'] == True]
            if len(dup_df) > 0:
                fig_dup = go.Figure(data=[
                    go.Histogram(x=dup_df['duplicate_score'], nbinsx=10, marker_color='coral')
                ])
                fig_dup.update_layout(xaxis_title="Duplicate Score (%)", yaxis_title="Jumlah", height=300)
                st.plotly_chart(fig_dup, use_container_width=True)
            else:
                st.info("Tidak ada duplikat di periode ini")


# ==================== PAGE 3: REVIEW DATA ====================

elif page == "🔍 Review Data":
    st.title("🔍 Review Data Surat Izin")
    st.markdown("---")
    
    df = get_all_records()
    
    if df.empty:
        st.info("📭 Belum ada data.")
    else:
        # Filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox(
                "Filter Status:",
                ["Semua", "✅ Eligible Reimburse", "⚠️ Perlu Review", "❌ Tidak Reimburseable"]
            )
        
        with col2:
            duplicate_filter = st.checkbox("Hanya Duplikat")
        
        with col3:
            warning_filter = st.checkbox("Hanya dengan Warning")
        
        # Apply filters
        filtered_df = df.copy()
        
        if status_filter == "✅ Eligible Reimburse":
            filtered_df = filtered_df[filtered_df['is_reimburseable'] == True]
        elif status_filter == "❌ Tidak Reimburseable":
            filtered_df = filtered_df[filtered_df['is_reimburseable'] == False]
        elif status_filter == "⚠️ Perlu Review":
            filtered_df = filtered_df[filtered_df['warning_flag'] == True]
        
        if duplicate_filter:
            filtered_df = filtered_df[filtered_df['is_duplicate'] == True]
        
        if warning_filter:
            filtered_df = filtered_df[filtered_df['warning_flag'] == True]
        
        # Display table
        display_cols = ['surat_id', 'nik', 'nama', 'tanggal_izin', 'durasi', 'diagnosa', 
                       'is_reimburseable', 'kategori', 'is_duplicate', 'warning_flag', 'upload_date']
        
        st.write(f"**Total Records: {len(filtered_df)}**")
        st.dataframe(filtered_df[display_cols], use_container_width=True, height=600)


# ==================== PAGE 4: CONFIG ====================

elif page == "⚙️ Konfigurasi Penyakit":
    st.title("⚙️ Konfigurasi Master Data Penyakit")
    st.markdown("---")
    
    st.info("📌 Tabel ini menentukan apakah penyakit dapat direimburse berdasarkan jenis kelamin dan kategori penyakit")
    
    # Display current config
    disease_list = []
    for disease, info in DISEASE_MASTER.items():
        # Determine gender status
        if info['reimburseable_male'] and info['reimburseable_female']:
            gender_status = "👥 Semua"
        elif info['reimburseable_male']:
            gender_status = "👨 Laki-laki"
        elif info['reimburseable_female']:
            gender_status = "👩 Perempuan"
        else:
            gender_status = "❌ Tidak Ada"
        
        disease_list.append({
            'Penyakit': disease,
            'Status': '✅ Bisa' if info['reimburseable'] else '❌ Tidak Bisa',
            'Kategori': info['kategori'],
            'Jenis Kelamin': gender_status,
            'Catatan': info.get('catatan', '')
        })
    
    config_df = pd.DataFrame(disease_list)
    st.dataframe(config_df, use_container_width=True)
    
    st.markdown("---")
    st.write("**📝 Catatan:** Untuk mengubah konfigurasi, edit `DISEASE_MASTER` di file `llm_client.py`")
    
    # Display info about changes
    st.subheader("📋 Informasi Field:")
    col1, col2 = st.columns(2)
    with col1:
        st.write("""
        - **Status**: ✅ Bisa / ❌ Tidak Bisa
        - **Kategori**: RINGAN / SEDANG / BERAT
        """)
    with col2:
        st.write("""
        - **Jenis Kelamin**: Eligibilitas berdasarkan gender
        - **Catatan**: Penjelasan detail penyakit
        """)

