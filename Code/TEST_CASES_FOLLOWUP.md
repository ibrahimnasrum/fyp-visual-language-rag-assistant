# Test Cases for Follow-up Quality - EXECUTION LOG

**Date:** January 14, 2026  
**Version:** v8.3 with logging  
**Status:** FIXES IMPLEMENTED (v9.2)

---

## ✅ Test Case 1: Filter Persistence (COMPLETE)

### Results:
- **Bug #1:** Route mismatch (sales_kpi → rag_docs) ✅ CONFIRMED → ✅ FIXED
- **Bug #2:** Filter lost (Selangor not persisted) ✅ CONFIRMED → ✅ FIXED
- **Bug #3:** Month parsing error (January → 2024-06) ✅ CONFIRMED → ✅ FIXED
- **Confidence:** 95%

**Evidence:**
```
Turn 1: State: Selangor, Month: 2024-06 (should be 2024-01)
Turn 2: ROUTE → rag_docs, no filter extraction
```

### Fixes Applied (v9.2):

**Fix #1: Context-Aware Route Detection**
- Enhanced `detect_intent()` to accept `conversation_history`
- If no keywords match, checks previous query for domain context
- If previous was sales-related, stays in sales_kpi route
- If previous was HR-related, stays in hr_kpi route

**Fix #2: Filter Inheritance System**
- Added `CONVERSATION_STATE` global dict to store last_filters
- Enhanced `extract_sales_filters()` to accept `previous_filters` parameter
- Filters now persist across queries unless explicitly overridden
- Logs inherited filters with "→ Inherited X: Y from previous query"

**Fix #3: Proper Month Extraction**
- Fixed `extract_context_from_answer()` to use `extract_month_from_query()`
- Now correctly parses "January 2024" via MONTH_ALIASES
- Falls back to regex only if proper extraction fails

---

## ✅ Test Case 2: Context Loss (COMPLETE)

