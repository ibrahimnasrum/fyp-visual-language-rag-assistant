# FYP Research Progress Tracker

**Project:** Visual Language RAG Assistant  
**Student:** [Your Name]  
**Date Started:** 2026-01-15  
**Last Updated:** 2026-01-15

---

## Quick Status Overview

| Category | Experiments | Completed | Status |
|----------|-------------|-----------|--------|
| **Query Understanding** | 2 | 0.5 | 🟡 In Progress |
| **Data Representation** | 3 | 0 | 🔴 Not Started |
| **Answer Generation** | 3 | 0 | 🔴 Not Started |
| **Architecture** | 2 | 0 | 🔴 Not Started |
| **System Integration** | 2 | 0 | 🔴 Not Started |
| **Visual Understanding** | 2 | 0 | 🟡 Optional |
| **Evaluation** | 1 | 0 | 🔴 Not Started |
| **TOTAL** | **15** | **0.5** | **3%** |

---

## Tier 1: Critical Experiments (MUST DO)

### 🟡 Experiment 1: Routing Methods Comparison
**Status:** 🟡 IN PROGRESS (Implementation complete, testing in progress)  
**Priority:** ⭐⭐⭐ CRITICAL  
**Effort:** 2 days  
**Impact:** High (affects 100% of queries)  
**Started:** 2026-01-15

**Methods to Test:**
- [x] Keyword routing (baseline - already implemented)
- [x] Semantic similarity routing (routing_semantic.py - COMPLETE)
- [x] LLM classification routing (routing_llm.py - COMPLETE)
- [x] Hybrid routing (routing_hybrid.py - COMPLETE)

**Metrics:**
- [ ] Routing accuracy (% correct domain) - TESTING
- [ ] End-to-end accuracy (% correct answers) - TESTING
- [ ] Average latency (ms per query) - TESTING
- [ ] Total cost ($ per 100 queries) - TBD
- [ ] Explainability score (1-5) - TBD

**Files Created:**
- [x] `routing_factory.py` - Factory pattern for router switching (118 lines)
- [x] `routing_semantic.py` - Semantic routing implementation (162 lines)
- [x] `routing_llm.py` - LLM classification implementation (172 lines)
- [x] `routing_hybrid.py` - Hybrid approach (252 lines)
- [x] `compare_routing_methods.py` - Analysis script (245 lines)
- [x] `test_routers.py` - Quick validation (78 lines)
- [x] `EXPERIMENT_01_ROUTING_RESULTS.md` - Results documentation template
- [x] Modified `automated_tester_csv.py` - Added --router flag
- [x] Modified `oneclick_my_retailchain_v8.2_models_logging.py` - Pluggable router support

**Test Status:**
- [x] Quick router validation (test_routers.py)
- [ ] Keyword baseline (test_results_20260115_163233.csv) - RUNNING
- [ ] Semantic routing test - PENDING
- [ ] Hybrid routing test - PENDING
- [ ] LLM routing test - SKIPPED (too slow - 8 hours)

**Test Commands:**
```bash
# Quick validation
python test_routers.py  # COMPLETE

# Baseline (keyword routing)
python automated_tester_csv.py  # RUNNING (started 16:32:33)

# Semantic routing
python automated_tester_csv.py --router semantic  # NEXT

# Hybrid routing
python automated_tester_csv.py --router hybrid  # AFTER SEMANTIC

# Compare results
python compare_routing_methods.py test_results_*.csv
```

**Expected Results:**
- Keyword: 70-75% accuracy, 0ms overhead (baseline)
- Semantic: 75-80% accuracy, 20ms overhead
- Hybrid: 78-85% accuracy, 10ms overhead
- LLM: 80-85% accuracy, 3000ms overhead (SKIPPED)

**Decision Criteria:**
- If accuracy improvement >5%: Use semantic/hybrid
- If latency critical: Use keyword
- If cost matters: Avoid LLM routing
- **Predicted Winner:** Hybrid (best balance)

**Notes:**
```
2026-01-15 17:30 - Implementation complete
- Created 6 new files (1,027 lines of code)
- Modified 2 existing files for pluggable routing
- Router factory pattern allows easy switching
- Quick tests show semantic/hybrid work correctly
- Waiting for baseline test to complete (~20 mins remaining)

Next Steps:
1. Wait for baseline completion (test_results_20260115_163233.csv)
2. Run semantic routing test (~60 mins)
3. Run hybrid routing test (~60 mins)
4. Compare results with compare_routing_methods.py
5. Update EXPERIMENT_01_ROUTING_RESULTS.md with findings
6. Generate visualizations (accuracy vs latency scatter plot)

Timeline:
- Day 1 (Today): Implementation ✅ + Baseline test 🟡 + Semantic test 🔜
- Day 2 (Tomorrow): Hybrid test + Analysis + Documentation
```

