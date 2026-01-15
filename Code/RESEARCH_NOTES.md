# Research Notes: System Failure Analysis
## Date: January 14, 2026
## Objective: Identify root causes of answer quality issues

---

## Research Framework

### Core Research Question
**"Why do follow-up questions produce inconsistent or incorrect answers compared to main queries?"**

### Sub-questions
1. Is it a context loss problem?
2. Is it a routing mismatch problem?
3. Is it an LLM hallucination problem?
4. Is it a data type/format problem?
5. Is it a verification gap problem?

---

## Hypothesis Development

### Hypothesis 1: Context Loss in Conversation Flow
**Confidence:** 85% → 90% (increased after analysis)

**Theory:**
Follow-up questions lose critical context (state filter, month filter, etc.) from the main query, causing the system to operate on wrong data subset.

**Evidence FOR:**
- ✅ TEST_CASES_FOLLOWUP.md explicitly describes this failure pattern
- ✅ FU01 scenario shows "Compare with previous month" loses state filter
- ✅ No explicit mechanism found for passing context between turns
- ✅ conversation_history passed but may not include structured filters

**Evidence AGAINST:**
- ⚠️ v9 intent parser DOES extract filters from query text
- ⚠️ If follow-up says "compare Selangor", parser should extract it
- ❌ But if follow-up just says "compare with previous month", parser has no text to extract

**Predicted Observable Outcomes:**
- [ ] Test: "Show Selangor sales" → "Compare with last month"
  - Expected: Selangor June vs Selangor May
  - Predicted: ALL states June vs ALL states May
- [ ] Check conversation_history structure
  - Expected: Includes previous answer text only
  - Predicted: Does NOT include structured filters dict

**Confidence Assessment:**
- Initial: 85% (hypothetical)
- After TEST_CASES review: 90% (documented failure pattern)
- Needs: Actual execution test to confirm

**Self-Critique:**
- Am I assuming follow-ups are poorly phrased? Maybe they explicitly mention state.
- Need to see actual generated follow-up text to confirm.
- Could be a prompt engineering issue, not just context passing.

---

### Hypothesis 2: Semantic Type Mismatch (Answer Format)
**Confidence:** 95% → 100% (CONFIRMED and FIXED)

**Theory:**
System calculates correct NUMBERS but returns wrong ANSWER TYPE. Query asks for percentage, system returns dollar amount.

**Evidence FOR:**
- ✅ DIAGNOSIS_AND_SOLUTION.md explicitly describes this: "Expected: 16.4%, Actual: RM 16,421.18"
- ✅ Bug was in v8.2, fixed in v9.0 by adding intent detection
- ✅ Root cause: `answer_sales_ceo_kpi()` had hardcoded format (always returns "Value: RM X")
- ✅ Verification checked NUMBERS but not TYPES

**Evidence AGAINST:**
- ❌ None - this is confirmed by documentation and code analysis

**Observable Confirmation:**
- ✅ v9.0 added `parse_query_intent()` to detect intent type
- ✅ v9.0 added specialized executors: `execute_percentage_query()`, `execute_comparison_query()`
- ✅ v9.0 added semantic verification: `verify_answer_semantics()`

**Fix Implemented:**
```python
# v8.2: WRONG
return f"Value: RM {total}"  # Always returns dollar amount

# v9.0: CORRECT
if intent.intent_type == 'percentage':
    return execute_percentage_query()  # Returns percentage format
elif intent.intent_type == 'comparison':
    return execute_comparison_query()  # Returns comparison table
```

**Confidence Assessment:**
- Initial: 95% (documented)
- After code review: 100% (confirmed in BUG_FIXES_v9.1.md)

**Self-Critique:**
- This is not a hypothesis anymore - it's a confirmed fact.
- Should move to "Confirmed Root Causes" section.

---

### Hypothesis 3: Data Type Mismatch (Period vs Int)
**Confidence:** 90% → 100% (CONFIRMED and FIXED)

**Theory:**
YearMonth column contains Period objects but filter code compares with integers, causing 0 rows returned.

**Evidence FOR:**
- ✅ BUG_FIXES_v9.1.md Bug #1, #2, #6 all relate to this
- ✅ Debug logs show: "YearMonth dtype: period[M]" but "Looking for: 202406 (type: int)"
- ✅ `Period('2024-06') == 202406` returns `False`
- ✅ Caused division by zero when denominator filter returned 0 rows

**Evidence AGAINST:**
- ❌ None - confirmed by actual debug output in user conversation

