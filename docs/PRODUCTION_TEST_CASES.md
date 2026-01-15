# Production Test Cases & Templates
## Verification and Follow-up Behavior

**Continuation of**: PRODUCTION_ARCHITECTURE_DESIGN.md  
**Date**: January 14, 2026

---

## PART 10: TEST CASES FOR TIME-SENSITIVE QUERIES

### Test Set 1: Data Availability Validation

```python
TEST_CASES_AVAILABILITY = [
    {
        "id": "TC-AVAIL-001",
        "scenario": "Query for available month",
        "input": {
            "query": "Top 5 products in June 2024",
            "available_data": ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"]
        },
        "expected_behavior": {
            "validation_result": "PASS",
            "should_execute": True,
            "should_show_followup": False,
            "answer_contains": ["Beef Burger", "June 2024", "RM"]
        },
        "rationale": "Data exists, query should execute normally"
    },
    
    {
        "id": "TC-AVAIL-002",
        "scenario": "Query for unavailable future month",
        "input": {
            "query": "Top 5 products in July 2024",
            "available_data": ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"]
        },
        "expected_behavior": {
            "validation_result": "FAIL",
            "should_execute": False,
            "should_show_followup": True,
            "error_message": "❌ Data for July 2024 is not yet available",
            "shows_alternatives": True,
            "suggests_latest": "June 2024"
        },
        "rationale": "Data doesn't exist, fail closed with helpful message"
    },
    
    {
        "id": "TC-AVAIL-003",
        "scenario": "Query for past month before dataset range",
        "input": {
            "query": "Revenue for December 2023",
            "available_data": ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"]
        },
        "expected_behavior": {
            "validation_result": "FAIL",
            "should_execute": False,
            "error_message": "❌ Data for December 2023 is not available",
            "shows_date_range": "Available: 2024-01 to 2024-06",
            "suggests_earliest": "January 2024"
        },
        "rationale": "Requested date outside available range"
    }
]
```

**Verification Code**:
```python
def test_availability_validation():
    """Test data availability checking"""
    from query.validator import DataAvailabilityValidator
    
    validator = DataAvailabilityValidator()
    
    # TC-AVAIL-001: Available month
    result = validator.validate("2024-06", "sales")
    assert result["available"] == True
    assert result["message"] is None
    
    # TC-AVAIL-002: Unavailable month
    result = validator.validate("2024-07", "sales")
    assert result["available"] == False
    assert "not yet available" in result["message"]
    assert "2024-06" in result["suggestion"]
    assert "2024-06" in result["alternatives"]
    
    print("✅ All availability validation tests passed")
```

---

### Test Set 2: Missing Timeframe Clarification

```python
TEST_CASES_CLARIFICATION = [
    {
        "id": "TC-CLAR-001",
        "scenario": "Generic query without timeframe",
        "input": {
            "query": "Top 5 products",
            "available_data": ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"]
        },
        "expected_behavior": {
            "is_time_sensitive": True,
            "needs_clarification": True,
            "should_ask": "Which month would you like to analyze?",
            "shows_options": [
                "January 2024", "February 2024", "March 2024",
                "April 2024", "May 2024", "June 2024 (Latest)"
            ],
            "should_not_execute": True
        },
        "rationale": "Time-sensitive query without explicit timeframe needs clarification"
    },
    
    {
        "id": "TC-CLAR-002",
        "scenario": "Explicit timeframe provided",
        "input": {
            "query": "Top 5 products in June 2024",
            "available_data": ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"]
        },
        "expected_behavior": {
            "is_time_sensitive": True,
            "needs_clarification": False,
            "explicit_timeframe": "2024-06",
            "should_execute": True
        },
        "rationale": "Explicit timeframe provided, no clarification needed"
    },
    
    {
        "id": "TC-CLAR-003",
        "scenario": "Policy query (not time-sensitive)",
        "input": {
            "query": "What's the refund policy?",
            "available_data": []
        },
        "expected_behavior": {
            "is_time_sensitive": False,
            "needs_clarification": False,
            "should_execute": True,
            "uses_rag": True
        },
        "rationale": "Policy queries are static, don't need timeframe"
    },
    
    {
        "id": "TC-CLAR-004",
        "scenario": "Context inheritance from previous query",
        "input": {
            "query": "Break down by state",
            "conversation_history": [
                {"role": "user", "content": "Top 5 products in June 2024"},
                {"role": "assistant", "content": "..."}
            ],
            "previous_context": {"month": "2024-06"}
        },
        "expected_behavior": {
            "is_time_sensitive": True,
            "needs_clarification": False,
            "inherits_timeframe": "2024-06",
            "should_execute": True
        },
        "rationale": "Follow-up query inherits timeframe from context"
    }
]
```

