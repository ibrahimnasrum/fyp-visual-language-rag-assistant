# FYP System Improvement Analysis & Research Notes
**Date**: January 15, 2026  
**Test Run**: test_results_20260115_112123.csv  
**Baseline Performance**: 57/94 passed (60.6%)

---

## 📊 SECTION 1: FAILURE PATTERN ANALYSIS

### Summary of Test Results
```
Total Tests: 94
├─ ✅ PASSED: 57 (60.6%)
├─ ⚠️  ROUTE_FAIL: 25 (26.6%)  ← PRIMARY ISSUE
├─ ⚠️  ANSWER_FAIL: 12 (12.8%)  ← SECONDARY ISSUE
└─ ❌ ERRORS: 0 (0.0%)          ← FIXED (format_num + memory)
```

### Performance Metrics
- **Average Response Time**: 41.84s (too slow for production)
- **Fastest Query**: 0.01s (KPI queries)
- **Slowest Query**: 132.59s (RAG document queries)
- **Follow-up Generation**: 2.5 avg, 78/94 with followups (83%)

---

## 🔍 SECTION 2: DETAILED FAILURE BREAKDOWN

### A. ANSWER_FAIL Analysis (12 failures = 12.8%)

**Root Cause**: Format error still occurring despite fix
```
Error: "Cannot specify ',' with 's'."
```

**Affected Questions** (All sales KPI with specific state/product filters):
1. UI01 - sales bulan 2024-06 berapa?
2. UI04 - sales ikut state bulan 2024-06
3. S01 - sales bulan 2024-06 berapa?
4. S03 - revenue bulan 2024-05
5. S10 - sales state Selangor bulan 2024-06 berapa?
6. S11 - sales ikut state bulan 2024-06
7. R02 - sales
8. R04 - salse bulan 2024-06
9. R08 - berapa sales for Cheese Burger in Mei 2024?
10. CEO06 - Which product is growing fastest in recent months?
11. CEO22 - What's our average transaction value by channel?
12. CEO37 - Which product category should we expand?

**Pattern**: All involve sales_kpi route with state/product-level breakdowns

**Hypothesis**: 
- Format_num is fixed in v8.2 code but NOT being executed correctly
- OR there's another location calling the old format_num
- OR the fix wasn't applied to all format_num usages

**Confidence**: 95% - Error message is identical to original bug

---

### B. ROUTE_FAIL Analysis (25 failures = 26.6%)

**Pattern 1: HR KPI → RAG_DOCS misrouting** (10 cases - 40% of route fails)
```
Expected: hr_kpi
Actual: rag_docs
```

**Affected Questions**:
1. H06 - berapa staff kitchen? (hr_kpi → rag_docs)
2. H07 - average employee tenure (hr_kpi → rag_docs)
3. H08 - staff with more than 5 years (hr_kpi → rag_docs)
4. H10 - total payroll expense (hr_kpi → rag_docs)
5. R03 - staff (hr_kpi → rag_docs)
6. R05 - headcont by stat (hr_kpi → rag_docs)
7. CEO11 - Which branch has the most employees? (hr_kpi → rag_docs)
8. CEO16 - How many managers have left? (hr_kpi → rag_docs)
9. CEO27 - Show me salary range for kitchen staff (hr_kpi → rag_docs)
10. CEO29 - What's the age distribution of our workforce? (hr_kpi → rag_docs)
11. CEO30 - What's the average tenure for managers? (hr_kpi → rag_docs)

**Hypothesis**: 
- HR queries with detailed breakdowns (tenure, age, department-specific) trigger RAG route
- Keywords like "kitchen", "managers", "age distribution" bias toward document search
- Router may lack training examples for granular HR analytics

**Confidence**: 85%

---

**Pattern 2: Sales KPI → RAG_DOCS misrouting** (8 cases - 32% of route fails)
```
Expected: sales_kpi
Actual: rag_docs
```

