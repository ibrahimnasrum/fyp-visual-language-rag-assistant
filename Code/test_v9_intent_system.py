# Test v9 Intent System
# Comprehensive test for percentage, comparison, and breakdown queries

"""
To run this test:
1. Start the app: python oneclick_my_retailchain_v8.2_models_logging.py
2. Wait for app to load completely
3. Test queries in the browser at http://127.0.0.1:7860 (or whatever port shows)
"""

# =========================
# Test Cases for v9 Intent System
# =========================

TEST_QUERIES = {
    "percentage": [
        "What percentage of June 2024 sales came from Selangor?",
        "What % of May sales were Burger products?",
        "Berapa peratus jualan June dari Penang?",
        "What percentage of total sales came from Burger Classic in June?",
    ],
    
    "comparison": [
        "Compare June vs May sales",
        "Compare Selangor vs Penang sales in June",
        "Compare June 2024 versus May 2024",
        "Selangor vs Penang sales for May",
        "Compare Burger Classic vs Burger Cheese sales",
    ],
    
    "breakdown": [
        "Top 5 products in Selangor",
        "Top 10 products for June 2024",
        "Show breakdown by state for June",
        "Top 5 branches by sales",
        "Rank products by sales in Penang",
    ],
    
    "total": [
        "Total sales for June 2024",
        "Show me sales for Burger products in May",
        "Total sales in Selangor for June",
        "Sales for Penang in May 2024",
    ]
}

# =========================
# Expected Results
# =========================

EXPECTED_RESULTS = {
    "percentage": {
        "format": "## 📊 Sales Percentage Analysis",
        "must_contain": ["%", "percentage", "Percentage:"],
        "must_not_contain": ["Value: RM"],  # Should NOT show simple dollar total
        "verification": "✅ **Verified**: Calculated directly from data"
    },
    
    "comparison": {
        "format": "## 📊 Time Comparison - Sales (RM)" or "## 📊 State Comparison - Sales (RM)",
        "must_contain": ["|", "Difference", "% Change", "vs"],
        "must_not_contain": [],
        "verification": "✅ **Verified**: Calculated directly from data"
    },
    
    "breakdown": {
        "format": "## 📊 Top",
        "must_contain": ["1.", "2.", "3.", "of total"],  # Rankings
        "must_not_contain": [],
        "verification": "✅ **Verified**: Calculated directly from data"
    },
    
    "total": {
        "format": "## ✅ Total Sales (RM)",
        "must_contain": ["Value: RM", "Executive Summary"],
        "must_not_contain": [],
        "verification": "✅ **Verified"
    }
}

# =========================
# Manual Testing Instructions
# =========================