**Observable Confirmation:**
```
DEBUG output (before fix):
   YearMonth dtype: period[M]
   YearMonth sample values: ['2024-01', '2024-02', '2024-03']
   Looking for: 202406 (type: <class 'int'>)
   After filter: 0 rows  ← BUG
```

**Fix Implemented:**
```python
# v9.1: Compare Period to Period directly
if hasattr(value, 'to_timestamp'):  # pd.Period object
    result = result[result['YearMonth'] == value]  # Direct comparison
```

**Confidence Assessment:**
- Initial: 90% (suspected from error messages)
- After debug logs: 100% (confirmed)

**Self-Critique:**
- Again, this is confirmed fact, not hypothesis.
- Root cause analysis was correct.

---

### Hypothesis 4: RAG Retrieval Inconsistency
**Confidence:** 70% → 75% (likely but not confirmed)

**Theory:**
FAISS retrieves different documents for main query vs follow-up, causing inconsistent answers even for semantically similar questions.

**Evidence FOR:**
- ✅ RESEARCH_FOLLOWUP_QUALITY.md lists this as Hypothesis 2 (70%)
- ✅ Reasonable concern: Embeddings may be sensitive to phrasing
- ⚠️ "Medical leave policy" vs "How many took medical leave" are semantically different (should route differently)

**Evidence AGAINST:**
- ❌ No actual test results showing different retrievals
- ❌ May be confusing RAG retrieval with routing issue (H5)
- ❌ FAISS should be deterministic for identical queries

**What Would Prove This:**
- [ ] Test: Run same query twice, check if k=12 retrieved docs differ
- [ ] Test: Run semantically similar queries, measure overlap in retrieved docs
- [ ] Measure: Cosine similarity between queries and retrieval overlap

**Predicted Outcomes:**
- If TRUE: Same query gives different docs on re-run (non-deterministic)
- If FALSE: Same query always retrieves same docs (deterministic)

**Confidence Assessment:**
- Initial: 70% (theoretical concern)
- After analysis: 75% (plausible but needs testing)
- Caveat: May be a routing problem, not retrieval problem

**Self-Critique:**
- Am I conflating two issues? RAG retrieval vs route selection?
- "Medical leave policy" SHOULD route to rag_docs
- "How many took leave" SHOULD route to hr_kpi (different route entirely)
- This may not be retrieval inconsistency but intentional route difference.
- Need to separate: (a) same-route retrieval consistency, (b) cross-route handling

---

### Hypothesis 5: Route Mismatch in Follow-ups
**Confidence:** 90% → 85% (high but partially mitigated)

**Theory:**
Main query routes to deterministic KPI, follow-up routes to RAG, causing data source mismatch and inconsistent numbers.

**Evidence FOR:**
- ✅ TEST_CASES_FOLLOWUP.md TC2 explicitly describes this
- ✅ Main: "medical leave policy" → rag_docs (RAG)
- ✅ Follow: "how many took leave" → Should go to hr_kpi, might go to rag_docs
- ✅ If routed to RAG, LLM might hallucinate numbers

**Evidence AGAINST:**
- ⚠️ v8.2+ has route detection: `detect_intent()` should route correctly
- ⚠️ HR keywords should trigger hr_kpi route
- ❌ No evidence of actual route mismatch in production

**What Would Prove This:**
- [ ] Log actual routes taken for main + follow-up pairs
- [ ] Test: "medical leave policy" (rag) → "how many employees took leave" (should be hr_kpi)
- [ ] Check if follow-up routes to hr_kpi or rag_docs

**Predicted Outcomes:**
- If TRUE: Follow-up routes to rag_docs, hallucinates count
- If FALSE: Follow-up correctly routes to hr_kpi, shows CSV count

**Confidence Assessment:**
- Initial: 90% (documented concern)
- After code review: 85% (routing logic exists but may not be perfect)

**Self-Critique:**
- Route detection exists, but is it tested for follow-ups?
- May be a training/prompt issue: LLM generates follow-up that doesn't trigger correct route
- Need actual route logs to confirm.

---

### Hypothesis 6: LLM Hallucination in RAG Answers
**Confidence:** 95% → 90% (high but mitigated by prompts)

**Theory:**
When context is insufficient or ambiguous, LLM generates plausible-sounding but factually incorrect answers.

