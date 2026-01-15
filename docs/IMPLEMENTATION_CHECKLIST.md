# Implementation Checklist
## Production Architecture Deployment Guide

**Quick Reference**: Step-by-step checklist for implementing dynamic data pipeline

---

## 📋 PRE-IMPLEMENTATION SETUP

### ✅ Review Phase (Day 0)
- [ ] Read [PRODUCTION_EXECUTIVE_SUMMARY.md](PRODUCTION_EXECUTIVE_SUMMARY.md)
- [ ] Review [PRODUCTION_ARCHITECTURE_DESIGN.md](PRODUCTION_ARCHITECTURE_DESIGN.md)
- [ ] Review [PRODUCTION_TEST_CASES.md](PRODUCTION_TEST_CASES.md)
- [ ] Understand current v8.2 codebase
- [ ] Set up development environment

---

## 🏗️ PHASE 1: CORE INFRASTRUCTURE (Days 1-3)

### Day 1: Module Structure & Data Catalog

#### Create Directory Structure
```bash
cd Code/
mkdir -p core query execution indexing
touch core/__init__.py
touch query/__init__.py
touch execution/__init__.py
touch indexing/__init__.py
```

- [ ] Create `core/` directory
- [ ] Create `query/` directory
- [ ] Create `execution/` directory
- [ ] Create `indexing/` directory
- [ ] Add `__init__.py` to each module

#### Implement Data Catalog
- [ ] Create `core/data_catalog.py`
- [ ] Copy code from PRODUCTION_ARCHITECTURE_DESIGN.md (Section 8.2)
- [ ] Test catalog initialization
- [ ] Test `register_sales_data()`
- [ ] Test `is_available()`
- [ ] Test `get_available_months()`

**Verification**:
```python
from core.data_catalog import get_data_catalog
catalog = get_data_catalog()
print(catalog.get_available_months("sales"))
# Expected: List of months or []
```

---

### Day 2: Data Loader & Validator

#### Implement Data Loader
- [ ] Create `core/data_loader.py`
- [ ] Copy code from Section 8.3
- [ ] Implement `load_sales_month()`
- [ ] Implement caching logic
- [ ] Test cache hit/miss

**Verification**:
```python
from core.data_loader import get_data_loader
loader = get_data_loader()
df = loader.load_sales_month("2024-06")
print(f"Loaded {len(df)} rows")
# Expected: DataFrame with >0 rows
```

#### Implement Validator
- [ ] Create `query/validator.py`
- [ ] Copy code from Section 8.4
- [ ] Implement `validate()`
- [ ] Implement `get_clarification_prompt()`
- [ ] Test with available and unavailable months

**Verification**:
```python
from query.validator import validate_data_availability
result = validate_data_availability("2024-07", "sales")
print(result)
# Expected: {"available": False, "message": "...", ...}
```

---

### Day 3: Data Preparation

#### Split Existing CSV
- [ ] Create script `scripts/split_csv_by_month.py`:

```python
import pandas as pd
import os

# Load full dataset
df = pd.read_csv("data/MY_Retail_Sales_2024H1.csv")
df["Date"] = pd.to_datetime(df["Date"])
df["YearMonth"] = df["Date"].dt.to_period("M")

# Create output directory
os.makedirs("data/sales", exist_ok=True)

# Split by month
for month in df["YearMonth"].unique():
    month_df = df[df["YearMonth"] == month]
    filename = f"data/sales/MY_Retail_Sales_{month}.csv"
    month_df.to_csv(filename, index=False)
    print(f"✅ Created: {filename} ({len(month_df)} rows)")
```

- [ ] Run split script
- [ ] Verify files created in `data/sales/`
- [ ] Verify each file has correct date range

#### Initialize Catalog
- [ ] Create script `scripts/initialize_catalog.py`:

