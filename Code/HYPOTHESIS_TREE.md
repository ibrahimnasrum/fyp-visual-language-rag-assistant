# Hypothesis Tree: System Failure Analysis
## Date: January 14, 2026
## Framework: Competing hypotheses for root cause identification

---

## Problem Statement

**Observation:** Follow-up questions and complex queries sometimes produce:
1. Wrong answer types ($ instead of %)
2. Inconsistent numbers across follow-ups
3. Generic answers without data grounding
4. System crashes (division by zero)

**Goal:** Identify PRIMARY root cause(s) and rank competing explanations.

---

## Hypothesis Tree Structure

```
Why do answers fail?
├── Layer 1: Query Understanding Failures
│   ├── H1.1: Intent misclassification (wrong query type detected)
│   ├── H1.2: Filter extraction failure (state/month not captured)
│   └── H1.3: Ambiguous phrasing (user query unclear)
│
├── Layer 2: Execution Failures  
│   ├── H2.1: Data type mismatch (Period vs int)
│   ├── H2.2: Filter application bug (sequential if statements)
│   └── H2.3: Division by zero (denominator = 0)
│
├── Layer 3: Output Format Failures
│   ├── H3.1: Semantic type mismatch (% query returns $)
│   ├── H3.2: Route mismatch (deterministic vs RAG)
│   └── H3.3: Template hardcoding (one-size-fits-all format)
│
├── Layer 4: Context Management Failures
│   ├── H4.1: Context loss between turns
│   ├── H4.2: Filter persistence failure
│   └── H4.3: Follow-up generation doesn't embed context
│
└── Layer 5: LLM Failures
    ├── H5.1: Hallucination (invents data)
    ├── H5.2: Retrieval inconsistency (wrong docs fetched)
    └── H5.3: Prompt ineffectiveness (anti-hallucination rules ignored)
```

---

## Detailed Hypothesis Analysis

### Layer 1: Query Understanding Failures

#### H1.1: Intent Misclassification
**Claim:** System detects wrong query type (e.g., thinks "percentage" is "total").

**Confidence:** 10% (LOW)

**Evidence FOR:**
- Could explain semantic type mismatch

**Evidence AGAINST:**
- ✅ v9.0 added explicit intent detection with keywords: "percentage", "vs", "top"
- ✅ Code shows clear patterns: `if 'percentage' in q or '% of' in q`
- ❌ No reports of "top 5" being treated as "total"

**Diagnostic Test:**
```python
# Test queries with clear intent
assert detect_intent_type("What percentage of sales") == "percentage"
assert detect_intent_type("Compare June vs May") == "comparison"
assert detect_intent_type("Top 5 products") == "breakdown"
```

**Conclusion:** UNLIKELY to be primary cause. Intent detection logic is straightforward.

---

#### H1.2: Filter Extraction Failure
**Claim:** System fails to extract state/month/product filters from query.

**Confidence:** 30% (MEDIUM)

**Evidence FOR:**
- ⚠️ Complex queries with multiple filters might miss some
- ⚠️ "Burger products" needs product name matching (fuzzy match)
- ⚠️ Follow-ups might not explicitly mention filters ("compare with last month")

**Evidence AGAINST:**
- ✅ Existing functions: `extract_sales_filters()`, `extract_month_from_query()` work for main queries
- ✅ Test cases show filters ARE extracted: S11 (state), S12 (state + product)

**Diagnostic Test:**
```python
# Test filter extraction
filters = extract_sales_filters("Sales in Selangor for June")
assert filters['state'] == 'Selangor'
assert filters['month'] == 202406
```

**For Follow-ups:**
```python
# Failure case
query = "Compare with previous month"
# Problem: No explicit month mentioned, needs context from previous turn
```

**Conclusion:** 
- For main queries: WORKING (confidence: 90%)
- For follow-ups: POTENTIAL ISSUE (confidence: 70% that this fails)

---

#### H1.3: Ambiguous User Phrasing
**Claim:** User query is inherently ambiguous, impossible to interpret correctly.

**Confidence:** 15% (LOW)

**Examples:**
- "Show me sales" - Which month? Which state?
- "What's different?" - Different from what? Which dimension?

**Evidence FOR:**
- ⚠️ FU03 scenario: "What's different about top performers?" is vague
- ⚠️ System can't read user's mind

**Evidence AGAINST:**
- ✅ For such cases, system should ask clarifying questions
- ✅ Most queries in questions.csv are reasonably specific