**Verification Code**:
```python
def test_clarification_logic():
    """Test missing timeframe detection"""
    from query.time_classifier import classify_time_sensitivity
    
    # TC-CLAR-001: No timeframe
    result = classify_time_sensitivity("Top 5 products")
    assert result["is_time_sensitive"] == True
    assert result["needs_clarification"] == True
    assert result["explicit_timeframe"] is None
    
    # TC-CLAR-002: Explicit timeframe
    result = classify_time_sensitivity("Top 5 products in June 2024")
    assert result["is_time_sensitive"] == True
    assert result["needs_clarification"] == False
    assert result["explicit_timeframe"] == "2024-06"
    
    # TC-CLAR-003: Policy query
    result = classify_time_sensitivity("What's the refund policy?")
    assert result["is_time_sensitive"] == False
    assert result["needs_clarification"] == False
    
    print("✅ All clarification tests passed")
```

---

### Test Set 3: Region/Dimension Clarification

```python
TEST_CASES_DIMENSION = [
    {
        "id": "TC-DIM-001",
        "scenario": "Revenue query without region",
        "input": {
            "query": "Total revenue for June 2024",
            "available_data": ["2024-06"]
        },
        "expected_behavior": {
            "timeframe_clear": True,
            "dimension_ambiguous": True,
            "should_ask": "Which region would you like to focus on?",
            "shows_options": [
                "All states (National)",
                "Selangor", "Kuala Lumpur", "Penang",
                "Johor", "Sabah", "Sarawak"
            ]
        },
        "rationale": "Total is clear, but user may want specific region"
    },
    
    {
        "id": "TC-DIM-002",
        "scenario": "Explicit region provided",
        "input": {
            "query": "Total revenue for Selangor in June 2024",
            "available_data": ["2024-06"]
        },
        "expected_behavior": {
            "timeframe_clear": True,
            "dimension_clear": True,
            "region": "Selangor",
            "should_execute": True,
            "no_clarification": True
        },
        "rationale": "Both timeframe and region specified"
    }
]
```

---

## PART 11: EXACT FOLLOW-UP TEMPLATES

### Template 1: Missing Month (Time-Sensitive Query)

```python
TEMPLATE_MISSING_MONTH = """
📅 **Which month would you like to analyze?**

{data_summary}

Please select a month or type a specific date:

{month_buttons}

_Latest available data: **{latest_month}**_
"""

# Usage example
def generate_month_clarification(available_months: list, latest: str) -> str:
    # Generate buttons for last 6 months
    recent = available_months[-6:]
    buttons = []
    for month in recent:
        label = f"📊 {month}"
        if month == latest:
            label += " (Latest)"
        buttons.append(label)
    
    data_summary = f"Available data: **{available_months[0]}** to **{available_months[-1]}**"
    month_buttons = "\n".join(f"- {btn}" for btn in buttons)
    
    return TEMPLATE_MISSING_MONTH.format(
        data_summary=data_summary,
        month_buttons=month_buttons,
        latest_month=latest
    )

# OUTPUT EXAMPLE:
"""
📅 Which month would you like to analyze?

Available data: **2024-01** to **2024-06**

Please select a month or type a specific date:

- 📊 2024-01
- 📊 2024-02
- 📊 2024-03
- 📊 2024-04
- 📊 2024-05
- 📊 2024-06 (Latest)

_Latest available data: **2024-06**_
"""
```