---

### 🔴 Experiment 2: Embedding Model Comparison
**Status:** 🔴 Not Started  
**Priority:** ⭐⭐⭐ CRITICAL  
**Effort:** 1 day  
**Impact:** High (affects RAG retrieval quality)

**Models to Test:**
- [ ] all-MiniLM-L6-v2 (current baseline - 80MB, 384 dim)
- [ ] all-mpnet-base-v2 (420MB, 768 dim)
- [ ] paraphrase-multilingual-MiniLM-L12-v2 (470MB, 384 dim)

**Metrics:**
- [ ] Retrieval Precision@5 (% relevant docs in top 5)
- [ ] Retrieval Recall@10 (% relevant docs retrieved)
- [ ] Mean Reciprocal Rank (MRR)
- [ ] Encoding speed (ms per query)
- [ ] Model loading time (seconds)
- [ ] Memory footprint (MB)

**Test Queries:**
```python
test_queries = [
    "berapa sales bulan 2024-06?",      # Mixed Malay-English
    "What is total revenue?",            # Pure English
    "headcount ikut state",              # Mixed
    "How many employees in Selangor?",   # Pure English
]
```

**Implementation:**
```python
# test_embedding_models.py
from sentence_transformers import SentenceTransformer
import time

models = {
    'MiniLM-L6': "all-MiniLM-L6-v2",
    'mpnet-base': "all-mpnet-base-v2",
    'multilingual': "paraphrase-multilingual-MiniLM-L12-v2"
}

results = {}
for name, model_name in models.items():
    print(f"\nTesting {name}...")
    
    # Load model
    start = time.time()
    embedder = SentenceTransformer(model_name)
    load_time = time.time() - start
    
    # Build index
    emb = embedder.encode(summaries)
    index = build_faiss_index(emb)
    
    # Test retrieval
    precision_scores = []
    for query in test_queries:
        relevant_docs = retrieve_and_evaluate(query, index, embedder)
        precision_scores.append(relevant_docs / 5)
    
    results[name] = {
        'precision@5': np.mean(precision_scores),
        'load_time': load_time,
        'memory': get_memory_usage()
    }

# Generate comparison table
print_results_table(results)
```

**Decision Criteria:**
- If bilingual queries >30%: Use multilingual model
- If memory <512MB: Use MiniLM-L6
- If precision improvement >10%: Use mpnet-base
- **Predicted Winner:** multilingual (for Malaysia mixed language)

**Notes:**
```
[Add observations]
```

---

### 🔴 Experiment 3: LLM Model Selection
**Status:** 🔴 Not Started  
**Priority:** ⭐⭐⭐ CRITICAL  
**Effort:** 1 day (can run overnight)  
**Impact:** High (affects answer quality)

**Models to Test:**
- [ ] mistral:latest (4.4GB - current baseline)
- [ ] llama3:8b (4.7GB)
- [ ] gemma2:2b (1.6GB)
- [ ] qwen2:7b (4.4GB - multilingual)

**Metrics:**
- [ ] Answer accuracy (% correct)
- [ ] Hallucination rate (% fabricated numbers)
- [ ] Response latency (seconds)
- [ ] Memory usage (GB)
- [ ] Bilingual performance (Malay vs English)

**Test Approach:**
```python
# test_llm_models.py
models = ["mistral:latest", "llama3:8b", "gemma2:2b", "qwen2:7b"]

for model in models:
    print(f"\n{'='*60}")
    print(f"Testing {model}")
    print(f"{'='*60}")
    
    results = []
    for test_case in test_suite:
        # Generate answer
        start = time.time()
        answer = generate_answer_with_model(model, test_case.query)
        latency = time.time() - start
        
        # Evaluate
        accuracy = check_correctness(answer, test_case.expected)
        hallucination = detect_hallucination(answer, test_case.context)
        
        results.append({
            'query': test_case.query,
            'accuracy': accuracy,
            'hallucination': hallucination,
            'latency': latency
        })
    
    # Summarize
    print(f"Accuracy: {np.mean([r['accuracy'] for r in results]):.1%}")
    print(f"Hallucination: {np.mean([r['hallucination'] for r in results]):.1%}")
    print(f"Avg Latency: {np.mean([r['latency'] for r in results]):.1f}s")
```

