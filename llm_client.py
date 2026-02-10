import requests
import os
import base64
import re
import io
from datetime import datetime
from dotenv import load_dotenv
from PIL import Image

try:
    from pdf2image import convert_from_path
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL")

# ==================== GEMINI IMAGE READING ====================

# ==================== PDF & IMAGE HANDLING ====================

def convert_pdf_to_images(pdf_path: str) -> list:
    """
    Konversi PDF ke image list. Jika PDF_SUPPORT tidak tersedia, return empty list.
    """
    if not PDF_SUPPORT:
        return []
    
    try:
        images = convert_from_path(pdf_path, dpi=300)
        return images
    except Exception as e:
        print(f"Error converting PDF: {str(e)}")
        return []


def read_image_with_gemini(image_path: str) -> str:
    """
    Baca gambar surat izin dokter menggunakan Gemini API.
    Support untuk JPG, PNG, dan PDF (akan dikonversi ke image dahulu)
    """
    try:
        # Handle PDF files
        ext = image_path.lower().split('.')[-1]
        
        if ext == 'pdf':
            if not PDF_SUPPORT:
                return "Error: PDF support tidak tersedia. Install pdf2image dengan: pip install pdf2image"
            
            # Convert PDF to images
            images = convert_pdf_to_images(image_path)
            if not images:
                return "Error: Gagal mengkonversi PDF ke gambar"
            
            # Process first page only (most doctor's letters are single page)
            image = images[0]
            
            # Convert PIL image to base64
            # Ensure it's PNG format
            if isinstance(image, Image.Image):
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                image_data = base64.standard_b64encode(buffer.getvalue()).decode("utf-8")
                media_type = "image/png"
            else:
                return "Error: Gagal mengkonversi PDF"
        else:
            # Handle regular image files
            with open(image_path, "rb") as image_file:
                image_data = base64.standard_b64encode(image_file.read()).decode("utf-8")
            
            media_type_map = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'webp': 'image/webp'
            }
            media_type = media_type_map.get(ext, 'image/jpeg')
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": media_type,
                                "data": image_data
                            }
                        },
                        {
                            "text": """Ekstrak data dari surat izin dokter ini:
                            
Berikan output dalam format:
NIK: [nilai]
Nama: [nilai]
Tanggal Izin: [nilai dalam format DD MMMM YYYY]
Durasi: [nilai dalam hari]
Diagnosa: [nilai]
Dokter: [nilai]
Rumah Sakit: [nilai]

Jika ada field yang tidak terlihat, tulis TIDAK_DITEMUKAN"""
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(
            GEMINI_BASE_URL,
            headers=headers,
            json=payload,
            params={"key": GEMINI_API_KEY}
        )
        
        if response.status_code != 200:
            return f"Error: {response.status_code} - {response.text}"
        
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    
    except Exception as e:
        return f"Error: {str(e)}"


# ==================== DATA PARSING & NORMALIZATION ====================

def parse_ocr_text(raw_text: str) -> dict:
    """
    Parse raw OCR text ke structured format
    """
    result = {
        "nik": None,
        "nama": None,
        "tanggal_izin": None,
        "durasi": None,
        "diagnosa": None,
        "dokter": None,
        "rumah_sakit": None,
        "raw_text": raw_text
    }
    
    lines = raw_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            
            if key == 'nik' and value != "TIDAK_DITEMUKAN":
                result['nik'] = value
            elif key == 'nama' and value != "TIDAK_DITEMUKAN":
                result['nama'] = value
            elif key == 'tanggal izin' and value != "TIDAK_DITEMUKAN":
                result['tanggal_izin'] = normalize_date(value)
            elif key == 'durasi' and value != "TIDAK_DITEMUKAN":
                result['durasi'] = extract_duration(value)
            elif key == 'diagnosa' and value != "TIDAK_DITEMUKAN":
                result['diagnosa'] = normalize_diagnosis(value)
            elif key == 'dokter' and value != "TIDAK_DITEMUKAN":
                result['dokter'] = value
            elif key == 'rumah sakit' and value != "TIDAK_DITEMUKAN":
                result['rumah_sakit'] = value
    
    return result


def normalize_date(date_str: str) -> str:
    """
    Konversi ke format YYYY-MM-DD
    """
    months = {
        'januari': '01', 'january': '01', 'jan': '01',
        'februari': '02', 'february': '02', 'feb': '02',
        'maret': '03', 'march': '03', 'mar': '03',
        'april': '04', 'apr': '04',
        'mei': '05', 'may': '05',
        'juni': '06', 'june': '06', 'jun': '06',
        'juli': '07', 'july': '07', 'jul': '07',
        'agustus': '08', 'august': '08', 'aug': '08',
        'september': '09', 'sept': '09', 'sep': '09',
        'oktober': '10', 'october': '10', 'oct': '10',
        'november': '11', 'nov': '11',
        'desember': '12', 'december': '12', 'dec': '12'
    }
    
    date_str = date_str.lower()
    
    # Try format: DD MMMM YYYY
    for month_name, month_num in months.items():
        if month_name in date_str:
            parts = date_str.split()
            try:
                day = parts[0].zfill(2)
                year = parts[-1]
                return f"{year}-{month_num}-{day}"
            except:
                pass
    
    # Try format: YYYY-MM-DD
    if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
        return date_str
    
    return None


def extract_duration(duration_str: str) -> int:
    """
    Ekstrak durasi dalam hari
    """
    numbers = re.findall(r'\d+', duration_str)
    if numbers:
        return int(numbers[0])
    return None


def normalize_diagnosis(diagnosis: str) -> str:
    """
    Normalisasi diagnosis
    """
    diagnosis = diagnosis.upper().strip()
    
    # Mapping sinonim
    synonyms = {
        'DEMAM': ['DEMAM', 'FEBRIS', 'PANAS', 'FEVER'],
        'TIPES': ['TIPES', 'TYPHUS', 'TYPUS'],
        'DBD': ['DBD', 'DENGUE', 'DEMAM BERDARAH'],
        'PILEK': ['PILEK', 'COMMON COLD', 'RHINITIS'],
        'BATUK': ['BATUK', 'COUGH'],
        'SAKIT KEPALA': ['SAKIT KEPALA', 'HEADACHE', 'MIGRAIN'],
        'DIARE': ['DIARE', 'DIARRHEA'],
        'ASMA': ['ASMA', 'ASTHMA'],
        'HIPERTENSI': ['HIPERTENSI', 'HYPERTENSION'],
        'DIABETES': ['DIABETES'],
    }
    
    for standard, variants in synonyms.items():
        for variant in variants:
            if variant in diagnosis:
                return standard
    
    return diagnosis


# ==================== DISEASE CLASSIFICATION ====================

DISEASE_MASTER = {
    'DEMAM': {
        'reimburseable': False,
        'kategori': 'RINGAN',
        'status_text': 'Tidak Bisa',
        'reimburseable_male': False,
        'reimburseable_female': False,
        'catatan': 'Penyakit ringan, tidak direimburse'
    },
    'PILEK': {
        'reimburseable': False,
        'kategori': 'RINGAN',
        'status_text': 'Tidak Bisa',
        'reimburseable_male': False,
        'reimburseable_female': False,
        'catatan': 'Penyakit ringan, tidak direimburse'
    },
    'BATUK': {
        'reimburseable': False,
        'kategori': 'RINGAN',
        'status_text': 'Tidak Bisa',
        'reimburseable_male': False,
        'reimburseable_female': False,
        'catatan': 'Penyakit ringan, tidak direimburse'
    },
    'SAKIT KEPALA': {
        'reimburseable': False,
        'kategori': 'RINGAN',
        'status_text': 'Tidak Bisa',
        'reimburseable_male': False,
        'reimburseable_female': False,
        'catatan': 'Penyakit ringan, tidak direimburse'
    },
    'TIPES': {
        'reimburseable': True,
        'kategori': 'SEDANG',
        'status_text': 'Bisa',
        'reimburseable_male': True,
        'reimburseable_female': True,
        'catatan': 'Penyakit menular, bisa direimburse semua gender'
    },
    'DBD': {
        'reimburseable': True,
        'kategori': 'BERAT',
        'status_text': 'Bisa',
        'reimburseable_male': True,
        'reimburseable_female': True,
        'catatan': 'Penyakit berat, bisa direimburse semua gender'
    },
    'DIARE': {
        'reimburseable': True,
        'kategori': 'SEDANG',
        'status_text': 'Bisa',
        'reimburseable_male': True,
        'reimburseable_female': True,
        'catatan': 'Penyakit menular, bisa direimburse semua gender'
    },
    'ASMA': {
        'reimburseable': True,
        'kategori': 'SEDANG',
        'status_text': 'Bisa',
        'reimburseable_male': True,
        'reimburseable_female': True,
        'catatan': 'Penyakit kronis, bisa direimburse semua gender'
    },
    'HIPERTENSI': {
        'reimburseable': True,
        'kategori': 'SEDANG',
        'status_text': 'Bisa',
        'reimburseable_male': True,
        'reimburseable_female': True,
        'catatan': 'Penyakit kronis, bisa direimburse semua gender'
    },
    'DIABETES': {
        'reimburseable': True,
        'kategori': 'BERAT',
        'status_text': 'Bisa',
        'reimburseable_male': True,
        'reimburseable_female': True,
        'catatan': 'Penyakit kronis berat, bisa direimburse semua gender'
    },
}


def classify_disease(diagnosis: str) -> dict:
    """
    Klasifikasi penyakit dan tentukan reimbursability
    """
    diagnosis = diagnosis.upper().strip()
    
    if diagnosis in DISEASE_MASTER:
        info = DISEASE_MASTER[diagnosis]
        return {
            'is_reimburseable': info['reimburseable'],
            'kategori': info['kategori'],
            'warning': None if info['reimburseable'] else 'Penyakit tidak dapat direimburse'
        }
    
    return {
        'is_reimburseable': None,
        'kategori': 'TIDAK_DIKETAHUI',
        'warning': 'Diagnosis tidak ditemukan di master data'
    }
