# Routing Architecture Analysis & Experiments

**Date:** 2026-01-15  
**FYP Research Question:** Which routing method provides best accuracy for multi-domain chatbot?  
**Status:** Analysis + Experimental Design  
**Purpose:** Answer "Why choose keyword routing?" with evidence

---

## Executive Summary

**Current System:** Keyword-based routing with 4 destinations (visual, hr_kpi, sales_kpi, rag_docs)  
**Research Question:** Is keyword routing optimal, or should we use semantic/LLM-based routing?  
**Proposed Solution:** Compare 4 routing architectures systematically with 94-question test suite

---

## Part 1: Test Question Validation ✅

### Analysis of 94 Test Questions

**Categories:**
- UI Examples: 7 questions
- Sales KPI: 15 questions
- HR KPI: 10 questions
- RAG/Docs: 16 questions
- Robustness: 9 questions
- CEO Strategic: 37 questions

### Issues Found & Resolutions

#### ✅ Issue 1: Spelling Errors (INTENTIONAL)
```python
R04: "salse bulan 2024-06" → Tests typo tolerance
R05: "headcont by stat" → Tests robustness
```
**Resolution:** Keep as-is - tests error handling

#### ⚠️ Issue 2: Ambiguous Queries
```python
R01: "top products" → No month specified
R02: "sales" → No context
R03: "staff" → Generic query
```
**Current Problem:** These likely fail or return None  
**Proposed Fix:** Add default behavior:
- Use latest month if no period specified
- Show summary statistics if too generic
- Document limitations

#### ⚠️ Issue 3: Out-of-Range Data
```python
S15: "sales bulan July 2024" → Data ends at June 2024
```
**Expected Behavior:** "No data available for July 2024"  
**Test:** Verify system handles gracefully

#### ✅ Issue 4: Mixed Language
```python
R08: "berapa sales for Cheese Burger in Mei 2024?" 
```
**Status:** Good test for bilingual support  
**Current System:** Should handle "Mei" → May mapping

### AI Prompt Quality Assessment

**Current Prompt Structure:** (Lines 3183-3330, oneclick_my_retailchain_v8.2_models_logging.py)

```python
def build_ceo_prompt(...):
    # 1. Conversation history (last 3 exchanges)
    # 2. User preferences/memory
    # 3. Retrieved RAG context (documents)
    # 4. Computed KPI facts (CSV data)
    # 5. OCR text (if image provided)
    # 6. Query-specific guidance (few-shot)
    # 7. CEO question
    # 8. Response instructions
```

**Strengths:**
- ✅ Hierarchical source priority
- ✅ Query type classification (performance/trend/comparison/policy/root_cause)
- ✅ Few-shot examples for each query type
- ✅ Explicit citation requirements
- ✅ Structured output format

**Potential Issues:**
- ⚠️ Token efficiency: 150-char truncation for history might lose context
- ⚠️ No explicit instruction for handling missing data
- ⚠️ Query type classifier uses substring matching (same limitation as routing)

**Recommendation:** Prompts are well-structured. Focus on routing layer first, then optimize prompts if needed.

---

## Part 2: Why Keyword Routing? (Current Architecture Analysis)

### Current Implementation

**Location:** `detect_intent()` function, lines 3944-4013

**Architecture:**
```
User Query → detect_intent()
    ├─ Priority 1: Image present? → visual
    ├─ Priority 2: Match DOC_KEYWORDS? → rag_docs
    ├─ Priority 3: Match HR_KEYWORDS? → hr_kpi
    ├─ Priority 4: Match SALES_KEYWORDS? → sales_kpi
    ├─ Priority 5: Check conversation history → inherit domain
    └─ Default: → rag_docs
```

**Keyword Lists:**
- **HR_KEYWORDS (28 terms):** headcount, staff, employee, attrition, payroll, age, tenure, managers, kitchen, etc.
- **SALES_KEYWORDS (35+ terms):** sales, revenue, product, branch, state, channel, top, compare, highest, price, etc.
- **DOC_KEYWORDS (~15 terms):** policy, leave, SOP, procedure, entitlement, claim, guideline, etc.

**Matching Method:** Word-boundary regex (\b) for single words, substring for phrases

### Why Was Keyword Routing Chosen?

**Apparent Reasons (from code comments):**

1. **Speed** - No LLM call needed (0ms routing overhead)
2. **Determinism** - Same query always routes the same way
3. **Explainability** - Can trace why routing decision was made
4. **Cost** - No API calls for routing
5. **Simplicity** - Easy to debug and maintain

**But:** No documentation exists explaining WHY this was chosen over alternatives!

### Limitations Identified