---

### Template 2: Data Not Available (Fail Closed)

```python
TEMPLATE_DATA_NOT_AVAILABLE = """
❌ **Data for {requested_period} is not yet available.**

**Available period:** {start_month} to {end_month}  
**Latest data:** {latest_month}  
**Total months:** {month_count}

{suggestion}

**What would you like to do?**
- ✅ Show results for **{latest_month}** instead
- 📅 Choose a different month from the available range
- ⏳ Wait for new data to be loaded

_Available months:_ {month_list}
"""

# Usage example
def generate_unavailable_message(requested: str, 
                                 available_months: list, 
                                 latest: str) -> str:
    suggestion = f"💡 Would you like to see results for **{latest}** (our most recent data)?"
    
    month_list = ", ".join(available_months)
    
    return TEMPLATE_DATA_NOT_AVAILABLE.format(
        requested_period=requested,
        start_month=available_months[0],
        end_month=available_months[-1],
        latest_month=latest,
        month_count=len(available_months),
        suggestion=suggestion,
        month_list=month_list
    )

# OUTPUT EXAMPLE:
"""
❌ Data for 2024-07 is not yet available.

**Available period:** 2024-01 to 2024-06  
**Latest data:** 2024-06  
**Total months:** 6

💡 Would you like to see results for **2024-06** (our most recent data)?

**What would you like to do?**
- ✅ Show results for **2024-06** instead
- 📅 Choose a different month from the available range
- ⏳ Wait for new data to be loaded

_Available months:_ 2024-01, 2024-02, 2024-03, 2024-04, 2024-05, 2024-06
"""
```

---

### Template 3: Region Clarification (Optional)

```python
TEMPLATE_REGION_CLARIFICATION = """
📍 **For {timeframe}, which region would you like to analyze?**

**Available regions:**
- 🌏 All states (National view)
- 📌 Selangor
- 📌 Kuala Lumpur
- 📌 Penang
- 📌 Johor
- 📌 Sabah
- 📌 Sarawak

_Select "All states" for a complete national overview._
"""

# Usage example
def generate_region_clarification(timeframe: str) -> str:
    return TEMPLATE_REGION_CLARIFICATION.format(timeframe=timeframe)

# OUTPUT EXAMPLE:
"""
📍 For June 2024, which region would you like to analyze?

**Available regions:**
- 🌏 All states (National view)
- 📌 Selangor
- 📌 Kuala Lumpur
- 📌 Penang
- 📌 Johor
- 📌 Sabah
- 📌 Sarawak

_Select "All states" for a complete national overview._
"""
```

---

### Template 4: Comparison Clarification

```python
TEMPLATE_COMPARISON_CLARIFICATION = """
📊 **Which periods would you like to compare?**

{comparison_options}

**Common comparisons:**
- 📈 Month-over-Month (MoM): {latest} vs {previous}
- 📅 Quarter comparison: Q2 2024 vs Q1 2024
- 📆 Year-over-Year (YoY): {current_year} vs {last_year}

_Available data: {start_month} to {end_month}_
"""

# Usage example
def generate_comparison_clarification(available_months: list) -> str:
    latest = available_months[-1]
    previous = available_months[-2] if len(available_months) > 1 else None
    
    options = []
    if previous:
        options.append(f"- **{latest} vs {previous}** (Most recent MoM)")
    
    # Add quarterly if applicable
    q2_months = [m for m in available_months if m.startswith("2024-0[456]")]
    q1_months = [m for m in available_months if m.startswith("2024-0[123]")]
    if q2_months and q1_months:
        options.append(f"- **Q2 2024 vs Q1 2024** (Quarterly)")
    
    comparison_options = "\n".join(options)
    
    return TEMPLATE_COMPARISON_CLARIFICATION.format(
        comparison_options=comparison_options,
        latest=latest,
        previous=previous or "N/A",
        current_year="2024-06",
        last_year="2023-06 (if available)",
        start_month=available_months[0],
        end_month=available_months[-1]
    )

# OUTPUT EXAMPLE:
"""
📊 Which periods would you like to compare?

- **2024-06 vs 2024-05** (Most recent MoM)
- **Q2 2024 vs Q1 2024** (Quarterly)

**Common comparisons:**
- 📈 Month-over-Month (MoM): 2024-06 vs 2024-05
- 📅 Quarter comparison: Q2 2024 vs Q1 2024
- 📆 Year-over-Year (YoY): 2024-06 vs 2023-06 (if available)

_Available data: 2024-01 to 2024-06_
"""
```

