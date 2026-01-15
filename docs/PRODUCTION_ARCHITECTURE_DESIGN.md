# Production Architecture Design
## Dynamic Data Pipeline Implementation

**Continuation of**: PRODUCTION_ARCHITECTURE_ANALYSIS.md  
**Date**: January 14, 2026

---

## PART 7: SYSTEM ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────────────┐
│                      PRODUCTION ARCHITECTURE                     │
└─────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│                          DATA INGESTION LAYER                           │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐      ┌──────────────────┐      ┌──────────────┐     │
│  │   WATCHER   │─────▶│  DATA VALIDATOR  │─────▶│   INDEXER    │     │
│  │  (File Mon.)│      │  (Schema Check)  │      │ (FAISS Build)│     │
│  └─────────────┘      └──────────────────┘      └──────────────┘     │
│        │                       │                        │              │
│        │ Detects new CSVs      │ Validates schema       │ Rebuilds     │
│        ▼                       ▼                        ▼              │
│  data/sales/*.csv       data_catalog.json        cache/faiss_*.bin   │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        DATA MANAGEMENT LAYER                            │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐         ┌──────────────────────┐                 │
│  │  DATA CATALOG   │◀───────▶│   DATA LOADER        │                 │
│  │  (Metadata)     │         │   (Smart Cache)      │                 │
│  └─────────────────┘         └──────────────────────┘                 │
│          │                              │                              │
│          │ Tracks available data        │ Loads on-demand              │
│          ▼                              ▼                              │
│    {                              df_sales[month]                      │
│      "2024-07": {                 Cached in memory                     │
│        "status": "validated",     TTL: 1 hour                          │
│        "rows": 5100               Invalidate on new data               │
│      }                                                                  │
│    }                                                                    │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      QUERY PROCESSING LAYER                             │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────┐      ┌─────────────────────┐                    │
│  │  QUERY PARSER    │─────▶│  TIME VALIDATOR     │                    │
│  │  (Intent + Time) │      │  (Check Avail.)     │                    │
│  └──────────────────┘      └─────────────────────┘                    │
│          │                            │                                │
│          │                            ├─ Available? ──▶ Execute        │
│          │                            │                                │
│          │                            └─ Missing? ─────▶ Clarify       │
│          ▼                                         │                   │
│    "Top products                            ┌─────▼────────┐           │
│     in July 2024"                           │   FOLLOWUP   │           │
│          │                                  │   GENERATOR  │           │
│          │                                  └──────────────┘           │
│          │                                         │                   │
│          ▼                                         ▼                   │
│    {                                        "Which month?"             │
│      "is_time_sensitive": true,            [Jan] [Feb] ... [Jun]      │
│      "timeframe": "2024-07",                                           │
│      "needs_clarification": false                                      │
│    }                                                                    │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         EXECUTION LAYER                                 │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌────────────────────┐         ┌──────────────────┐                  │
│  │   KPI EXECUTOR     │         │   RAG EXECUTOR   │                  │
│  │   (Deterministic)  │         │   (LLM-based)    │                  │
│  └────────────────────┘         └──────────────────┘                  │
│          │                                │                            │
│          │ For sales/HR metrics           │ For policies/docs          │
│          ▼                                ▼                            │
│    Load df[month]                   FAISS search                       │
│    Apply filters                    Retrieve docs                      │
│    Aggregate                        LLM generation                     │
│    Format answer                                                       │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        VERIFICATION LAYER                               │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────┐       ┌────────────────────┐                │
│  │  GROUND TRUTH CHECK  │       │  SEMANTIC CHECK    │                │
│  │  (Number accuracy)   │       │  (Format match)    │                │
│  └──────────────────────┘       └────────────────────┘                │
│                                                                         │
│  If KPI answer differs from ground truth by >5%:                       │
│    → Flag as potential hallucination                                   │
│    → Show correction notice                                            │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                            ┌──────────────┐
                            │  USER ANSWER │
                            └──────────────┘
```

---

## PART 8: MODULE DESIGN

### 8.1 Module Structure

```
Code/
├── core/
│   ├── __init__.py
│   ├── data_catalog.py        # Metadata management
│   ├── data_loader.py         # Smart data loading with cache
│   ├── data_watcher.py        # File monitoring for auto-ingestion
│   └── data_validator.py      # Schema validation
│
├── query/
│   ├── __init__.py
│   ├── parser.py              # Query parsing and intent detection
│   ├── time_classifier.py     # Time-sensitivity detection
│   ├── validator.py           # Data availability validation
│   └── followup_generator.py  # Generate clarification questions
│
├── execution/
│   ├── __init__.py
│   ├── kpi_executor.py        # Deterministic KPI execution
│   ├── rag_executor.py        # RAG-based document retrieval
│   └── verification.py        # Answer verification
│
├── indexing/
│   ├── __init__.py
│   ├── faiss_builder.py       # FAISS index construction
│   └── cache_manager.py       # Cache invalidation logic
│
└── oneclick_my_retailchain_v9_production.py  # Main orchestrator
```

---

### 8.2 Core Module: data_catalog.py

```python
"""
Data Catalog Management
Tracks available data, metadata, and freshness
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd

class DataCatalog:
    """
    Manages metadata about available datasets
    """
    
    def __init__(self, catalog_path: str = "data/metadata/data_catalog.json"):
        self.catalog_path = catalog_path
        self.catalog = self._load_catalog()
    
    def _load_catalog(self) -> Dict:
        """Load catalog from disk or create new"""
        if os.path.exists(self.catalog_path):
            with open(self.catalog_path, 'r') as f:
                return json.load(f)
        return {"sales": {}, "hr": {}, "latest": {}}
    
    def _save_catalog(self):
        """Persist catalog to disk"""
        os.makedirs(os.path.dirname(self.catalog_path), exist_ok=True)
        with open(self.catalog_path, 'w') as f:
            json.dump(self.catalog, f, indent=2, default=str)
    
    def register_sales_data(self, year_month: str, file_path: str, 
                           df: pd.DataFrame) -> bool:
        """
        Register new sales data in catalog
        
        Args:
            year_month: "2024-07"
            file_path: Path to CSV file
            df: DataFrame to extract metadata from
        
        Returns:
            True if successfully registered
        """
        metadata = {
            "file": file_path,
            "rows": len(df),
            "date_range": [
                df["Date"].min().strftime("%Y-%m-%d"),
                df["Date"].max().strftime("%Y-%m-%d")
            ],
            "states": sorted(df["State"].unique().tolist()),
            "products": sorted(df["Product"].unique().tolist()),
            "branches": sorted(df["Branch"].unique().tolist()),
            "total_revenue": float(df["Total Sale"].sum()),
            "total_transactions": len(df),
            "ingestion_date": datetime.now().isoformat(),
            "status": "validated"
        }
        
        self.catalog["sales"][year_month] = metadata
        self.catalog["latest"]["sales"] = year_month
        self._save_catalog()
        
        print(f"✅ Registered sales data for {year_month}")
        print(f"   Rows: {metadata['rows']:,}")
        print(f"   Revenue: RM {metadata['total_revenue']:,.2f}")
        
        return True
    
    def is_available(self, year_month: str, data_type: str = "sales") -> bool:
        """Check if data for specific period is available"""
        return year_month in self.catalog.get(data_type, {})
    
    def get_available_months(self, data_type: str = "sales") -> List[str]:
        """Get list of all available months"""
        return sorted(self.catalog.get(data_type, {}).keys())
    
    def get_latest_month(self, data_type: str = "sales") -> Optional[str]:
        """Get latest available month"""
        return self.catalog.get("latest", {}).get(data_type)
    
    def get_metadata(self, year_month: str, data_type: str = "sales") -> Optional[Dict]:
        """Get metadata for specific period"""
        return self.catalog.get(data_type, {}).get(year_month)
    
    def get_date_range_info(self, data_type: str = "sales") -> Dict:
        """Get summary of available date range"""
        months = self.get_available_months(data_type)
        if not months:
            return {"available": False}
        
        return {
            "available": True,
            "start": months[0],
            "end": months[-1],
            "count": len(months),
            "months": months
        }


# Global singleton instance
_catalog = None

def get_data_catalog() -> DataCatalog:
    """Get or create global catalog instance"""
    global _catalog
    if _catalog is None:
        _catalog = DataCatalog()
    return _catalog
```

---

### 8.3 Core Module: data_loader.py

```python
"""
Smart Data Loader with Caching
Loads data on-demand with memory and disk caching
"""

import os
import pandas as pd
from typing import Optional, Dict
from datetime import datetime, timedelta
from core.data_catalog import get_data_catalog

class DataLoader:
    """
    Manages data loading with intelligent caching
    """
    
    def __init__(self, cache_ttl_minutes: int = 60):
        self.catalog = get_data_catalog()
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        
        # In-memory cache
        self._sales_cache: Dict[str, Dict] = {}
        # Structure: {"2024-07": {"df": DataFrame, "loaded_at": datetime}}
    
    def load_sales_month(self, year_month: str, 
                        force_reload: bool = False) -> Optional[pd.DataFrame]:
        """
        Load sales data for specific month
        
        Args:
            year_month: "2024-07"
            force_reload: Bypass cache
        
        Returns:
            DataFrame or None if not available
        """
        # Check availability first
        if not self.catalog.is_available(year_month, "sales"):
            print(f"❌ Data for {year_month} not available")
            return None
        
        # Check cache
        if not force_reload and year_month in self._sales_cache:
            cached = self._sales_cache[year_month]
            age = datetime.now() - cached["loaded_at"]
            
            if age < self.cache_ttl:
                print(f"📦 Using cached data for {year_month} (age: {age.seconds}s)")
                return cached["df"]
        
        # Load from disk
        metadata = self.catalog.get_metadata(year_month, "sales")
        file_path = metadata["file"]
        
        print(f"📂 Loading {year_month} from disk: {file_path}")
        df = pd.read_csv(file_path)
        
        # Normalize
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["YearMonth"] = df["Date"].dt.to_period("M")
        
        for col in ["Quantity", "Unit Price", "Total Sale"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        
        # Cache it
        self._sales_cache[year_month] = {
            "df": df,
            "loaded_at": datetime.now()
        }
        
        print(f"✅ Loaded {len(df):,} rows for {year_month}")
        return df
    
    def load_all_sales(self) -> pd.DataFrame:
        """Load all available sales data (combined)"""
        all_months = self.catalog.get_available_months("sales")
        
        dfs = []
        for month in all_months:
            df = self.load_sales_month(month)
            if df is not None:
                dfs.append(df)
        
        if not dfs:
            return pd.DataFrame()
        
        combined = pd.concat(dfs, ignore_index=True)
        print(f"📊 Combined sales data: {len(combined):,} rows across {len(all_months)} months")
        return combined
    
    def invalidate_cache(self, year_month: Optional[str] = None):
        """
        Invalidate cache
        
        Args:
            year_month: Specific month to invalidate, or None for all
        """
        if year_month:
            if year_month in self._sales_cache:
                del self._sales_cache[year_month]
                print(f"🗑️ Cache invalidated for {year_month}")
        else:
            self._sales_cache.clear()
            print("🗑️ All cache cleared")


# Global singleton
_loader = None

def get_data_loader() -> DataLoader:
    """Get or create global loader instance"""
    global _loader
    if _loader is None:
        _loader = DataLoader()
    return _loader
```

---

### 8.4 Query Module: validator.py

```python
"""
Data Availability Validation
Checks if requested data exists before execution
"""

from typing import Dict, Optional
from core.data_catalog import get_data_catalog

class DataAvailabilityValidator:
    """
    Validates data availability and generates helpful error messages
    """
    
    def __init__(self):
        self.catalog = get_data_catalog()
    
    def validate(self, year_month: str, data_type: str = "sales") -> Dict:
        """
        Validate data availability
        
        Returns:
            {
                "available": bool,
                "message": str | None,
                "alternatives": list[str],
                "suggestion": str | None
            }
        """
        if self.catalog.is_available(year_month, data_type):
            return {
                "available": True,
                "message": None,
                "alternatives": [],
                "suggestion": None
            }
        
        # Data not available - generate helpful message
        date_range = self.catalog.get_date_range_info(data_type)
        
        if not date_range["available"]:
            return {
                "available": False,
                "message": f"❌ No {data_type} data available in the system.",
                "alternatives": [],
                "suggestion": "Please contact data team to ingest data."
            }
        
        latest = self.catalog.get_latest_month(data_type)
        
        message = f"❌ Data for **{year_month}** is not yet available.\n\n"
        message += f"**Available period**: {date_range['start']} to {date_range['end']}\n"
        message += f"**Latest data**: {latest}\n"
        message += f"**Total months available**: {date_range['count']}"
        
        return {
            "available": False,
            "message": message,
            "alternatives": date_range["months"],
            "suggestion": f"Would you like to see results for **{latest}** instead?"
        }
    
    def get_clarification_prompt(self, data_type: str = "sales") -> str:
        """
        Generate clarification prompt when no timeframe specified
        """
        latest = self.catalog.get_latest_month(data_type)
        months = self.catalog.get_available_months(data_type)
        
        prompt = "📅 **Which month would you like to analyze?**\n\n"
        prompt += f"Available data: {months[0]} to {months[-1]}\n"
        prompt += f"Latest: **{latest}**\n\n"
        prompt += "Please specify a month or select from:\n"
        
        # Show last 6 months as buttons
        recent = months[-6:] if len(months) > 6 else months
        for m in recent:
            label = f"{m} (Latest)" if m == latest else m
            prompt += f"- {label}\n"
        
        return prompt


def validate_data_availability(year_month: str, 
                               data_type: str = "sales") -> Dict:
    """Convenience function for validation"""
    validator = DataAvailabilityValidator()
    return validator.validate(year_month, data_type)
```

---

## PART 9: IMPLEMENTATION PLAN

### Step 1: Prepare Data Structure (Day 1)

**Actions**:
1. Create directory structure:
   ```
   data/
   ├── sales/
   │   ├── MY_Retail_Sales_2024_01.csv
   │   ├── MY_Retail_Sales_2024_02.csv
   │   └── ...
   ├── hr/
   │   └── MY_Retail_HR_2024_Q2.csv
   └── metadata/
       ├── data_catalog.json
       └── document_catalog.json
   ```

2. Split existing `MY_Retail_Sales_2024H1.csv` into monthly files:
   ```python
   # Split script
   df = pd.read_csv("data/MY_Retail_Sales_2024H1.csv")
   df["Date"] = pd.to_datetime(df["Date"])
   df["YearMonth"] = df["Date"].dt.to_period("M")
   
   for month in df["YearMonth"].unique():
       month_df = df[df["YearMonth"] == month]
       filename = f"data/sales/MY_Retail_Sales_{month}.csv"
       month_df.to_csv(filename, index=False)
       print(f"Created: {filename} ({len(month_df)} rows)")
   ```

3. Initialize catalog:
   ```python
   from core.data_catalog import DataCatalog
   
   catalog = DataCatalog()
   
   # Register each month
   for file in glob.glob("data/sales/*.csv"):
       df = pd.read_csv(file)
       month = extract_month_from_filename(file)  # "2024-01"
       catalog.register_sales_data(month, file, df)
   ```

**Result**: Data organized by month, catalog initialized

---

### Step 2: Implement Core Modules (Day 2-3)

**Priority Order**:
1. ✅ `data_catalog.py` - Metadata management
2. ✅ `data_loader.py` - Smart loading with cache
3. ✅ `validator.py` - Data availability checks
4. ✅ `followup_generator.py` - Clarification prompts

**Testing**:
```python
# Test catalog
catalog = get_data_catalog()
assert catalog.is_available("2024-06", "sales") == True
assert catalog.is_available("2024-07", "sales") == False

# Test loader
loader = get_data_loader()
df = loader.load_sales_month("2024-06")
assert len(df) > 0

# Test validator
result = validate_data_availability("2024-07", "sales")
assert result["available"] == False
assert "2024-06" in result["suggestion"]
```

**Result**: Core infrastructure working

---

### Step 3: Integrate with Query Processing (Day 4-5)

**Modify**: `oneclick_my_retailchain_v8.2_models_logging.py`

**Changes**:

```python
# BEFORE (v8.2)
def answer_sales_ceo_kpi(q: str, trace=None):
    month = extract_month_from_query(q)
    sub = df_sales[df_sales["YearMonth"] == month].copy()
    
    if sub.empty:
        return f"❗ Tiada rekod untuk {month}"
    # ...

# AFTER (v9 Production)
def answer_sales_ceo_kpi(q: str, trace=None):
    # 1. Check if time-sensitive
    classification = classify_time_sensitivity(q)
    
    # 2. If needs clarification, generate follow-up
    if classification["needs_clarification"]:
        return generate_clarification_prompt(q, classification)
    
    # 3. Extract timeframe
    month = classification["explicit_timeframe"] or extract_month_from_query(q)
    
    # 4. Validate availability
    validation = validate_data_availability(month, "sales")
    if not validation["available"]:
        return validation["message"]
    
    # 5. Load data on-demand
    loader = get_data_loader()
    df = loader.load_sales_month(month)
    
    # 6. Execute query (existing logic)
    sub = df.copy()
    # ... filter and aggregate ...
    
    return answer
```

**Result**: Queries now check availability before execution

---

### Step 4: Implement Data Watcher (Day 6)

**Purpose**: Auto-detect new CSV files and ingest them

```python
"""
data_watcher.py
Monitors data directory for new files
"""

import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class DataFileHandler(FileSystemEventHandler):
    """Handle new CSV file events"""
    
    def on_created(self, event):
        if event.is_directory:
            return
        
        if event.src_path.endswith('.csv'):
            print(f"📥 New file detected: {event.src_path}")
            self.process_new_file(event.src_path)
    
    def process_new_file(self, file_path: str):
        """Process and register new sales data"""
        # Extract month from filename
        # Example: MY_Retail_Sales_2024_07.csv → "2024-07"
        basename = os.path.basename(file_path)
        match = re.search(r'(\d{4})_(\d{2})', basename)
        
        if not match:
            print(f"⚠️ Couldn't parse month from: {basename}")
            return
        
        year, month = match.groups()
        year_month = f"{year}-{month}"
        
        # Validate and register
        try:
            df = pd.read_csv(file_path)
            
            # Validate schema
            required_cols = ["Date", "State", "Product", "Total Sale"]
            if not all(col in df.columns for col in required_cols):
                print(f"❌ Invalid schema in {basename}")
                return
            
            # Register in catalog
            catalog = get_data_catalog()
            catalog.register_sales_data(year_month, file_path, df)
            
            # Invalidate FAISS cache
            # TODO: Trigger FAISS rebuild
            
            print(f"✅ Successfully ingested {year_month}")
            
        except Exception as e:
            print(f"❌ Error processing {basename}: {e}")


def start_watcher(watch_dir: str = "data/sales"):
    """Start monitoring directory"""
    event_handler = DataFileHandler()
    observer = Observer()
    observer.schedule(event_handler, watch_dir, recursive=False)
    observer.start()
    
    print(f"👀 Watching {watch_dir} for new data files...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()
```

**Usage**:
```python
# In production, run in background thread
import threading

watcher_thread = threading.Thread(
    target=start_watcher, 
    args=("data/sales",),
    daemon=True
)
watcher_thread.start()
```

**Result**: New CSV files automatically detected and registered

---

### Step 5: Update FAISS Indexing (Day 7)

**Goal**: Rebuild FAISS index when new data arrives

**Changes to indexing**:

```python
def build_faiss_index_incremental(new_month: str):
    """
    Add new month to existing FAISS index
    """
    # Load new data
    loader = get_data_loader()
    new_df = loader.load_sales_month(new_month)
    
    # Generate summaries for new data
    new_summaries = []
    for _, row in new_df.iterrows():
        summary = f"[SALES] Date={row['DateStr']}; State={row['State']}; ..."
        new_summaries.append(summary)
    
    # Encode new summaries
    embeddings = embedder.encode(new_summaries, convert_to_numpy=True)
    faiss.normalize_L2(embeddings)
    
    # Add to existing index
    global index, summaries
    index.add(embeddings)
    summaries.extend(new_summaries)
    
    # Save updated index
    faiss.write_index(index, "storage/cache/faiss_index.bin")
    with open("storage/cache/summaries.pkl", "wb") as f:
        pickle.dump(summaries, f)
    
    print(f"✅ FAISS index updated with {len(new_summaries)} new entries")
```

**Result**: FAISS index stays synchronized with data

---

## ANALYSIS COMPLETE - CHUNK 2

**Status**: ✅ COMPLETED
- Architecture diagram provided (text-based)
- Module structure defined (data_catalog, data_loader, validator)
- Implementation plan outlined (7 days, 5 steps)
- Code examples provided for key modules

**Next Chunk**: Test cases and follow-up templates