**Conclusion:** MINOR ISSUE. Should handle with clarification, not fail silently.

---

### Layer 2: Execution Failures

#### H2.1: Data Type Mismatch (Period vs Int)
**Claim:** YearMonth column has Period objects, but code compares with integers.

**Confidence:** 100% (CONFIRMED and FIXED)

**Evidence:**
- ✅ Debug logs show: `Period('2024-06') == 202406 → False`
- ✅ BUG_FIXES_v9.1.md Bug #6 documents this
- ✅ Fix: Compare Period to Period directly

**Impact:** CRITICAL - Caused 0 rows returned, division by zero.

**Status:** ✅ FIXED in v9.1

---

#### H2.2: Filter Application Bug (Sequential If)
**Claim:** Sequential `if` statements cause both YearMonth AND DateStr filters to run, resulting in 0 rows.

**Confidence:** 100% (CONFIRMED and FIXED)

**Evidence:**
```python
# BUG:
if 'YearMonth' in result.columns:
    result = result[result['YearMonth'] == value]  # Filters to 4819 rows
if 'DateStr' in result.columns:
    result = result[result['DateStr'].str.contains(value)]  # Runs on 4819 rows, finds 0
```

**Fix:**
```python
# FIXED:
if 'YearMonth' in result.columns:
    ...
elif 'DateStr' in result.columns:  # Only runs if YearMonth doesn't exist
    ...
```