**Hallucination Detection:**
```python
def detect_hallucination(answer, context):
    """Check if answer contains numbers not in context"""
    import re
    
    # Extract all numbers from answer
    answer_numbers = set(re.findall(r'\d+(?:,\d+)*(?:\.\d+)?', answer))
    
    # Extract all numbers from context
    context_numbers = set(re.findall(r'\d+(?:,\d+)*(?:\.\d+)?', context))
    
    # Check if answer has numbers not in context
    fabricated = answer_numbers - context_numbers
    
    return len(fabricated) > 0
```

**Decision Criteria:**
- If accuracy difference <5%: Choose fastest model
- If hallucination >10%: Avoid that model
- If bilingual important: Consider qwen2
- **Predicted Winner:** mistral (current) or llama3 (most accurate)

**Notes:**
```
[Add observations]
```

---

## Tier 2: Important Experiments (SHOULD DO)

### 🔴 Experiment 4: Deterministic vs RAG Architecture
**Status:** 🔴 Not Started  
**Priority:** ⭐⭐ IMPORTANT  
**Effort:** 1 day

**Approaches to Test:**
- [ ] Pure RAG (no deterministic handlers)
- [ ] Hybrid (current - deterministic first, RAG fallback)
- [ ] Ensemble (combine both answers)

**Why This Matters:**
Justifies the hybrid architecture design decision

**Test Plan:**
```python
# Compare on KPI queries only
kpi_queries = [q for q in test_suite if q.type in ['sales_kpi', 'hr_kpi']]

architectures = {
    'pure_rag': PureRAGArchitecture(),
    'hybrid': HybridArchitecture(),
    'ensemble': EnsembleArchitecture()
}

for name, arch in architectures.items():
    for query in kpi_queries:
        answer = arch.answer(query)
        accuracy = evaluate(answer, query.expected)
        # Track results
```

**Expected Finding:**
- Pure RAG: 50-60% accuracy on KPI queries (LLM fabricates numbers)
- Hybrid: 85-95% accuracy (deterministic = exact answers)
- Ensemble: 80-90% accuracy (averaging reduces accuracy)

**Notes:**
```
[Add observations]
```

---

### 🔴 Experiment 5: Context Window Size (k parameter)
**Status:** 🔴 Not Started  
**Priority:** ⭐⭐ IMPORTANT  
**Effort:** 4 hours

**k values to test:** [5, 10, 12, 15, 20, 30]

**Hypothesis:** k=12 is optimal balance between precision and recall

**Test:**
```python
k_values = [5, 10, 12, 15, 20, 30]

for k in k_values:
    results = []
    for query in test_suite:
        context = retrieve_context(query, k=k)
        answer = generate_answer(context, query)
        
        accuracy = evaluate(answer)
        token_count = count_tokens(context)
        latency = measure_latency()
        
        results.append({
            'k': k,
            'accuracy': accuracy,
            'tokens': token_count,
            'latency': latency
        })
    
    # Find accuracy plateau point
```

**Expected Finding:**
- k=5: Low accuracy (70%) - too little context
- k=12: Good accuracy (85%) - current setting
- k=20: Similar accuracy (86%) - diminishing returns
- k=30: No improvement (86%) - too much noise

**Decision:** k=12 optimal (accuracy plateaus, reduces token cost)

**Notes:**
```
[Add observations]
```

---

### 🔴 Experiment 6: Prompt Engineering Strategies
**Status:** 🔴 Not Started  
**Priority:** ⭐⭐ IMPORTANT  
**Effort:** 1 day

**Strategies to Test:**
- [ ] Few-shot (current)
- [ ] Zero-shot
- [ ] Chain-of-Thought
- [ ] ReAct

**Test Implementation:**
```python
strategies = {
    'few_shot': build_few_shot_prompt,
    'zero_shot': build_zero_shot_prompt,
    'cot': build_cot_prompt,
    'react': build_react_prompt
}

for name, builder in strategies.items():
    for query in test_suite:
        prompt = builder(context, query)
        answer = llm.generate(prompt)
        
        # Evaluate
        accuracy = evaluate(answer)
        tokens = count_tokens(prompt)
        format_score = check_output_format(answer)  # 1-5
        
        # Track results
```

