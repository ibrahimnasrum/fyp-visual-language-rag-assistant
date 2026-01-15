# Complete FYP Architecture Justification Framework

**Date:** 2026-01-15  
**Purpose:** Systematic analysis of ALL design decisions with experimental comparisons  
**Status:** Research Planning & Implementation Roadmap  
**FYP Requirement:** Justify every architectural choice with evidence

---

## Executive Summary

Your system makes **15+ critical design decisions**. For FYP, you need to:
1. **Identify** each design choice
2. **List** alternative approaches
3. **Experiment** to compare performance
4. **Justify** why you chose each method
5. **Document** with quantified metrics

This document provides a complete framework for your FYP research.

---

## Part 1: Architectural Decision Inventory

### 1.1 Query Understanding Layer

#### Decision 1: Routing Method
**Current:** Keyword-based routing with priority hierarchy  
**File:** oneclick_my_retailchain_v8.2_models_logging.py, lines 3944-4013  
**Code:**
```python
def detect_intent(text, has_image, conversation_history):
    # Priority: Image → Docs → HR → Sales → History → Default
    if has_image: return "visual"
    if keyword_match(DOC_KEYWORDS, text): return "rag_docs"
    if keyword_match(HR_KEYWORDS, text): return "hr_kpi"
    if keyword_match(SALES_KEYWORDS, text): return "sales_kpi"
    return "rag_docs"  # default
```

**Alternatives:**
- A) Keyword routing (current)
- B) Semantic similarity routing (embeddings)
- C) LLM classification (mistral/llama)
- D) Hybrid (keyword fast path + semantic fallback)
- E) Multi-label classification (can belong to multiple domains)

**Evaluation Metrics:**
- Routing accuracy (% correct domain assignment)
- Latency (ms per query)
- Cost ($ per 1000 queries)
- Explainability score (1-5)

**Experiment Plan:** See ROUTING_EXPERIMENTS_FYP.md

---

#### Decision 2: Keyword Matching Algorithm
**Current:** Word boundary regex (\b) for single words, substring for phrases  
**File:** lines 3656-3681  
**Code:**
```python
def keyword_match(keywords, text):
    for k in keywords:
        if ' ' in k:  # Multi-word phrase
            if k in text: matched_keywords.append(k)
        else:  # Single word
            if re.search(rf'\b{re.escape(k)}\b', text):
                matched_keywords.append(k)
```

**Alternatives:**
- A) Word boundary regex (current)
- B) Simple substring matching
- C) Fuzzy matching (handle typos with edit distance)
- D) Stemming/lemmatization (match "products" to "product")
- E) Synonym expansion (match "revenue" to "sales", "income")

**Why Current Method:**
- Pro: Prevents substring collisions ("age" no longer matches "percentage")
- Con: Requires manual plural additions ("products" ≠ "product")

**Experiment:**
```python
# Test with typos, plurals, synonyms
test_cases = [
    ("salse bulan 2024-06", "sales"),  # Typo
    ("top products", "product"),       # Plural
    ("revenue June", "sales"),         # Synonym
]

methods = {
    'word_boundary': keyword_match_word_boundary,
    'fuzzy': keyword_match_fuzzy,
    'stemming': keyword_match_with_stemming
}

for query, expected in test_cases:
    for method_name, method in methods.items():
        matched = method([expected], query)
        print(f"{method_name}: {matched}")
```

---

### 1.2 Data Representation Layer

#### Decision 3: Embedding Model
**Current:** sentence-transformers/all-MiniLM-L6-v2  
**File:** line 1729  
**Code:**
```python
embedder = SentenceTransformer("all-MiniLM-L6-v2", device=device)
```

**Alternatives:**
| Model | Size | Dimensions | Speed | Quality |
|-------|------|------------|-------|---------|
| **all-MiniLM-L6-v2** (current) | 80MB | 384 | Fast | Good |
| all-mpnet-base-v2 | 420MB | 768 | Medium | Better |
| paraphrase-multilingual-MiniLM-L12-v2 | 470MB | 384 | Medium | Bilingual |
| msmarco-distilbert-base-v4 | 260MB | 768 | Fast | QA-optimized |
| e5-base-v2 | 440MB | 768 | Medium | State-of-art |

