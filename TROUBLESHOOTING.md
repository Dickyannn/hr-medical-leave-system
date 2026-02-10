# 🆘 TROUBLESHOOTING & FAQ

## ⚡ Quick Fixes

### Problem 1: ModuleNotFoundError (Missing Dependencies)
**Error:**
```
ModuleNotFoundError: No module named 'streamlit'
```

**Solution:**
```bash
pip install -r requirements.txt
```

**Or manually:**
```bash
pip install streamlit pandas plotly requests python-dotenv pillow
```

---

### Problem 2: API Key Not Found
**Error:**
```
AttributeError: 'NoneType' object is not subscriptable
```
or
```
Error: API key is not set
```

**Solution:**
1. Check `.env` file exists in same directory as `app.py`
2. Verify file contains:
   ```
   GEMINI_API_KEY=AIzaSyB-H5Dx2fqxLcSQKnhg6gstsQFSpHNl_ms
   GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent
   ```
3. Make sure no typos in variable names
4. Restart Streamlit app

---

### Problem 3: Port Already in Use
**Error:**
```
Address already in use :: port 8501
```

**Solution:**
```bash
# Find process using port 8501
netstat -ano | findstr :8501

# Kill process (replace PID with actual number)
taskkill /PID <PID> /F

# Or use different port
streamlit run app.py --server.port 8502
```

---

### Problem 4: Image Upload Not Working
**Error:**
```
File upload error
```

**Solution:**
- Use supported formats: JPG, PNG, PDF
- File size should be < 20MB
- Try different file first to isolate issue
- Check file is not corrupted

---

### Problem 5: Database Locked
**Error:**
```
sqlite3.OperationalError: database is locked
```

**Solution:**
```bash
# Close all Streamlit terminals
# Delete lock file if exists
rm surat_izin.db-journal

# Restart app
streamlit run app.py
```

---

### Problem 6: OCR Returns Empty Text
**Error:**
```
Raw text is empty or blank
```

**Possible Causes:**
- Image quality too low
- Image is not a text document
- API call failed
- API quota exceeded

**Solution:**
- Use clearer scans/photos
- Check API key quotas
- Verify internet connection
- Try different image

---

### Problem 7: Streamlit Crashes on Startup
**Error:**
```
StreamlitAPIException or AttributeError
```

**Solution:**
1. Delete cache:
   ```bash
   rm -rf ~/.streamlit/
   rm -rf ./.streamlit/
   ```

2. Reinstall Streamlit:
   ```bash
   pip install --upgrade streamlit
   ```

3. Run again:
   ```bash
   streamlit run app.py
   ```

---

## 🔍 Debugging Tips

### 1. Enable Verbose Logging
```bash
streamlit run app.py --logger.level=debug
```

### 2. Check Python Version
```bash
python --version
# Should be 3.8 or higher
```

### 3. Verify Dependencies
```bash
python test_setup.py
```

### 4. Test API Connection
```python
import requests
import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GEMINI_API_KEY")
url = os.getenv("GEMINI_BASE_URL")

print(f"API Key: {key[:20]}...")
print(f"Base URL: {url}")

# Try simple test
response = requests.post(
    url,
    json={"test": "data"},
    params={"key": key}
)
print(f"Status: {response.status_code}")
```

### 5. Database Inspection
```python
import sqlite3

conn = sqlite3.connect("surat_izin.db")
cursor = conn.cursor()

# Get all records
cursor.execute("SELECT COUNT(*) FROM surat_izin")
print(f"Total records: {cursor.fetchone()[0]}")

# Show schema
cursor.execute("PRAGMA table_info(surat_izin)")
for row in cursor.fetchall():
    print(row)

conn.close()
```

---

## ❓ FAQ

### Q1: Can I change disease reimbursement status?
**A:** Yes! Edit `DISEASE_MASTER` dictionary in `llm_client.py`:
```python
DISEASE_MASTER = {
    'DEMAM': {'reimburseable': True, 'kategori': 'RINGAN'},  # Change to True
    ...
}
```
Then restart app.

---

### Q2: How do I delete a record?
**A:** Currently, records are kept for audit trail. To delete:
```python
import sqlite3
conn = sqlite3.connect("surat_izin.db")
cursor = conn.cursor()
cursor.execute("DELETE FROM surat_izin WHERE surat_id = ?", ("SURAT_xxx",))
conn.commit()
conn.close()
```

---

### Q3: Can I export data to Excel?
**A:** Yes! In Review page, use browser's download feature on the table. Or:
```python
import pandas as pd
df = pd.read_sql_query("SELECT * FROM surat_izin", sqlite3.connect("surat_izin.db"))
df.to_excel("export.xlsx", index=False)
```

---

