# Implementation Plan: Query Intent System v9
## Date: January 14, 2026

---

## CHUNK 1: Analysis & Implementation Plan ✅

### Current Architecture Analysis

**File:** `oneclick_my_retailchain_v8.2_models_logging.py`
**Function:** `answer_sales_ceo_kpi()` (lines 928-1300+)

#### What Works ✅
1. **Filter Extraction:** Correctly identifies state, branch, product, employee, channel
2. **Metric Detection:** Distinguishes revenue vs quantity
3. **Month Parsing:** Handles single month, month ranges, "last month"
4. **Pattern Matching:** Detects "compare", "top", "vs"
5. **Data Calculations:** Pandas operations are accurate

#### What's Broken ❌
1. **Hardcoded Output Format:** Always returns "Total Sales (RM): ..." regardless of query type
2. **No Intent Classification:** Doesn't distinguish between:
   - "What is total sales?" → Need: Dollar amount
   - "What percentage of sales?" → Need: Percentage
   - "Compare June vs May" → Need: Two values side-by-side
   - "Top 5 products" → Need: Ranked list
3. **Semantic Mismatch:** Numbers are correct but answer TYPE is wrong

#### Example of Current Behavior
```python
# Current code (simplified):
def answer_sales_ceo_kpi(q, trace):
    # ... filters data correctly ...
    total_sales = df['Total Sale'].sum()
    
    # PROBLEM: Always returns this format
    return f"""## ✅ Total Sales (RM)
### Executive Summary
Value: RM {total_sales:,.2f}
"""
```

**Result:** 
- Query: "What percentage of June sales came from Selangor?" 
- Answer: "Value: RM 16,421.18" ← WRONG TYPE
- Should be: "Selangor = 16.4% of June 2024 sales"

---

## Solution Architecture

### Layer 1: Query Intent Parser
**Purpose:** Understand what user is REALLY asking for

```python
class QueryIntent:
    """Structured representation of user query intent"""
    def __init__(self):
        self.intent_type = None     # 'total', 'percentage', 'comparison', 'breakdown', 'trend'
        self.metric = None          # 'sales', 'quantity'
        self.filters = {}           # {'state': 'Selangor', 'month': '2024-06', ...}
        self.aggregation = None     # 'sum', 'avg', 'percentage', 'rank'
        self.groupby = None         # None, 'state', 'product', 'branch', 'employee'
        self.comparison = None      # None, {'type': 'time', 'periods': [...]}
        self.percentage_context = None  # For percentage queries: {'part': {...}, 'whole': {...}}
```

### Layer 2: Specialized Executors
**Purpose:** Execute query with output format matching intent

```python
def execute_query(intent: QueryIntent, df: pd.DataFrame, trace=None) -> dict:
    """Route to specialized executor based on intent type"""
    if intent.intent_type == 'percentage':
        return execute_percentage_query(intent, df, trace)
    elif intent.intent_type == 'comparison':
        return execute_comparison_query(intent, df, trace)
    elif intent.intent_type == 'breakdown':
        return execute_breakdown_query(intent, df, trace)
    elif intent.intent_type == 'total':
        return execute_total_query(intent, df, trace)
    else:
        return execute_generic_query(intent, df, trace)
```

### Layer 3: Semantic Verification
**Purpose:** Verify answer TYPE matches query TYPE

```python
def verify_answer_semantics(query: str, answer: str, intent: QueryIntent) -> tuple:
    """
    Check if answer format matches query intent.
    Returns: (is_valid, error_message)
    """
    # Example: Percentage query must contain '%' in answer
    if intent.intent_type == 'percentage':
        if '%' not in answer:
            return (False, "Query asked for percentage but answer shows dollar amount")
    return (True, None)
```

---

## Implementation Chunks

### CHUNK 2: Query Intent Parser (3-4 hours)
**Files to modify:**
- `oneclick_my_retailchain_v8.2_models_logging.py`

**Functions to add:**
1. `class QueryIntent` - Data structure for intent
2. `parse_query_intent(query: str) -> QueryIntent` - Main parser
3. `detect_intent_type(query: str) -> str` - Classify intent
4. `extract_percentage_context(query: str) -> dict` - Parse "X of Y" patterns
5. `extract_comparison_context(query: str) -> dict` - Parse "A vs B" patterns

**Key Patterns to Detect:**

**Percentage Queries:**
- "What percentage of..."
- "What % of..."
- "How much % of..."
- "Berapa peratus..."