**Why Current:**
- Fast encoding (30ms per query)
- Small model size (80MB)
- Good for general text similarity
- **But:** Not optimized for bilingual (Malay/English mix)

**Experiment:**
```python
models = [
    "all-MiniLM-L6-v2",
    "all-mpnet-base-v2",
    "paraphrase-multilingual-MiniLM-L12-v2"
]

test_queries = [
    "berapa sales bulan 2024-06?",  # Mixed Malay-English
    "What is total revenue?",
    "headcount ikut state"
]

for model_name in models:
    embedder = SentenceTransformer(model_name)
    
    # Test retrieval accuracy
    for query in test_queries:
        emb = embedder.encode([query])
        scores, idx = index.search(emb, k=5)
        relevant_docs = check_relevance(idx, query)
        print(f"{model_name}: {relevant_docs}/5 relevant")
```

**Evaluation Metrics:**
- Retrieval precision@5 (% relevant docs in top 5)
- Encoding speed (ms)
- Model loading time (s)
- Memory footprint (MB)

---

#### Decision 4: Vector Database / Index Type
**Current:** FAISS IndexFlatIP (cosine similarity, flat index)  
**File:** line 1746  
**Code:**
```python
faiss.normalize_L2(emb)  # Normalize for cosine similarity
index = faiss.IndexFlatIP(emb.shape[1])  # Flat inner product
index.add(emb)
```

**Alternatives:**
| Index Type | Search Speed | Memory | Accuracy | Use Case |
|------------|--------------|--------|----------|----------|
| **IndexFlatIP** (current) | O(n) | Low | 100% | Small datasets (<100K) |
| IndexIVFFlat | O(log n) | Medium | 95-99% | Medium datasets (100K-1M) |
| IndexHNSW | O(log n) | High | 98-99.5% | Fast search priority |
| IndexLSH | O(1) | Low | 85-95% | Very fast, approximate |

**Current Dataset Size:** 30,568 vectors (Sales=29,635, HR=820, Docs=113)

**Why Current:**
- Dataset small enough for flat search (<50K vectors)
- 100% recall (no approximation)
- Simple to implement
- **Trade-off:** O(n) search = 30ms latency (acceptable for <50K)

**When to Change:**
- If dataset >100K vectors → Use IndexIVFFlat
- If need <10ms latency → Use IndexHNSW
- If dataset >1M vectors → Use IndexIVFPQ (product quantization)

**Experiment:**
```python
# Compare index types
indices = {
    'FlatIP': faiss.IndexFlatIP(384),
    'IVFPQ': faiss.index_factory(384, "IVF100,PQ8"),
    'HNSW': faiss.IndexHNSWFlat(384, 32)
}

# Build each index
for name, idx in indices.items():
    if 'IVF' in name:
        idx.train(emb)  # IVF requires training
    idx.add(emb)

# Benchmark
for query in test_queries:
    for name, idx in indices.items():
        start = time.time()
        scores, results = idx.search(query_emb, k=10)
        latency = time.time() - start
        
        # Calculate recall@10
        true_results = flat_index.search(query_emb, k=10)[1]
        recall = len(set(results[0]) & set(true_results[0])) / 10
        
        print(f"{name}: {latency*1000:.1f}ms, recall={recall:.1%}")
```

---

#### Decision 5: Context Window Size (k parameter)
**Current:** k=12 for most queries, k=40 for filtering  
**File:** line 3043  
**Code:**
```python
def retrieve_context(query, k=12, mode="all"):
    k0 = min(max(k * 5, 40), index.ntotal)  # Retrieve 40 candidates
    scores, idx = index.search(q_emb, k=k0)
    candidates = [summaries[i] for i in idx[0]]
    if mode == "docs":
        candidates = [c for c in candidates if c.startswith("[DOC:")]
    return "\n".join(candidates[:k])  # Return final k=12
```

**Alternatives:**
- A) Fixed k=12 (current)
- B) Adaptive k based on query type (policy=5, analysis=20)
- C) Similarity threshold (return all >0.7 score)
- D) Dynamic k based on token budget
- E) MMR (Maximal Marginal Relevance) for diversity

**Why k=12:**
- Fits in LLM context window (12 docs ≈ 2000 tokens)
- Balances precision vs recall
- **But:** May miss relevant docs ranked 13-20