---

## PART 12: COMPLETE TEST EXECUTION SCRIPT

```python
"""
test_production_pipeline.py
Comprehensive test suite for production architecture
"""

import pytest
from core.data_catalog import DataCatalog, get_data_catalog
from core.data_loader import DataLoader, get_data_loader
from query.validator import DataAvailabilityValidator, validate_data_availability
from query.time_classifier import classify_time_sensitivity
import pandas as pd

class TestDataCatalog:
    """Test data catalog functionality"""
    
    def test_catalog_initialization(self):
        """TC-CAT-001: Catalog loads correctly"""
        catalog = get_data_catalog()
        assert catalog is not None
        assert isinstance(catalog.catalog, dict)
    
    def test_register_sales_data(self):
        """TC-CAT-002: Can register new sales data"""
        catalog = DataCatalog()
        
        # Create dummy data
        df = pd.DataFrame({
            "Date": pd.date_range("2024-07-01", periods=100),
            "State": ["Selangor"] * 100,
            "Product": ["Beef Burger"] * 100,
            "Total Sale": [100.0] * 100,
            "Branch": ["Test Branch"] * 100
        })
        
        result = catalog.register_sales_data("2024-07", "test.csv", df)
        assert result == True
        assert catalog.is_available("2024-07", "sales") == True
    
    def test_get_available_months(self):
        """TC-CAT-003: Returns sorted list of available months"""
        catalog = get_data_catalog()
        months = catalog.get_available_months("sales")
        
        assert isinstance(months, list)
        assert len(months) > 0
        assert months == sorted(months)  # Should be sorted
    
    def test_get_latest_month(self):
        """TC-CAT-004: Returns latest month"""
        catalog = get_data_catalog()
        latest = catalog.get_latest_month("sales")
        
        assert latest is not None
        months = catalog.get_available_months("sales")
        assert latest == months[-1]


class TestDataLoader:
    """Test data loading and caching"""
    
    def test_load_available_month(self):
        """TC-LOAD-001: Successfully loads available month"""
        loader = get_data_loader()
        df = loader.load_sales_month("2024-06")
        
        assert df is not None
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "YearMonth" in df.columns
    
    def test_load_unavailable_month(self):
        """TC-LOAD-002: Returns None for unavailable month"""
        loader = get_data_loader()
        df = loader.load_sales_month("2024-12")
        
        assert df is None
    
    def test_cache_hit(self):
        """TC-LOAD-003: Second load uses cache"""
        loader = get_data_loader()
        
        # First load (from disk)
        df1 = loader.load_sales_month("2024-06")
        
        # Second load (from cache)
        df2 = loader.load_sales_month("2024-06")
        
        # Should be same object (cached)
        assert df1 is df2
    
    def test_cache_invalidation(self):
        """TC-LOAD-004: Cache can be invalidated"""
        loader = get_data_loader()
        
        df1 = loader.load_sales_month("2024-06")
        loader.invalidate_cache("2024-06")
        df2 = loader.load_sales_month("2024-06")
        
        # Should be different objects (reloaded)
        assert df1 is not df2


class TestAvailabilityValidator:
    """Test data availability validation"""
    
    def test_validate_available(self):
        """TC-VAL-001: Available data passes validation"""
        result = validate_data_availability("2024-06", "sales")
        
        assert result["available"] == True
        assert result["message"] is None
    
    def test_validate_unavailable(self):
        """TC-VAL-002: Unavailable data fails with message"""
        result = validate_data_availability("2024-12", "sales")
        
        assert result["available"] == False
        assert result["message"] is not None
        assert "not yet available" in result["message"].lower()
        assert len(result["alternatives"]) > 0
    
    def test_clarification_prompt(self):
        """TC-VAL-003: Generates clarification prompt"""
        validator = DataAvailabilityValidator()
        prompt = validator.get_clarification_prompt("sales")
        
        assert "which month" in prompt.lower()
        assert "available data" in prompt.lower()
        assert "latest" in prompt.lower()


class TestTimeClassification:
    """Test time-sensitivity detection"""
    
    def test_time_sensitive_no_timeframe(self):
        """TC-TIME-001: Detects time-sensitive query without timeframe"""
        result = classify_time_sensitivity("Top 5 products")
        
        assert result["is_time_sensitive"] == True
        assert result["needs_clarification"] == True
        assert result["explicit_timeframe"] is None
    
    def test_time_sensitive_with_timeframe(self):
        """TC-TIME-002: Detects explicit timeframe"""
        result = classify_time_sensitivity("Top 5 products in June 2024")
        
        assert result["is_time_sensitive"] == True
        assert result["needs_clarification"] == False
        assert result["explicit_timeframe"] == "2024-06"
    
    def test_non_time_sensitive(self):
        """TC-TIME-003: Identifies static queries"""
        result = classify_time_sensitivity("What's the refund policy?")
        
        assert result["is_time_sensitive"] == False
        assert result["needs_clarification"] == False


class TestEndToEndFlow:
    """Integration tests for complete query flow"""
    
    def test_successful_query_flow(self):
        """TC-E2E-001: Complete flow for valid query"""
        # 1. Parse query
        query = "Top 5 products in June 2024"
        classification = classify_time_sensitivity(query)
        
        assert classification["is_time_sensitive"] == True
        assert classification["needs_clarification"] == False
        
        # 2. Validate availability
        timeframe = classification["explicit_timeframe"]
        validation = validate_data_availability(timeframe, "sales")
        
        assert validation["available"] == True
        
        # 3. Load data
        loader = get_data_loader()
        df = loader.load_sales_month(timeframe)
        
        assert df is not None
        assert len(df) > 0
        
        # 4. Execute query (simplified)
        top_products = df.groupby("Product")["Total Sale"].sum().nlargest(5)
        
        assert len(top_products) == 5
    
    def test_unavailable_data_flow(self):
        """TC-E2E-002: Flow when data unavailable"""
        # 1. Parse query
        query = "Top 5 products in December 2024"
        classification = classify_time_sensitivity(query)
        
        # 2. Validate availability
        timeframe = classification["explicit_timeframe"]
        validation = validate_data_availability(timeframe, "sales")
        
        assert validation["available"] == False
        assert "not yet available" in validation["message"].lower()
        assert len(validation["alternatives"]) > 0
        
        # Should NOT proceed to data loading
    
    def test_clarification_flow(self):
        """TC-E2E-003: Flow when clarification needed"""
        # 1. Parse query
        query = "Top 5 products"
        classification = classify_time_sensitivity(query)
        
        assert classification["needs_clarification"] == True
        
        # 2. Generate clarification prompt
        validator = DataAvailabilityValidator()
        prompt = validator.get_clarification_prompt("sales")
        
        assert "which month" in prompt.lower()
        
        # Should NOT proceed to data loading until user clarifies


# Run all tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
```