```python
from core.data_catalog import DataCatalog
import pandas as pd
import glob
import re

catalog = DataCatalog()

for file_path in sorted(glob.glob("data/sales/*.csv")):
    # Extract month from filename
    match = re.search(r'(\d{4})-(\d{2})', file_path)
    if match:
        year_month = f"{match.group(1)}-{match.group(2)}"
        
        # Load and register
        df = pd.read_csv(file_path)
        df["Date"] = pd.to_datetime(df["Date"])
        catalog.register_sales_data(year_month, file_path, df)
        print(f"✅ Registered: {year_month}")

print("\n📊 Catalog Summary:")
print(f"Available months: {catalog.get_available_months('sales')}")
print(f"Latest month: {catalog.get_latest_month('sales')}")
```

- [ ] Run initialization script
- [ ] Verify `data/metadata/data_catalog.json` created
- [ ] Verify all 6 months registered

**Verification**:
```bash
cat data/metadata/data_catalog.json
# Expected: JSON with sales.2024-01 through sales.2024-06
```

---

## 🔍 PHASE 2: QUERY VALIDATION (Days 4-5)

### Day 4: Time Classifier

#### Implement Time Classifier
- [ ] Create `query/time_classifier.py`:

```python
import re

def classify_time_sensitivity(query: str) -> dict:
    """Classify if query is time-sensitive"""
    q_lower = query.lower()
    
    # Static queries (policies, procedures)
    static_keywords = ["policy", "sop", "procedure", "guideline", "refund"]
    if any(k in q_lower for k in static_keywords):
        return {
            "is_time_sensitive": False,
            "explicit_timeframe": None,
            "needs_clarification": False,
            "data_type": "policy"
        }
    
    # Dynamic queries (KPIs, metrics)
    dynamic_keywords = ["top", "revenue", "sales", "compare", "highest"]
    if any(k in q_lower for k in dynamic_keywords):
        # Check for explicit timeframe
        timeframe = extract_explicit_timeframe(query)
        
        return {
            "is_time_sensitive": True,
            "explicit_timeframe": timeframe,
            "needs_clarification": (timeframe is None),
            "data_type": "sales"
        }
    
    # Default: not time-sensitive
    return {
        "is_time_sensitive": False,
        "explicit_timeframe": None,
        "needs_clarification": False,
        "data_type": "general"
    }

def extract_explicit_timeframe(query: str) -> str:
    """Extract yyyy-mm from query"""
    match = re.search(r'\b(20\d{2})[-/](0?[1-9]|1[0-2])\b', query)
    if match:
        year, month = match.groups()
        return f"{year}-{int(month):02d}"
    
    # Check for month names
    months = {
        "january": 1, "jan": 1,
        "february": 2, "feb": 2,
        "march": 3, "mar": 3,
        "april": 4, "apr": 4,
        "may": 5,
        "june": 6, "jun": 6,
        "july": 7, "jul": 7,
        "august": 8, "aug": 8,
        "september": 9, "sep": 9,
        "october": 10, "oct": 10,
        "november": 11, "nov": 11,
        "december": 12, "dec": 12
    }
    
    q_lower = query.lower()
    for month_name, month_num in months.items():
        if month_name in q_lower:
            # Look for year
            year_match = re.search(r'\b(20\d{2})\b', q_lower)
            if year_match:
                year = year_match.group(1)
                return f"{year}-{month_num:02d}"
    
    return None
```

- [ ] Test with static queries ("What's the policy?")
- [ ] Test with dynamic queries ("Top products")
- [ ] Test with explicit timeframe ("Top products in June 2024")

**Verification**:
```python
from query.time_classifier import classify_time_sensitivity

# Test 1: Static
result = classify_time_sensitivity("What's the refund policy?")
assert result["is_time_sensitive"] == False

# Test 2: Dynamic without timeframe
result = classify_time_sensitivity("Top 5 products")
assert result["is_time_sensitive"] == True
assert result["needs_clarification"] == True

# Test 3: Dynamic with timeframe
result = classify_time_sensitivity("Top 5 products in June 2024")
assert result["is_time_sensitive"] == True
assert result["needs_clarification"] == False
assert result["explicit_timeframe"] == "2024-06"

print("✅ All tests passed")
```