**Experiment:**
```python
# Test different k values
k_values = [5, 10, 12, 15, 20, 30]

for k in k_values:
    contexts = retrieve_context(test_query, k=k)
    answer = generate_answer(contexts, test_query)
    
    # Evaluate
    accuracy = evaluate_answer(answer, ground_truth)
    latency = measure_latency()
    token_count = count_tokens(contexts)
    
    print(f"k={k}: accuracy={accuracy:.1%}, tokens={token_count}, latency={latency}ms")

# Find optimal k (best accuracy/token ratio)
```

---

### 1.3 Answer Generation Layer

#### Decision 6: LLM Model Selection
**Current:** Ollama with mistral:latest (4.4GB) as default  
**File:** Multiple locations, e.g., line 3669  
**Code:**
```python
# User can select: llama3, mistral, gemma2
response = ollama.chat(
    model="mistral:latest",
    messages=[{"role": "user", "content": prompt}],
    options={"num_ctx": 2048, "temperature": 0}
)
```

**Alternatives:**
| Model | Size | Speed | Quality | Memory | Language |
|-------|------|-------|---------|--------|----------|
| **mistral:latest** (current) | 4.4GB | Medium | Good | 6GB | English |
| llama3:8b | 4.7GB | Slow | Better | 8GB | English |
| gemma2:2b | 1.6GB | Fast | Fair | 3GB | English |
| qwen2:7b | 4.4GB | Medium | Good | 6GB | Multilingual |
| phi3:mini | 2.3GB | Fast | Good | 4GB | English |

**Why mistral:**
- Smaller than llama3 (4.4GB vs 4.7GB)
- Better memory stability
- Good balance of speed vs quality
- **But:** Not optimized for Malay language

**Experiment:**
```python
models = ["mistral:latest", "llama3:8b", "gemma2:2b", "qwen2:7b"]

for model in models:
    results = []
    for test_query in test_suite:
        start = time.time()
        answer = generate_answer_with_model(model, test_query)
        latency = time.time() - start
        
        # Evaluate
        accuracy = check_correctness(answer, ground_truth)
        hallucination = detect_hallucination(answer, context)
        
        results.append({
            'model': model,
            'accuracy': accuracy,
            'latency': latency,
            'hallucination': hallucination
        })
    
    # Summarize per model
    print(f"{model}: accuracy={np.mean([r['accuracy'] for r in results]):.1%}")
```

**Evaluation Metrics:**
- Answer accuracy (% correct)
- Hallucination rate (% fabricated numbers)
- Latency (seconds per query)
- Bilingual performance (Malay queries)

---

#### Decision 7: Prompt Engineering Strategy
**Current:** Few-shot with query type classification  
**File:** lines 3183-3330  
**Code:**
```python
def build_ceo_prompt(context, query, query_type, ...):
    parts = []
    # 1. Conversation history
    # 2. User preferences
    # 3. Retrieved context
    # 4. Computed KPI facts
    # 5. OCR text
    # 6. Query-specific guidance (few-shot examples)
    # 7. CEO question
    # 8. Response instructions
    return "\n".join(parts)
```

**Alternatives:**
- A) Few-shot with examples (current)
- B) Zero-shot with detailed instructions
- C) Chain-of-Thought (step-by-step reasoning)
- D) ReAct (Reasoning + Acting)
- E) Template-based (fill-in-the-blank)

**Why Few-Shot:**
- Guides LLM output format
- Reduces hallucination with examples
- Better than zero-shot for structured outputs
- **But:** Long prompts (increases latency)

**Experiment:**
```python
prompt_strategies = {
    'few_shot': build_few_shot_prompt,
    'zero_shot': build_zero_shot_prompt,
    'chain_of_thought': build_cot_prompt,
    'react': build_react_prompt
}

for strategy_name, builder in prompt_strategies.items():
    for test_query in test_suite:
        prompt = builder(context, test_query)
        answer = llm.generate(prompt)
        
        # Evaluate
        accuracy = evaluate(answer)
        tokens = count_tokens(prompt)
        cost = calculate_cost(tokens)
        
        print(f"{strategy_name}: accuracy={accuracy:.1%}, tokens={tokens}, cost=${cost:.4f}")
```

---

#### Decision 8: Temperature Setting
**Current:** temperature=0 (deterministic)  
**File:** Multiple locations  
**Code:**
```python
options={"num_ctx": 2048, "temperature": 0, "num_predict": 400}
```

