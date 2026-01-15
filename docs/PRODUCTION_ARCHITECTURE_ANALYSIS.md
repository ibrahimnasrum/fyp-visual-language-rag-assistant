# Production Architecture Analysis & Design
## Dynamic Data Pipeline for CEO Chatbot

**Date**: January 14, 2026  
**Purpose**: Design auto-updating system that handles new data without code changes  
**Current Version**: v8.2

---

## PART 1: CURRENT SYSTEM ANALYSIS

### 1.1 Current Data Loading Architecture

**Location**: Lines 1574-1615 in `oneclick_my_retailchain_v8.2_models_logging.py`

```python
# CURRENT APPROACH (STATIC)
SALES_CSV = os.path.join(DATA_DIR, "MY_Retail_Sales_2024H1.csv")
df_sales = pd.read_csv(SALES_CSV)
df_sales["YearMonth"] = df_sales["Date"].dt.to_period("M")

AVAILABLE_SALES_MONTHS = sorted(df_sales["YearMonth"].dropna().unique().tolist())
LATEST_SALES_MONTH = max(AVAILABLE_SALES_MONTHS) if AVAILABLE_SALES_MONTHS else None

# Metadata extracted at startup
STATES = sorted(df_sales["State"].dropna().unique().tolist())
PRODUCTS = sorted(df_sales["Product"].dropna().unique().tolist())
```

**Problems**:
- ❌ Hardcoded filename (`2024H1.csv`)
- ❌ Data loaded once at startup - never refreshed
- ❌ Adding July 2024 data requires code change + restart
- ❌ AVAILABLE_SALES_MONTHS becomes stale
- ❌ FAISS index cached but never invalidated

---

### 1.2 Current Query Processing

**Month Extraction** (Line 1776):
```python
def extract_month_from_query(q: str, previous_context: dict = None):
    # Checks: "bulan ini", "last month", yyyy-mm, text months
    # Fallback: LATEST_SALES_MONTH (stale!)
    return LATEST_SALES_MONTH
```

**Filter Extraction** (Line 1860):
```python
def extract_sales_filters(q: str, previous_filters: dict = None):
    # Extracts: State, Branch, Product, Employee, Channel
    # Smart inheritance with dimension-switch detection
```

**Query Execution** (Line 2000+):
```python
def answer_sales_ceo_kpi(q: str, trace=None):
    month = extract_month_from_query(q)
    sub = df_sales[df_sales["YearMonth"] == month].copy()
    
    if sub.empty:
        return f"❗ Tiada rekod untuk {month}"
    # ... process and return answer
```

**Problems**:
- ❌ No validation: "Show me sales for July 2024" → fails silently if July doesn't exist
- ❌ No proactive clarification: "Top products" → assumes LATEST_SALES_MONTH
- ❌ Empty result gives generic error, doesn't explain what data IS available

---

### 1.3 Current FAISS Caching

**Location**: Lines 1670-1693

```python
CACHE_DIR = os.path.join(STORAGE_DIR, "cache")
index_cache_path = os.path.join(CACHE_DIR, "faiss_index.bin")
summaries_cache_path = os.path.join(CACHE_DIR, "summaries.pkl")

if os.path.exists(index_cache_path):
    index = faiss.read_index(index_cache_path)
    with open(summaries_cache_path, "rb") as f:
        summaries = pickle.load(f)
else:
    # Build index from scratch
    # ... encode and save
```

**Problems**:
- ❌ No cache invalidation mechanism
- ❌ Adding new data requires manual cache deletion
- ❌ No timestamp tracking for data freshness

---

### 1.4 Current Conversation State

**Location**: Line 453

```python
CONVERSATION_STATE = {
    'last_filters': {...},
    'last_context': {'month': '2024-06', 'top_performer': 'Beef Burger'}
}
```

**Strengths**:
- ✅ Tracks filters across conversation
- ✅ Smart inheritance (dimension-switch detection)
- ✅ Month context preservation