### Results:
- **Bug #4:** Month context lost in follow-up ✅ CONFIRMED → ✅ FIXED
- **Bug #5:** Top performer identity lost ✅ CONFIRMED → NEEDS FIX
- **Route persistence:** ✅ WORKING (Fix #1 effective)
- **Confidence:** 90%

**Evidence:**
```
Turn 1: Top 5 in January → Extracted context: {'month': '2024-01'}
Turn 2: "Show details for top performer" → Reverted to {'month': '2024-06'}
Answer showed June data instead of January
```

### Fixes Applied (v9.3):

**Fix #4: Month Context Inheritance**
- Enhanced `extract_month_from_query()` to accept `previous_context` parameter
- If query doesn't specify month, inherits from previous context
- Logs: "→ Inherited Month: 2024-01 from previous query"
- Stores month in `CONVERSATION_STATE['last_context']`

**Fix #5 TODO: Top Performer Extraction**
- Need to extract top performer name from answer
- Pass to follow-up query as filter
- Store in CONVERSATION_STATE for reference

---

## ⏳ Test Case 3: Route Mismatch (PENDING)

### Execute:
**Query 1:** `Top 5 products by revenue in January 2024`  
**Query 2:** `Show details for the top performer`

### Watch For:
- 🔀 ROUTE changes
- 🔍 Product filter in Q2 (should have top product name)
- 📝 Extracted context: {top_performer: ???}

### Hypothesis H4.1:
Top performer context will be LOST ❌

---

## ⏳ Test Case 3: Route Mismatch (PENDING)

### Execute:
**Query 1:** `How many employees do we have?`  
**Query 2:** `What about in Penang?`

### Watch For:
- 🔀 ROUTE in Q1: hr_kpi
- 🔀 ROUTE in Q2: should stay hr_kpi, probably switches to rag_docs

### Hypothesis H3.2:
Route will switch incorrectly ❌

---

## ⏳ Test Case 4: Temporal Context (PENDING)

### Execute:
**Query 1:** `Sales in January 2024`  
**Query 2:** `How about February?`

### Watch For:
- 📝 Extracted context Q1: {year: '2024'}
- 📝 Extracted context Q2: {year: ???}

### Hypothesis H4.1:
Year 2024 will be lost ❌

---

## ⏳ Test Case 5: Multi-Entity (PENDING)

### Execute:
**Query 1:** `Samsung sales in Selangor for January 2024`  
**Query 2:** `Compare with Penang`

### Watch For:
- 🔍 FILTER Q1: State, Product, Month
- 🔍 FILTER Q2: State (switched), Product (???), Month (???)

### Hypothesis H4.1:
Product & Month will be lost ❌

---

## 📊 Progress

- [x] Test Case 1: Filter Persistence - 3 bugs found
- [ ] Test Case 2: Context Loss
- [ ] Test Case 3: Route Mismatch
- [ ] Test Case 4: Temporal Context
- [ ] Test Case 5: Multi-Entity

**Next:** Execute Test Case 2-5, paste logs after each

---

## Original Test Case Archive

## Test Case 1: State Comparison Consistency

### Main Query
**User:** "Show Selangor sales for June 2024"
**Expected Route:** `sales_kpi` (deterministic)
**Expected Answer:** Exact RM value from CSV

### Follow-up 1
**Generated:** "Compare 2024-06 with previous month"
**Expected Route:** `sales_kpi` (deterministic)
**Expected:** Should use SAME filtering (Selangor only)
**Actual Risk:** May compare ALL states (context lost)

### Follow-up 2
**Generated:** "Show top 3 products in Selangor"
**Expected Route:** `sales_kpi` (deterministic)
**Expected:** Filter to Selangor + June + top 3 products
**Actual Risk:** May show all months or all states

### Verification Method
```python
# Ground truth from pandas
df_sales[(df_sales['State']=='Selangor') & (df_sales['YearMonth']==202406)]['Total Sale'].sum()

# Compare with system answer
# If mismatch > 1%, FAILED
```

---

## Test Case 2: Cross-Route Consistency

### Main Query
**User:** "What's our medical leave policy?"
**Expected Route:** `rag_docs` (RAG-based)
**Expected Answer:** From HR_Policy_MY.txt

### Follow-up 1
**Generated:** "How many employees took medical leave this year?"
**Expected Route:** `hr_kpi` (deterministic)
**Expected:** Count from HR.csv
**Actual Risk:** Routes to RAG, gives vague answer without data

### Follow-up 2
**Generated:** "Show medical leave by department"
**Expected Route:** `hr_kpi` (deterministic)
**Expected:** Grouped data from HR.csv
**Actual Risk:** RAG hallucinates numbers

### Verification Method
```python
# Check routing
assert detect_intent(follow_up_1) == "hr_kpi"

# Check data source
assert answer_contains_csv_data(response)
assert not is_hallucinated(response)
```

---

## Test Case 3: Context Persistence

### Conversation Flow
1. **User:** "Show KL sales"
   - System extracts: state=KL
   - Answer: RM 380,000

2. **User clicks follow-up:** "Show top products in KL"
   - Should maintain: state=KL, use same month as query 1
   - Expected: Top products for KL only
   - Risk: Shows top products for ALL states

3. **User clicks follow-up:** "Compare with Selangor"
   - Should maintain: month from query 1
   - Expected: KL vs Selangor for same period
   - Risk: Uses different months or all data

### Verification Method
```python
# Check if follow-up maintains filters
context1 = extract_context_from_answer(answer1, query1)
context2 = extract_context_from_answer(answer2, query2)

assert context2.get('state') == context1.get('state')  # State should persist
assert context2.get('month') == context1.get('month')  # Month should persist
```

---

## Test Case 4: Numerical Accuracy

### Main Query
**User:** "Total sales June 2024"
**Ground Truth:** `df_sales[df_sales['YearMonth']==202406]['Total Sale'].sum()`
**Let's say:** RM 2,456,789.50

### Follow-up 1
**Generated:** "Break down by state"
**Expected:** Sum of states should equal RM 2,456,789.50
**Verification:** `sum(state_totals) == main_total`

### Follow-up 2
**Generated:** "Show Selangor portion"
**Expected:** Should be subset of RM 2,456,789.50
**Verification:** `selangor_total < main_total`

### Common Failure Modes
- ❌ LLM rounds differently (RM 2.46M vs RM 2,456,789.50)
- ❌ LLM uses different date range
- ❌ LLM hallucinates numbers entirely
- ❌ Sum of parts ≠ whole (due to rounding or data mismatch)

---

## Test Case 5: Ambiguous Follow-up Handling

### Main Query
**User:** "Show me sales performance"
**System Answer:** (vague - all states, all months?)

### Follow-up (Auto-generated)
**Generated:** "What's driving performance?"
**Problem:** Which performance? Which state? Which month?
**Expected:** Should ask for clarification OR use latest month + all states
**Actual Risk:** Gives generic answer or hallucinates

### Better Follow-up
**Should Generate:** "What's driving June 2024 performance across all states?"
**Specific, executable, less ambiguous**

---

## Test Matrix

| Test Case | Main Route | Follow Route | Context Maintained? | Data Consistent? | Pass/Fail |
|-----------|-----------|--------------|---------------------|-----------------|-----------|
| TC1: State Filter | sales_kpi | sales_kpi | ? | ? | ❓ |
| TC2: Cross-Route | rag_docs | hr_kpi | ? | ? | ❓ |
| TC3: Context Loss | sales_kpi | sales_kpi | ? | ? | ❓ |
| TC4: Number Match | sales_kpi | sales_kpi | ? | ? | ❓ |
| TC5: Vague Follow | rag_docs | rag_docs | ? | ? | ❓ |

---

## Expected Failure Patterns

Based on code analysis, predicted failures:

1. **Context Loss (High Probability)**
   - Follow-up doesn't carry forward state/month filters
   - Extracted context not passed as parameter
   
2. **Route Mismatch (High Probability)**
   - Main: deterministic → Follow: RAG (or vice versa)
   - Different data sources = inconsistent numbers

3. **Number Hallucination (Medium Probability)**
   - LLM generates plausible but incorrect numbers
   - No verification against ground truth

4. **Ambiguous Follow-ups (Medium Probability)**
   - Generated follow-ups too vague
   - "Compare with last month" - which month is "last"?

5. **Missing Anti-Hallucination (High Probability)**
   - Follow-up answers not verified against CSV
   - No confidence scoring
   - No "I don't know" responses

---

## Recommended Test Execution Order

1. **Quick Smoke Test** (5 min)
   - Run TC1 manually
   - Check if numbers match ground truth
   
2. **Automated Test Suite** (30 min)
   - Create test script for all 5 TCs
   - Compare outputs to pandas calculations
   
3. **User Simulation** (15 min)
   - CEO-like queries: "How's Selangor doing?"
   - Click through 3 levels of follow-ups
   - Check if story remains consistent

4. **Edge Cases** (10 min)
   - Empty results (no data for that month)
   - Invalid follow-ups (nonsensical questions)
   - Very long conversation chains (10+ messages)