**Alternatives:**
- A) Temperature = 0 (current, deterministic)
- B) Temperature = 0.3 (slightly creative)
- C) Temperature = 0.7 (balanced)
- D) Temperature = 1.0 (very creative)
- E) Adaptive temperature (0 for KPI, 0.7 for insights)

**Why Temperature=0:**
- Deterministic answers (same query → same answer)
- Better for factual KPI queries
- Easier to test and debug
- **But:** Less creative for explanatory questions

**Experiment:**
```python
temperatures = [0, 0.3, 0.5, 0.7, 1.0]

for temp in temperatures:
    # Run same query 5 times
    answers = []
    for _ in range(5):
        ans = generate_answer(query, temperature=temp)
        answers.append(ans)
    
    # Calculate variance
    variance = measure_answer_variance(answers)
    accuracy = np.mean([evaluate(a) for a in answers])
    
    print(f"T={temp}: accuracy={accuracy:.1%}, variance={variance:.2f}")
```

---

### 1.4 Hybrid Architecture Layer

#### Decision 9: Deterministic vs RAG Routing Priority
**Current:** Try deterministic first, fallback to RAG  
**File:** lines 4062-4120  
**Code:**
```python
def rag_query_ui(user_input, ...):
    intent = detect_intent(user_input, has_image, conversation_history)
    
    if intent == "sales_kpi":
        sales_ans = answer_sales_ceo_kpi(user_input)
        if sales_ans is None:
            route = "rag_sales"  # Fallback to RAG
    
    elif intent == "hr_kpi":
        hr_ans = answer_hr(user_input)
        if hr_ans is None:
            route = "rag_docs"  # Fallback to RAG
    
    # Generate answer with RAG
    return generate_answer_with_model_stream(...)
```

**Alternatives:**
- A) Deterministic first, RAG fallback (current)
- B) RAG only (no deterministic handlers)
- C) Always use both, ensemble answers
- D) LLM decides which method to use
- E) Confidence-based routing

**Why Deterministic First:**
- Exact answers for structured queries (100% accuracy for SUM, AVG)
- Fast (0.1ms vs 20s for LLM)
- No hallucination risk for numbers
- **But:** Limited to predefined patterns

**Experiment:**
```python
architectures = {
    'deterministic_first': hybrid_architecture,
    'rag_only': rag_only_architecture,
    'ensemble': ensemble_architecture
}

for arch_name, arch in architectures.items():
    for test_query in test_suite:
        answer = arch.answer(test_query)
        
        # Evaluate
        accuracy = evaluate_answer(answer)
        latency = measure_latency()
        
        print(f"{arch_name}: accuracy={accuracy:.1%}, latency={latency:.1f}s")
```

---

#### Decision 10: Handler Implementation (Pandas vs SQL)
**Current:** Pandas DataFrames for data manipulation  
**File:** answer_sales_ceo_kpi() and answer_hr() functions  
**Code:**
```python
# Current: Pandas
df_filtered = df_sales[df_sales["YearMonth"] == month]
total = float(df_filtered["TotalSale"].sum())

# Alternative: SQL
result = df_sales.query(f"YearMonth == '{month}'")
total = result["TotalSale"].sum()
```

**Alternatives:**
- A) Pandas (current)
- B) SQL queries via pandas.query()
- C) DuckDB (SQL on DataFrames)
- D) Polars (faster than Pandas)
- E) Direct CSV parsing with Python

**Why Pandas:**
- Flexible data manipulation
- Familiar syntax
- Rich ecosystem
- **But:** Slower than Polars/DuckDB for large datasets

**Experiment:**
```python
# Benchmark data processing methods
methods = {
    'pandas': lambda df: df[df["YearMonth"] == "2024-06"]["TotalSale"].sum(),
    'pandas_query': lambda df: df.query("YearMonth == '2024-06'")["TotalSale"].sum(),
    'duckdb': lambda df: duckdb.query("SELECT SUM(TotalSale) FROM df WHERE YearMonth='2024-06'"),
    'polars': lambda df: pl.DataFrame(df).filter(pl.col("YearMonth") == "2024-06")["TotalSale"].sum()
}

for method_name, method in methods.items():
    start = time.time()
    result = method(df_sales)
    latency = time.time() - start
    
    print(f"{method_name}: {result}, latency={latency*1000:.1f}ms")
```

