# FYP Test Queries - Manual Testing Guide

This document contains all test queries used in the evaluation framework for manual testing.

---

## 📋 CATEGORY 1: Time Sensitivity Classification (10 queries)

### Static Queries (Should NOT be time-sensitive)

**Test 1:** What products are available?
- **Expected:** Classification = "static", Time-sensitive = False
- **Purpose:** Tests if system recognizes static information queries

**Test 2:** List all states
- **Expected:** Classification = "static", Time-sensitive = False
- **Purpose:** Tests state listing query

**Test 3:** Show me all branches
- **Expected:** Classification = "static", Time-sensitive = False
- **Purpose:** Tests branch listing query

---

### Dynamic Queries WITH Timeframe (Should NOT need clarification)

**Test 4:** Total revenue in January 2024
- **Expected:** Classification = "dynamic", Time-sensitive = True, Has timeframe
- **Purpose:** Tests month name detection

**Test 5:** Sales in 2024-01
- **Expected:** Classification = "dynamic", Time-sensitive = True, Has timeframe
- **Purpose:** Tests numeric date format detection

**Test 6:** Revenue for H1 2024
- **Expected:** Classification = "dynamic", Time-sensitive = True, Has timeframe
- **Purpose:** Tests half-year period detection

---

### Dynamic Queries WITHOUT Timeframe (NEEDS clarification)

**Test 7:** What is the total revenue?
- **Expected:** Classification = "dynamic", Time-sensitive = True, Needs clarification
- **Purpose:** Tests revenue query without month (should ask for timeframe)

**Test 8:** Show me sales performance
- **Expected:** Classification = "dynamic", Time-sensitive = True, Needs clarification
- **Purpose:** Tests performance query without timeframe

**Test 9:** Top 5 products
- **Expected:** Classification = "hybrid", Time-sensitive = True, Needs clarification
- **Purpose:** Tests ranking query (hybrid because could be overall or time-bound)

**Test 10:** Total transactions
- **Expected:** Classification = "dynamic", Time-sensitive = True, Needs clarification
- **Purpose:** Tests transaction query without timeframe

---

## 📋 CATEGORY 2: Data Availability Validation (10 queries)

### Available Months (Should PASS)

**Test 11:** 2024-01
- **Expected:** Available = True, Message contains "Data available"
- **Purpose:** Tests valid month in YYYY-MM format

**Test 12:** 2024-02
- **Expected:** Available = True, Message contains "Data available"
- **Purpose:** Tests second valid month

**Test 13:** January 2024
- **Expected:** Available = True, Message contains "Data available"
- **Purpose:** Tests month name format

---

### Unavailable Months (Should FAIL with helpful message)

**Test 14:** 2023-12
- **Expected:** Available = False, Message suggests "Data not available"
- **Purpose:** Tests month before data range (should suggest alternatives)

**Test 15:** 2024-07
- **Expected:** Available = False, Message suggests "Data not available"
- **Purpose:** Tests month after data range

**Test 16:** December 2023
- **Expected:** Available = False, Message suggests "Data not available"
- **Purpose:** Tests unavailable month in name format

---

### Special Cases

**Test 17:** (No month specified)
- **Expected:** Available = True, Message "Using all available data"
- **Purpose:** Tests default behavior when no timeframe given

**Test 18:** invalid-month
- **Expected:** Available = False, Message "Could not parse"
- **Purpose:** Tests invalid format handling

**Test 19:** xyz
- **Expected:** Available = False, Message "Could not parse"
- **Purpose:** Tests garbage input handling

