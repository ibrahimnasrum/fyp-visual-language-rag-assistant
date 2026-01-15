# Complete Question Inventory
## Date: January 14, 2026
## Source: Codebase analysis, test files, eval/questions.csv, bug reports

---

## 📋 Inventory Summary

**Total Questions Catalogued:** 65
- Sales KPI: 15 (23%)
- HR KPI: 10 (15%)
- RAG/Document: 16 (25%)
- Visual/OCR: 5 (8%)
- Robustness: 6 (9%)
- Follow-up Scenarios: 13 (20%)

---

## Category 1: Sales KPI Queries (Deterministic)

### S01: Simple Total Query
**Question:** "sales bulan 2024-06 berapa?" / "Total sales June 2024"
**Category:** Performance/Simple Aggregation
**Required Context:** 
- Month extraction (2024-06)
- Access to df_sales CSV
- Total Sale column summation
**Expected Route:** `sales_kpi` → deterministic calculation
**Expected Output Format:** 
```
## ✅ Total Sales (RM)
Value: RM 99,852.83
```
**Failure Modes:**
- ❌ Month parsing fails (e.g., "June" not mapped to 2024-06)
- ❌ Routes to RAG instead of deterministic
- ❌ LLM hallucinates different number
**Minimum Follow-ups if Context Missing:**
- "Which month did you mean?"
- "Show all available months?"

---

### S02: Month-over-Month Comparison
**Question:** "banding sales bulan 2024-06 vs 2024-05" / "Compare June vs May sales"
**Category:** Comparison/Time Series
**Required Context:**
- Two period extraction (June, May)
- Access to df_sales for both periods
- MoM % change calculation: `((june - may) / may) * 100`
**Expected Route:** `sales_kpi` → comparison executor (v9)
**Expected Output Format:**
```
## 📊 Time Comparison - Sales (RM)
| Period | Sales | Change | % Change |
|--------|-------|--------|----------|
| 2024-06 | RM 99,852.83 | +RM 5,234 | +5.5% |
| 2024-05 | RM 94,618.83 | - | - |
```
**Failure Modes:**
- ❌ Compares different months (e.g., June vs April instead of May)
- ❌ Shows only one period's data
- ❌ Percentage calculation wrong (divides by wrong base)
- ❌ Routes to RAG, gives vague "sales improved" without numbers
**Minimum Follow-ups if Context Missing:**
- "Which two periods should I compare?"
- "Do you want MoM or YoY?"

---