---

### 1.5 System Integration Layer

#### Decision 11: Caching Strategy
**Current:** FAISS index caching with pickle  
**File:** lines 1735-1765  
**Code:**
```python
CACHE_INDEX = Path("faiss_index_cache.pkl")
CACHE_SUMMARIES = Path("summaries_cache.pkl")

if CACHE_INDEX.exists():
    print("📦 Loading cached FAISS index...")
    with open(CACHE_INDEX, "rb") as f:
        index = pickle.load(f)
    with open(CACHE_SUMMARIES, "rb") as f:
        summaries = pickle.load(f)
else:
    # Build index
    # Save cache
    with open(CACHE_INDEX, "wb") as f:
        pickle.dump(index, f)
```

**Alternatives:**
- A) Pickle caching (current)
- B) No caching (rebuild every time)
- C) Redis (distributed cache)
- D) Save as binary files (faiss.write_index)
- E) Incremental updates (only new data)

**Why Pickle:**
- Simple to implement
- Fast loading (<1s for 30K vectors)
- Good for single-server deployment
- **But:** Not suitable for distributed systems

**Trade-offs:**
- Cold start: 60s (build index)
- Warm start: 0.5s (load cache)
- Cache invalidation: Manual (delete cache file)

---

#### Decision 12: Conversation Memory
**Current:** Stateless (no persistent memory)  
**File:** USER_MEMORY dictionary, but resets per session  
**Code:**
```python
USER_MEMORY = {}  # Resets when server restarts

def rag_query_ui(user_input, ..., conversation_history=[]):
    # conversation_history passed from Gradio state
    # But not persisted to disk/database
```

**Alternatives:**
- A) Stateless (current)
- B) Session-based (store in Redis)
- C) Persistent database (PostgreSQL)
- D) Vector memory (embed past conversations)
- E) Hierarchical memory (short-term + long-term)

**Why Stateless:**
- Simple to implement
- No database required
- Good for MVP/prototype
- **But:** Loses context after server restart

**Experiment:** Not needed - implementation choice based on requirements

---

### 1.6 Visual Understanding Layer

#### Decision 13: OCR Method
**Current:** PaddleOCR for table extraction  
**File:** lines 1805-1870  
**Code:**
```python
if PADDLE_OCR_AVAILABLE:
    ocr_model = PaddleOCR(use_angle_cls=True, lang='en')
```

**Alternatives:**
- A) PaddleOCR (current)
- B) Tesseract OCR
- C) EasyOCR
- D) Google Cloud Vision API
- E) Azure Computer Vision

**Why PaddleOCR:**
- Offline (no API costs)
- Good accuracy for tables
- Supports multiple languages
- **But:** Large model size (100MB+)

**Experiment:** (Lower priority - visual features less critical)

---

#### Decision 14: Image Captioning Model
**Current:** BLIP-2 (optional, disabled by default)  
**File:** lines 1788-1803  
**Code:**
```python
BLIP2_AVAILABLE = False  # Disabled for memory efficiency

if BLIP2_AVAILABLE:
    blip2_model = Blip2ForConditionalGeneration.from_pretrained(
        "Salesforce/blip2-flan-t5-small"
    )
```

**Alternatives:**
- A) BLIP-2 small (current, disabled)
- B) CLIP + GPT (vision-language)
- C) LLaVA (open-source VLM)
- D) GPT-4 Vision API
- E) No captioning (OCR only)

**Why Disabled:**
- High memory usage (2GB+)
- Slow inference (5-10s per image)
- OCR sufficient for table/chart queries
- **Trade-off:** Can't understand scene context

---

### 1.7 Evaluation & Testing Layer

#### Decision 15: Test Framework
**Current:** Custom CSV-based testing  
**File:** automated_tester_csv.py  
**Code:**
```python
def test_question(test_data):
    outputs = list(rag_query_ui(question, ...))
    # Compare actual_route vs expected_route
    # Check if answer contains expected keywords
```

**Alternatives:**
- A) Custom framework (current)
- B) pytest with fixtures
- C) RAGAS (RAG evaluation framework)
- D) LangChain evaluators
- E) Manual evaluation

**Why Custom:**
- Full control over metrics
- Easy CSV export for analysis
- Simple to understand
- **But:** Reinventing the wheel

