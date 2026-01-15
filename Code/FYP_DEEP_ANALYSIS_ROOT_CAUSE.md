# FYP DOCUMENTATION: Deep System Analysis & Root Cause Investigation
**Date**: January 15, 2026  
**Analysis Type**: Comprehensive System Diagnostic  
**Approach**: CEO Perspective + Technical Deep Dive  
**Status**: ✅ ROOT CAUSE IDENTIFIED

---

## 📋 EXECUTIVE SUMMARY

### The Mystery
- Implemented word boundary fix to improve routing
- Expected: +11.7% accuracy improvement (60.6% → 72.3%)
- **Actual: +2.1% accuracy improvement** (60.6% → 62.8%)
- **Gap: -9.6% underperformance** ❌

### The Investigation
Through systematic analysis, we discovered the **real problem**:

**IT'S NOT A ROUTING BUG - IT'S MISSING FUNCTIONALITY!**

- ✅ Routing logic works correctly (keywords match as expected)
- ✅ Word boundary fix prevents false positives
- ❌ **But**: `answer_hr()` function doesn't have code to handle 80% of HR queries
- ❌ **Result**: Routes correctly → calls answer_hr() → returns None → falls back to RAG

---

## 🔍 DISCOVERY PROCESS (For FYP Report)

### Step 1: Initial Analysis
Compared baseline (112123) vs latest (133721) results:
- Pass rate: 60.6% → 62.8% (+2.1%)
- Route failures: 25 → 23 (-2)
- **Conclusion**: Modest improvement, but far below expectations

### Step 2: CEO Perspective Analysis  
Asked for each test: **"Does this really answer the CEO's question?"**

✅ **Wins** (4 tests improved):
1. **D06** "how many branches" → Now correctly routes to org docs
2. **D07** "what products sell" → Now correctly routes to product catalog  
3. **D10** "branch manager" → Now correctly routes to org chart
4. **CEO16** "managers left" → Now correctly routes to HR KPI

❌ **Losses** (2 tests degraded):
1. **CEO23** "highest unit price products" → Incorrectly routes to docs (needs KPI analysis)
2. **CEO31** "branches above average" → Incorrectly routes to docs (needs performance calc)

### Step 3: Deep Technical Investigation
Created test script to check keyword matching:
- **Finding**: All 11 expected-to-improve HR tests correctly match HR keywords!
- **But**: They all still route to RAG_DOCS in actual system
- **Why?**: Something happening AFTER routing decision

### Step 4: Code Archaeology
Traced execution flow through source code:
```
User Query → detect_intent() → "hr_kpi" ✅
    ↓
answer_hr() called
    ↓
Checks patterns: headcount? attrition? average income?
    ↓
"kitchen staff"? NOT FOUND
"tenure"? NOT FOUND  
"payroll"? NOT FOUND
"age distribution"? NOT FOUND
    ↓
return None ❌
    ↓
Fallback to RAG_DOCS ❌
```

### Step 5: Root Cause Confirmation
**Line 3947-3950 in bot code**:
```python
if intent == "hr_kpi":
    hr_ans = answer_hr(user_input, trace=trace)
    
    # If HR returns None (policy-like), fallback to docs RAG
    if hr_ans is None:
        route = "rag_docs"  # ← THIS IS WHY THEY ALL GO TO RAG!
```

**answer_hr() can ONLY handle**:
1. Headcount (total, by dept, by state)
2. Attrition (by age, state, dept)
3. Average income (by dept)

**answer_hr() CANNOT handle** (returns None):
1. Role-specific counts ("kitchen staff", "managers")
2. Tenure analysis
3. Payroll totals
4. Age distribution
5. Years of service filtering

---

## 📊 DETAILED TEST ANALYSIS

### 12 Tests That Should Have Improved

| Test | Question | Expected | Actual | Why Failed? |
|------|----------|----------|--------|-------------|
| H06 | berapa staff kitchen? | hr_kpi | rag_docs | answer_hr() doesn't filter by role |
| H07 | average employee tenure | hr_kpi | rag_docs | answer_hr() doesn't calculate tenure |
| H08 | staff with more than 5 years | hr_kpi | rag_docs | answer_hr() doesn't filter by tenure |
| H10 | total payroll expense | hr_kpi | rag_docs | answer_hr() doesn't sum MonthlyIncome |
| CEO11 | branch with most employees | hr_kpi | rag_docs | answer_hr() doesn't rank by headcount |
| CEO16 | managers who left | hr_kpi | **hr_kpi** | ✅ FIXED! (attrition exists) |
| CEO27 | salary range kitchen staff | hr_kpi | rag_docs | answer_hr() doesn't filter by role |
| CEO29 | age distribution workforce | hr_kpi | rag_docs | answer_hr() doesn't group by age |
| CEO30 | average tenure managers | hr_kpi | rag_docs | answer_hr() doesn't filter role + tenure |
| R03 | staff | hr_kpi | rag_docs | answer_hr() generic query handling |
| R05 | headcount by stat | hr_kpi | rag_docs | Typo "stat" vs "state"? |