**Expected Finding:**
- Few-shot: Best format adherence (5/5), good accuracy (85%)
- Zero-shot: Poor format (3/5), decent accuracy (80%)
- CoT: Good accuracy (87%), but slow (2x tokens)
- ReAct: Overkill for simple KPI queries

**Notes:**
```
[Add observations]
```

---

## Tier 3: Optional Experiments (NICE TO HAVE)

### 🟡 Experiment 7-9: Lower Priority
- FAISS Index Types (low impact - dataset small)
- Temperature Settings (deterministic needed)
- Data Processing Methods (pandas sufficient)

**Status:** Consider only if time permits

---

## Documentation Checklist

### Per Experiment
- [ ] Write hypothesis (H0 vs H1)
- [ ] Describe experimental design
- [ ] Document implementation code
- [ ] Run tests and collect data
- [ ] Create results table
- [ ] Perform statistical analysis (t-test)
- [ ] Justify decision with trade-offs
- [ ] Generate visualizations (bar chart, scatter plot)
- [ ] Write FYP contribution section

### Overall FYP Chapters
- [ ] **Chapter 3: Methodology**
  - 3.1 System Architecture Overview
  - 3.2 Design Decisions Framework
  - 3.3 Experimental Methodology
  - 3.4 Evaluation Metrics
- [ ] **Chapter 4: Implementation**
  - 4.1 Routing Layer Implementation
  - 4.2 Data Representation Layer
  - 4.3 Answer Generation Layer
  - 4.4 Integration & Optimization
- [ ] **Chapter 5: Results & Analysis**
  - 5.1 Baseline Performance
  - 5.2 Routing Methods Comparison
  - 5.3 Model Selection Results
  - 5.4 Architecture Justification
  - 5.5 Overall System Performance
- [ ] **Chapter 6: Discussion**
  - 6.1 Key Findings
  - 6.2 Trade-off Analysis
  - 6.3 Production Considerations
  - 6.4 Limitations
- [ ] **Chapter 7: Conclusion**
  - 7.1 Summary of Contributions
  - 7.2 Future Work

---

## Timeline

### Week 1: Core Experiments
- **Mon:** Routing experiments (keyword, semantic)
- **Tue:** Routing experiments (LLM, hybrid)
- **Wed:** Embedding models comparison
- **Thu:** LLM models comparison
- **Fri:** Deterministic vs RAG architecture

### Week 2: Analysis & Documentation
- **Mon:** Context window + prompt strategies
- **Tue:** Statistical analysis
- **Wed:** Generate visualizations
- **Thu:** Write methodology + results chapters
- **Fri:** Write discussion + conclusion

---

## Notes & Observations

### 2026-01-15: Initial Planning
- Created complete architecture justification framework
- Identified 15 design decisions requiring experiments
- Prioritized into 3 tiers based on FYP impact
- Current status: Waiting for baseline test to complete (test_results_20260115_163233.csv)

### Next Actions:
1. ⏳ Wait for baseline test completion (~30 mins remaining)
2. ✅ Analyze baseline results
3. 🎯 Start Experiment 1 (Routing Methods)

---

## Quick Reference: File Locations

### Documentation Files
- `FYP_COMPLETE_ARCHITECTURE_JUSTIFICATION.md` - Full framework
- `ROUTING_EXPERIMENTS_FYP.md` - Routing experiment details
- `FYP_RESEARCH_PROGRESS.md` - This file (progress tracker)
- `FYP_DEEP_ANALYSIS_ROOT_CAUSE.md` - Investigation narrative
- `IMPROVEMENT_02_COMPLETE.md` - Implementation details

### Code Files
- `oneclick_my_retailchain_v8.2_models_logging.py` - Main bot
- `automated_tester_csv.py` - Test framework
- `analyze_results.py` - Results comparison tool
- `check_targets.py` - Target test verification

### Test Results
- `test_results_20260115_112123.csv` - Baseline (60.6%)
- `test_results_20260115_133721.csv` - Word boundary fix (62.8%)
- `test_results_20260115_163233.csv` - Handler improvements (running...)

---

## Experiment Results Summary

### Experiment 1: Routing Methods
**Status:** 🔴 Not Started  
**Results:** [To be filled]

### Experiment 2: Embedding Models
**Status:** 🔴 Not Started  
**Results:** [To be filled]

### Experiment 3: LLM Models
**Status:** 🔴 Not Started  
**Results:** [To be filled]

---

**Last Updated:** 2026-01-15  
**Overall Progress:** 0/15 experiments (0%)  
**Target Completion:** 2 weeks from start date