**Affected Questions**:
1. CEO05 - Are we growing or declining from Jan to June? (sales_kpi → rag_docs)
2. CEO07 - What's the average sales per employee? (sales_kpi → rag_docs)
3. CEO08 - Who is our top performing employee by revenue? (sales_kpi → rag_docs)
4. CEO09 - Which branch generates most revenue per staff? (sales_kpi → rag_docs)
5. CEO20 - What's our payment method distribution? (sales_kpi → rag_docs)
6. CEO21 - Is delivery growing faster than dine-in? (sales_kpi → rag_docs)
7. CEO25 - Show me average unit price trends Jan to June (sales_kpi → rag_docs)

**Hypothesis**: 
- Analytical/trend questions ("growing", "trends", "distribution") trigger RAG
- Combined metrics (sales + employee) confuse router
- Need explicit training for time-series trend queries

**Confidence**: 90%

---

**Pattern 3: RAG_DOCS → Sales KPI misrouting** (7 cases - 28% of route fails)
```
Expected: rag_docs
Actual: sales_kpi
```

**Affected Questions**:
1. D06 - how many branches we have? (rag_docs → sales_kpi)
2. D07 - what products do we sell? (rag_docs → sales_kpi)
3. D09 - opening hours for KL branch (rag_docs → sales_kpi)
4. D10 - Penang branch manager siapa? (rag_docs → sales_kpi)
5. D12 - performance review process (rag_docs → sales_kpi)
6. D13 - Why did sales drop in Selangor? (rag_docs → sales_kpi)
7. D14 - How can we improve Cheese Burger sales? (rag_docs → sales_kpi)

**Hypothesis**: 
- Keywords like "branch", "product", "sales" strongly bias toward sales_kpi
- Organizational questions (manager names, hours, review process) need RAG
- Router prioritizes KPI route over document route when ambiguous

**Confidence**: 95%

---

## 🎯 SECTION 3: COMPETING HYPOTHESES

### Hypothesis Tree

```
ROOT PROBLEM: 60.6% accuracy (need >95%)
│
├─ BRANCH 1: Answer Failures (12.8%)
│  │
│  ├─ H1.1: format_num not applied everywhere [Confidence: 95%]
│  │   Evidence: Identical error message, all sales KPI queries
│  │   Test: Search all format_num calls, verify fix applied
│  │
│  ├─ H1.2: Old code path still exists [Confidence: 80%]
│  │   Evidence: Multiple bot versions in Code/ folder
│  │   Test: Check if old oneclick files still referenced
│  │
│  └─ H1.3: Number formatting in a different function [Confidence: 60%]
│      Evidence: Only affects state/product breakdowns
│      Test: Search for all .format() or f"{x:," patterns
│
├─ BRANCH 2: Route Failures - HR Misrouting (11/25 = 44%)
│  │
│  ├─ H2.1: Router lacks granular HR examples [Confidence: 90%]
│  │   Evidence: "tenure", "kitchen staff", "managers" → RAG
│  │   Solution: Add 20+ HR breakdown examples to training
│  │
│  ├─ H2.2: Keyword bias toward documents [Confidence: 85%]
│  │   Evidence: Descriptive terms trigger RAG over KPI
│  │   Solution: Adjust router weights, add negative examples
│  │
│  └─ H2.3: No hybrid query support [Confidence: 70%]
│      Evidence: "salary range for kitchen" needs both HR + docs
│      Solution: Implement dual-route queries
│
├─ BRANCH 3: Route Failures - Sales Misrouting (8/25 = 32%)
│  │
│  ├─ H3.1: Trend analysis keywords → RAG [Confidence: 95%]
│  │   Evidence: "growing", "trends", "distribution" misrouted
│  │   Solution: Add temporal analysis examples to sales_kpi
│  │
│  ├─ H3.2: Combined metrics confuse router [Confidence: 85%]
│  │   Evidence: "sales per employee" needs both routes
│  │   Solution: Pre-process to identify composite queries
│  │
│  └─ H3.3: Router doesn't understand time aggregation [Confidence: 80%]
│      Evidence: "Jan to June" should be sales_kpi, goes to RAG
│      Solution: Add time-range pattern detection
│
└─ BRANCH 4: Route Failures - RAG → Sales (7/25 = 28%)
   │
   ├─ H4.1: Strong keyword bias to sales_kpi [Confidence: 95%]
   │   Evidence: Any mention of "branch", "product", "sales" → KPI
   │   Solution: Context-aware routing (organizational vs analytical)
   │
   ├─ H4.2: No "how-to" or "policy" detection [Confidence: 90%]
   │   Evidence: "performance review process" → sales instead of docs
   │   Solution: Add question-type classification layer
   │
   └─ H4.3: Missing intent recognition [Confidence: 85%]
       Evidence: "Why" and "How to improve" need docs, not KPI
       Solution: Detect explanatory vs factual queries
```

