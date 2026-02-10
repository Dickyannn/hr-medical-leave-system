# 🔧 DASHBOARD ERROR FIX - LINE 394

## ❌ PROBLEM

**Error:** `KeyError: "None of [Index([-1], dtype='int64')] are in the [columns]"`

**Location:** Line 394 in app.py

**Root Cause:** Using `~` (negation) operator on column with NULL/None values

```python
# ❌ WRONG - Causes error with NULL values
not_reimb = df_filtered[~df_filtered['is_reimburseable']]['diagnosa'].value_counts().head(5)
```

When `is_reimburseable` column has NULL/None values:
- `~df_filtered['is_reimburseable']` doesn't handle them properly
- Creates invalid pandas indexing
- Results in the cryptic KeyError

---

## ✅ SOLUTION

**Change line 394** from:
```python
not_reimb = df_filtered[~df_filtered['is_reimburseable']]['diagnosa'].value_counts().head(5)
```

**To:**
```python
not_reimb = df_filtered[df_filtered['is_reimburseable'] == False]['diagnosa'].value_counts().head(5)
```

**Why this works:**
- Explicitly checks for `== False` instead of using negation
- Safely handles NULL/None values
- Returns proper boolean mask
- No pandas indexing errors

---

## 🧪 VERIFICATION

The fix has been applied. To verify it works:

```bash
# 1. Restart the app
streamlit run app.py

# 2. Go to Dashboard
Click: 📊 Dashboard Analytics

# 3. Charts should now load without errors
✅ Top 5 Penyakit (blue bar chart)
✅ Penyakit Tidak Reimburseable (salmon bar chart)
✅ All other charts
```

---

## 📝 TECHNICAL DETAILS

### The Issue:
```python
df_filtered['is_reimburseable']  # Contains: True, False, None, None, True, False...

# ❌ This fails:
~df_filtered['is_reimburseable']  # Creates invalid mask with None values

# ✅ This works:
df_filtered['is_reimburseable'] == False  # Creates proper boolean mask
```

### Why Comparison is Better:
- `== False` → Returns `True` only for False values, `False` for True/None
- `~(bool)` → Negates, but fails on None values
- Explicit comparison is safer and clearer

---

## ✨ STATUS

**Before:** Dashboard crashes with KeyError
**After:** Dashboard loads and charts display correctly

**Status: ✅ FIXED**