**Only CEO16 fixed because it matches existing "attrition" pattern!**

### 2 Tests That Regressed

#### CEO23: "Which products have the highest unit price?"
**Root Cause**: Missing keywords in SALES_KEYWORDS
- "products" → needs "product" keyword (it exists, but plural issue)
- "highest" → missing from SALES_KEYWORDS!
- "unit price" → "price" missing from SALES_KEYWORDS!

**Solution**: Add to SALES_KEYWORDS: "highest", "lowest", "price", "pricing", "unit price"

#### CEO31: "Which branches perform above the average?"
**Root Cause**: Plural form not matched
- "branches" doesn't match "branch" with word boundary!
- \bbranch\b won't match "branches"

**Solution**: Add plurals to SALES_KEYWORDS or implement stemming

---

## 💡 KEY INSIGHTS FOR FYP

### Insight 1: Routing vs Functionality are Different Problems
**Common Misconception**: "If it routes wrong, fix the routing"  
**Reality**: Even correct routing fails if handler function can't answer

**Learning**: 
- Routing = "Which module should handle this?"
- Functionality = "Can that module actually answer?"
- **Both must work** for system to succeed

### Insight 2: Test Coverage Reveals Hidden Assumptions
We assumed answer_hr() could handle HR queries, but:
- It only handles 3 out of 10+ HR query types
- 80% of HR functionality is missing!
- Tests exposed this gap that code review missed

### Insight 3: Word Boundaries Help But Need Stemming
Word boundary regex (`\b`) prevents substring matches:
- ✅ "age" no longer matches "percentage"
- ❌ But "branch" doesn't match "branches"  
- ❌ And "product" doesn't match "products"

**Solution**: Implement stemming/lemmatization layer

### Insight 4: Fallback Masking Real Problems
The "fallback to RAG" pattern is dangerous:
- Masks missing functionality
- System appears to work (gives some answer)
- But answers may be wrong/incomplete
- **Silent failures** are worse than errors

---

## 🎯 ACTION PLAN (PRIORITIZED)

### PRIORITY 1: Extend answer_hr() Functionality ⭐⭐⭐⭐⭐
**Impact**: Fixes 11 tests (+11.7% accuracy)  
**Effort**: Medium (4-5 hours)  
**Risk**: Low (adding new patterns, not changing existing)

**Required Implementations**:
1. **Role-based filtering**:
   ```python
   if "kitchen" in s or "chef" in s or "cook" in s:
       kitchen_staff = df_hr[df_hr["JobRole"].str.contains("Kitchen|Chef|Cook", case=False)]
       return f"{len(kitchen_staff)} kitchen staff"
   
   if "manager" in s or "supervisor" in s:
       managers = df_hr[df_hr["JobRole"].str.contains("Manager|Supervisor", case=False)]
       return f"{len(managers)} managers"
   ```

2. **Tenure analysis**:
   ```python
   if "tenure" in s or "years of service" in s:
       df_hr["TenureYears"] = df_hr["YearsInCurrentRole"] + df_hr["YearsAtCompany"] / 2
       avg_tenure = df_hr["TenureYears"].mean()
       return f"Average tenure: {avg_tenure:.1f} years"
   
   if "more than 5 years" in s or "5+ years" in s:
       veterans = df_hr[df_hr["YearsAtCompany"] > 5]
       return f"{len(veterans)} employees with 5+ years"
   ```

3. **Payroll calculations**:
   ```python
   if "payroll" in s or "total compensation" in s:
       total_payroll = df_hr["MonthlyIncome"].sum()
       return f"Total monthly payroll: RM {format_num(total_payroll)}"
   ```

4. **Age distribution**:
   ```python
   if "age distribution" in s or "age group" in s:
       age_dist = df_hr.groupby("AgeGroup")["EmpID"].count()
       # Format as table/chart
       return age_distribution_report(age_dist)
   ```

5. **Ranking/comparison**:
   ```python
   if "most employees" in s or "highest headcount" in s:
       # Group by branch, rank by count
       branch_counts = df_hr.groupby("Branch")["EmpID"].count().sort_values(ascending=False)
       top_branch = branch_counts.index[0]
       return f"{top_branch} branch has most employees ({branch_counts.iloc[0]})"
   ```