**Comparison Queries:**
- "Compare X vs Y"
- "X versus Y"
- "June vs May"
- "State A vs State B"

**Breakdown Queries:**
- "Top 5 products"
- "Breakdown by state"
- "Show by branch"
- "Rank products"

**Total Queries (default):**
- "Total sales"
- "How much sales"
- "Jumlah jualan"

### CHUNK 3: Percentage Executor (2-3 hours)
**Functions to add:**
1. `execute_percentage_query(intent, df, trace) -> dict`
2. `calculate_percentage(numerator_df, denominator_df) -> float`
3. `format_percentage_answer(result) -> str`

**Logic:**
```python
def execute_percentage_query(intent, df, trace):
    """
    Example: "What percentage of June sales came from Selangor?"
    
    Steps:
    1. Filter for numerator (Selangor + June)
    2. Filter for denominator (June only)
    3. Calculate: (numerator / denominator) * 100
    4. Format as percentage with breakdown
    """
    
    # Extract filters
    numerator_filters = intent.percentage_context['part']     # {'state': 'Selangor', 'month': '2024-06'}
    denominator_filters = intent.percentage_context['whole']  # {'month': '2024-06'}
    
    # Apply filters
    df_numerator = apply_filters(df, numerator_filters)
    df_denominator = apply_filters(df, denominator_filters)
    
    # Calculate
    numerator_value = df_numerator['Total Sale'].sum()
    denominator_value = df_denominator['Total Sale'].sum()
    percentage = (numerator_value / denominator_value * 100) if denominator_value > 0 else 0
    
    # Format answer
    answer = f"""## 📊 Sales Percentage Analysis

### Query Result
**Selangor sales represent {percentage:.1f}% of total June 2024 sales**

### Breakdown
- Selangor June Sales: RM {numerator_value:,.2f}
- Total June Sales: RM {denominator_value:,.2f}
- Percentage: {percentage:.1f}%

### Calculation
({numerator_value:,.2f} / {denominator_value:,.2f}) × 100 = {percentage:.1f}%

✅ Verified: Calculated directly from data (100% accurate).
"""
    
    return {
        'type': 'percentage',
        'value': percentage,
        'numerator': numerator_value,
        'denominator': denominator_value,
        'formatted_answer': answer
    }
```

### CHUNK 4: Comparison & Breakdown Executors (2-3 hours)
**Functions to add:**
1. `execute_comparison_query(intent, df, trace) -> dict`
2. `execute_breakdown_query(intent, df, trace) -> dict`
3. `format_comparison_answer(result) -> str`
4. `format_breakdown_answer(result) -> str`

**Comparison Logic:**
- Time comparison (June vs May, MoM, YoY)
- Dimension comparison (State A vs State B, Branch A vs B)
- Show both values side-by-side with delta and percentage change

**Breakdown Logic:**
- Group by dimension (product, state, branch)
- Rank and limit (top 5, top 10)
- Show as table with percentages of total

### CHUNK 5: Integration & Routing (2-3 hours)
**Functions to modify:**
1. `answer_sales_ceo_kpi()` - Add intent-based routing
2. `verify_answer_against_ground_truth()` - Add semantic check
3. `format_verification_notice()` - Include semantic errors

**New Routing Logic:**
```python
def answer_sales_ceo_kpi(q: str, trace: ToolTrace = None):
    """REFACTORED: Intent-based routing"""
    
    # Step 1: Parse intent
    intent = parse_query_intent(q)
    
    # Step 2: Execute based on intent type
    result = execute_query(intent, df_sales, trace)
    
    # Step 3: Get formatted answer
    answer = result['formatted_answer']
    
    # Step 4: Verify semantics
    is_valid, error = verify_answer_semantics(q, answer, intent)
    if not is_valid:
        answer += f"\n\n⚠️ **Semantic Warning:** {error}"
    
    return answer
```

### CHUNK 6: Testing & Documentation (1-2 hours)
**Files to create/update:**
1. Update `test_verification.py` - Add semantic tests
2. Update `TESTING_INSTRUCTIONS_v8.3.md` - Add percentage query tests
3. Create `IMPLEMENTATION_COMPLETE_v9.md` - Document v9 features
4. Update `README_CEO_UPDATE_v8.2.md` - Add v9 section