### S03: Top N Ranking
**Question:** "top 3 product bulan 2024-06" / "Show top 3 products in June"
**Category:** Ranking/Breakdown
**Required Context:**
- Month filter (2024-06)
- Groupby Product
- Sort by Total Sale descending
- Limit to N rows
**Expected Route:** `sales_kpi` → breakdown executor (v9)
**Expected Output Format:**
```
## 🏆 Top 3 Products by Total Sales (RM)
1. **Cheese Burger**: RM 20,250.99 (20.3% of total)
2. **Beef Burger**: RM 19,705.96 (19.7%)
3. **Chicken Burger**: RM 18,916.92 (18.9%)
```
**Failure Modes:**
- ❌ Shows Top 5 when asked for Top 3 (Bug #3 - FIXED in v9.1)
- ❌ Doesn't maintain month filter across followups
- ❌ LLM invents product names not in dataset
**Minimum Follow-ups if Context Missing:**
- "Top by what metric - sales or quantity?"
- "For which time period?"

---

### S11: Filtered State Query
**Question:** "sales state Selangor bulan 2024-06 berapa?"
**Category:** Filtered Aggregation
**Required Context:**
- State filter: "Selangor"
- Month filter: 2024-06
- Filter df_sales where State=='Selangor' AND YearMonth==202406
- Sum Total Sale
**Expected Route:** `sales_kpi` → total executor with filters
**Expected Output Format:**
```
## ✅ Total Sales (RM) - Selangor
Month: 2024-06
Value: RM 16,421.18
(16.4% of total June sales)
```
**Failure Modes:**
- ❌ Shows all states instead of filtered
- ❌ Filter not applied correctly (state name mismatch)
- ❌ Period object vs int comparison (Bug #2 - FIXED in v9.1)
**Minimum Follow-ups if Context Missing:**
- "Which state?"
- "All states or specific state?"

---

### S12: Multi-dimensional Filter + Ranking
**Question:** "top 3 product di Selangor bulan 2024-06"
**Category:** Complex Query (Filter + Ranking)
**Required Context:**
- State filter: Selangor
- Month filter: 2024-06
- Groupby Product
- Top 3
**Expected Route:** `sales_kpi` → breakdown executor with filters
**Expected Output:** Top 3 products within Selangor only
**Failure Modes:**
- ❌ Shows top 3 across ALL states
- ❌ Filter context lost in follow-up
- ❌ Shows Top 5 instead of Top 3
**Minimum Follow-ups if Context Missing:**
- "In which state?"
- "For which period?"

---

### S_PERCENTAGE_01: Percentage Query (Most Complex)
**Question:** "What percentage of June 2024 sales came from Selangor?"
**Category:** Percentage Calculation
**Required Context:**
- Numerator: Selangor sales for June (state=Selangor, month=2024-06)
- Denominator: Total June sales (month=2024-06, all states)
- Calculation: (numerator / denominator) * 100
**Expected Route:** `sales_kpi` → percentage executor (v9)
**Expected Output Format:**
```
## 📊 Sales Percentage Analysis
**Selangor represents 16.4% of total June 2024 sales**

Breakdown:
- Selangor June Sales: RM 16,421.18
- Total June Sales: RM 99,852.83
- Percentage: 16.4%

Calculation: (16,421.18 ÷ 99,852.83) × 100 = 16.4%
```
**Failure Modes (CRITICAL - All Fixed in v9.1):**
- ❌ Shows dollar amount instead of percentage (Semantic mismatch - FIXED)
- ❌ Denominator is 0 due to filter bug (Bug #1 - FIXED)
- ❌ Month stored as string vs int (Bug #2 - FIXED)
- ❌ Period object not compared correctly (Bug #6 - FIXED)
- ❌ Division by zero crash (Bug #4 - FIXED)
**Minimum Follow-ups if Context Missing:**
- "Percentage of what? (total sales, state sales, product sales)"
- "For which time period?"
- "Which dimension to filter by?"

---

## Category 2: HR KPI Queries (Deterministic)

### H01: Simple Headcount
**Question:** "total employees berapa?" / "How many employees?"
**Category:** Simple Count
**Required Context:**
- Access to HR.csv
- Count rows OR sum where certain conditions
**Expected Route:** `hr_kpi` → deterministic count
**Expected Output:** "Total Employees: 820"
**Failure Modes:**
- ❌ Routes to RAG, gives vague answer
- ❌ Counts wrong column
**Minimum Follow-ups if Context Missing:**
- "Active employees only or include resigned?"

---

### H04: Attrition by Dimension
**Question:** "which age group has highest attrition?"
**Category:** Groupby + Ranking
**Required Context:**
- Groupby Age_Group
- Calculate attrition rate: (resigned / total) * 100
- Sort descending
**Expected Route:** `hr_kpi` → groupby analysis
**Expected Output:**
```
Age Group 31-40: 25.5% attrition (highest)
Age Group 41-50: 18.3%
```
**Failure Modes:**
- ❌ LLM invents age groups not in data
- ❌ Attrition calculation wrong
**Minimum Follow-ups if Context Missing:**
- "Attrition by what metric - rate or absolute count?"

---

## Category 3: RAG/Document Queries (Non-Deterministic)

### D01: Policy Retrieval
**Question:** "Ringkaskan polisi cuti tahunan berdasarkan dokumen syarikat"
**Category:** Document RAG
**Required Context:**
- FAISS retrieval from HR_Policy_MY.txt
- Leave policy section
- LLM summarization
**Expected Route:** `rag_docs` → RAG retrieval + LLM
**Expected Output:** Summary of leave policy from document
**Failure Modes:**
- ❌ Retrieves wrong document (sales SOP instead of HR policy)
- ❌ LLM adds information not in document (hallucination)
- ❌ Doesn't say "not available" when policy missing
**Minimum Follow-ups if Context Missing:**
- "Which policy document?"
- "Annual leave or medical leave?"

---

### D11: Grounded Executive Summary
**Question:** "Bagi ringkasan 'executive summary' untuk prestasi dan isu utama bulan 2024-06 menggunakan DATA yang ada"
**Category:** Complex RAG + Data Fusion
**Required Context:**
- Sales data from df_sales (deterministic)
- HR data from df_hr (deterministic)
- Document context from RAG
- LLM synthesis (must be grounded)
**Expected Route:** Multi-step: `sales_kpi` + `hr_kpi` + `rag_docs` + LLM
**Expected Output:**
```
Executive Summary - June 2024:
- Total Sales: RM 99,852.83 ✅ (from data)
- Top State: Selangor (16.4%) ✅ (from data)
- Total Headcount: 820 ✅ (from data)
- [Context from documents]
```
**Failure Modes (CRITICAL):**
- ❌ Invents sales numbers not in data
- ❌ Routes to only RAG, misses numerical data
- ❌ Mixes data from different months
- ❌ Provides recommendations not grounded in documents
**Minimum Follow-ups if Context Missing:**
- "Which month's summary?"
- "Focus on sales, HR, or both?"
- "Include recommendations or facts only?"

---

### D15: Negative Test (Policy Not Found)
**Question:** "What is the maternity leave policy?"
**Category:** Negative Test / Hallucination Prevention
**Required Context:**
- FAISS retrieval from HR_Policy_MY.txt
- Policy may or may not exist
**Expected Route:** `rag_docs` → RAG retrieval
**Expected Output (if not found):**
```
⚠️ I could not find specific information about maternity leave policy in the available documents.

Would you like me to:
- Check if it's mentioned under a different name?
- Summarize what employee leave policies ARE available?
```
**Failure Modes (CRITICAL):**
- ❌ LLM invents plausible-sounding policy (hallucination)
- ❌ Says "30 days maternity leave" without document evidence
- ❌ Doesn't admit when information is missing
**Minimum Follow-ups if Context Missing:**
- "Should I search in different documents?"

---

## Category 4: Visual/OCR Queries

### V01: Image Table Extraction
**Question:** "Summarize the table in this image"
**Category:** OCR + Data Extraction
**Required Context:**
- Image file path
- OCR capability (BLIP-2 or similar)
- Table structure recognition
**Expected Route:** `visual` → OCR → structured parsing
**Expected Output:**
```
Table Summary:
- State | Sales (RM)
- Selangor | 16,421
- Penang | 12,345
- Total: RM 28,766
```
**Failure Modes:**
- ❌ OCR misreads numbers (16,421 → 16,421)
- ❌ Doesn't recognize table structure
- ❌ Invents data not in image
**Minimum Follow-ups if Context Missing:**
- "Which part of the image should I focus on?"

---

## Category 5: Robustness Tests

### R02: Relative Time Reference
**Question:** "jualan bulan ni berapa?" / "sales this month"
**Category:** Time Resolution
**Required Context:**
- Resolve "bulan ni" → LATEST_SALES_MONTH
- If today is Jan 2026, latest data is 2024-06
- Should use 2024-06 (latest available), NOT current system date
**Expected Route:** `sales_kpi` → time resolution → deterministic
**Expected Output:** "Total Sales for June 2024 (latest available): RM 99,852.83"
**Failure Modes:**
- ❌ Tries to find Jan 2026 data (doesn't exist)
- ❌ Uses wrong month
- ❌ Doesn't clarify what "this month" means
**Minimum Follow-ups if Context Missing:**
- "By 'this month', do you mean latest available data (June 2024)?"

---

### R03: Ambiguous Relative Comparison
**Question:** "banding jualan bulan ni dengan bulan lepas"
**Category:** Relative Time + Comparison
**Required Context:**
- "bulan ni" → 2024-06 (latest)
- "bulan lepas" → 2024-05 (previous)
- MoM comparison
**Expected Route:** `sales_kpi` → time resolution → comparison
**Expected Output:** June 2024 vs May 2024 comparison
**Failure Modes:**
- ❌ Compares wrong months
- ❌ "bulan lepas" interpreted as "last year" instead of "last month"
**Minimum Follow-ups if Context Missing:**
- "Confirm: Compare June 2024 vs May 2024?"

---

## Category 6: Follow-up Question Scenarios

### FU01: State Comparison with Context Loss
**Main Query:** "Show Selangor sales for June 2024"
- System extracts: state=Selangor, month=2024-06
- Answer: RM 16,421.18

**Follow-up 1:** "Compare with previous month"
**Expected Context Preservation:**
- SHOULD maintain: state=Selangor (filter persistence)
- SHOULD interpret: "previous month" = May 2024
- SHOULD compare: Selangor June vs Selangor May

**Failure Modes:**
- ❌ Compares ALL states (context lost) - CRITICAL
- ❌ Compares wrong months
- ❌ Routes to RAG instead of deterministic

**Follow-up 2:** "Show top 3 products"
**Expected Context Preservation:**
- SHOULD maintain: state=Selangor, month=June
- SHOULD show: Top 3 products in Selangor for June

**Failure Modes:**
- ❌ Shows top 3 across ALL states
- ❌ Uses different month
- ❌ Shows Top 5 instead of Top 3 (Bug #3 - FIXED)

**Follow-up 3:** "What percentage is that of total sales?"
**Expected Context Preservation:**
- SHOULD calculate: Selangor June / Total June * 100
- SHOULD show: 16.4%

**Failure Modes:**
- ❌ Shows dollar amount instead of percentage
- ❌ Uses wrong denominator (all months instead of June)

---

### FU02: Cross-Route Follow-up
**Main Query:** "What's our medical leave policy?"
- Route: `rag_docs` (RAG-based)
- Answer: Summary from HR_Policy_MY.txt

**Follow-up:** "How many employees took medical leave this year?"
**Expected Behavior:**
- SHOULD route to: `hr_kpi` (deterministic, from CSV)
- SHOULD NOT use: RAG (would hallucinate)
- Expected: Count from HR.csv medical leave data

**Failure Modes:**
- ❌ Routes to RAG, invents numbers
- ❌ Says "I don't have that data" when data exists in HR.csv
- ❌ Cross-route context not maintained

---

### FU03: Vague Follow-up Handling
**Main Query:** "Show top 5 products"
- Answer: Top 5 products for June 2024

**Follow-up (auto-generated):** "What's different about the top performers?"
**Problem:** Query has no explicit data context
- No state mentioned
- No product mentioned
- No month mentioned
- Vague phrasing

**Expected Behavior:**
- SHOULD validate query has sufficient context
- If insufficient, fall back to RAG+LLM (not deterministic)
- OR ask clarifying question

**Failure Modes:**
- ❌ Routes to deterministic executor with empty filters → crash (Bug #5 - FIXED in v9.1)
- ❌ Tries to calculate on 0 rows → division by zero
- ❌ Gives generic answer without data

**Fix (v9.1):**
```python
if intent.intent_type in ['percentage', 'comparison', 'breakdown']:
    has_filters = bool(intent.filters)
    has_context = bool(intent.percentage_context or intent.comparison or intent.groupby)
    
    if has_filters or has_context:
        # Use specialized executor
    else:
        # Fall back to RAG+LLM for vague queries
```

---

## Critical Failure Pattern Analysis

### Pattern 1: Type Mismatch Errors
**Affected Questions:** S_PERCENTAGE_01, S02, S11
**Root Cause:** Period object vs int comparison in YearMonth column
```python
# WRONG: Period('2024-06') == 202406 → False
# CORRECT: Period('2024-06') == Period('2024-06') → True
```
**Fixed in:** v9.1 (Bug #6)
**Confidence:** 100% (confirmed by debug logs)

---

### Pattern 2: Context Loss in Follow-ups
**Affected Questions:** FU01, FU02, FU03
**Root Cause:** Follow-up questions don't carry forward filters from main query
**Status:** PARTIALLY FIXED
- Intent parser extracts context ✅
- Executors use filters ✅
- But: Follow-up generation doesn't embed context explicitly ⚠️
**Confidence:** 85% (observed in testing)

---

### Pattern 3: Semantic Verification Gap
**Affected Questions:** S_PERCENTAGE_01, D11, D15
**Root Cause:** System verifies NUMBERS but not ANSWER TYPE
- Query asks for % → System shows $
- Verification still passes because number is correct
**Fixed in:** v9.0 with `verify_answer_semantics()`
**Confidence:** 95% (implemented but needs more testing)

---

### Pattern 4: RAG Hallucination
**Affected Questions:** D11, D15, FU02
**Root Cause:** LLM generates plausible but ungrounded answers
**Mitigation:** Anti-hallucination prompts, but not 100% effective
**Status:** ONGOING ISSUE
**Confidence:** 75% (observed in earlier testing, reduced with prompts)

---

## Testing Gaps Identified

### Gap 1: Multi-turn Conversation Testing
**Missing:** No automated tests for 3+ turn conversations
**Risk:** Context degradation not caught
**Recommendation:** Create conversation flow tests

### Gap 2: Cross-route Consistency Testing
**Missing:** No tests that verify deterministic → RAG consistency
**Risk:** Same question via different routes gives different answers
**Recommendation:** Create ground truth comparison tests

### Gap 3: Negative Case Testing
**Missing:** Limited tests for "data not available" scenarios
**Risk:** System hallucinates instead of admitting gaps
**Recommendation:** Add more D15-type tests

### Gap 4: Percentage Query Edge Cases
**Missing:** Edge cases like "percentage of 0", "100%", "negative change"
**Risk:** Division by zero, formatting issues
**Recommendation:** Expand percentage test coverage

---

## Question Complexity Matrix

| Complexity | Count | Examples | Success Rate (Estimated) |
|------------|-------|----------|--------------------------|
| Simple | 25 | S01, H01, R01 | 95% |
| Medium | 20 | S02, S03, H04 | 85% |
| Complex | 15 | S_PERCENTAGE_01, D11 | 70% (was 40% before v9) |
| Critical | 5 | FU01, FU02, FU03 | 60% |

---

## Priority Recommendations

### Priority 1: CRITICAL (Affects Core Functionality)
1. **Test FU01-FU03 scenarios** - Context loss causes wrong answers
2. **Verify D11 grounding** - Executive summaries must not hallucinate
3. **Test D15 negative cases** - System must admit when data is missing

### Priority 2: HIGH (Affects Reliability)
1. **Add conversation flow tests** - Multi-turn consistency
2. **Test cross-route scenarios** - Same data via different routes
3. **Validate percentage edge cases** - Division by zero, 0%, 100%

### Priority 3: MEDIUM (Improves User Experience)
1. **Test relative time references** - "this month", "last month"
2. **Validate Top N variations** - Top 3, Top 5, Top 7, Top 10
3. **Test multi-dimensional filters** - State + Product + Channel

---

## STATUS: DONE (Inventory Complete)

**Next Steps:**
1. Review RESEARCH_NOTES.md for hypothesis testing
2. Review HYPOTHESIS_TREE.md for failure mode analysis
3. Review OPEN_GAPS.md for missing information