---

### Day 5: Integration with answer_sales_ceo_kpi()

#### Backup Current Code
```bash
cp Code/oneclick_my_retailchain_v8.2_models_logging.py Code/oneclick_my_retailchain_v8.2_models_logging.py.backup
```

- [ ] Create backup of v8.2 file

#### Modify answer_sales_ceo_kpi()

**Current code** (around line 2000):
```python
def answer_sales_ceo_kpi(q: str, trace=None):
    month = extract_month_from_query(q)
    sub = df_sales[df_sales["YearMonth"] == month].copy()
    
    if sub.empty:
        return f"❗ Tiada rekod untuk {month}"
    # ... rest of logic
```

**New code**:
```python
def answer_sales_ceo_kpi(q: str, trace=None):
    from query.time_classifier import classify_time_sensitivity
    from query.validator import validate_data_availability
    from core.data_loader import get_data_loader
    
    # 1. Classify query
    classification = classify_time_sensitivity(q)
    
    # 2. If needs clarification, return prompt
    if classification["needs_clarification"]:
        from query.validator import DataAvailabilityValidator
        validator = DataAvailabilityValidator()
        return validator.get_clarification_prompt("sales")
    
    # 3. Extract timeframe
    month = classification["explicit_timeframe"]
    if not month:
        # Try previous context or fallback to extract_month_from_query
        month = extract_month_from_query(q, 
                    previous_context=CONVERSATION_STATE.get('last_context'))
    
    # 4. Validate availability
    validation = validate_data_availability(str(month), "sales")
    if not validation["available"]:
        return validation["message"]
    
    # 5. Load data on-demand
    loader = get_data_loader()
    df = loader.load_sales_month(str(month))
    
    if df is None or df.empty:
        return f"❗ Error loading data for {month}"
    
    # 6. Continue with existing logic (filters, aggregation, etc.)
    sub = df.copy()
    
    # ... rest of existing code unchanged ...
```

- [ ] Locate `answer_sales_ceo_kpi()` function
- [ ] Add imports at top
- [ ] Add classification step
- [ ] Add clarification check
- [ ] Add validation step
- [ ] Replace `df_sales` with `loader.load_sales_month()`
- [ ] Test with sample queries

**Verification**:
```python
# Test 1: Available month with explicit timeframe
result = answer_sales_ceo_kpi("Top 5 products in June 2024")
assert "Beef Burger" in result  # Should execute normally

# Test 2: Unavailable month
result = answer_sales_ceo_kpi("Top 5 products in December 2024")
assert "not yet available" in result  # Should fail closed

# Test 3: No timeframe
result = answer_sales_ceo_kpi("Top 5 products")
assert "Which month" in result  # Should ask clarification

print("✅ Integration working")
```

---

## 🤖 PHASE 3: AUTO-INGESTION (Days 6-7)

### Day 6: File Watcher

#### Install Dependencies
```bash
pip install watchdog
```

- [ ] Install watchdog library
- [ ] Verify installation: `python -c "import watchdog; print('OK')"`

#### Implement Watcher
- [ ] Create `core/data_watcher.py`
- [ ] Copy code from PRODUCTION_ARCHITECTURE_DESIGN.md (Section 9, Step 4)
- [ ] Test with manual file drop

**Manual Test**:
```python
# Terminal 1: Start watcher
from core.data_watcher import start_watcher
start_watcher("data/sales")

# Terminal 2: Drop test file
# (Create a dummy 2024-07 CSV)
# Wait for watcher to detect and process
```

- [ ] Verify watcher detects new file
- [ ] Verify catalog updated
- [ ] Verify cache invalidated

---

### Day 7: FAISS Incremental Update

#### Update FAISS Builder
- [ ] Locate FAISS index building code (around line 1670)
- [ ] Add function to incrementally add new month

