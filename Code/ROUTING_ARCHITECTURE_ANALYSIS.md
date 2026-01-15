# Routing Architecture Analysis & Experiments

**Date:** 2026-01-15  
**FYP Research Question:** Which routing method provides best accuracy for multi-domain chatbot?  
**Status:** Analysis + Experimental Design

---

## Part 1: Test Question Validation

### Current Test Database
- **Total Questions:** 94
- **Categories:** UI Examples (7), Sales (15), HR (10), RAG/Docs (16), Robustness (9), CEO Strategic (37)
- **Source:** automated_tester_csv.py, lines 37-154

### Potential Issues Identified

#### 1. Spelling Errors (Intentional for Robustness)
```python
{"id": "R04", "q": "salse bulan 2024-06", "route": "sales_kpi"},  # "salse" → "sales"
{"id": "R05", "q": "headcont by stat", "route": "hr_kpi"},        # "headcont" → "headcount"
```
**Status:** ✅ CORRECT - These are robustness tests to check typo tolerance

#### 2. Ambiguous Questions (Generic Queries)
```python
{"id": "R01", "q": "top products", "route": "sales_kpi"},          # No month specified
{"id": "R02", "q": "sales", "route": "sales_kpi"},                # No context
{"id": "R03", "q": "staff", "route": "hr_kpi"},                   # No context
```
**Status:** ⚠️ DESIGN QUESTION - Should system:
- **Option A:** Ask for clarification (conversational)
- **Option B:** Use latest month by default (assumption)
- **Option C:** Return summary across all time (comprehensive)

**Current Behavior:** System likely returns None or generic answer

#### 3. Out-of-Scope Questions (Deliberate)
```python
{"id": "R06", "q": "What's the weather today?", "route": "rag_docs"},
{"id": "R07", "q": "Can you book a meeting?", "route": "rag_docs"},
```
**Status:** ✅ CORRECT - Tests graceful handling of out-of-scope queries

#### 4. Date Format Ambiguity
```python
{"id": "S15", "q": "sales bulan July 2024", "route": "sales_kpi"}  # Data only has 2024-01 to 2024-06
```
**Status:** ⚠️ DATA ISSUE - July 2024 doesn't exist in dataset
**Expected:** System should say "No data available for July 2024"

#### 5. Mixed Language Consistency
```python
{"id": "R08", "q": "berapa sales for Cheese Burger in Mei 2024?", "route": "sales_kpi"}  # Malay "Mei" = May
```
**Status:** ✅ CORRECT - Tests mixed language understanding

### AI Prompt Quality Review

Let me check the LLM prompts used in answer generation:

<function_calls>
<invoke name="grep_search">
<parameter name="includePattern">oneclick_my_retailchain_v8.2_models_logging.py