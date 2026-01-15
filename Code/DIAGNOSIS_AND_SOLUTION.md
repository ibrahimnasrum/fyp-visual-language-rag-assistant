# System Diagnosis and Proper Solution

## Date: January 14, 2026

---

## Problem Statement

The current system (v8.3) has verification and deterministic features, but still produces **wrong answer types** for complex queries.

### Test Results That Failed:

#### Test 1: Percentage Query ❌
**Query:** "What percentage of total June sales came from Selangor?"
**Expected:** "Selangor represents 16.4% of June sales"
**Actual:** "Value: RM 16,421.18" (wrong type!)
**Verification:** "✅ Verified" (false positive - shouldn't verify when answer type is wrong)

#### Test 2: Filtered Query ⚠️
**Query:** "Show me total sales for all products starting with 'Burger' in Selangor for May 2024"
**Expected:** Clear statement showing filtered results with breakdown
**Actual:** Generic "Value: RM 17,189.46" without showing what was filtered
**Verification:** "✅ Verified" (number is correct but answer lacks clarity)

#### Test 3: Branch Query ⚠️
**Query:** "Show me total sales for the Petaling Jaya branch in May 2024"
**Expected:** Branch-specific analysis
**Actual:** Generic "Value: RM 106,995.11" without branch confirmation
**Verification:** "✅ Verified" (correct number but generic format)

---

## Root Cause Analysis

### Issue 1: Deterministic Function is Too Simple
**File:** `oneclick_my_retailchain_v8.2_models_logging.py`
**Function:** `answer_sales_ceo_kpi()` (lines ~1134-1433)

**Problem:**
```python
def answer_sales_ceo_kpi(query: str, trace=None):
    # ... filters data correctly ...
    # But ALWAYS returns this format:
    return f"""## ✅ Total Sales (RM)
Month: {month}

### Executive Summary
Value: RM {total_sales:,.2f}
"""
```

**Why it fails:**
- ✅ Filtering works (Selangor, Burger products, May)
- ✅ Calculation is accurate
- ❌ Output format is hardcoded
- ❌ Doesn't understand query intent (percentage vs total vs breakdown)

### Issue 2: Verification Checks Numbers, Not Semantics
**File:** `oneclick_my_retailchain_v8.2_models_logging.py`
**Function:** `verify_answer_against_ground_truth()` (lines ~284-330)

**Problem:**
```python
def verify_answer_against_ground_truth(answer, query, route, context):
    claims = extract_numerical_claims(answer)  # Finds "16,421.18"
    ground_truth = compute_ground_truth(...)   # Calculates "16,421.18"
    # Compares numbers: ✅ Match!
    # But doesn't check: Did user ask for $ or %?
```

**Why it fails:**
- ✅ Numbers are verified
- ❌ Answer TYPE is not verified
- ❌ "Show me RM" vs "Show me %" treated the same

### Issue 3: No Query Intent Understanding
**Missing Component:**

```python
# This doesn't exist:
def understand_query_intent(query: str) -> QueryIntent:
    """
    Parse: "What percentage of June sales came from Selangor?"
    Return: {
        'type': 'PERCENTAGE',
        'numerator_filter': {'state': 'Selangor', 'month': '2024-06'},
        'denominator_filter': {'month': '2024-06'},
        'expected_format': 'percentage'
    }
    """
```

---

## Proper Solution Architecture

### Layer 1: Query Intent Parser
**Purpose:** Understand what user is REALLY asking for

```python
class QueryIntent:
    def __init__(self):
        self.intent_type = None  # 'total', 'percentage', 'comparison', 'breakdown', 'trend'
        self.metric = None       # 'sales', 'quantity', 'avg_price'
        self.filters = {}        # {'state': 'Selangor', 'month': '2024-06', ...}
        self.aggregation = None  # 'sum', 'avg', 'count', 'percentage'
        self.groupby = None      # None, 'state', 'product', 'branch'
        self.comparison = None   # None, {'type': 'vs_previous', 'dimension': 'month'}

def parse_query_intent(query: str) -> QueryIntent:
    """
    Examples:
    
    "Total sales June 2024" 
    → QueryIntent(type='total', metric='sales', filters={'month': '2024-06'})
    
    "What percentage of June sales came from Selangor?"
    → QueryIntent(type='percentage', 
                  numerator={'state': 'Selangor', 'month': '2024-06'},
                  denominator={'month': '2024-06'})
    
    "Compare June vs May sales"
    → QueryIntent(type='comparison', metric='sales',
                  comparison={'type': 'time', 'periods': ['2024-06', '2024-05']})
    
    "Top 5 products in Selangor"
    → QueryIntent(type='breakdown', metric='sales', 
                  filters={'state': 'Selangor'},
                  groupby='product', limit=5)
    """
    
    intent = QueryIntent()
    q = query.lower()
    
    # Detect intent type
    if 'percentage' in q or '% of' in q or 'what % of' in q:
        intent.intent_type = 'percentage'
    elif 'compare' in q or 'vs' in q or 'versus' in q:
        intent.intent_type = 'comparison'
    elif 'top' in q or 'best' in q or 'breakdown' in q or 'by' in q:
        intent.intent_type = 'breakdown'
    elif 'trend' in q or 'over time' in q:
        intent.intent_type = 'trend'
    else:
        intent.intent_type = 'total'
    
    # Extract filters (state, month, product, branch)
    # ... detailed parsing logic ...
    
    return intent
```

### Layer 2: Query Executor
**Purpose:** Execute query with correct output format

```python
def execute_sales_query(intent: QueryIntent, df: pd.DataFrame) -> dict:
    """
    Execute query and return result in format matching intent.
    
    Returns:
    {
        'type': 'percentage',
        'value': 16.4,
        'numerator': 16421.18,
        'denominator': 99852.83,
        'filters_applied': {'state': 'Selangor', 'month': '2024-06'},
        'formatted_answer': "Selangor sales represent 16.4% of total June sales..."
    }
    """
    
    if intent.intent_type == 'percentage':
        return execute_percentage_query(intent, df)
    elif intent.intent_type == 'comparison':
        return execute_comparison_query(intent, df)
    elif intent.intent_type == 'breakdown':
        return execute_breakdown_query(intent, df)
    elif intent.intent_type == 'total':
        return execute_total_query(intent, df)
    else:
        return execute_generic_query(intent, df)


def execute_percentage_query(intent: QueryIntent, df: pd.DataFrame) -> dict:
    """
    Example: "What percentage of June sales came from Selangor?"
    """
    # Filter for numerator (Selangor + June)
    df_numerator = df.copy()
    if intent.numerator_filters:
        for key, val in intent.numerator_filters.items():
            if key == 'state':
                df_numerator = df_numerator[df_numerator['State'] == val]
            elif key == 'month':
                df_numerator = df_numerator[df_numerator['DateStr'].str.contains(val)]
            # ... other filters ...
    
    numerator_value = df_numerator['Total Sale'].sum()
    
    # Filter for denominator (June only)
    df_denominator = df.copy()
    if intent.denominator_filters:
        for key, val in intent.denominator_filters.items():
            if key == 'month':
                df_denominator = df_denominator[df_denominator['DateStr'].str.contains(val)]
            # ... other filters ...
    
    denominator_value = df_denominator['Total Sale'].sum()
    
    # Calculate percentage
    percentage = (numerator_value / denominator_value * 100) if denominator_value > 0 else 0
    
    # Format answer
    formatted_answer = f"""## 📊 Sales Percentage Analysis

### Query Result
**{intent.numerator_filters.get('state', 'Filtered')} sales represent {percentage:.1f}% of total June sales**

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
        'filters_applied': intent.numerator_filters,
        'formatted_answer': formatted_answer
    }
```

### Layer 3: Semantic Verification
**Purpose:** Verify answer TYPE matches query TYPE

```python
def verify_answer_semantics(query: str, answer: str, result: dict) -> tuple:
    """
    Check if answer format matches query intent.
    
    Returns: (is_valid, error_message)
    """
    q = query.lower()
    
    # Check 1: Percentage query must have % in answer
    if 'percentage' in q or '% of' in q:
        if '%' not in answer:
            return (False, "Query asked for percentage but answer shows dollar amount")
        if result.get('type') != 'percentage':
            return (False, "Query asked for percentage but got total instead")
        return (True, None)
    
    # Check 2: Comparison query must show multiple values
    if 'compare' in q or 'vs' in q:
        # Count how many RM values appear
        rm_count = answer.count('RM ')
        if rm_count < 2:
            return (False, "Comparison query but answer only shows one value")
        return (True, None)
    
    # Check 3: Breakdown query must show table or list
    if 'top' in q or 'breakdown' in q or 'by state' in q or 'by product' in q:
        # Check for table or numbered list
        has_table = '|' in answer or '\n-' in answer
        has_list = re.search(r'\d+\.\s\*\*', answer)  # "1. **Product**"
        if not (has_table or has_list):
            return (False, "Breakdown query but answer doesn't show breakdown")
        return (True, None)
    
    # Check 4: Total query should show single value
    return (True, None)
```

---

## Implementation Plan

### Phase 1: Add Query Intent Parser (2-3 hours)
1. Create `parse_query_intent()` function
2. Handle patterns:
   - Percentage: "what % of", "percentage of"
   - Comparison: "compare", "vs", "versus"
   - Breakdown: "top", "by state", "by product"
   - Total: everything else
3. Extract filters: state, month, product, branch
4. Test with sample queries

### Phase 2: Refactor Query Executors (3-4 hours)
1. Create `execute_percentage_query()`
2. Create `execute_comparison_query()`
3. Create `execute_breakdown_query()`
4. Update `execute_total_query()` (existing)
5. Add proper formatting for each type

### Phase 3: Add Semantic Verification (1-2 hours)
1. Create `verify_answer_semantics()`
2. Check answer type matches query type
3. Integrate with existing numerical verification
4. Show semantic errors separately

### Phase 4: Integration (2-3 hours)
1. Replace `answer_sales_ceo_kpi()` with new system
2. Update routing logic
3. Test all query types
4. Handle edge cases

### Total Estimated Time: 8-12 hours

---

## Expected Results After Fix

### Query 1: Percentage
**Input:** "What percentage of June sales came from Selangor?"
**Output:**
```
## 📊 Sales Percentage Analysis

### Query Result
**Selangor sales represent 16.4% of total June sales**

### Breakdown
- Selangor June Sales: RM 16,421.18
- Total June Sales: RM 99,852.83
- Percentage: 16.4%

✅ Verified: Calculated directly from data (100% accurate).
✅ Semantic Check: Answer type (percentage) matches query type.
```

### Query 2: Filtered Total
**Input:** "Show me total sales for all products starting with 'Burger' in Selangor for May 2024"
**Output:**
```
## 📊 Sales Analysis

### Query Result
**Total Sales: RM 17,189.46**

### Filters Applied
- Products: Burger Classic, Burger Cheese, Burger Deluxe, Burger Spicy (4 products)
- State: Selangor
- Month: May 2024
- Rows: 831 transactions

### Breakdown by Product
1. **Burger Classic**: RM 8,234.50 (47.9%)
2. **Burger Cheese**: RM 5,123.80 (29.8%)
3. **Burger Deluxe**: RM 2,890.16 (16.8%)
4. **Burger Spicy**: RM 941.00 (5.5%)

✅ Verified: Calculated directly from data (100% accurate).
```

### Query 3: Branch
**Input:** "Show me total sales for the Petaling Jaya branch in May 2024"
**Output:**
```
## 📊 Branch Performance

### Query Result
**Petaling Jaya Branch - May 2024**

### Performance Summary
- Total Sales: RM 106,995.11
- Transactions: 5,235
- Average Transaction: RM 20.44
- Branch Rank: #2 out of 12 branches

### Comparison
- vs April 2024: +12.3%
- vs May 2023: +8.7%

✅ Verified: Calculated directly from data (100% accurate).
```

---

## Decision Point

**Option A: Implement Full Solution (8-12 hours)**
- Build query intent parser
- Create specialized executors
- Add semantic verification
- Production-ready, handles all query types

**Option B: Quick Patch (2-3 hours)**
- Add percentage calculation to existing function
- Add basic type checking
- Won't handle all cases, but fixes worst issues

**Option C: Document Limitations**
- Update docs to show supported query types
- Add examples of what works vs doesn't work
- Quick fix: 1 hour

---

## Recommendation

**Implement Option A (Full Solution)** because:
1. Current system is fundamentally broken for non-trivial queries
2. Verification layer can't fix semantic mismatches
3. CEO users will ask complex questions
4. Proper solution prevents future issues
5. 8-12 hours is reasonable for production-ready system

The verification and deterministic features I built (v8.3) are good additions, but they can't fix the underlying issue: **the system doesn't understand what users are asking for**.

---

**Would you like me to proceed with implementing the full solution (Option A)?**