**Evidence FOR:**
- ✅ RESEARCH_FOLLOWUP_QUALITY.md Hypothesis 4: 95% confidence
- ✅ D15 test: "maternity leave policy" should say "not available" but might hallucinate
- ✅ D11 test: Executive summary must be grounded, but LLM might invent numbers
- ✅ General LLM behavior: Fills gaps with plausible content

**Evidence AGAINST:**
- ⚠️ v8.2 added "CRITICAL ANTI-HALLUCINATION RULES" in prompts
- ⚠️ Verification logic checks numbers against ground truth
- ⚠️ System instructs LLM to say "not available" when data is missing

**Mitigation Implemented:**
```python
# CEO system prompt includes:
"CRITICAL ANTI-HALLUCINATION RULES:
- If you don't have exact data, say 'I don't have that information'
- Never invent numbers or facts
- If policy not found, say 'Policy not available in documents'"
```

**Observable Outcomes:**
- [ ] Test D15: "maternity leave policy" (not in docs)
  - Expected: "Policy not available"
  - Risk: "30 days maternity leave" (hallucinated)
- [ ] Test D11: "Executive summary June 2024"
  - Expected: Uses only numbers from CSV + doc context
  - Risk: Invents sales numbers, states, products

**Confidence Assessment:**
- Initial: 95% (LLMs naturally hallucinate)
- After mitigation: 90% (reduced but not eliminated)
- Reality: Anti-hallucination prompts help but aren't 100% effective

**Self-Critique:**
- Am I being too pessimistic? Maybe prompts work better than I think.
- Need actual test results on D15-type negative cases.
- Verification catches numerical hallucinations (compares to CSV).
- But doesn't catch: "Selangor is the best performing state because of better management" (ungrounded opinion).

---

## Cross-Hypothesis Dependencies

### Dependency 1: Context Loss → Route Mismatch
If H1 (context loss) is true, it makes H5 (route mismatch) MORE likely.
- Lost context → Vague follow-up → Wrong route triggered

### Dependency 2: Route Mismatch → Hallucination
If H5 (route mismatch) is true, it makes H6 (hallucination) MORE likely.
- Wrong route (rag instead of kpi) → No CSV data → LLM fills gap → Hallucination

### Dependency 3: Type Mismatch → Verification Gap
H2 (type mismatch) and H3 (data type) both caused verification to pass incorrectly.
- Number was correct, but type was wrong → False positive verification

---

## Research Execution Plan

### Phase 1: Confirmed Facts (COMPLETED)
- ✅ H2: Semantic type mismatch - CONFIRMED and FIXED
- ✅ H3: Data type (Period vs int) - CONFIRMED and FIXED

### Phase 2: High-Confidence Hypotheses (NEEDS TESTING)
- [ ] H1: Context loss in follow-ups
  - Action: Create test that logs filters between turns
  - Action: Generate follow-up, check if it includes context
- [ ] H5: Route mismatch
  - Action: Log actual routes for main + follow-up pairs
  - Action: Test TC2 scenario from TEST_CASES_FOLLOWUP.md

### Phase 3: Medium-Confidence Hypotheses (NEEDS MORE DATA)
- [ ] H4: RAG retrieval inconsistency
  - Action: Run same query 10 times, check retrieval consistency
  - Action: Measure doc overlap for similar queries
- [ ] H6: LLM hallucination
  - Action: Test D15 negative cases
  - Action: Test D11 grounded summaries

---

## Competing Explanations Framework

### For "Follow-up gives wrong answer" - Which is the PRIMARY cause?

**Option A: Context Loss (H1)**
- Probability: 40%
- Evidence: Documented in test cases, no clear solution implemented
- Counter: Intent parser should extract from text

**Option B: Route Mismatch (H5)**
- Probability: 30%
- Evidence: Cross-route scenarios described
- Counter: Route detection logic exists

**Option C: LLM Hallucination (H6)**
- Probability: 20%
- Evidence: General LLM behavior
- Counter: Anti-hallucination prompts added

**Option D: Combination of A+B**
- Probability: 10%
- Most likely: Context lost → wrong route → hallucination (cascade failure)

### For "Percentage query returned $" - SOLVED
- Primary cause: H2 (semantic type mismatch) - 100% confirmed
- Secondary cause: H3 (data type mismatch) - 100% confirmed
- Status: FIXED in v9.0 and v9.1

---

## Self-Critique Questions

### Bias Check
1. **Am I over-emphasizing documented issues?**
   - Yes - focus is on TEST_CASES and BUG_FIXES docs
   - Risk: Missing undocumented issues
   - Mitigation: Proposed new tests (Phase 2 & 3)