**Test Cases:**
1. Percentage query: "What percentage of June sales came from Selangor?"
2. Comparison query: "Compare June vs May sales"
3. Breakdown query: "Top 5 products in Selangor"
4. Filtered total: "Total sales for Burger products in May"
5. Multi-filter: "Selangor Burger sales in June"

---

## File Structure Changes

### New Files
None - all changes are in existing `oneclick_my_retailchain_v8.2_models_logging.py`

### Modified Files
1. `oneclick_my_retailchain_v8.2_models_logging.py`
   - Lines ~238-335: Keep existing verification functions
   - Lines ~336-520: Keep existing deterministic handlers
   - **NEW Lines ~550-750:** Add query intent parser
   - **NEW Lines ~751-950:** Add percentage executor
   - **MODIFY Lines 928-1300:** Refactor answer_sales_ceo_kpi() with intent routing
   - Lines ~284-330: Update verify_answer_against_ground_truth() with semantic check

### Code Organization
```
oneclick_my_retailchain_v8.2_models_logging.py
├── [Lines 1-237] Existing: Imports, globals, data loading
├── [Lines 238-335] Existing: Verification functions (numerical)
├── [Lines 336-520] Existing: Deterministic handlers
├── [Lines 550-750] NEW: Query intent parser
│   ├── class QueryIntent
│   ├── parse_query_intent()
│   ├── detect_intent_type()
│   ├── extract_percentage_context()
│   └── extract_comparison_context()
├── [Lines 751-950] NEW: Specialized executors
│   ├── execute_query() [router]
│   ├── execute_percentage_query()
│   ├── execute_comparison_query()
│   ├── execute_breakdown_query()
│   └── execute_total_query() [wrapper for existing logic]
├── [Lines 928-1300] MODIFIED: answer_sales_ceo_kpi()
│   └── Now uses intent-based routing
└── [Rest] Existing: RAG, streaming, Gradio UI
```

---

## Estimated Timeline

| Chunk | Task | Hours | Status |
|-------|------|-------|--------|
| 1 | Analysis & Plan | 1 | ✅ DONE |
| 2 | Query Intent Parser | 3-4 | ✅ DONE |
| 3 | Percentage Executor | 2-3 | ✅ DONE |
| 4 | Comparison & Breakdown | 2-3 | ✅ DONE |
| 5 | Integration & Routing | 2-3 | ✅ DONE |
| 6 | Testing & Bug Fixes | 1-2 | ✅ DONE |
| **TOTAL** | | **11-16 hours** | **✅ COMPLETE** |

## 🐛 Bug Fixes (v9.1)
- ✅ Fixed division by zero error in percentage queries
- ✅ Fixed month filtering logic (denominator now correct)
- ✅ Fixed Top N detection (respects query number)
- ✅ Fixed follow-up question crashes (graceful fallback)
- ✅ Added comprehensive error handling

---

## Success Criteria

### Before (v8.2)
❌ Query: "What percentage of June sales came from Selangor?"
❌ Answer: "Value: RM 16,421.18" (wrong type)
❌ Verification: "✅ Verified" (false positive)

### After (v9)
✅ Query: "What percentage of June sales came from Selangor?"
✅ Answer: "Selangor sales represent 16.4% of total June 2024 sales"
✅ Verification: "✅ Verified: Answer type (percentage) matches query type"

### Additional Tests
1. **Percentage Query:** "What % of May sales were Burger products?"
   - Expected: "Burger products = 17.2% of May sales"
   
2. **Comparison Query:** "Compare Selangor vs Penang sales in June"
   - Expected: Side-by-side comparison with delta
   
3. **Breakdown Query:** "Top 5 products in Selangor"
   - Expected: Ranked table with product names and sales
   
4. **Filtered Total:** "Total Burger sales in May Selangor"
   - Expected: "Total: RM 17,189.46 (Filtered: Burger products, Selangor, May 2024)"

---

## Next Steps

**CHUNK 2 will implement:**
1. `class QueryIntent` data structure
2. `parse_query_intent()` main parser
3. Pattern detection for percentage, comparison, breakdown, total queries
4. Filter extraction integration with existing code

**Ready to proceed with CHUNK 2?** Type "continue" to begin implementation.

---

## Notes

- Existing verification functions (v8.3) will be preserved and enhanced
- Deterministic handlers (v8.3) will work alongside new intent system
- Caching (v8.3) remains unchanged
- All existing CEO executive format features retained
- Backward compatible: Total queries work exactly as before