**Experiment:** Compare custom vs RAGAS metrics

---

## Part 2: Prioritized Experiment Roadmap

### Tier 1: Critical for FYP (Must Do)

**Experiment 1: Routing Methods Comparison** ⭐⭐⭐
- **Impact:** High (affects 100% of queries)
- **Effort:** 2 days
- **File:** ROUTING_EXPERIMENTS_FYP.md (already created)
- **Metrics:** Routing accuracy, E2E accuracy, latency, cost
- **Expected Finding:** Hybrid routing best for production

**Experiment 2: Embedding Model Comparison** ⭐⭐⭐
- **Impact:** High (affects RAG quality)
- **Effort:** 1 day
- **Test:** 3 models on 94 queries, measure retrieval precision
- **Expected Finding:** Multilingual model better for mixed Malay/English

**Experiment 3: LLM Model Selection** ⭐⭐⭐
- **Impact:** High (affects answer quality)
- **Effort:** 1 day (can run overnight)
- **Test:** 4 models on 94 queries, measure accuracy + hallucination
- **Expected Finding:** mistral best balance, llama3 most accurate

---

### Tier 2: Important for FYP (Should Do)

**Experiment 4: Deterministic vs RAG Architecture** ⭐⭐
- **Impact:** Medium (justifies hybrid design)
- **Effort:** 1 day
- **Test:** Pure RAG vs Hybrid on KPI queries
- **Expected Finding:** Hybrid 20%+ more accurate for structured queries

**Experiment 5: Context Window Size (k)** ⭐⭐
- **Impact:** Medium (affects retrieval quality)
- **Effort:** 4 hours
- **Test:** k=5,10,12,15,20,30 on 94 queries
- **Expected Finding:** k=12 optimal (accuracy plateaus after 15)

**Experiment 6: Prompt Engineering Strategies** ⭐⭐
- **Impact:** Medium (affects output format)
- **Effort:** 1 day
- **Test:** Few-shot vs Zero-shot vs CoT on 94 queries
- **Expected Finding:** Few-shot best for structured output

---

### Tier 3: Nice to Have (Optional)

**Experiment 7: FAISS Index Types** ⭐
- **Impact:** Low (dataset small)
- **Effort:** 4 hours
- **Expected:** Flat index sufficient for 30K vectors

**Experiment 8: Temperature Settings** ⭐
- **Impact:** Low (deterministic needed for KPI)
- **Effort:** 2 hours
- **Expected:** T=0 best for factual queries

**Experiment 9: Data Processing Methods** ⭐
- **Impact:** Low (latency acceptable)
- **Effort:** 2 hours
- **Expected:** Pandas sufficient, Polars 2-3x faster

---

## Part 3: Implementation Schedule

### Week 1: Core Architecture Experiments
**Day 1-2: Routing Methods**
- Implement semantic routing
- Implement LLM routing
- Implement hybrid routing
- Run full test suite (4 x 94 queries)
- Document results in ROUTING_EXPERIMENTS_FYP.md

**Day 3: Embedding Models**
- Test 3 embedding models
- Measure retrieval precision@5
- Document model selection rationale

**Day 4: LLM Models**
- Test 4 LLM models
- Measure accuracy, hallucination, latency
- Document model selection

**Day 5: Deterministic vs RAG**
- Implement pure RAG baseline
- Compare hybrid vs RAG-only
- Document architecture justification

---

### Week 2: Optimization & Documentation
**Day 6: Context & Prompts**
- Test k values (context window)
- Test prompt strategies
- Document optimal configurations

**Day 7: Results Analysis**
- Create comparison tables
- Generate visualizations
- Statistical significance testing

**Day 8-9: FYP Writing**
- Write methodology chapter
- Write results chapter
- Create presentation slides

**Day 10: Buffer**
- Handle unexpected issues
- Final testing
- Proofread documentation

---

## Part 4: Documentation Template

### For Each Experiment