2. **Am I assuming LLMs always hallucinate?**
   - Possibly - H6 confidence is 90% without hard evidence
   - Reality: Prompts DO work, just not 100%
   - Need: Actual test on negative cases to measure rate

3. **Am I conflating symptoms with causes?**
   - Example: "Wrong answer" could be due to H1, H5, or H6
   - Need: Systematic elimination through testing
   - Approach: Test each hypothesis independently

### Missing Perspectives
1. **User intent ambiguity** - Maybe user's phrasing is inherently ambiguous?
2. **Data quality issues** - Maybe CSV has inconsistencies?
3. **Edge cases** - Maybe it works 90% of the time, fails on edge cases?

### What Could I Be Wrong About?
1. **H1 (Context loss)** - Maybe intent parser is good enough, context extraction from text works
2. **H4 (Retrieval)** - Maybe FAISS is perfectly consistent, not an issue
3. **H6 (Hallucination)** - Maybe anti-hallucination prompts are more effective than I think

---

## Observable Metrics to Track

### Metric 1: Context Preservation Rate
- **Definition:** % of follow-ups that correctly maintain filters from main query
- **Target:** >90%
- **How to measure:** Log filters before/after follow-up, compare
- **Current status:** UNKNOWN (not measured yet)

### Metric 2: Route Consistency Rate
- **Definition:** % of follow-ups that route to correct intent
- **Target:** >95%
- **How to measure:** Manual labeling of correct routes, compare with actual
- **Current status:** UNKNOWN

### Metric 3: Numerical Accuracy Rate
- **Definition:** % of answers where numbers match ground truth (±5%)
- **Target:** >95% for deterministic, >80% for RAG
- **How to measure:** Compare with pandas calculations
- **Current status:** HIGH for v9.1 (percentage fix increased this)

### Metric 4: Hallucination Rate
- **Definition:** % of RAG answers that contain ungrounded claims
- **Target:** <5%
- **How to measure:** Manual review of 100 random RAG answers
- **Current status:** UNKNOWN (subjective measure)

### Metric 5: Semantic Correctness Rate
- **Definition:** % of answers where answer TYPE matches query TYPE
- **Target:** >95%
- **How to measure:** Check if % query gets %, comparison query gets table, etc.
- **Current status:** HIGH for v9.0+ (semantic verification added)

---

## Research Prioritization

### Priority 1: CRITICAL (Affects Correctness)
1. Test H1 (Context loss) - Could cause wrong answers
2. Test H5 (Route mismatch) - Could cause data source errors
3. Measure Metric 3 (Numerical accuracy) - Core requirement

### Priority 2: HIGH (Affects Reliability)
1. Test H6 (Hallucination) - Could cause trust issues
2. Measure Metric 1 (Context preservation) - Needed for multi-turn
3. Measure Metric 2 (Route consistency) - Needed for reliability

### Priority 3: MEDIUM (Improves Understanding)
1. Test H4 (RAG retrieval) - May or may not be an issue
2. Measure Metric 4 (Hallucination rate) - Hard to quantify
3. Edge case testing - Good to have

---

## Next Research Actions

### Immediate (Today)
1. ✅ Complete QUESTION_INVENTORY.md - DONE
2. ✅ Complete RESEARCH_NOTES.md - IN PROGRESS
3. ⏳ Complete HYPOTHESIS_TREE.md - NEXT
4. ⏳ Complete OPEN_GAPS.md - NEXT

### Short-term (This Week)
1. Create automated test for H1 (context loss)
2. Create test logs for H5 (route mismatch)
3. Run D15-type tests for H6 (hallucination)

### Medium-term (This Month)
1. Collect metrics for 100 conversations
2. Measure hallucination rate manually
3. Create ground truth test suite

---

## STATUS: DONE (Research Framework Complete)

**Key Findings:**
- 2 hypotheses CONFIRMED and FIXED (H2, H3)
- 4 hypotheses NEED TESTING (H1, H4, H5, H6)
- 5 metrics defined for ongoing tracking
- Clear prioritization for testing

**Confidence Levels Updated:**
- H1: 85% → 90% (context loss likely)
- H2: 95% → 100% (CONFIRMED)
- H3: 90% → 100% (CONFIRMED)
- H4: 70% → 75% (RAG retrieval needs testing)
- H5: 90% → 85% (route logic exists but needs validation)
- H6: 95% → 90% (mitigated but not eliminated)