**Problems**:
- ❌ No data availability check before inheriting month
- ❌ If user asks about July (not yet available), silently fails

---

## PART 2: STATIC vs DYNAMIC CLASSIFICATION

### 2.1 STATIC (Evergreen) Data

**Definition**: Data that doesn't change or changes rarely

| Category | Examples | Update Frequency | Storage |
|----------|----------|------------------|---------|
| **Company Policies** | HR Policy, SOP documents | Yearly | `docs/*.txt` files |
| **Product Catalog** | List of products sold | Quarterly | Could be extracted from sales data |
| **Store Locations** | States, Cities, Branches | Yearly | Metadata table or config |
| **Employee Roles** | Job titles, departments | Monthly | HR CSV |
| **Operational Procedures** | Refund policy, guidelines | Yearly | Document RAG |

**Characteristics**:
- Can be cached indefinitely (until explicit update)
- Questions like "What's the refund policy?" → Always same answer
- No timeframe context needed

---

### 2.2 DYNAMIC (Time-Sensitive) Data

**Definition**: Data that changes regularly and requires timeframe context

| Category | Examples | Update Frequency | Timeframe Required |
|----------|----------|------------------|-------------------|
| **Sales KPIs** | Revenue, quantity sold | Daily/Monthly | YES - "Which month?" |
| **Top Performers** | Top products, top states | Monthly | YES - "Which period?" |
| **Comparisons** | MoM growth, YoY trends | Monthly | YES - "Compare which months?" |
| **Inventory** | Stock levels (if tracked) | Daily | YES - "As of when?" |
| **HR Metrics** | Headcount, attrition rate | Monthly | YES - "Which month?" |

**Characteristics**:
- Must check data availability before answering
- Questions like "Top products" → Need to ask "Which month?"
- Answer validity depends on data freshness

---

### 2.3 HYBRID Data

**Definition**: Static structure, dynamic values

| Category | Examples | Behavior |
|----------|----------|----------|
| **Product prices** | Burger RM 12.90 | Structure static, prices change quarterly |
| **Employee list** | SalesRep_01 to _12 | List stable, but turnover occurs |
| **Branch names** | "Shah Alam Branch 1" | Rarely changes, but new branches open |

**Handling**:
- Treat structure as static (cacheable)
- Treat values as dynamic (refresh on data update)

---

## PART 3: DATA SCHEMA DESIGN

### 3.1 Core Sales Data Schema

```python
# FILE: data/sales/MY_Retail_Sales_YYYY_MM.csv
# Example: data/sales/MY_Retail_Sales_2024_07.csv

SALES_SCHEMA = {
    # Temporal
    "TransactionID": "string",       # PK: TXN0000001
    "Date": "datetime",              # 2024-07-15
    "YearMonth": "period[M]",        # 2024-07 (derived)
    
    # Location
    "State": "string",               # Selangor
    "City": "string",                # Shah Alam
    "Branch": "string",              # Shah Alam Branch 1
    "Region": "string",              # Selangor (redundant with State)
    
    # Product
    "Product": "string",             # Beef Burger
    "Quantity": "int",               # 3
    "Unit Price": "float",           # 12.90
    "Total Sale": "float",           # 38.70
    
    # Context
    "Employee": "string",            # SalesRep_05
    "Channel": "string",             # Dine-in | Takeaway | Delivery
    "PaymentMethod": "string",       # Cash | Card | eWallet
    
    # Metadata
    "source_file": "string",         # MY_Retail_Sales_2024_07.csv
    "ingestion_timestamp": "datetime", # 2024-07-01 00:05:00
    "data_quality_flag": "bool"      # True if validated
}
```

---

### 3.2 Metadata Schema (Data Catalog)