**Problem 1: Keyword Collisions**
- "age" matched "percentage", "average" (FIXED in v8.2.1 with word boundaries)
- Plurals don't match: "products" ≠ "product" with \b (FIXED by adding plurals)

**Problem 2: Ambiguous Keywords**
- "staff" appears in both "kitchen staff" (HR) and "How many staff left in 2022?" (could be dates)
- "average" could be sales average or HR average

**Problem 3: Missing Keywords**
- CEO23: "Which products have highest unit price?" missed "highest", "price"
- CEO31: "Which branches perform above average?" missed "above", "branches"

**Problem 4: No Semantic Understanding**
- "Show me underperforming locations" → No keyword match → Wrong routing
- "Calculate total compensation" → Might miss "payroll" keyword

**Problem 5: Maintenance Burden**
- Need to manually add keywords as new query patterns emerge
- 94 tests require iterative keyword tuning

---

## Part 3: Alternative Routing Methods (Comparative Analysis)

### Method 1: Keyword-Based Routing (CURRENT)

**Implementation:**
```python
def detect_intent_keyword(query):
    if keyword_match(HR_KEYWORDS, query):
        return "hr_kpi"
    if keyword_match(SALES_KEYWORDS, query):
        return "sales_kpi"
    if keyword_match(DOC_KEYWORDS, query):
        return "rag_docs"
    return "rag_docs"  # default
```

**Pros:**
- ⚡ Ultra-fast (0.001s)
- 💰 Zero cost
- 🔍 Fully explainable
- 🎯 Deterministic

**Cons:**
- ❌ Requires manual keyword curation
- ❌ No semantic understanding
- ❌ Prone to keyword collisions
- ❌ Struggles with new query patterns

**Expected Accuracy:** 60-85% (current baseline: 62.8%)

---

### Method 2: Semantic Similarity Routing

**Implementation:**
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

# Pre-compute embeddings for each domain
domain_examples = {
    "hr_kpi": "headcount staff employees attrition payroll salary tenure",
    "sales_kpi": "sales revenue product branch state channel performance",
    "rag_docs": "policy leave SOP procedure guideline claim refund"
}

domain_embeddings = {k: model.encode(v) for k, v in domain_examples.items()}

def detect_intent_semantic(query):
    query_embedding = model.encode(query)
    similarities = {
        domain: cosine_similarity(query_embedding, emb)
        for domain, emb in domain_embeddings.items()
    }
    return max(similarities, key=similarities.get)
```

**Pros:**
- ✅ Understands synonyms ("compensation" → "payroll")
- ✅ No keyword maintenance
- ✅ Handles new query patterns
- ✅ Semantic understanding

**Cons:**
- ⏱️ Slower (10-50ms per query)
- 💰 Model loading overhead
- 🎯 Non-deterministic (threshold tuning needed)
- 🔍 Less explainable

**Expected Accuracy:** 70-90%

---

### Method 3: LLM-Based Classification

**Implementation:**
```python
def detect_intent_llm(query):
    prompt = f"""
Classify this CEO query into one category:
- hr_kpi: Human resources, employees, headcount, attrition, salary
- sales_kpi: Sales, revenue, products, branches, performance
- rag_docs: Company policies, procedures, SOPs, guidelines

Query: {query}

Answer with ONLY one word: hr_kpi, sales_kpi, or rag_docs
"""
    
    response = ollama.generate(model="mistral:latest", prompt=prompt)
    return response.strip().lower()
```

**Pros:**
- ✅ Best semantic understanding
- ✅ Can explain reasoning
- ✅ Handles complex/ambiguous queries
- ✅ No keyword maintenance

**Cons:**
- 🐌 Very slow (2-10s per query)
- 💰 High cost (LLM inference for every query)
- 🎯 Non-deterministic
- ⚠️ May hallucinate incorrect routes

**Expected Accuracy:** 75-95%

---

### Method 4: Hybrid (Keyword + Semantic Fallback)

**Implementation:**
```python
def detect_intent_hybrid(query):
    # Try keyword matching first (fast path)
    if keyword_match(HR_KEYWORDS, query, threshold=0.8):  # High confidence
        return "hr_kpi"
    if keyword_match(SALES_KEYWORDS, query, threshold=0.8):
        return "sales_kpi"
    if keyword_match(DOC_KEYWORDS, query, threshold=0.8):
        return "rag_docs"
    
    # Fallback to semantic (slow path for ambiguous queries)
    return detect_intent_semantic(query)