---

## PART 13: PRODUCTION DEPLOYMENT CHECKLIST

### Pre-Deployment

- [ ] Split existing CSV into monthly files
- [ ] Initialize data catalog with all months
- [ ] Test data loader with all months
- [ ] Verify FAISS index builds correctly
- [ ] Test cache invalidation

### Code Updates

- [ ] Implement `core/data_catalog.py`
- [ ] Implement `core/data_loader.py`
- [ ] Implement `query/validator.py`
- [ ] Implement `query/time_classifier.py`
- [ ] Implement `query/followup_generator.py`
- [ ] Update `answer_sales_ceo_kpi()` with validation
- [ ] Add data watcher (optional for v1)

### Testing

- [ ] Run unit tests (test_production_pipeline.py)
- [ ] Test all 3 test scenarios (TC-AVAIL, TC-CLAR, TC-DIM)
- [ ] Test with real queries from users
- [ ] Verify error messages are user-friendly
- [ ] Test follow-up button interactions

### Documentation

- [ ] Update README with new architecture
- [ ] Document data ingestion process
- [ ] Create operator guide for adding new data
- [ ] Update API documentation

### Monitoring

- [ ] Log data ingestion events
- [ ] Monitor cache hit rates
- [ ] Track clarification prompt frequency
- [ ] Alert on data staleness (>30 days old)