```markdown
## Experiment X: [Decision Name]

### Hypothesis
H0: Method A and Method B have equal performance
H1: Method A outperforms Method B on metric M

### Experimental Design
- **Test Dataset:** 94 questions from automated_tester_csv.py
- **Methods Compared:** A, B, C, D
- **Evaluation Metrics:** 
  - Primary: Accuracy (% correct answers)
  - Secondary: Latency (ms), Cost ($), Memory (MB)
- **Statistical Test:** Paired t-test, α=0.05

### Implementation
```python
# Code for experiment
```

### Results
| Method | Accuracy | Latency | Cost | Memory |
|--------|----------|---------|------|--------|
| A | 75.0% | 25ms | $0 | 80MB |
| B | 82.3% | 150ms | $0.10 | 420MB |
| C | 88.5% | 3000ms | $2.50 | 100MB |

### Statistical Analysis
- Method C significantly better than A (p<0.001)
- Method B vs C not significant (p=0.07)

### Decision Justification
**Chosen:** Method B (all-mpnet-base-v2)
**Reasoning:**
- 7.3% accuracy improvement over A
- 20x faster than C
- 25x cheaper than C
- Acceptable 125ms latency increase
- Good balance of performance vs cost

### Trade-offs
- **Pros:** Better retrieval, reasonable speed, cost-effective
- **Cons:** Larger model (420MB vs 80MB), higher memory
- **When to reconsider:** If memory <512MB or need <50ms latency

### FYP Contribution
This experiment demonstrates systematic evaluation of embedding models
for bilingual RAG systems, with quantified trade-offs between accuracy,
speed, and resource usage.
```

---

## Part 5: Analysis Tools

### Tool 1: Experiment Runner
```python
# experiments_framework.py

class ExperimentRunner:
    def __init__(self, test_suite, metrics):
        self.test_suite = test_suite
        self.metrics = metrics
        self.results = []
    
    def run_experiment(self, methods, name):
        print(f"\n{'='*60}")
        print(f"Experiment: {name}")
        print(f"{'='*60}\n")
        
        for method_name, method_impl in methods.items():
            print(f"Testing {method_name}...")
            
            method_results = []
            for test in self.test_suite:
                result = method_impl.run(test)
                metrics = self.evaluate(result, test)
                method_results.append(metrics)
            
            # Aggregate
            summary = self.aggregate_results(method_results)
            summary['method'] = method_name
            self.results.append(summary)
        
        # Statistical tests
        self.run_statistical_tests()
        
        # Generate report
        self.generate_report(name)
    
    def evaluate(self, result, test):
        return {
            'accuracy': self.metrics['accuracy'](result, test.expected),
            'latency': result.latency,
            'cost': self.metrics['cost'](result),
            'memory': self.metrics['memory']()
        }
    
    def aggregate_results(self, results):
        return {
            'accuracy_mean': np.mean([r['accuracy'] for r in results]),
            'accuracy_std': np.std([r['accuracy'] for r in results]),
            'latency_mean': np.mean([r['latency'] for r in results]),
            'cost_total': sum([r['cost'] for r in results]),
            'memory_peak': max([r['memory'] for r in results])
        }
    
    def run_statistical_tests(self):
        # Paired t-test between methods
        from scipy import stats
        
        for i, method_a in enumerate(self.results):
            for method_b in self.results[i+1:]:
                t_stat, p_value = stats.ttest_rel(
                    method_a['accuracies'],
                    method_b['accuracies']
                )
                
                print(f"\n{method_a['method']} vs {method_b['method']}:")
                print(f"  t-statistic: {t_stat:.3f}")
                print(f"  p-value: {p_value:.4f}")
                print(f"  Significant: {'Yes' if p_value < 0.05 else 'No'}")
    
    def generate_report(self, experiment_name):
        # Create markdown report
        report = f"# {experiment_name} Results\n\n"
        
        # Summary table
        report += "## Summary\n\n"
        report += "| Method | Accuracy | Latency | Cost | Memory |\n"
        report += "|--------|----------|---------|------|--------|\n"
        
        for result in self.results:
            report += f"| {result['method']} | "
            report += f"{result['accuracy_mean']:.1%} | "
            report += f"{result['latency_mean']:.0f}ms | "
            report += f"${result['cost_total']:.2f} | "
            report += f"{result['memory_peak']:.0f}MB |\n"
        
        # Save report
        filename = f"EXPERIMENT_{experiment_name.upper()}_RESULTS.md"
        with open(filename, 'w') as f:
            f.write(report)
        
        print(f"\n✅ Report saved: {filename}")
```