### Q4: What's the maximum file size for upload?
**A:** Streamlit default is 200MB. Can be changed in `.streamlit/config.toml`:
```
[client]
maxUploadSize = 200
```

---

### Q5: Can I add more diseases to master data?
**A:** Yes! Add to `DISEASE_MASTER`:
```python
DISEASE_MASTER = {
    ...existing...
    'COVID': {'reimburseable': True, 'kategori': 'BERAT'},
    'MALARIA': {'reimburseable': True, 'kategori': 'BERAT'},
}
```

---

### Q6: How do I change duplicate detection threshold?
**A:** Edit `check_duplicate()` function in `app.py`:
```python
if score >= 80:  # Change 80 to desired threshold (0-100)
    return True, score, ...
```

---

### Q7: Can duplicate detection be disabled?
**A:** Yes, in `app.py`, find duplicate check and comment out:
```python
is_dup, dup_score, dup_note = check_duplicate(processed_data)
# Change to:
is_dup, dup_score, dup_note = False, 0.0, ""
```

---

### Q8: How do I backup the database?
**A:** Simple copy the file:
```bash
# Windows
copy surat_izin.db surat_izin_backup.db

# Linux/Mac
cp surat_izin.db surat_izin_backup.db
```

---

### Q9: Can I reset all data?
**A:** Yes, delete database file:
```bash
# Windows
del surat_izin.db

# Linux/Mac
rm surat_izin.db
```
App will recreate empty database on restart.

---

### Q10: How do I change the app title/theme?
**A:** Edit top of `app.py`:
```python
st.set_page_config(
    page_title="Your Custom Title",
    layout="wide",
    initial_sidebar_state="expanded"
)
```

---

## 🔧 Advanced Configuration

### Change Gemini Model
In `llm_client.py`, edit:
```python
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"
```

Available models:
- `gemini-2.5-flash` (current - fast)
- `gemini-1.5-pro` (powerful)
- `gemini-1.5-flash` (fast)

---

### Customize OCR Prompt
In `read_image_with_gemini()`, modify the prompt:
```python
"text": """Your custom prompt here
Extract data from medical certificate:
[Your fields here]"""
```

---

### Adjust Dashboard Colors
In `app.py`, edit chart colors:
```python
fig = go.Figure(data=[
    go.Bar(..., marker_color='YOUR_COLOR')
])
```

Available colors: 'lightblue', 'salmon', 'teal', 'mediumpurple', 'lightgreen', etc.

---

## 📊 Performance Tips

### Optimize for Large Datasets
1. Add database indexing:
```python
cursor.execute("CREATE INDEX IF NOT EXISTS idx_nik ON surat_izin(nik)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_date ON surat_izin(tanggal_izin)")
```

2. Use pagination in Review page
3. Cache dashboard queries:
```python
@st.cache_data
def get_all_records():
    # ... database query
```

---

### Speed Up OCR
- Use JPG format (smaller than PNG)
- Compress image before upload
- Use gemini-2.5-flash (faster than pro)

---

## 🔐 Security Best Practices

1. **Never commit .env to git**
   ```bash
   echo ".env" >> .gitignore
   ```

2. **Use environment variables in production**
   ```bash
   export GEMINI_API_KEY="xxx"
   export GEMINI_BASE_URL="xxx"
   streamlit run app.py
   ```

3. **Rotate API keys regularly**

4. **Use HTTPS in production**

5. **Implement user authentication**
   ```python
   import streamlit_authenticator as stauth
   # Add auth middleware
   ```

---

## 📝 Logging & Monitoring

### Enable App Logging
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
```

---

## 🚀 Deployment

### Deploy to Streamlit Cloud
```bash
# 1. Push code to GitHub
git push origin main

# 2. Go to https://share.streamlit.io
# 3. Connect GitHub repo
# 4. Deploy
```

### Deploy with Docker
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "app.py"]
```

```bash
docker build -t hr-app .
docker run -p 8501:8501 hr-app
```

---

## 📞 Support Resources

- **Streamlit Docs:** https://docs.streamlit.io
- **Gemini API Docs:** https://ai.google.dev/tutorials
- **SQLite Docs:** https://www.sqlite.org/docs.html
- **Plotly Docs:** https://plotly.com/python/

---

## 📋 Checklist Before Production

- [ ] Test with sample medical certificates
- [ ] Verify OCR accuracy
- [ ] Test duplicate detection with known duplicates
- [ ] Verify disease classification is correct
- [ ] Test database backup/restore
- [ ] Review security settings
- [ ] Check API quotas
- [ ] Load test with 100+ records
- [ ] Train HR users
- [ ] Document custom configurations
- [ ] Setup monitoring/logging

---

**Still having issues?**

1. Run: `python test_setup.py`
2. Check console output for errors
3. Review logs: Streamlit logs in terminal
4. Check database: `python debug_db.py`
5. Contact support with error message