```python
def update_faiss_index_for_new_month(year_month: str):
    """Add new month data to existing FAISS index"""
    from core.data_loader import get_data_loader
    global index, summaries
    
    # Load new month
    loader = get_data_loader()
    new_df = loader.load_sales_month(year_month)
    
    if new_df is None:
        print(f"⚠️ No data for {year_month}")
        return
    
    # Generate summaries
    new_summaries = []
    for _, row in new_df.iterrows():
        summary = (
            f"[SALES] Date={row.get('DateStr','')}; "
            f"State={row.get('State','')}; "
            f"Product={row.get('Product','')}; "
            f"TotalSale={row.get('Total Sale','')}"
        )
        new_summaries.append(summary)
    
    # Encode
    embeddings = embedder.encode(new_summaries, convert_to_numpy=True)
    faiss.normalize_L2(embeddings)
    
    # Add to index
    index.add(embeddings)
    summaries.extend(new_summaries)
    
    # Save
    CACHE_DIR = "storage/cache"
    faiss.write_index(index, f"{CACHE_DIR}/faiss_index.bin")
    with open(f"{CACHE_DIR}/summaries.pkl", "wb") as f:
        pickle.dump(summaries, f)
    
    print(f"✅ FAISS updated: +{len(new_summaries)} entries for {year_month}")
```

- [ ] Add incremental update function
- [ ] Call from watcher after registration
- [ ] Test with new file drop

**Verification**:
```python
# Drop new file
# Wait for auto-ingestion
# Query should work immediately
result = answer_sales_ceo_kpi("Top products in July 2024")
assert "Beef Burger" in result or "Top" in result
print("✅ Auto-ingestion working")
```

---

## 🧪 PHASE 4: TESTING & DEPLOYMENT (Days 8-10)

### Day 8: Unit Testing

#### Create Test File
- [ ] Create `tests/test_production_pipeline.py`
- [ ] Copy code from PRODUCTION_TEST_CASES.md (Part 12)
- [ ] Run tests: `pytest tests/test_production_pipeline.py -v`

**Expected Output**:
```
tests/test_production_pipeline.py::TestDataCatalog::test_catalog_initialization PASSED
tests/test_production_pipeline.py::TestDataCatalog::test_register_sales_data PASSED
tests/test_production_pipeline.py::TestDataLoader::test_load_available_month PASSED
tests/test_production_pipeline.py::TestAvailabilityValidator::test_validate_available PASSED
...
==================== 15 passed in 5.2s ====================
```

- [ ] All tests pass
- [ ] Fix any failures
- [ ] Achieve 100% pass rate

---

### Day 9: Integration Testing

#### End-to-End Test Cases
- [ ] Test Case 1: Valid query with available data
  ```python
  query = "Top 5 products in June 2024"
  result = answer_sales_ceo_kpi(query)
  assert "Beef Burger" in result
  ```

- [ ] Test Case 2: Query for unavailable data
  ```python
  query = "Top 5 products in December 2024"
  result = answer_sales_ceo_kpi(query)
  assert "not yet available" in result
  ```

- [ ] Test Case 3: Query without timeframe
  ```python
  query = "Top 5 products"
  result = answer_sales_ceo_kpi(query)
  assert "Which month" in result
  ```

- [ ] Test Case 4: Context inheritance
  ```python
  # First query
  CONVERSATION_STATE['last_context'] = {'month': '2024-06'}
  # Follow-up query
  query = "Break down by state"
  result = answer_sales_ceo_kpi(query)
  assert "2024-06" in result or "June" in result
  ```

- [ ] Test Case 5: Auto-ingestion
  ```python
  # Create dummy July data
  # Drop in data/sales/
  # Wait 10 seconds
  query = "Top products in July 2024"
  result = answer_sales_ceo_kpi(query)
  assert "not yet available" not in result
  ```

---

### Day 10: Documentation & Deployment