```python
# FILE: data/metadata/data_catalog.json

DATA_CATALOG_SCHEMA = {
    "sales": {
        "2024-01": {
            "file": "data/sales/MY_Retail_Sales_2024_01.csv",
            "rows": 4750,
            "date_range": ["2024-01-01", "2024-01-31"],
            "states": ["Selangor", "Kuala Lumpur", "Penang", "Johor", "Sabah", "Sarawak"],
            "products": ["Beef Burger", "Chicken Burger", ...],
            "total_revenue": 99665.52,
            "ingestion_date": "2024-01-01 00:05:00",
            "status": "validated"
        },
        "2024-02": {...},
        ...
        "2024-07": {
            "file": "data/sales/MY_Retail_Sales_2024_07.csv",
            "rows": 5100,
            "date_range": ["2024-07-01", "2024-07-31"],
            "states": ["Selangor", "Kuala Lumpur", "Penang", "Johor", "Sabah", "Sarawak"],
            "products": ["Beef Burger", "Chicken Burger", ...],
            "total_revenue": 105234.18,
            "ingestion_date": "2024-07-01 00:05:00",
            "status": "validated"
        }
    },
    "hr": {
        "2024-Q2": {...}
    },
    "latest": {
        "sales": "2024-07",
        "hr": "2024-Q2"
    }
}
```

**Purpose**:
- Quick lookup: "Is July 2024 data available?"
- Fast metadata: "What states exist in July?"
- Cache invalidation: Compare ingestion timestamps

---

### 3.3 Document Metadata Schema

```python
# FILE: data/metadata/document_catalog.json

DOCUMENT_CATALOG = {
    "HR_Policy_MY.txt": {
        "category": "policy",
        "last_updated": "2024-01-01",
        "version": "v2024.1",
        "is_static": True,
        "cache_until": "2025-01-01"
    },
    "Sales_SOP_MY.txt": {
        "category": "procedure",
        "last_updated": "2023-12-15",
        "version": "v2023.4",
        "is_static": True,
        "cache_until": "2024-12-31"
    }
}
```

---

## PART 4: QUERY CLASSIFICATION

### 4.1 Time-Sensitivity Detection

**Algorithm**:
```python
def classify_time_sensitivity(query: str) -> dict:
    """
    Returns:
    {
        "is_time_sensitive": bool,
        "explicit_timeframe": str | None,  # "2024-07", "July", "Q2"
        "needs_clarification": bool,
        "data_type": "sales" | "hr" | "policy"
    }
    """
    q_lower = query.lower()
    
    # Static queries
    if any(k in q_lower for k in ["policy", "sop", "procedure", "guideline"]):
        return {
            "is_time_sensitive": False,
            "explicit_timeframe": None,
            "needs_clarification": False,
            "data_type": "policy"
        }
    
    # Time-sensitive KPI queries
    if any(k in q_lower for k in ["top", "highest", "revenue", "sales", "compare"]):
        timeframe = extract_explicit_timeframe(query)
        return {
            "is_time_sensitive": True,
            "explicit_timeframe": timeframe,
            "needs_clarification": (timeframe is None),
            "data_type": "sales"
        }
    
    # HR queries
    if any(k in q_lower for k in ["employee", "headcount", "attrition"]):
        timeframe = extract_explicit_timeframe(query)
        return {
            "is_time_sensitive": True,
            "explicit_timeframe": timeframe,
            "needs_clarification": (timeframe is None),
            "data_type": "hr"
        }
```

### 4.2 Examples

| Query | Time-Sensitive? | Needs Clarification? | Data Type |
|-------|----------------|---------------------|-----------|
| "What's the refund policy?" | ❌ No | ❌ No | policy |
| "Top 5 products" | ✅ Yes | ✅ YES - "Which month?" | sales |
| "Top 5 products in July 2024" | ✅ Yes | ❌ No (explicit) | sales |
| "Compare sales July vs June" | ✅ Yes | ❌ No (explicit) | sales |
| "Total revenue for Selangor" | ✅ Yes | ✅ YES - "Which month?" | sales |
| "Headcount by department" | ✅ Yes | ✅ YES - "As of when?" | hr |

---

## PART 5: DATA AVAILABILITY VALIDATION

### 5.1 Validation Flow