TESTING_INSTRUCTIONS = """
## Manual Testing Instructions for v9 Intent System

### Setup
1. Open terminal in Code/ directory
2. Run: python oneclick_my_retailchain_v8.2_models_logging.py
3. Wait for "Running on local URL: http://..." message
4. Open browser to the URL shown

### Test 1: Percentage Query ✅
**Query:** "What percentage of June 2024 sales came from Selangor?"

**Expected Output:**
```
## 📊 Sales Percentage Analysis

### Executive Summary
**Selangor represents 16.4% of total June 2024 sales**

### Detailed Breakdown
- **Selangor Sales:** RM 16,421.18
- **Total June 2024 Sales:** RM 99,852.83
- **Percentage:** 16.4%

### Calculation Method
(16,421.18 ÷ 99,852.83) × 100 = 16.4%

✅ **Verified:** Calculated directly from data (100% accurate).
```

**Pass Criteria:**
✅ Shows percentage (16.4%)
✅ Shows both numerator and denominator
✅ Shows calculation method
✅ Does NOT show "Value: RM" format
✅ Verification badge present

---

### Test 2: Comparison Query ✅
**Query:** "Compare June vs May sales"

**Expected Output:**
```
## 📊 Time Comparison - Sales (RM)

### Executive Summary
**June vs May: 📈 Increase of RM X,XXX.XX (X.X%)**

### Comparison Details
| Dimension | Sales (RM) | Transactions |
|-----------|------------|--------------|
| June      | RM XX,XXX  | XXX         |
| May       | RM XX,XXX  | XXX         |
| Difference| RM XX,XXX  | XXX         |

✅ **Verified:** Calculated directly from data (100% accurate).
```

**Pass Criteria:**
✅ Shows both June and May values
✅ Shows difference and % change
✅ Uses comparison table format
✅ Shows direction (📈 or 📉)
✅ Verification badge present

---

### Test 3: Breakdown Query ✅
**Query:** "Top 5 products in Selangor"

**Expected Output:**
```
## 📊 Top 5 Product - Sales (RM)

### Rankings
1. **Burger Classic**: RM XX,XXX.XX (XX.X% of total)
2. **Burger Cheese**: RM XX,XXX.XX (XX.X% of total)
3. **Burger Deluxe**: RM XX,XXX.XX (XX.X% of total)
4. **Fries**: RM XX,XXX.XX (XX.X% of total)
5. **Drinks**: RM XX,XXX.XX (XX.X% of total)

### Summary Statistics
- **Total Sales:** RM XXX,XXX.XX
- **Top 5 Contribution:** RM XXX,XXX.XX (XX% of total)

✅ **Verified:** Calculated directly from data (100% accurate).
```

**Pass Criteria:**
✅ Shows ranked list (1, 2, 3, 4, 5)
✅ Shows product names
✅ Shows sales amounts
✅ Shows percentage of total for each
✅ Verification badge present

---

### Test 4: Semantic Error Detection ⚠️
**Query:** "What percentage of June sales came from Selangor?"
**If system incorrectly returns dollar amount instead of percentage:**

**Expected Output:**
```
⚠️ **Semantic Error**: Query asked for percentage but answer shows dollar amount instead

The answer format doesn't match what you asked for. This may indicate an issue with query understanding.
```

**Pass Criteria:**
✅ Detects semantic mismatch
✅ Shows clear error message
✅ Explains the problem

---

### Test 5: Backward Compatibility ✅
**Query:** "Total sales for June 2024"

**Expected Output:**
```
## ✅ Total Sales (RM)
Month: 2024-06

### Executive Summary
Value: RM 99,852.83

### Evidence Used
- Data Source: Structured Sales KPI
- Rows Analyzed: 805

✅ **Verified:** Calculated directly from data (100% accurate).
```

**Pass Criteria:**
✅ Uses existing format (not broken)
✅ Shows correct total
✅ Verification badge present
✅ All existing features still work

---

## Quick Test Checklist

Test each query type and check off:

**Percentage Queries:**
- [ ] "What percentage of June sales came from Selangor?" - Shows %
- [ ] "What % of May sales were Burger products?" - Shows %
- [ ] Answer format is percentage, NOT dollar amount
- [ ] Calculation method is shown

**Comparison Queries:**
- [ ] "Compare June vs May sales" - Shows both values side-by-side
- [ ] "Compare Selangor vs Penang" - Shows state comparison
- [ ] Difference and % change shown
- [ ] Direction indicator (📈/📉) present

**Breakdown Queries:**
- [ ] "Top 5 products in Selangor" - Shows ranked list
- [ ] "Top 10 products for June" - Shows 10 items
- [ ] Percentages of total shown
- [ ] Summary statistics included

**Semantic Verification:**
- [ ] Percentage query never returns just dollar amount
- [ ] Comparison query never returns single value
- [ ] Breakdown query never returns simple total

**Backward Compatibility:**
- [ ] "Total sales for June" still works
- [ ] Complex range queries still work
- [ ] State comparison queries still work
- [ ] All v8.2 features still functional

---

## Troubleshooting

**Issue:** Query returns old format (Value: RM) for percentage queries
**Solution:** Check parse_query_intent() is detecting 'percentage' intent correctly

**Issue:** Semantic error shown when answer is correct
**Solution:** Check verify_answer_semantics() patterns

**Issue:** App crashes on startup
**Solution:** Check for syntax errors with: python -m py_compile oneclick_my_retailchain_v8.2_models_logging.py

**Issue:** Numbers don't match expected
**Solution:** Check apply_filters_to_dataframe() is filtering correctly

---

## Success Criteria Summary

✅ All percentage queries return percentage format (not dollar)
✅ All comparison queries show side-by-side comparison
✅ All breakdown queries show ranked lists
✅ Semantic verification catches type mismatches
✅ All v8.2 features still work (backward compatible)
✅ No crashes or errors
✅ Performance is acceptable (<2 seconds per query)

"""

if __name__ == "__main__":
    print("=" * 80)
    print("v9 INTENT SYSTEM TEST CASES")
    print("=" * 80)
    print(TESTING_INSTRUCTIONS)
    
    print("\n" + "=" * 80)
    print("QUICK REFERENCE: TEST QUERIES")
    print("=" * 80)
    
    for intent_type, queries in TEST_QUERIES.items():
        print(f"\n{intent_type.upper()} QUERIES:")
        for i, query in enumerate(queries, 1):
            print(f"  {i}. {query}")
    
    print("\n" + "=" * 80)
    print("Copy these queries into the app to test!")
    print("=" * 80)