**Test 20:** 2024-13
- **Expected:** Available = False, Message "Could not parse"
- **Purpose:** Tests invalid month number (13th month doesn't exist)

---

## 📋 CATEGORY 3: Integrated System Queries (Real Usage)

### Queries to Test in Main System (v8.2)

**Test 21:** What is total revenue?
- **Expected System Response:** "📅 This query requires a time period. Available data: 2024-01, 2024-02, 2024-03..."
- **Purpose:** System should ask for clarification

**Test 22:** Revenue in December 2023
- **Expected System Response:** "❌ Data not available for 2023-12. Available months: 2024-01... Did you mean 2024-01?"
- **Purpose:** System should provide helpful error with suggestions

**Test 23:** Revenue in January 2024
- **Expected System Response:** [Actual revenue number for January 2024]
- **Purpose:** Valid query should return correct answer

**Test 24:** Revenue for Selangor in January 2024
- **Expected System Response:** [Revenue for Selangor in Jan 2024]
- **Purpose:** Filter + timeframe query
- **Cache Note:** First time = MISS, repeat should = HIT

**Test 25:** Revenue for Selangor in January 2024 (REPEAT)
- **Expected System Response:** [Same as Test 24]
- **Purpose:** Test cache hit (should be faster, check cache stats)

**Test 26:** What is the revenue for Penang in February 2024?
- **Expected System Response:** [Revenue for Penang in Feb 2024]
- **Purpose:** Different state + different month = new cache entry

**Test 27:** Top 5 products by revenue in Q1 2024
- **Expected System Response:** [List of top 5 products with revenue for Jan-Mar 2024]
- **Purpose:** Range query with ranking

**Test 28:** Compare Selangor vs Penang revenue in March 2024
- **Expected System Response:** [Comparison table or statement]
- **Purpose:** Comparison query with explicit timeframe

**Test 29:** Show breakdown by channel in April 2024
- **Expected System Response:** [Revenue by channel for April 2024]
- **Purpose:** Breakdown/grouping query

**Test 30:** What products are sold in Selangor?
- **Expected System Response:** [List of products available in Selangor]
- **Purpose:** Static query (no timeframe needed)

---

## 🧪 How to Test Manually

### Method 1: Test Individual Modules

```python
cd Code
python

# Test Time Classifier
from query.time_classifier import TimeClassifier
tc = TimeClassifier()

# Try each query from Category 1
result = tc.classify("What is the total revenue?")
print(result)
# Expected: {'is_time_sensitive': True, 'needs_clarification': True, ...}

# Test Data Validator
from query.validator import DataValidator
dv = DataValidator("../data/MY_Retail_Sales_2024H1.csv")

# Try each query from Category 2
result = dv.validate("2024-01")
print(result)
# Expected: {'available': True, 'message': 'Data available for 2024-01', ...}

result = dv.validate("2023-12")
print(result)
# Expected: {'available': False, 'message': 'Data not available...', 'suggestion': ...}
```

---

### Method 2: Test Integrated System

```bash
cd Code
python oneclick_my_retailchain_v8.2_models_logging.py
```

Then in the Gradio interface, try queries from Category 3 (Tests 21-30).

**Watch for:**
- 📅 Clarification requests (for queries without timeframe)
- ❌ Error messages with suggestions (for unavailable months)
- ✅ Cache HIT/MISS messages in console
- ✅ Correct answers for valid queries

---

### Method 3: Run Automated Evaluation

```bash
cd Code
Run_FYP_Tests.bat

# OR manually:
cd tests
python run_fyp_tests.py
```

This runs all 30 tests automatically and generates `fyp_evaluation_results.json`.

---

## 📊 Expected Results Summary

### Category 1: Time Classification
- **Target Accuracy:** 90-100%
- **Critical Tests:** 
  - Test 7, 8, 10 (should request clarification)
  - Test 4, 5, 6 (should NOT request clarification)

### Category 2: Data Validation
- **Target Accuracy:** 100%
- **Critical Tests:**
  - Test 14, 15, 16 (should provide helpful alternatives)
  - Test 17 (should use all data by default)

### Category 3: Integrated System
- **Expected Behavior:**
  - Clarification requests for ambiguous queries
  - Helpful error messages for unavailable data
  - Cache hits on repeated queries
  - Correct answers for valid queries

---

## 🎯 For Thesis Chapter 5

Use these queries to demonstrate:

1. **Before Enhancement:** Run queries in old v8.2 (if you have backup)
   - Test 21 → Returns ambiguous answer
   - Test 22 → Returns empty/wrong data
   - Test 24 (3x) → No caching, same load time

2. **After Enhancement:** Run queries in new v8.2
   - Test 21 → Clear clarification request
   - Test 22 → Helpful error with suggestions
   - Test 24 (3x) → Cache hits visible, faster responses

3. **Metrics to Record:**
   - Accuracy: Did system respond correctly?
   - Response time: How fast? (especially cache hits)
   - Error rate: How many errors before/after?
   - User experience: Is clarification helpful?

---

## 📸 Screenshots for Thesis

Take screenshots of:
1. Test 21 response (clarification request)
2. Test 22 response (helpful error message)
3. Cache statistics after running Tests 24-25
4. Evaluation results summary (from automated tests)
5. Side-by-side comparison (before/after enhancement)

---

## 💡 Quick Test Script

Copy this to test all queries quickly:

```python
# Quick test script - save as quick_test.py
from query.time_classifier import TimeClassifier
from query.validator import DataValidator

tc = TimeClassifier()
dv = DataValidator("../data/MY_Retail_Sales_2024H1.csv")

# Category 1 queries
queries_cat1 = [
    "What products are available?",
    "What is the total revenue?",
    "Total revenue in January 2024",
]

print("CATEGORY 1: Time Classification")
for q in queries_cat1:
    result = tc.classify(q)
    print(f"Q: {q}")
    print(f"   → {result['classification']}, sensitive={result['is_time_sensitive']}\n")

# Category 2 queries
months_cat2 = ["2024-01", "2023-12", "invalid-month"]

print("\nCATEGORY 2: Data Validation")
for m in months_cat2:
    result = dv.validate(m)
    print(f"Month: {m}")
    print(f"   → Available={result['available']}, Message={result['message']}\n")
```

---

**Ready to test!** Start with Method 1 for quick module tests, then Method 2 for full system demo, and finally Method 3 for complete evaluation.