```
User Query: "Top products in July 2024"
    ↓
[1] Parse timeframe → "2024-07"
    ↓
[2] Check data_catalog.json → Available?
    ↓
    ├─ YES → Proceed with query
    │         Load df_sales for 2024-07
    │         Execute aggregation
    │         Return answer
    ↓
    └─ NO → Fail closed
              Return: "❌ Data for July 2024 is not yet available.
                       Available months: Jan-Jun 2024
                       Latest data: June 2024"
```

### 5.2 Implementation

```python
def validate_data_availability(timeframe: str, data_type: str) -> dict:
    """
    Returns:
    {
        "available": bool,
        "message": str,  # Error message if not available
        "alternatives": list[str]  # Suggest available periods
    }
    """
    catalog = load_data_catalog()
    
    if data_type == "sales":
        available_months = list(catalog["sales"].keys())
        
        if timeframe in available_months:
            return {
                "available": True,
                "message": None,
                "alternatives": []
            }
        else:
            latest = catalog["latest"]["sales"]
            return {
                "available": False,
                "message": f"❌ Data for {timeframe} is not yet available.",
                "alternatives": available_months,
                "suggestion": f"Latest available data: {latest}"
            }
```

---

## PART 6: FOLLOW-UP QUESTION TEMPLATES

### 6.1 Missing Timeframe Templates

**Pattern**: User asks time-sensitive question without specifying period

```python
FOLLOWUP_TEMPLATES = {
    "sales_no_month": {
        "question": "📅 Which month would you like to analyze?",
        "options": [
            "January 2024",
            "February 2024",
            "March 2024",
            "April 2024",
            "May 2024",
            "June 2024 (Latest)",
            "Custom range..."
        ],
        "note": "Latest available data: June 2024"
    },
    
    "sales_no_region": {
        "question": "📍 Which region/state would you like to focus on?",
        "options": [
            "All states (National)",
            "Selangor",
            "Kuala Lumpur",
            "Penang",
            "Johor",
            "Sabah",
            "Sarawak"
        ]
    },
    
    "comparison_incomplete": {
        "question": "📊 Which periods would you like to compare?",
        "options": [
            "June 2024 vs May 2024 (MoM)",
            "Q2 2024 vs Q1 2024",
            "June 2024 vs June 2023 (YoY)",
            "Custom comparison..."
        ]
    },
    
    "data_not_available": {
        "message": "❌ Data for {requested_period} is not yet available.",
        "available_data": "Available: {start_month} to {end_month}",
        "suggestion": "Would you like to see results for {latest_month} instead?",
        "options": [
            "Yes, show {latest_month}",
            "No, I'll wait for new data"
        ]
    }
}
```

### 6.2 Examples

**Example 1: Missing Month**
```
User: "Top 5 products"
Bot: "📅 Which month would you like to analyze?
      
      [January 2024] [February 2024] [March 2024]
      [April 2024] [May 2024] [June 2024 (Latest)]
      
      Latest available data: June 2024"
```

**Example 2: Data Not Available**
```
User: "Show me sales for July 2024"
Bot: "❌ Data for July 2024 is not yet available.
     
     Available months: January 2024 - June 2024
     Latest data: June 2024
     
     Would you like to see results for June 2024 instead?
     
     [Yes, show June 2024] [No, I'll wait]"
```

**Example 3: Region Clarification**
```
User: "Total revenue this month"
Bot: "📍 For June 2024, which region?
     
     [All states (National)] [Selangor] [Kuala Lumpur]
     [Penang] [Johor] [Sabah] [Sarawak]"
```

---

## ANALYSIS COMPLETE - CHUNK 1

**Status**: ✅ COMPLETED
- Current system analyzed (static data loading, month extraction, FAISS caching)
- Static vs Dynamic classification defined
- Data schemas designed (Sales, Metadata, Document catalog)
- Query classification algorithm provided
- Data availability validation flow designed
- Follow-up question templates specified

**Next Chunk**: Architecture diagram and implementation plan