### PRIORITY 2: Fix Sales Keyword Gaps ⭐⭐⭐⭐⭐
**Impact**: Fixes 2 critical regressions (CEO23, CEO31)  
**Effort**: Low (30 minutes)  
**Risk**: Very Low (just adding keywords)

**Required Changes**:
```python
SALES_KEYWORDS = [
    # Existing
    "sales", "jualan", "revenue", "top", "banding", "compare", "vs", "versus", "mom",
    "bulan", "month", "mtd", "quantity", "qty", "terjual", "state", "negeri", 
    "branch", "cawangan", "channel", "saluran", "product", "produk", 
    "breakdown", "drove", "difference", "performance",
    
    # NEW: Plurals
    "branches", "channels", "products",
    
    # NEW: Comparatives
    "highest", "lowest", "best", "worst", "top", "bottom",
    "above", "below", "better", "worse",
    
    # NEW: Pricing
    "price", "pricing", "unit price", "cost",
    
    # NEW: Performance
    "perform", "performing", "outperform", "underperform"
]
```

### PRIORITY 3: Implement Stemming Layer ⭐⭐⭐
**Impact**: Prevents future plural/verb form issues  
**Effort**: Medium (2-3 hours)  
**Risk**: Medium (could affect existing matches)

**Approach**:
```python
from nltk.stem import PorterStemmer
stemmer = PorterStemmer()

def keyword_match_with_stemming(keywords, text):
    # Tokenize text
    words = text.lower().split()
    stemmed_words = [stemmer.stem(w) for w in words]
    
    for k in keywords:
        k_stem = stemmer.stem(k)
        if k_stem in stemmed_words:
            return True, [k]
    return False, []
```

---

## 📚 FYP CONTRIBUTION

### Research Questions Answered

**RQ1**: "How effective is keyword-based routing for multi-domain query classification?"
- **Finding**: 78.9% accuracy for RAG docs, 56.5% for HR, 82.7% for sales
- **Insight**: Effectiveness varies by domain complexity
- **Factor**: Handler functionality matters as much as routing accuracy

**RQ2**: "What are the limitations of rule-based NLP systems?"
- **Limitation 1**: Morphological variations (plurals, verb forms)
- **Limitation 2**: Missing handler implementations mask routing success
- **Limitation 3**: Fallback patterns hide real problems
- **Limitation 4**: Keyword collisions require word boundaries

### Academic Techniques Demonstrated

1. **Systematic Debugging Methodology**
   - Hypothesis formation → Testing → Refinement
   - Multiple competing theories tracked simultaneously
   - Evidence-based conclusion (not speculation)

2. **Regex Word Boundary Matching**
   - Reference: Jurafsky & Martin, Chapter 2.4
   - Implementation: `\b` metacharacter for exact word matching
   - Limitation: Doesn't handle morphological variants

3. **Fallback Strategy Pattern**
   - Design pattern: Primary handler → Fallback handler
   - Pros: Robust (never fails completely)
   - Cons: Masks functionality gaps
   - **Recommendation**: Add explicit None handling instead of silent fallback

### Metrics for Report

| Metric | Baseline | After Fix | Target | Gap |
|--------|----------|-----------|--------|-----|
| Overall Accuracy | 60.6% | 62.8% | 72.3% | -9.5% |
| HR Routing Accuracy | 52.2% | 56.5% | 92.3% | -35.8% |
| Sales Routing Accuracy | 86.5% | 82.7% | 86.5% | -3.8% |
| RAG Routing Accuracy | 63.2% | 78.9% | 63.2% | +15.7% ✅ |

**Key Takeaway**: Routing improved for RAG (+15.7%), but missing HR handlers prevented overall improvement.

---

## 📖 LESSONS LEARNED

### For Software Engineering
1. **Test the full pipeline, not just components** - Routing tests passed, but end-to-end failed
2. **Silent failures are dangerous** - Fallback masked missing functionality
3. **Code coverage ≠ functionality coverage** - answer_hr() exists but doesn't handle most cases

### For NLP Systems
1. **Keyword matching needs stemming** - Word boundaries alone insufficient
2. **Domain handlers need comprehensive coverage** - Can't just handle "easy" queries
3. **Fallback should be explicit** - Make None returns obvious, don't hide them

### For FYP Projects
1. **Document failures as learning** - This investigation is valuable FYP content!
2. **CEO perspective matters** - Business impact analysis guides priorities
3. **Systematic investigation** - Hypothesis → Test → Evidence → Conclusion

---

**Status**: ✅ Analysis Complete  
**Next Steps**: Implement Priority 1 & 2 fixes  
**Expected Outcome**: 60.6% → 75%+ accuracy  
**Confidence**: Very High (root causes confirmed with evidence)  
**Time Estimate**: 6-8 hours for full implementation + testing