---

## 📚 SECTION 4: LITERATURE REVIEW (Reference Folder)

### Available Resources
1. **Chapter 6 - Prompt Engineering.pdf**
   - Expected content: Few-shot learning, chain-of-thought, prompt templates
   
2. **Chapter 7 - Advanced Text Generation.pdf**
   - Expected content: RAG techniques, retrieval optimization, generation quality

3. **Hands-On Large Language Models.pdf**
   - Expected content: Practical LLM implementation, evaluation metrics

### Research Questions to Answer
1. How to improve query routing accuracy? (Chapter 6)
2. What RAG retrieval techniques increase relevance? (Chapter 7)
3. How to evaluate answer quality? (Hands-On LLM)

---

## 🛠️ SECTION 5: IMPROVEMENT STRATEGIES (Prioritized)

### PRIORITY 1: Fix Answer Failures (Quick Win)
**Target**: 12 → 0 failures (+12.8% accuracy)

**Strategy**: 
1. Search for ALL format_num usage points
2. Verify fix is applied consistently
3. Check for alternative number formatting code

**Expected Impact**: +12.8% (72/94 = 76.6% pass rate)
**Effort**: Low (2-3 hours)
**Risk**: Low

---

### PRIORITY 2: Improve HR Query Routing
**Target**: 11 HR misroutes → 0 (+11.7% accuracy)

**Strategy A: Enhanced Training Examples**
- Add 30 HR-specific training examples with granular breakdowns
- Include: tenure by department, staff by role, attrition by group
- Technique: Few-shot learning (from Chapter 6)

**Strategy B: Keyword Detection Rules**
- Detect HR-specific terms: "tenure", "attrition", "payroll", "staff count"
- Override RAG route when HR metrics + time/breakdown requested
- Technique: Rule-based augmentation

**Expected Impact**: +11.7% (84/94 = 89.4% pass rate)
**Effort**: Medium (1 day)
**Risk**: Medium (may affect other routes)

---

### PRIORITY 3: Improve Sales Trend Query Routing
**Target**: 8 sales misroutes → 0 (+8.5% accuracy)

**Strategy A: Temporal Pattern Detection**
- Identify time-series queries: "trend", "growing", "over time", "Jan to June"
- Force sales_kpi route for time comparisons
- Technique: Pattern matching + route override

**Strategy B: Composite Query Decomposition**
- Break down "sales per employee" into: (sales_kpi) / (hr_kpi)
- Implement multi-step query execution
- Technique: Query planning (Chapter 7)

**Expected Impact**: +8.5% (92/94 = 97.9% pass rate)
**Effort**: High (2 days)
**Risk**: High (complex implementation)

---

### PRIORITY 4: Improve RAG → Sales Routing
**Target**: 7 RAG misroutes → 0 (+7.4% accuracy)

**Strategy A: Intent Classification**
- Classify queries: factual (KPI) vs explanatory (RAG)
- "What/How many" → KPI, "Why/How to" → RAG
- Technique: Intent detection layer

**Strategy B: Organizational Context Detection**
- Detect organizational questions: "manager", "opening hours", "process"
- Force rag_docs route for policy/operational queries
- Technique: Entity + context rules