```

**Pros:**
- ⚡ Fast for clear queries (90% of queries)
- ✅ Semantic for ambiguous queries (10% of queries)
- 💰 Cost-effective (mostly free, occasional embedding)
- 🎯 Best of both worlds

**Cons:**
- 🔧 More complex implementation
- 🎚️ Threshold tuning required
- 📊 Need two systems maintained

**Expected Accuracy:** 75-92%

---

## Part 4: Experimental Design

### Hypothesis

**H0 (Null):** All routing methods have equal accuracy  
**H1:** Hybrid routing (keyword + semantic) provides highest accuracy

### Experimental Setup

**Test Dataset:** 94 questions from automated_tester_csv.py  
**Ground Truth:** Expected route for each question  
**Evaluation Metrics:**
1. **Routing Accuracy:** % of correct domain assignments
2. **End-to-End Accuracy:** % of correct final answers
3. **Latency:** Average routing time per query
4. **Cost:** Total inference cost for 94 queries
5. **Explainability:** Can system trace why route was chosen?

### Implementation Plan

#### Phase 1: Baseline (Current System)
```bash
# Already running - test_results_20260115_163233.csv
# Expected: ~62.8% overall accuracy
```

#### Phase 2: Implement Alternative Routing Methods

**Step 1: Semantic Routing**
```python
# File: routing_semantic.py
# Install: pip install sentence-transformers
# Implement detect_intent_semantic()
# Modify bot to use this router
# Run: python automated_tester_csv.py --router semantic
```

**Step 2: LLM Routing**
```python
# File: routing_llm.py  
# Implement detect_intent_llm() using Ollama
# Modify bot to use this router
# Run: python automated_tester_csv.py --router llm
```

**Step 3: Hybrid Routing**
```python
# File: routing_hybrid.py
# Combine keyword (fast) + semantic (fallback)
# Threshold: 2+ keyword matches = high confidence
# Run: python automated_tester_csv.py --router hybrid
```

#### Phase 3: Comparative Analysis

**Test Execution:**
```bash
# Run all 4 routing methods
python automated_tester_csv.py --router keyword  # 45 mins
python automated_tester_csv.py --router semantic # 60 mins
python automated_tester_csv.py --router llm      # 4-8 hours!
python automated_tester_csv.py --router hybrid   # 50 mins
```

**Analysis Script:**
```python
# compare_routing_methods.py
import pandas as pd

results = {
    'keyword': pd.read_csv('test_results_keyword.csv'),
    'semantic': pd.read_csv('test_results_semantic.csv'),
    'llm': pd.read_csv('test_results_llm.csv'),
    'hybrid': pd.read_csv('test_results_hybrid.csv')
}

# Calculate metrics
for method, df in results.items():
    routing_accuracy = (df['actual_route'] == df['expected_route']).mean()
    end_to_end_accuracy = df['pass'].mean()
    avg_latency = df['latency'].mean()
    
    print(f"{method}: {routing_accuracy:.1%} routing, {end_to_end_accuracy:.1%} E2E, {avg_latency:.2f}s")
```

### Expected Results Table

| Metric | Keyword | Semantic | LLM | Hybrid | Best |
|--------|---------|----------|-----|--------|------|
| **Routing Accuracy** | 70-85% | 75-90% | 80-95% | 80-92% | LLM/Hybrid |
| **End-to-End Accuracy** | 62-75% | 68-82% | 72-88% | 70-85% | LLM |
| **Avg Latency (ms)** | 0.1ms | 20ms | 3000ms | 10ms | Keyword |
| **Cost per 100 queries** | $0 | $0 | $0.50 | $0.02 | Keyword |
| **Explainability** | 100% | 30% | 70% | 80% | Keyword |
| **Maintenance Effort** | High | Low | Low | Medium | Semantic |

**Predicted Winner by Use Case:**
- **Production System:** Hybrid (best accuracy/cost trade-off)
- **Real-Time Chat:** Keyword (fastest)
- **Batch Processing:** LLM (most accurate)
- **Low Resources:** Keyword (no dependencies)

---

## Part 5: Implementation Roadmap

### Timeline (2-3 days)

**Day 1: Semantic Routing**
- Install sentence-transformers
- Implement detect_intent_semantic()
- Create routing_semantic.py module
- Modify bot to support --router flag
- Run full test suite (60 mins)
- Analyze results

**Day 2: LLM & Hybrid Routing**
- Implement detect_intent_llm()
- Implement detect_intent_hybrid()
- Run test suites (8-10 hours total)
- Generate comparison tables

**Day 3: Analysis & Documentation**
- Statistical analysis (t-tests)
- Create visualization charts
- Write FYP findings section
- Document recommendation

### Code Changes Required

**File 1: routing_methods.py** (NEW)
```python
class RouterFactory:
    """Factory for different routing methods"""
    
    @staticmethod
    def get_router(method='keyword'):
        if method == 'keyword':
            return detect_intent_keyword
        elif method == 'semantic':
            return detect_intent_semantic
        elif method == 'llm':
            return detect_intent_llm
        elif method == 'hybrid':
            return detect_intent_hybrid
        else:
            raise ValueError(f"Unknown routing method: {method}")
