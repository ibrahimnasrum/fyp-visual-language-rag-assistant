# Phase 2: Empirical Data Collection Guide

**Date:** January 14, 2026  
**Prerequisites:** Logging infrastructure v8.3 implemented  
**Goal:** Collect empirical data to test hypotheses H4.1, H4.2, H3.2, H5.1

---

## Quick Start

### 1. Run the Application
```bash
cd Code
Run_MY_Assistant_v8.2_CEO.bat
```

### 2. Execute Test Queries
Use queries from **Section 3** below. Run each query as a conversation with follow-ups.

### 3. Save Terminal Output
Copy all console output to: `logs/empirical_testing_20260114.txt`

---

## What to Look For

### ✅ Route Logging (GAP-002)
```
🔀 ROUTE: 'Total revenue January' → sales_kpi (matched: ['revenue'])
```
**Verify:**
- Route appears for every query
- Keywords make sense
- Follow-ups use correct route

### ✅ Filter Logging (GAP-001)
```
🔍 FILTER EXTRACTION: 'Sales in Selangor'
   State: Selangor
   Product: None
   ...
```
**Verify:**
- Filters extracted from initial query
- Follow-up query: "How about Samsung?" should ADD product filter
- Filters should persist (H4.2 test)

### ✅ Follow-up Logging (GAP-003)
```
📝 FOLLOW-UP GENERATION:
   Extracted context: {'state': 'Selangor'}
   Generated follow-ups:
      1. Compare with Penang
```
**Verify:**
- Context extraction captures key entities
- Follow-ups are contextually relevant
- Context matches filter extraction (H4.1 test)

### ✅ Conversation Logging (GAP-004)
```
📊 CONVERSATION_HISTORY (2 turns):
   [0] user: Total revenue January
   [1] assistant: RM 2.4M
```
**Verify:**
- History shows previous turns
- User queries preserved
- Assistant answers summarized

---

## Test Queries (Critical Path)

### Test Case 1: Filter Persistence (H4.2)
```
Query 1: "Total revenue for Selangor in January 2024"
Expected: 🔍 State: Selangor, filters extracted

Query 2: "How about Samsung products?"
Expected: 🔍 State: Selangor (persisted), Product: Samsung (new)
HYPOTHESIS: State filter will be LOST ❌
```

### Test Case 2: Context Loss (H4.1)
```
Query 1: "Top 5 products by revenue"
Expected: 📝 Context: {groupby: 'Product', limit: 5}

Query 2: "Show the top performer details"
Expected: 📝 Context: {top_performer: 'Samsung'}
HYPOTHESIS: Top performer context will be LOST ❌
```

### Test Case 3: Route Mismatch (H3.2)
```
Query 1: "How many employees do we have?"
Expected: 🔀 ROUTE → hr_kpi

Query 2: "What about in Penang?"
Expected: 🔀 ROUTE → hr_kpi (should stay in HR domain)
HYPOTHESIS: Route will switch to sales_kpi or rag_docs ❌
```

### Test Case 4: Temporal Context (H4.1)
```
Query 1: "Sales in January 2024"
Expected: 📝 Context: {month: 'January', year: '2024'}

Query 2: "How about February?"
Expected: 📝 Context: {month: 'February', year: '2024'}
HYPOTHESIS: Year context will be LOST ❌
```

### Test Case 5: Multi-Entity Context (H4.1)
```
Query 1: "Samsung sales in Selangor for January"
Expected: 🔍 State: Selangor, Product: Samsung, Month: January

Query 2: "Compare with Penang"
Expected: 🔍 State: Penang (switched), Product: Samsung (persisted), Month: January (persisted)
HYPOTHESIS: Product AND Month will be LOST ❌
```

---

## Data Collection Checklist

For each test case, record:

- [ ] Initial query text
- [ ] 🔀 Route decision + matched keywords
- [ ] 🔍 All extracted filters
- [ ] 📝 Extracted context dict
- [ ] Generated follow-up questions (all 3)
- [ ] Follow-up query text (user's actual follow-up)
- [ ] 🔀 Follow-up route decision
- [ ] 🔍 Follow-up filters (check persistence)
- [ ] 📊 Conversation history structure
- [ ] Final answer correctness

---

## Analysis Template

After collecting data, analyze each test case:

### Test Case X: [Name]
**Hypothesis:** [e.g., H4.2 - Filter persistence failure]

**Initial Query:**
```
Query: "..."
🔀 ROUTE: → XXX
🔍 Filters: {...}
```

**Follow-up Query:**
```
Query: "..."
🔀 ROUTE: → XXX
🔍 Filters: {...}
📝 Context: {...}
```

**Result:**
- ✅ CONFIRMED / ❌ REJECTED
- Observation: [What actually happened]
- Evidence: [Log excerpts]

---

## Expected Findings (Predictions)

Based on analysis in HYPOTHESIS_TREE.md:

| Hypothesis | Expected Outcome | Confidence |
|------------|------------------|------------|
| H4.1 - Context loss | ✅ CONFIRMED | 90% |
| H4.2 - Filter persistence failure | ✅ CONFIRMED | 85% |
| H3.2 - Route mismatch | ✅ CONFIRMED | 75% |
| H5.1 - LLM hallucination | ⚠️ PARTIAL | 90% (mitigated by v8.2) |

---

## Success Criteria

Phase 2 is complete when:
1. ✅ 5+ test cases executed with logs
2. ✅ All 4 logging types verified working
3. ✅ Evidence collected for 4 primary hypotheses
4. ✅ Patterns documented in analysis
5. ✅ Root causes confirmed or rejected

---

## Next Phase: Phase 3 (Fix Implementation)

Once data confirms hypotheses, implement fixes:

1. **Context Inheritance System** (if H4.1 confirmed)
   - Enhance `extract_context_from_answer()`
   - Pass context dict to follow-up generation
   
2. **Filter Persistence Layer** (if H4.2 confirmed)
   - Store filters in conversation state
   - Merge previous filters with new filters

3. **Route Hints** (if H3.2 confirmed)
   - Pass previous route to follow-up generation
   - Add route constraints to follow-up questions

4. **Context Validation** (for all fixes)
   - Pre-LLM context check
   - Reject queries with insufficient context

---

## Files Reference

- Test queries source: `QUESTION_INVENTORY.md`
- Hypothesis details: `HYPOTHESIS_TREE.md`, `RESEARCH_NOTES.md`
- Gap analysis: `OPEN_GAPS.md`
- Implementation: `IMPLEMENTATION_COMPLETE_v8.3.md`

---

**Status:** Ready to begin data collection  
**Estimated Time:** 30-45 minutes for 5 test cases  
**Output:** Empirical evidence for hypothesis testing