**Expected Impact**: +7.4% (94/94 = 100% pass rate)
**Effort**: Medium (1 day)
**Risk**: Low

---

## 📈 SECTION 6: PROJECTED IMPROVEMENTS

### Cumulative Impact Forecast

| Priority | Strategy | Pass Rate | Gain | Cumulative | Effort | Risk |
|----------|----------|-----------|------|------------|--------|------|
| Baseline | - | 60.6% | - | 60.6% | - | - |
| P1 | Fix format_num | 76.6% | +16.0% | 76.6% | Low | Low |
| P2 | HR routing | 89.4% | +12.8% | 89.4% | Med | Med |
| P3 | Sales trends | 97.9% | +8.5% | 97.9% | High | High |
| P4 | RAG intent | 100.0% | +2.1% | 100.0% | Med | Low |

**Minimum Acceptable**: P1 + P2 = 89.4% (need >95%, keep going)
**Target Achievement**: P1 + P2 + P3 = 97.9% ✅
**Stretch Goal**: All priorities = 100.0% 🎯

---

## 🔬 SECTION 7: RESEARCH PHASE PLAN

### Phase 1: Deep Dive into Reference Materials (Next 2 hours)
- [ ] Read Chapter 6: Prompt Engineering techniques
  - Extract: Few-shot learning best practices
  - Extract: Query routing improvement methods
  - Extract: Prompt template optimization
  
- [ ] Read Chapter 7: Advanced RAG techniques
  - Extract: Retrieval quality metrics
  - Extract: Context ranking strategies
  - Extract: Multi-step reasoning approaches

- [ ] Skim Hands-On LLM: Evaluation methods
  - Extract: Answer quality metrics
  - Extract: A/B testing frameworks
  - Extract: Production deployment patterns

### Phase 2: Code Inspection (Next 1 hour)
- [ ] Find ALL format_num() usage locations
- [ ] Read query routing logic in detail
- [ ] Understand RAG retrieval pipeline
- [ ] Map out answer generation flow

### Phase 3: Implementation (Next 4-6 hours)
- [ ] P1: Fix answer failures (format_num)
- [ ] P2: Enhance HR routing (training examples + rules)
- [ ] P3: Improve sales trend routing (temporal detection)
- [ ] P4: Add intent classification (organizational queries)

### Phase 4: Testing & Documentation (Next 2 hours)
- [ ] Run comprehensive test suite
- [ ] Compare before/after metrics
- [ ] Document each change with evidence
- [ ] Create improvement summary report

---

## 📝 SECTION 8: CHANGE LOG TEMPLATE

For each improvement, document:

```markdown
### Change #X: [Brief Title]

**Problem**: [What was wrong]
**Root Cause**: [Why it happened]
**Solution**: [What was implemented]
**Technique Used**: [Academic/industry reference]
**Code Changes**: [Files modified, line numbers]

**Metrics Before**:
- Accuracy: X%
- Affected queries: N
- Average latency: Xs

**Metrics After**:
- Accuracy: Y%
- Affected queries: 0
- Average latency: Ys

**Improvement**: +Z% accuracy, -W seconds latency
**Evidence**: [Test results, screenshots, logs]
```

---

## 🎓 SECTION 9: ACADEMIC RIGOR

### Evaluation Framework
- **Accuracy**: % queries with correct route + valid answer
- **Precision**: % routed correctly among routed queries
- **Recall**: % correctly routed among all queries needing that route
- **F1 Score**: Harmonic mean of precision/recall
- **Latency**: P50, P95, P99 response times
- **User Satisfaction**: Follow-up relevance score

### A/B Testing Protocol
1. Baseline: Current system (60.6% accuracy)
2. Treatment: Improved system (target >95%)
3. Holdout: 10% test set not used for training
4. Metrics: All 6 metrics above
5. Statistical significance: p < 0.05

---

**Status**: Research phase initiated  
**Next Action**: Read Chapter 6 Prompt Engineering  
**Expected Completion**: 8-10 hours of focused work