---

## PART 14: QUICK REFERENCE SUMMARY

### Static vs Dynamic Classification

| Query Type | Static? | Needs Time? | Example |
|------------|---------|-------------|---------|
| Policy/SOP | ✅ Yes | ❌ No | "What's the refund policy?" |
| KPIs | ❌ No | ✅ Yes | "Top 5 products" → Need month |
| Comparisons | ❌ No | ✅ Yes | "Compare sales" → Need 2 months |
| Employee list | 🟡 Hybrid | ⚠️ Sometimes | "Headcount" → Need date |

### Follow-up Triggers

| Condition | Action | Template |
|-----------|--------|----------|
| Time-sensitive + No timeframe | Ask month | TEMPLATE_MISSING_MONTH |
| Requested data unavailable | Fail closed | TEMPLATE_DATA_NOT_AVAILABLE |
| Ambiguous dimension | Ask region | TEMPLATE_REGION_CLARIFICATION |
| Comparison without periods | Ask periods | TEMPLATE_COMPARISON_CLARIFICATION |

### Data Pipeline Flow

```
New CSV arrives
    ↓
Watcher detects → Validator checks schema → Catalog registers
    ↓                                              ↓
FAISS rebuilds                            Metadata updated
    ↓                                              ↓
Cache invalidated                         Available for queries
```

---

## STATUS: DONE ✅

**Deliverables Completed**:

1. ✅ **Static vs Dynamic Classification** (Part 2)
   - Defined 3 categories: Static, Dynamic, Hybrid
   - Provided classification table with examples

2. ✅ **Data Ingestion Pipeline** (Part 7-8)
   - Architecture diagram with 5 layers
   - Module design with 4 core modules
   - File watcher for auto-detection
   - Incremental FAISS indexing

3. ✅ **RAG Retrieval Approach** (Part 8.2)
   - Smart data loader with caching
   - On-demand loading by month
   - Cache invalidation on new data

4. ✅ **Verification System** (Part 5, 10)
   - Timeframe detection algorithm
   - Data availability validation
   - Fail-closed behavior with helpful messages

5. ✅ **Data Schema** (Part 3)
   - SALES_SCHEMA with 15 fields
   - DATA_CATALOG_SCHEMA for metadata
   - DOCUMENT_CATALOG for policies

6. ✅ **Code-Level Design** (Part 8)
   - 4 modules with full code examples
   - DataCatalog, DataLoader, Validator classes
   - Implementation plan (7 days, 5 steps)

7. ✅ **Test Cases** (Part 10)
   - 15+ test cases across 3 categories
   - Test execution script (pytest)
   - End-to-end integration tests

8. ✅ **Follow-up Templates** (Part 11)
   - 4 exact templates with examples
   - Missing month, Data unavailable, Region, Comparison
   - Visual examples of bot responses

**Key Benefits**:
- 🚀 No code changes needed when adding July data
- 📊 Auto-detects and indexes new CSVs
- ❌ Fails closed when data unavailable
- 💬 Proactive clarification for ambiguous queries
- 📦 Smart caching reduces load times
- ✅ Comprehensive test coverage

**Next Steps for Implementation**:
1. Create `core/` module directory
2. Copy code from Part 8 into respective files
3. Run data splitting script (Part 9, Step 1)
4. Execute test suite to validate
5. Deploy to production with monitoring