### Tool 2: Visualization Generator
```python
# visualizations.py

import matplotlib.pyplot as plt
import seaborn as sns

def plot_comparison(results, metric='accuracy'):
    """Create bar chart comparing methods"""
    methods = [r['method'] for r in results]
    values = [r[f'{metric}_mean'] for r in results]
    errors = [r[f'{metric}_std'] for r in results]
    
    plt.figure(figsize=(10, 6))
    plt.bar(methods, values, yerr=errors, capsize=5)
    plt.ylabel(metric.capitalize())
    plt.title(f'{metric.capitalize()} Comparison')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'comparison_{metric}.png', dpi=300)
    print(f"✅ Saved: comparison_{metric}.png")

def plot_tradeoff(results):
    """Create scatter plot of accuracy vs latency"""
    plt.figure(figsize=(10, 6))
    
    for result in results:
        plt.scatter(
            result['latency_mean'],
            result['accuracy_mean'],
            s=200,
            alpha=0.6
        )
        plt.annotate(
            result['method'],
            (result['latency_mean'], result['accuracy_mean']),
            xytext=(5, 5),
            textcoords='offset points'
        )
    
    plt.xlabel('Latency (ms)')
    plt.ylabel('Accuracy')
    plt.title('Accuracy vs Latency Trade-off')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('tradeoff_accuracy_latency.png', dpi=300)
    print("✅ Saved: tradeoff_accuracy_latency.png")

def plot_radar(results):
    """Create radar chart for multi-metric comparison"""
    # Normalize metrics to 0-1 scale
    metrics = ['accuracy', 'speed', 'cost', 'memory']
    
    # Implementation of radar chart
    # (Code omitted for brevity)
```

---

## Part 6: Success Criteria

### Minimum FYP Requirements ✅
- [ ] 3+ architectural decisions justified with experiments
- [ ] Quantified metrics for each decision
- [ ] Statistical significance testing
- [ ] Clear documentation of trade-offs
- [ ] Comparison tables and visualizations

### Good FYP (70-80%) ✅✅
- [ ] 5+ decisions with experiments
- [ ] Novel insights (e.g., hybrid routing)
- [ ] Comprehensive documentation
- [ ] Production deployment considerations
- [ ] Limitations and future work sections

### Excellent FYP (80-90%) ⭐⭐⭐
- [ ] 8+ decisions systematically analyzed
- [ ] Original contributions (new methods)
- [ ] Published-paper quality documentation
- [ ] Reusable experimental framework
- [ ] Open-source code + documentation

---

## Part 7: Time Investment

### Conservative Estimate (Minimum for passing FYP)
- **Routing experiments:** 2 days
- **Model comparisons:** 2 days  
- **Documentation:** 2 days
- **Total:** 6 days (1 week)

### Recommended (For good grade)
- **Core experiments:** 5 days
- **Analysis + visualization:** 2 days
- **FYP writing:** 3 days
- **Total:** 10 days (2 weeks)

### Ambitious (For excellent grade)
- **All experiments:** 7 days
- **Framework development:** 2 days
- **Comprehensive documentation:** 4 days
- **Total:** 13 days (2.5 weeks)

---

## Conclusion

You now have:
1. ✅ **Complete inventory** of 15 architectural decisions
2. ✅ **Alternative methods** for each decision
3. ✅ **Experimental designs** ready to implement
4. ✅ **Prioritized roadmap** (Tier 1 = must do, Tier 2 = should do, Tier 3 = nice to have)
5. ✅ **Documentation templates** for each experiment
6. ✅ **Analysis tools** (experiment runner, visualizations)
7. ✅ **Success criteria** for different FYP grades

**Next Steps:**
1. Wait for current test to complete (baseline for experiments)
2. Start with Tier 1 experiments (routing, embeddings, LLMs)
3. Document each experiment using the template
4. Generate visualizations and comparison tables
5. Write FYP chapters using documented results

**Your FYP will demonstrate:**
- Systematic evaluation methodology
- Evidence-based design decisions
- Quantified trade-offs
- Production-ready considerations
- Original research contributions

This transforms your project from "I implemented a chatbot" to "I systematically evaluated 15 architectural decisions with empirical evidence to build an optimized multi-domain RAG system."

---

**Status:** READY TO START EXPERIMENTS  
**Priority:** Tier 1 experiments first (routing → embeddings → LLMs)  
**Timeline:** 2 weeks for comprehensive experiments + documentation