**Status:** ✅ FIXED in v9.1 (Bug #1)

---

#### H2.3: Division by Zero
**Claim:** When denominator is 0, percentage calculation crashes.

**Confidence:** 100% (CONFIRMED and FIXED)

**Root Cause:** H2.1 + H2.2 caused denominator to be 0.

**Fix:** Added safety check and fallback:
```python
if denominator_value == 0:
    df_denominator = df.copy()  # Use all data as fallback
```

**Status:** ✅ FIXED in v9.1 (Bug #4)

---

### Layer 3: Output Format Failures

#### H3.1: Semantic Type Mismatch
**Claim:** Query asks for percentage, system returns dollar amount.

**Confidence:** 100% (CONFIRMED and FIXED)

**Evidence:**
- ✅ DIAGNOSIS_AND_SOLUTION.md: Expected 16.4%, got RM 16,421.18
- ✅ Root cause: `answer_sales_ceo_kpi()` always returned "Value: RM X" format

**Fix:** v9.0 added specialized executors:
```python
if intent.intent_type == 'percentage':
    return execute_percentage_query()  # Returns "16.4%" format
```

**Status:** ✅ FIXED in v9.0

---

#### H3.2: Route Mismatch
**Claim:** Main query routes to deterministic KPI, follow-up routes to RAG, causing data mismatch.

**Confidence:** 75% (LIKELY but not confirmed in production)

**Evidence FOR:**
- ⚠️ TEST_CASES_FOLLOWUP.md TC2 describes this scenario
- ⚠️ "Medical leave policy" (RAG) → "How many took leave" should route to hr_kpi

**Evidence AGAINST:**
- ✅ Route detection exists: `detect_intent()` checks keywords
- ⚠️ But does it work for follow-ups generated by LLM?

**Diagnostic Test:**
```python
# Test cross-route scenario
main_route = route_query("What's the medical leave policy?")  # Should be rag_docs
followup_route = route_query("How many employees took medical leave?")  # Should be hr_kpi
assert main_route == "rag_docs"
assert followup_route == "hr_kpi"
```

**Predicted Failure:**
- If followup_route == "rag_docs", LLM will hallucinate count (no CSV access)

**Status:** ⚠️ NEEDS TESTING

---

#### H3.3: Template Hardcoding
**Claim:** Output template is one-size-fits-all, doesn't adapt to query type.

**Confidence:** 0% (NOT TRUE for v9+)

**Evidence AGAINST:**
- ✅ v9.0 added specialized formatters for each intent type
- ✅ Percentage queries get percentage format
- ✅ Comparison queries get table format

**Conclusion:** NOT AN ISSUE in v9+. Was an issue in v8.2.

---

### Layer 4: Context Management Failures

#### H4.1: Context Loss Between Turns
**Claim:** Follow-up questions don't receive context from previous turn.

**Confidence:** 85% (HIGH - most likely unresolved issue)

**Evidence FOR:**
- ✅ TEST_CASES_FOLLOWUP.md FU01: "Compare with previous month" loses state filter
- ✅ conversation_history passed to LLM but may not include structured filters
- ⚠️ No explicit mechanism found for passing filter dict between turns

**Evidence AGAINST:**
- ⚠️ Intent parser extracts from query text, so if follow-up mentions state, it works
- ⚠️ But if follow-up says "previous month" without context, parser has nothing to extract

**Diagnostic Test:**
```python
# Conversation
Turn 1: "Show Selangor sales for June 2024"
  → Extracted: {state: 'Selangor', month: 202406}
  → Answer: RM 16,421.18

Turn 2: "Compare with previous month"
  → Extracted: {month: ???, state: ???}
  → Expected: {month: 202405, state: 'Selangor'}  # Inherit state
  → Actual: {month: 202405, state: None}  # Lost state context
```

**Impact:** CRITICAL - Causes wrong data subset to be used.

**Status:** ⚠️ LIKELY ISSUE - Needs testing and potential fix

---

#### H4.2: Filter Persistence Failure
**Claim:** Filters from main query don't persist to follow-up execution.

**Confidence:** 85% (Same as H4.1 - they're related)

**This is a CONSEQUENCE of H4.1:**
- If context is lost (H4.1), filters can't persist (H4.2)
- If context is preserved, filters still might not be applied due to executor logic

**Mechanism:**
```python
# Main query
intent1 = parse_query_intent("Selangor sales June")
  → filters = {state: 'Selangor', month: 202406}

# Follow-up
intent2 = parse_query_intent("Compare with May")
  → filters = {month: 202405}  # No state!

# Executor applies only the filters in intent2
df_filtered = apply_filters(df, intent2.filters)  # ALL states for May
```

**Fix Needed:**
- Pass previous_intent to follow-up parser
- Merge filters: `intent2.filters.update(intent1.filters)`

**Status:** ⚠️ DESIGN ISSUE - Not implemented

---

#### H4.3: Follow-up Generation Doesn't Embed Context
**Claim:** Generated follow-up questions are too vague, don't include explicit context.

**Confidence:** 70% (LIKELY - related to H4.1)

**Example:**
```python
# Main query result for "Selangor June sales"
# Generated follow-ups:
1. "Compare with previous month"  # Vague - doesn't say "Selangor"
2. "Show product breakdown"  # Vague - doesn't say "Selangor June"
3. "What's driving performance?"  # Very vague

# Better follow-ups:
1. "Compare Selangor June vs Selangor May"
2. "Show Selangor product breakdown for June"
3. "What drove Selangor June sales performance?"
```

**Root Cause:**
- Follow-up generation prompt doesn't emphasize context embedding
- LLM generates natural-sounding but context-light questions

**Fix Needed:**
```python
# Improve prompt for follow-up generation
"Generate 3 follow-up questions. IMPORTANT: Each question must explicitly mention:
- The specific filters used (state, month, product)
- The context from the previous answer
Example: 'Compare SELANGOR June vs May' not just 'Compare with previous month'"
```

**Status:** ⚠️ PROMPT ENGINEERING ISSUE

---

### Layer 5: LLM Failures

#### H5.1: Hallucination
**Claim:** LLM invents data when context is insufficient or ambiguous.

**Confidence:** 90% (HIGH - general LLM behavior, mitigated but not eliminated)

**Evidence FOR:**
- ✅ D15 test: "maternity leave policy" might return hallucinated "30 days"
- ✅ D11 test: Executive summary might invent sales numbers
- ✅ General LLM property: Fills gaps with plausible content

**Evidence AGAINST:**
- ⚠️ Anti-hallucination prompts added in v8.2:
  ```
  "If you don't have data, say 'I don't have that information'
   Never invent numbers or facts"
  ```
- ⚠️ Verification checks numbers against ground truth

**Mitigation Effectiveness:**
- For NUMBERS: HIGH (verification catches this)
- For QUALITATIVE claims: MEDIUM (hard to verify "best performing state because of X")

**Diagnostic Test:**
```python
# Test D15 (negative case)
response = query("What is the maternity leave policy?")
# If policy not in docs:
#   Expected: "Policy not available in documents"
#   Hallucination risk: "30 days maternity leave as per company policy"
```

**Status:** ⚠️ ONGOING RISK - Reduced but not eliminated

---

#### H5.2: Retrieval Inconsistency
**Claim:** FAISS retrieves different documents for semantically similar queries.

**Confidence:** 50% (UNCERTAIN - needs testing)

**Evidence FOR:**
- ⚠️ Theoretical concern: Embeddings sensitive to phrasing

**Evidence AGAINST:**
- ✅ FAISS should be deterministic for identical queries
- ❌ No observed instances of this in practice

**Diagnostic Test:**
```python
# Run same query 10 times
docs_list = [retrieve_context("sales June 2024", k=12) for _ in range(10)]
# Check consistency
assert all(docs == docs_list[0] for docs in docs_list)
```

**Conclusion:** UNLIKELY to be primary issue. Needs empirical testing.

---

#### H5.3: Prompt Ineffectiveness
**Claim:** Anti-hallucination prompts don't work; LLM ignores them.

**Confidence:** 30% (LOW-MEDIUM)

**Evidence FOR:**
- ⚠️ Prompts are not 100% effective (known limitation)
- ⚠️ Complex multi-step reasoning might bypass prompts

**Evidence AGAINST:**
- ✅ Prompts DO reduce hallucination rate (from literature)
- ✅ v8.2 prompts are explicit and clear

**Conclusion:** Prompts help but aren't perfect. H5.1 (hallucination) remains a risk.

---

## Hypothesis Ranking by Impact

### Tier 1: CONFIRMED ROOT CAUSES (Fixed)
1. **H2.1: Data type mismatch** - Confidence: 100%, Status: ✅ FIXED
   - Impact: CRITICAL (caused 0 rows, division by zero)
   
2. **H2.2: Sequential filter bug** - Confidence: 100%, Status: ✅ FIXED
   - Impact: CRITICAL (caused 0 rows)
   
3. **H3.1: Semantic type mismatch** - Confidence: 100%, Status: ✅ FIXED
   - Impact: HIGH (wrong answer type)

### Tier 2: LIKELY ACTIVE ISSUES (Need Fixing)
1. **H4.1: Context loss between turns** - Confidence: 85%, Status: ⚠️ ACTIVE
   - Impact: HIGH (wrong data subset in follow-ups)
   - Priority: FIX NEXT
   
2. **H4.2: Filter persistence failure** - Confidence: 85%, Status: ⚠️ ACTIVE
   - Impact: HIGH (consequence of H4.1)
   - Priority: FIX NEXT
   
3. **H5.1: LLM hallucination** - Confidence: 90%, Status: ⚠️ MITIGATED
   - Impact: MEDIUM-HIGH (trust issues)
   - Priority: ONGOING MONITORING

### Tier 3: POSSIBLE ISSUES (Need Testing)
1. **H3.2: Route mismatch** - Confidence: 75%, Status: ⚠️ NEEDS TEST
   - Impact: MEDIUM (data source inconsistency)
   
2. **H4.3: Vague follow-up generation** - Confidence: 70%, Status: ⚠️ DESIGN
   - Impact: MEDIUM (contributes to H4.1)
   
3. **H1.2: Filter extraction (follow-ups)** - Confidence: 70%, Status: ⚠️ NEEDS TEST
   - Impact: MEDIUM (relates to H4.1)

### Tier 4: UNLIKELY ISSUES
1. **H1.1: Intent misclassification** - Confidence: 10%
2. **H1.3: Ambiguous phrasing** - Confidence: 15%
3. **H5.2: Retrieval inconsistency** - Confidence: 50%
4. **H5.3: Prompt ineffectiveness** - Confidence: 30%

---

## Primary Failure Cascade

### Most Common Failure Path:
```
1. User asks: "Show Selangor sales for June"
   → System extracts: {state: 'Selangor', month: 202406}
   → Answer: RM 16,421.18 ✅

2. User clicks: "Compare with previous month" (generated follow-up)
   → H4.3: Follow-up is vague (doesn't say "Selangor")
   → H4.1: System loses state context
   → H1.2: Parser extracts only {month: 202405}, no state
   → H4.2: Filters not persisted
   → Executor uses: {month: 202405} for ALL states
   → Answer shows: Total May sales (not Selangor May)
   → Result: WRONG ANSWER ❌

Possible additional failure:
3. If follow-up is ambiguous enough:
   → H3.2: Routes to RAG instead of KPI
   → H5.1: LLM hallucinates numbers
   → Result: VERY WRONG ANSWER ❌❌
```

### Root Cause: Context Management (Layer 4)
**Primary:** H4.1 (Context loss)
**Secondary:** H4.3 (Vague follow-ups)
**Consequence:** H4.2 (Filter persistence failure)

---

## Competing Explanations for "Follow-up Wrong Answer"

### Explanation A: Context Loss Cascade (H4.1 + H4.3)
**Probability:** 70%
- Follow-up doesn't include explicit context
- Parser can't extract what's not there
- Filters don't persist

### Explanation B: Route Mismatch (H3.2)
**Probability:** 20%
- Follow-up routes to wrong handler (RAG vs KPI)
- Different data source used

### Explanation C: LLM Hallucination (H5.1)
**Probability:** 10%
- Even with correct route and context, LLM invents data

### Combination: A → B → C (Cascade)
- Most likely: Context lost (A) → Wrong route (B) → Hallucination (C)
- Probability: 5-10% for full cascade

---

## Testing Strategy

### Test 1: Isolate H4.1 (Context Loss)
```python
# Log conversation
Turn 1: "Selangor sales June"
  Log: intent1.filters = {state: 'Selangor', month: 202406}
  
Turn 2: "Compare with May"
  Log: intent2.filters = ???
  Expected: {state: 'Selangor', month: 202405}
  Failure: {month: 202405}  # Missing state
```

### Test 2: Isolate H3.2 (Route Mismatch)
```python
# Log routes
Query 1: "Medical leave policy"
  Log: route = "rag_docs" ✅
  
Query 2: "How many took medical leave?"
  Log: route = ???
  Expected: "hr_kpi"
  Failure: "rag_docs"
```

### Test 3: Isolate H5.1 (Hallucination)
```python
# Test negative case
Query: "Maternity leave policy"
  If not in docs:
    Expected: "Not available"
    Failure: "30 days" (invented)
```

---

## Decision Tree for Debugging

```
Answer is wrong?
├── Is the NUMBER wrong?
│   ├── YES → Check Layer 2 (Execution)
│   │   ├── Period vs int issue? (H2.1) ✅ FIXED
│   │   ├── Filter bug? (H2.2) ✅ FIXED
│   │   └── Division by zero? (H2.3) ✅ FIXED
│   └── NO → Number is correct, but...
│       └── Is the FORMAT wrong?
│           ├── YES → Check Layer 3 (Output Format)
│           │   ├── Type mismatch? (H3.1) ✅ FIXED
│           │   ├── Route mismatch? (H3.2) ⚠️ TEST
│           │   └── Template issue? (H3.3) ✅ FIXED
│           └── NO → Answer is completely ungrounded
│               └── Check Layer 5 (LLM Failures)
│                   ├── Hallucination? (H5.1) ⚠️ MONITOR
│                   ├── Retrieval? (H5.2) ⚠️ TEST
│                   └── Prompt? (H5.3) ⚠️ REFINE
│
└── Is this a FOLLOW-UP question?
    ├── YES → Check Layer 4 (Context)
    │   ├── Context lost? (H4.1) ⚠️ FIX
    │   ├── Filters not persisted? (H4.2) ⚠️ FIX
    │   └── Vague question? (H4.3) ⚠️ IMPROVE
    └── NO → Check Layer 1 (Understanding)
        ├── Intent wrong? (H1.1) ✅ OK
        ├── Filters not extracted? (H1.2) ✅ OK
        └── Ambiguous? (H1.3) ⚠️ CLARIFY
```

---

## Self-Critique

### What Am I Most Confident About?
- ✅ Layer 2 (Execution) issues are fixed - 100% confidence
- ✅ Layer 3.1 (Semantic type) is fixed - 100% confidence
- ✅ Layer 4 (Context) is the primary remaining issue - 85% confidence

### What Am I Least Confident About?
- ⚠️ H5.2 (Retrieval inconsistency) - 50% confidence, needs empirical test
- ⚠️ H3.2 (Route mismatch) - 75% confidence, needs production logs
- ⚠️ Interaction effects between hypotheses

### What Could I Be Wrong About?
- Maybe context IS being passed, but prompt engineering makes LLM ignore it?
- Maybe route mismatch is MORE common than I think?
- Maybe there are OTHER failure modes I haven't considered?

### Missing Perspectives
- User's actual phrasing patterns (real-world queries)
- Edge cases not covered in test files
- Performance under load (does caching affect retrieval?)

---

## STATUS: DONE (Hypothesis Tree Complete)

**Summary:**
- 13 hypotheses analyzed across 5 layers
- 3 confirmed and fixed (Tier 1)
- 3 likely active issues (Tier 2)
- 3 possible issues needing tests (Tier 3)
- 4 unlikely issues (Tier 4)

**Primary Root Cause:** Layer 4 - Context Management (H4.1, H4.2, H4.3)

**Next Action:** Review OPEN_GAPS.md for missing information needed to confirm remaining hypotheses.