#### Update Documentation
- [ ] Update main README.md with new architecture
- [ ] Create operator guide for adding new data
- [ ] Document troubleshooting steps
- [ ] Add examples of follow-up prompts

#### Deployment Checklist
- [ ] All tests passing
- [ ] No errors in logs
- [ ] Catalog contains all expected months
- [ ] FAISS index built successfully
- [ ] Cache directory exists and populated
- [ ] File watcher starts correctly

#### Production Deployment
- [ ] Create production data directory structure
- [ ] Copy monthly CSV files
- [ ] Initialize catalog in production
- [ ] Start application with watcher
- [ ] Monitor logs for first hour
- [ ] Test with real user queries

#### Monitoring Setup
- [ ] Log all data ingestion events
- [ ] Monitor catalog updates
- [ ] Track query validation failures
- [ ] Alert if data >30 days stale
- [ ] Dashboard for data freshness

---

## ✅ POST-DEPLOYMENT VALIDATION

### Week 1 Checks
- [ ] Day 1: Verify all existing queries still work
- [ ] Day 2: Test with user feedback
- [ ] Day 3: Drop test file for new month
- [ ] Day 4: Verify auto-ingestion working
- [ ] Day 5: Review logs for any errors

### Month 1 Checks
- [ ] New month data arrives automatically
- [ ] Catalog updates without manual intervention
- [ ] Queries for new month work immediately
- [ ] No code changes required
- [ ] Performance metrics within acceptable range

---

## 📊 SUCCESS CRITERIA

### Technical Metrics
- [ ] Test coverage: 100% of core modules
- [ ] Auto-ingestion time: <5 minutes for 5K rows
- [ ] Cache hit rate: >80%
- [ ] Query response time: <2 seconds
- [ ] Zero code changes for new data

### User Experience Metrics
- [ ] Clarification prompts shown when needed
- [ ] Error messages are helpful (not technical)
- [ ] Follow-up suggestions are relevant
- [ ] No hallucinations (fails closed when data missing)
- [ ] Context inheritance works across conversation

### Operational Metrics
- [ ] Data freshness: Latest month within 1 day of calendar
- [ ] Uptime: 99.9%
- [ ] Failed ingestions: <1%
- [ ] Manual interventions: 0 per month

---

## 🆘 TROUBLESHOOTING

### Issue: Catalog not updating
**Symptoms**: New file dropped but queries still fail  
**Check**:
- [ ] File watcher running? `ps aux | grep watcher`
- [ ] Correct filename format? `MY_Retail_Sales_YYYY_MM.csv`
- [ ] File in correct directory? `data/sales/`
- [ ] Schema valid? Check logs for validation errors

**Fix**: Manually register:
```python
from core.data_catalog import get_data_catalog
catalog = get_data_catalog()
catalog.register_sales_data("2024-07", "data/sales/file.csv", df)
```

---

### Issue: Cache not invalidating
**Symptoms**: Old data returned after new file added  
**Fix**:
```python
from core.data_loader import get_data_loader
loader = get_data_loader()
loader.invalidate_cache()  # Clear all
# or
loader.invalidate_cache("2024-07")  # Clear specific month
```

---

### Issue: FAISS index out of sync
**Symptoms**: RAG returns stale documents  
**Fix**: Rebuild index
```python
# Delete cache
rm storage/cache/faiss_index.bin
rm storage/cache/summaries.pkl

# Restart application (will rebuild)
```

---

## 📞 SUPPORT CONTACTS

**Development Team**: [Your team contact]  
**Data Operations**: [Data team contact]  
**Production Support**: [Support team contact]

---

## 🎉 COMPLETION CHECKLIST

- [ ] All 4 phases completed
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Production deployed
- [ ] Monitoring active
- [ ] Team trained on new system

**When all checked**: ✅ **PRODUCTION READY**

---

**Last Updated**: January 14, 2026  
**Version**: v9 Production  
**Status**: Ready for implementation