```

**File 2: automated_tester_csv.py** (MODIFY)
```python
# Add command-line flag
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--router', default='keyword', 
                    choices=['keyword', 'semantic', 'llm', 'hybrid'])
args = parser.parse_args()

# Use selected router
router = RouterFactory.get_router(args.router)
```

**File 3: oneclick_my_retailchain_v8.2_models_logging.py** (MODIFY)
```python
# Make detect_intent() pluggable
CURRENT_ROUTER = 'keyword'  # Can be changed globally

def detect_intent(text, has_image, conversation_history=None):
    router = RouterFactory.get_router(CURRENT_ROUTER)
    return router(text, has_image, conversation_history)
```

---

## Part 6: FYP Academic Contribution

### Research Novelty

**Contribution 1:** Systematic comparison of 4 routing architectures in production chatbot  
**Contribution 2:** Quantified trade-offs (accuracy vs latency vs cost vs explainability)  
**Contribution 3:** Hybrid approach combining deterministic + probabilistic methods  
**Contribution 4:** Reusable evaluation framework for routing comparison

### FYP Report Sections

**Chapter 3: Methodology**
- "3.5 Routing Architecture Selection"
- "3.6 Experimental Design for Router Comparison"

**Chapter 4: Implementation**
- "4.3 Multi-Method Router Framework"
- "4.4 Semantic Similarity Implementation"
- "4.5 LLM-based Classification"
- "4.6 Hybrid Routing Strategy"

**Chapter 5: Results & Analysis**
- "5.2 Routing Method Comparison"
- "5.3 Trade-off Analysis (Accuracy vs Latency)"
- "5.4 Statistical Significance Testing"

**Chapter 6: Discussion**
- "6.2 When to Use Each Routing Method"
- "6.3 Production Deployment Recommendations"

**Chapter 7: Conclusion**
- "7.3 Contribution: Hybrid Routing Framework"

### Expected Findings (Predictions)

1. **Keyword routing sufficient for 70-80% of queries**
   - Fast, deterministic, explainable
   - Good for production systems

2. **Semantic routing improves ambiguous query handling**
   - 10-15% accuracy gain over keyword-only
   - Minimal latency impact (~20ms)

3. **LLM routing most accurate but impractical for production**
   - Best accuracy (80-95%)
   - Too slow (3s per query)
   - Not cost-effective

4. **Hybrid approach optimal for production**
   - 75-85% keyword hit rate (fast path)
   - 15-25% semantic fallback (slow path)
   - Best accuracy/latency trade-off

---

## Part 7: Immediate Next Steps

### What Should We Do Now?

**Option A: Continue Current Test (Recommended)**
- Let test_results_20260115_163233.csv complete
- Analyze handler improvements first
- Use those results as baseline for routing experiments
- **Rationale:** Need clean baseline before changing architecture

**Option B: Start Routing Experiments Immediately**
- Implement semantic routing today
- Run parallel test with different router
- Compare results side-by-side
- **Rationale:** More experimental data for FYP

**Option C: Fix Test Questions First**
- Address ambiguous queries (R01-R03, S15)
- Add handling for generic queries
- Re-run baseline test
- **Rationale:** Ensure test validity before experiments

### My Recommendation

**Priority 1:** Wait for current test to complete (40 mins remaining)  
**Priority 2:** Analyze handler improvements vs baseline  
**Priority 3:** Fix test question issues (add default month handling)  
**Priority 4:** Implement semantic routing experiment  
**Priority 5:** Compare routing methods systematically

**FYP Value:** This gives you:
- Improvement 01: Word boundary fix (routing accuracy)
- Improvement 02: Handler extensions (answer generation)
- Improvement 03: Routing architecture comparison (novel research)

Three distinct contributions with quantified results!

---

## Conclusion

**Answer to "Why keyword routing?"**

Currently: **Assumed decision** - No documentation exists  
After experiments: **Evidence-based decision** - We can say:
- "Keyword routing chosen for X% accuracy with 0ms latency"
- "Semantic routing improves accuracy by Y% at cost of Zms"
- "Hybrid approach optimal for production: A% accuracy, Bms latency"

**This transforms assumption into research contribution!**

**Next Action:** Wait for test completion, then implement routing experiments?

---

**Document Status:** COMPLETE - Ready for experimental implementation  
**Estimated Effort:** 2-3 days for full routing comparison  
**FYP Value:** HIGH - Novel comparative analysis with quantified trade-offs
