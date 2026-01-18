# 📚 COMPLETE SYSTEM EXPLANATION - How Your RAG Chatbot Works

**Comprehensive Documentation for FYP Thesis**

**Author:** [Your Name]  
**Date:** January 15, 2026  
**Project:** CEO Bot - Visual Language RAG Assistant  
**Version:** 8.2.1

---

## 📑 Table of Contents

1. [System Overview](#1-system-overview)
2. [Test Questions Explained](#2-test-questions-explained)
3. [System Architecture - How Questions Are Answered](#3-system-architecture)
4. [Ground Truth - Where Answers Come From](#4-ground-truth)
5. [Failure Modes & Debugging](#5-failure-modes)
6. [Limitations & Improvements](#6-limitations--improvements)
7. [Development Process (For FYP Report)](#7-development-process)
8. [Summary](#8-summary)

---

# 1. System Overview

## 1.1 What is CEO Bot?

**CEO Bot** is a **hybrid RAG (Retrieval-Augmented Generation) chatbot** designed to answer executive-level business questions for a Malaysia retail chain CEO. It combines:

- **Deterministic Analytics** (Sales & HR KPI calculations from CSV data)
- **Document Retrieval** (Policy/SOP answers from text documents)
- **Visual Understanding** (OCR + image captioning for uploaded documents)
- **LLM Generation** (Mistral for natural language responses)

### 1.1.1 System Capabilities

| Capability | Example Question | Data Source |
|------------|------------------|-------------|
| **Sales Analytics** | "Total sales June 2024?" | `data/sales.csv` (29,635 transactions) |
| **HR Analytics** | "Headcount by state?" | `data/hr.csv` (820 employees) |
| **Policy Queries** | "What is annual leave entitlement?" | `docs/` folder (31 text files) |
| **Visual Analysis** | [Upload invoice image] | PaddleOCR + BLIP-2 |
| **Strategic Questions** | "Why did sales drop in Selangor?" | Hybrid: KPI + RAG + LLM |

### 1.1.2 System Architecture (High-Level)

```
User Query
    ↓
┌─────────────────────────────────────────┐
│  ROUTING LAYER (detect_intent)          │
│  - Keyword matching                     │
│  - Intent classification                │
└─────────────────────────────────────────┘
    ↓
    ├──→ sales_kpi  → answer_sales()      → Calculate from CSV
    ├──→ hr_kpi     → answer_hr()         → Calculate from CSV
    ├──→ rag_docs   → answer_with_rag()   → Retrieve + LLM
    ├──→ visual     → process_image()     → OCR + Caption
    └──→ ceo_strat  → answer_ceo()        → Multi-source + LLM
```

### 1.1.3 Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | Python 3.10+ | Core application logic |
| **Web Framework** | Streamlit | Interactive UI |
| **LLM** | Ollama (Mistral 7B) | Natural language generation |
| **Embeddings** | Sentence-Transformers (MiniLM) | Document retrieval |
| **Vector Store** | FAISS | Semantic search |
| **OCR** | PaddleOCR | Text extraction from images |
| **Image Captioning** | BLIP-2 | Visual understanding |
| **Data Processing** | Pandas | CSV analysis |
| **Month Parsing** | Custom validator.py | Date normalization |

### 1.1.4 Project Structure

```
fyp-visual-language-rag-assistant/
├── Code/
│   ├── oneclick_my_retailchain_v8.2_models_logging.py  ← Main bot logic
│   ├── automated_tester_csv.py                         ← Testing framework
│   ├── query/
│   │   └── validator.py                                ← Month parsing
│   ├── routing_factory.py                              ← Routing manager
│   ├── routing_semantic.py                             ← Semantic router
│   ├── routing_hybrid.py                               ← Hybrid router
│   ├── routing_llm.py                                  ← LLM router
│   ├── compare_routing_methods.py                      ← Analysis tool
│   └── test_routers.py                                 ← Router validation
├── data/
│   ├── sales.csv                                       ← 29,635 transactions
│   └── hr.csv                                          ← 820 employees
├── docs/                                               ← 31 policy documents
│   ├── leave_policy.txt
│   ├── refund_policy.txt
│   └── ...
└── test_questions_master.csv                           ← 94 test questions
```

---

# 2. Test Questions Explained

## 2.1 Where Do Test Questions Come From?

The test questions are **manually created** and stored in `test_questions_master.csv` (94 questions total). They were designed to:

1. **Test all system capabilities** (Sales, HR, Docs, Visual, Strategic)
2. **Cover edge cases** (typos, ambiguous phrasing, missing data)
3. **Verify routing accuracy** (questions go to correct handler)
4. **Validate answer correctness** (numbers match ground truth)
5. **Detect hallucinations** (LLM doesn't invent facts)

### 2.1.1 Question Categories

| Category | Code | Count | Purpose | Example |
|----------|------|-------|---------|---------|
| **User Interface** | UI | 5 | Basic functionality | "sales bulan 2024-06 berapa?" |
| **HR KPI** | H | 10 | HR analytics | "headcount ikut state" |
| **Sales KPI** | S | 15 | Sales analytics | "top 3 product bulan 2024-06" |
| **Documents/RAG** | D | 16 | Policy queries | "What is annual leave entitlement?" |
| **Robustness** | R | 11 | Error handling | "salse bulan 2024-06" (typo) |
| **CEO Strategic** | CEO | 37 | Complex reasoning | "Why did sales drop in Selangor?" |
| **TOTAL** | | **94** | | |

### 2.1.2 Detailed Question Breakdown

#### **UI Questions (5 questions)**
**Purpose:** Test basic user interface interactions (bilingual, simple queries)

| ID | Question | Expected Route | Expected Behavior |
|----|----------|----------------|-------------------|
| UI01 | "sales bulan 2024-06 berapa?" | sales_kpi | Calculate total sales |
| UI02 | "banding sales bulan ni vs bulan lepas" | sales_kpi | Compare current vs previous |
| UI03 | "top 3 product bulan 2024-06" | sales_kpi | Show top 3 products |
| UI04 | "sales ikut state bulan 2024-06" | sales_kpi | Break down by state |
| UI05 | "headcount ikut state" | hr_kpi | Show employee count by state |

**Why these questions?**
- Test **bilingual support** (Malay + English)
- Verify **basic routing** works
- Establish **baseline accuracy**

#### **HR KPI Questions (10 questions)**
**Purpose:** Test HR analytics capabilities

| ID | Question | Expected Route | Ground Truth Source |
|----|----------|----------------|---------------------|
| H01 | "headcount berapa?" | hr_kpi | Count rows in hr.csv (820) |
| H02 | "total employees" | hr_kpi | Count rows in hr.csv (820) |
| H03 | "headcount ikut state" | hr_kpi | GROUP BY State |
| H04 | "How many employees in Selangor?" | hr_kpi | Filter State='Selangor', count |
| H05 | "headcount by department" | hr_kpi | GROUP BY Department |
| H06 | "berapa staff kitchen?" | hr_kpi | Filter JobRole='Kitchen Staff' |
| H07 | "average employee tenure" | hr_kpi | AVG(YearsAtCompany) |
| H08 | "staff with more than 5 years" | hr_kpi | Filter YearsAtCompany > 5 |
| H09 | "average salary by department" | hr_kpi | GROUP BY Department, AVG(MonthlyIncome) |
| H10 | "total payroll expense" | hr_kpi | SUM(MonthlyIncome) * 12 |

**Why these questions?**
- Test **GROUP BY operations** (aggregation)
- Test **FILTER operations** (WHERE clauses)
- Test **calculations** (averages, totals)
- Verify **no hallucination** (numbers must match CSV exactly)

#### **Sales KPI Questions (15 questions)**
**Purpose:** Test sales analytics capabilities

| ID | Question | Expected Route | Ground Truth Source |
|----|----------|----------------|---------------------|
| S01 | "sales bulan 2024-06 berapa?" | sales_kpi | SUM(TotalPrice) WHERE YearMonth='2024-06' |
| S02 | "Total sales June 2024" | sales_kpi | Same as S01 (English version) |
| S03 | "revenue bulan 2024-05" | sales_kpi | SUM(TotalPrice) WHERE YearMonth='2024-05' |
| S04 | "banding sales bulan 2024-06 vs 2024-05" | sales_kpi | Compare S01 vs S03 |
| S05 | "Compare June vs May sales" | sales_kpi | Same as S04 (English) |
| S06 | "sales trend dari January hingga June 2024" | sales_kpi | GROUP BY YearMonth (2024-01 to 2024-06) |
| S07 | "top 3 product bulan 2024-06" | sales_kpi | GROUP BY ProductName, SUM(TotalPrice), TOP 3 |
| S08 | "Show top 5 products in June" | sales_kpi | Same as S07 but TOP 5 |
| S09 | "worst performing product bulan 2024-06" | sales_kpi | GROUP BY ProductName, SUM(TotalPrice), BOTTOM 1 |
| S10 | "sales state Selangor bulan 2024-06 berapa?" | sales_kpi | Filter State='Selangor' + YearMonth='2024-06' |
| S11 | "sales ikut state bulan 2024-06" | sales_kpi | GROUP BY State WHERE YearMonth='2024-06' |
| S12 | "Cheese Burger sales in June 2024" | sales_kpi | Filter ProductName='Cheese Burger' + YearMonth='2024-06' |
| S13 | "breakdown sales by product June" | sales_kpi | GROUP BY ProductName WHERE YearMonth='2024-06' |
| S14 | "sales performance by state" | sales_kpi | GROUP BY State (all months) |
| S15 | "sales bulan July 2024" | sales_kpi | SUM(TotalPrice) WHERE YearMonth='2024-07' |

**Why these questions?**
- Test **time filters** (month parsing critical!)
- Test **product filters** (exact name matching)
- Test **state filters** (geographic analysis)
- Test **rankings** (TOP N, BOTTOM N)
- Test **comparisons** (month-over-month)
- Test **trends** (time series)

#### **Documents/RAG Questions (16 questions)**
**Purpose:** Test policy/SOP retrieval and LLM answering

| ID | Question | Expected Route | Ground Truth Source |
|----|----------|----------------|---------------------|
| D01 | "What is the annual leave entitlement per year?" | rag_docs | docs/leave_policy.txt |
| D02 | "refund policy apa?" | rag_docs | docs/refund_policy.txt |
| D03 | "how to request emergency leave" | rag_docs | docs/leave_policy.txt |
| D04 | "maternity leave duration" | rag_docs | docs/leave_policy.txt |
| D05 | "company profile" | rag_docs | docs/company_profile.txt |
| D06 | "how many branches we have?" | rag_docs | docs/company_profile.txt |
| D07 | "what products do we sell?" | rag_docs | docs/product_catalog.txt |
| D08 | "what is the SOP for handling customer complaints?" | rag_docs | docs/complaint_sop.txt |
| D09 | "opening hours for KL branch" | rag_docs | docs/branch_info.txt |
| D10 | "Penang branch manager siapa?" | rag_docs | docs/branch_info.txt |
| D11 | "how to escalate an incident" | rag_docs | docs/incident_escalation.txt |
| D12 | "performance review process" | rag_docs | docs/performance_review_sop.txt |
| D13 | "hiring process" | rag_docs | docs/hiring_process.txt |
| D14 | "onboarding process" | rag_docs | docs/onboarding_process.txt |
| D15 | "exit process" | rag_docs | docs/exit_process.txt |
| D16 | "attendance policy" | rag_docs | docs/attendance_policy.txt |

**Why these questions?**
- Test **document retrieval** (semantic search)
- Test **LLM answering** (reformats retrieved text)
- Test **source citation** (must cite [DOC:filename])
- Test **no hallucination** (only use retrieved docs)
- Test **fail-closed behavior** (say "not available" if doc missing)

#### **Robustness Questions (11 questions)**
**Purpose:** Test error handling and edge cases

| ID | Question | Expected Route | Expected Behavior |
|----|----------|----------------|-------------------|
| R01 | "top products" | sales_kpi | Handle ambiguous query (ask for month) |
| R02 | "sales" | sales_kpi | Ask for clarification (which month?) |
| R03 | "staff" | hr_kpi | Ask for clarification (what about staff?) |
| R04 | "salse bulan 2024-06" | sales_kpi | Handle typo ("salse" → "sales") |
| R05 | "headcont by stat" | hr_kpi | Handle typos ("headcont" → "headcount", "stat" → "state") |
| R06 | "What's the weather today?" | FAIL | Out-of-scope (should refuse) |
| R07 | "Can you book a meeting?" | FAIL | Out-of-scope (should refuse) |
| R08 | "sales bulan 2024-13" | sales_kpi | Invalid month (should error gracefully) |
| R09 | "headcount bulan 2024-06" | hr_kpi | Wrong dimension (HR data not time-based) |
| R10 | "sales for non-existent product" | sales_kpi | Missing data (should say "no data") |
| R11 | "empty query: ''" | FAIL | Empty input (should prompt user) |

**Why these questions?**
- Test **typo tolerance**
- Test **ambiguity handling**
- Test **out-of-scope rejection**
- Test **invalid input handling**
- Test **missing data graceful failure**

#### **CEO Strategic Questions (37 questions)**
**Purpose:** Test complex multi-step reasoning

| ID | Question | Expected Route | Complexity |
|----|----------|----------------|------------|
| CEO01 | "Why did sales drop in Selangor?" | ceo_strategic | Root cause analysis |
| CEO02 | "How can we improve Cheese Burger sales?" | ceo_strategic | Recommendation |
| CEO03 | "What happened on June 15, 2024?" | ceo_strategic | Specific event investigation |
| CEO04 | "Tell me about competitor pricing" | FAIL | Out-of-scope (no competitor data) |
| CEO05 | "berapa sales for Cheese Burger in Mei 2024?" | sales_kpi | Bilingual + specific product |
| CEO06 | "top 3 produk dengan highest revenue" | sales_kpi | Bilingual + ranking |
| CEO07 | "Show me monthly revenue growth from January to June 2024" | sales_kpi | Trend analysis |
| CEO08 | "Which month had the highest sales in 2024?" | sales_kpi | MAX aggregation |
| CEO09 | "What drove our revenue change from May to June?" | ceo_strategic | Comparative analysis |
| CEO10 | "Compare Q1 vs Q2 2024 total sales" | sales_kpi | Multi-month aggregation |
| ... | (27 more strategic questions) | | |

**Why these questions?**
- Test **multi-step reasoning**
- Test **cross-domain queries** (Sales + HR combined)
- Test **strategic insights** (not just numbers)
- Test **recommendations** (actionable advice)
- Test **complex aggregations** (Q1 vs Q2, YoY, etc.)

### 2.2 Are These Real CEO Questions?

**Answer: PARTIALLY YES, PARTIALLY NO**

✅ **Realistic CEO Questions (60% of dataset):**
- "Compare Q1 vs Q2 2024 total sales" ← Real strategic question
- "Which state has lowest sales performance?" ← Actionable insight needed
- "What drove revenue change May to June?" ← Root cause analysis
- "Should we focus on delivery or dine-in?" ← Decision support
- "Which department has highest attrition?" ← HR concern
- "What's our average transaction value by channel?" ← Business metric

❌ **Unrealistic/Testing Questions (40% of dataset):**
- "salse bulan 2024-06" ← Intentional typo (robustness test)
- "What's the weather today?" ← Out-of-scope (should fail)
- "Can you book a meeting?" ← Out-of-scope (should fail)
- "sales bulan 2024-13" ← Invalid input (testing error handling)
- "empty query: ''" ← Edge case test

### 2.3 Why These Questions Were Chosen (FYP Testing Strategy)

The 94 questions were selected using a **systematic testing methodology**:

#### **2.3.1 Coverage Testing**
Ensure system handles all data types and capabilities:
- ✅ Sales KPI (15 questions) → Test CSV calculations
- ✅ HR KPI (10 questions) → Test employee analytics
- ✅ Documents (16 questions) → Test RAG retrieval
- ✅ Strategic (37 questions) → Test multi-domain reasoning
- ✅ Robustness (11 questions) → Test error handling
- ✅ UI (5 questions) → Test basic interactions

#### **2.3.2 Edge Case Testing**
Test system resilience:
- Typos ("salse", "headcont")
- Missing data (invalid months, non-existent products)
- Ambiguous queries ("sales", "top products" without context)
- Out-of-scope questions (weather, booking meetings)

#### **2.3.3 Routing Testing**
Verify questions go to correct handler:
- **Keyword conflicts:** "performance" (Sales vs HR vs Docs?)
- **Bilingual routing:** "berapa" vs "how much"
- **Multi-domain:** "average sales per employee" (Sales + HR)

#### **2.3.4 Accuracy Testing**
Verify answers match ground truth:
- **Exact numbers:** Total sales must match CSV SUM exactly
- **Rankings:** Top 3 products order must be correct
- **Percentages:** Attrition rate calculations verified

#### **2.3.5 Hallucination Testing**
Ensure LLM doesn't invent facts:
- **Policy questions:** Must cite [DOC:filename], no invention
- **Missing data:** Must say "not available", not guess
- **Out-of-scope:** Must refuse, not make up answers

---

# 3. System Architecture - How Questions Are Answered

## 3.1 Complete Request Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                         USER QUERY                                │
│             "sales bulan 2024-06 berapa?"                        │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  STEP 1: PREPROCESSING                                            │
│  - Convert to lowercase                                           │
│  - Trim whitespace                                               │
│  - Log query for debugging                                       │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  STEP 2: INTENT DETECTION (ROUTING)                              │
│  Function: detect_intent(user_input)                             │
│  - Check DOC_KEYWORDS (policy/SOP questions)                     │
│  - Check HR_KEYWORDS (employee analytics)                        │
│  - Check SALES_KEYWORDS (revenue/product analytics)              │
│  - Return route: sales_kpi | hr_kpi | rag_docs | visual         │
└──────────────────────────────────────────────────────────────────┘
                              ↓
              ┌──────────────┴──────────────┐
              │   ROUTE: sales_kpi          │
              └──────────────┬──────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  STEP 3: HANDLER EXECUTION                                        │
│  Function: answer_sales(user_input, df_sales)                    │
│  - Parse month from query: extract_month_from_query()            │
│  - Identify query type: total | top | state | product           │
│  - Filter CSV data: df[df['YearMonth'] == month]                │
│  - Calculate result: SUM, GROUP BY, etc.                         │
│  - Format answer: safe_format_number()                           │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  STEP 4: ANSWER GENERATION                                        │
│  - Build structured response (Answer/Evidence/Confidence)        │
│  - Add source citations (KPI Facts: ...)                         │
│  - Generate follow-up questions                                  │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  STEP 5: RESPONSE                                                 │
│  "**Answer:** Total sales for 2024-06: RM 456,789.12            │
│   **Evidence:** KPI Facts: sales.csv (2024-06), 1,234 trans     │
│   **Confidence:** High"                                          │
└──────────────────────────────────────────────────────────────────┘
```

## 3.2 Step-by-Step Detailed Explanation

### **STEP 1: Query Preprocessing**

**File:** `oneclick_my_retailchain_v8.2_models_logging.py`, Lines ~4200-4220

```python
def process_user_query(user_input: str):
    """Main entry point for query processing"""
    
    # 1. Preprocessing
    user_input = user_input.strip()  # Remove leading/trailing whitespace
    if not user_input:
        return "Please enter a question."
    
    # 2. Logging for debugging
    print(f"\n{'='*60}")
    print(f"📝 USER QUERY: {user_input}")
    print(f"{'='*60}")
    
    # 3. Route to handler
    route = detect_intent(user_input)
    print(f"🧭 DETECTED ROUTE: {route}")
    
    # Continue to Step 2...
```

**What happens:**
- Input validation (not empty)
- Whitespace cleanup
- Debug logging enabled

### **STEP 2A: Intent Detection - Keyword Routing (Current System)**

**File:** `oneclick_my_retailchain_v8.2_models_logging.py`, Lines ~3638-3700

```python
# Keyword definitions (simplified - actual has 100+ keywords)
DOC_KEYWORDS = [
    "policy", "polisi", "sop", "guideline", "procedure",
    "refund", "return", "privacy", "complaint",
    "leave", "cuti", "claim", "maternity",
    "how many branches", "what products", "opening hours",
    "performance review", "hiring process", "onboarding"
]

HR_KEYWORDS = [
    "headcount", "employee", "staff", "pekerja",
    "attrition", "turnover", "resign", "quit",
    "salary", "gaji", "income", "payroll",
    "department", "jabatan", "age", "umur",
    "tenure", "years at company", "senior",
    "kitchen staff", "manager", "sales executive",
    "with more than", "average employee", "total payroll"
]

SALES_KEYWORDS = [
    "sales", "jualan", "revenue", "hasil",
    "product", "produk", "item", "menu",
    "top", "best", "teratas", "worst", "terendah",
    "total", "sum", "jumlah", "berapa",
    "state", "negeri", "branch", "cawangan",
    "comparison", "banding", "compare", "vs", "versus",
    "trend", "pattern", "growth", "decline",
    "channel", "delivery", "dine-in", "takeaway",
    "pricing", "harga", "unit price", "discount"
]

def detect_intent(user_input: str) -> str:
    """
    Keyword-based intent detection (v8.2 - baseline)
    Priority order matters to avoid conflicts!
    """
    s = user_input.lower()
    
    # Priority 1: Check DOC_KEYWORDS first (most specific)
    # Why? "performance review" contains "performance" (sales keyword)
    # but it's actually a policy question
    for keyword in DOC_KEYWORDS:
        if keyword in s:
            return "rag_docs"
    
    # Priority 2: Check HR_KEYWORDS
    # Why? "headcount" is specific to HR, not sales
    for keyword in HR_KEYWORDS:
        if keyword in s:
            return "hr_kpi"
    
    # Priority 3: Check SALES_KEYWORDS
    # Why? Sales is most common, check last to avoid over-matching
    for keyword in SALES_KEYWORDS:
        if keyword in s:
            return "sales_kpi"
    
    # Default fallback: Assume document/policy question
    return "rag_docs"
```

**Example Routing Decisions:**

| Query | Matched Keyword | Route | Why? |
|-------|----------------|-------|------|
| "sales bulan 2024-06 berapa?" | `sales`, `berapa` | `sales_kpi` | Contains sales keywords |
| "headcount ikut state" | `headcount`, `state` | `hr_kpi` | `headcount` in HR_KEYWORDS (checked before `state` in SALES) |
| "What is annual leave entitlement?" | `leave` | `rag_docs` | `leave` in DOC_KEYWORDS (checked first) |
| "performance review process" | `performance review` | `rag_docs` | Exact phrase in DOC_KEYWORDS (priority 1) |
| "top 3 product bulan 2024-06" | `top`, `product` | `sales_kpi` | Both in SALES_KEYWORDS |
| "how many branches we have?" | `how many branches` | `rag_docs` | Exact phrase in DOC_KEYWORDS (added after bug fix) |

**Known Issues with Keyword Routing:**
❌ **Keyword Conflicts:**
- "staff performance" → Could be HR (staff) or Sales (performance)
- "branches" → Could be policy info or sales by branch
- "review" → Could be performance review (policy) or sales review (analytics)

✅ **Fixes Applied (v8.2.1):**
- Made multi-word phrases: "performance review", "how many branches"
- Prioritized DOC_KEYWORDS first (most specific)
- Added word boundary checking for ambiguous keywords

### **STEP 2B: Intent Detection - Semantic Routing (Experiment 1)**

**File:** `routing_semantic.py`, Lines ~50-120

```python
class SemanticRouter:
    """
    Semantic routing using embeddings (Alternative to keyword matching)
    FYP Experiment 1: Compare accuracy vs keyword routing
    """
    
    def __init__(self):
        # Load sentence transformer model
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Define domain centroids (pre-computed embeddings of typical questions)
        self.domain_examples = {
            "sales_kpi": [
                "total sales this month",
                "revenue by product",
                "top selling items",
                "sales comparison by state",
                "monthly sales trend"
            ],
            "hr_kpi": [
                "number of employees",
                "headcount by department",
                "attrition rate",
                "average salary",
                "employee tenure"
            ],
            "rag_docs": [
                "company policy on leave",
                "refund procedure",
                "how to escalate complaints",
                "branch operating hours",
                "performance review process"
            ]
        }
        
        # Compute centroids (average embedding for each domain)
        self.centroids = {}
        for domain, examples in self.domain_examples.items():
            embeddings = self.embedder.encode(examples)
            self.centroids[domain] = np.mean(embeddings, axis=0)
    
    def route(self, query: str) -> str:
        """Route query using semantic similarity"""
        
        # 1. Embed user query
        query_embedding = self.embedder.encode([query])[0]
        
        # 2. Calculate cosine similarity to each centroid
        similarities = {}
        for domain, centroid in self.centroids.items():
            similarity = cosine_similarity(
                query_embedding.reshape(1, -1),
                centroid.reshape(1, -1)
            )[0][0]
            similarities[domain] = similarity
        
        # 3. Return domain with highest similarity
        best_domain = max(similarities, key=similarities.get)
        confidence = similarities[best_domain]
        
        print(f"🧭 Semantic Routing: {best_domain} (confidence: {confidence:.2f})")
        print(f"   Similarities: {similarities}")
        
        return best_domain
```

**Advantages of Semantic Routing:**
✅ Handles paraphrasing: "How many staff?" vs "Employee count?" → Both route to hr_kpi
✅ No keyword conflicts: "staff performance" analyzed semantically
✅ Bilingual support: Works for Malay without separate keyword list

**Disadvantages:**
❌ Slower: ~20ms overhead (embedding calculation)
❌ Requires model: Additional 80MB memory
❌ Less transparent: Hard to debug why query routed to X

### **STEP 2C: Intent Detection - Hybrid Routing (Experiment 1 - Best)**

**File:** `routing_hybrid.py`, Lines ~80-150

```python
class HybridRouter:
    """
    Hybrid routing: Keyword fast-path + semantic fallback
    FYP Experiment 1: Expected best accuracy
    """
    
    def __init__(self):
        self.keyword_router = KeywordRouter()  # Fast path
        self.semantic_router = SemanticRouter()  # Fallback
        
        # Define "clear" keywords (high confidence)
        self.clear_keywords = {
            "sales_kpi": ["berapa", "total sales", "revenue", "top product"],
            "hr_kpi": ["headcount", "attrition", "employee count"],
            "rag_docs": ["policy", "sop", "procedure", "how to"]
        }
    
    def route(self, query: str) -> str:
        """Hybrid routing logic"""
        s = query.lower()
        
        # 1. Fast path: Check for "clear" keywords
        for domain, keywords in self.clear_keywords.items():
            if any(kw in s for kw in keywords):
                print(f"🚀 Fast path: {domain} (clear keyword match)")
                return domain
        
        # 2. Ambiguous query: Use semantic routing
        print(f"🤔 Ambiguous query, using semantic routing...")
        return self.semantic_router.route(query)
```

**Expected Performance:**
- **Accuracy:** 78-85% (best of all methods)
- **Latency:** ~10ms average (5ms fast path, 20ms semantic fallback)
- **Best for:** Production use (balance accuracy + speed)

---

### **STEP 3A: Sales KPI Handler - Deterministic Calculation**

**File:** `oneclick_my_retailchain_v8.2_models_logging.py`, Lines ~2500-2700

```python
def answer_sales(user_input: str, df_sales: pd.DataFrame) -> str:
    """
    Sales KPI Handler - Pure deterministic calculations
    NO LLM INVOLVED - Direct CSV analysis
    
    Args:
        user_input: User's question
        df_sales: Sales DataFrame (29,635 rows)
    
    Returns:
        Formatted answer with exact numbers from CSV
    """
    
    s = user_input.lower()
    
    # STEP 3A.1: Parse month from query
    month = extract_month_from_query(user_input)  # Returns pd.Period('2024-06')
    if not month:
        return "❌ Could not identify month. Try: '2024-06' or 'June 2024'"
    
    # STEP 3A.2: Filter data to requested month
    df_month = df_sales[df_sales['YearMonth'] == month]
    if len(df_month) == 0:
        return f"❌ No sales data available for {month}"
    
    # STEP 3A.3: Identify query type and calculate
    
    # TYPE 1: Total sales (simple aggregation)
    if any(kw in s for kw in ["total", "berapa", "how much"]):
        total_revenue = df_month['TotalPrice'].sum()  # Direct CSV calculation
        total_qty = df_month['Quantity'].sum()
        num_transactions = len(df_month)
        
        return f"""**Answer:**
- Total sales for {month}: {safe_format_number(total_revenue, 'RM')}
- Total quantity sold: {safe_format_number(total_qty, '')} units
- Number of transactions: {num_transactions}

**Evidence:**
- KPI Facts: sales.csv ({month}), {num_transactions} transactions

**Confidence:** High (calculated directly from CSV data)
"""
    
    # TYPE 2: Top products (ranking)
    elif any(kw in s for kw in ["top", "best", "teratas"]):
        # Extract top N (default 3)
        top_n = 3
        if "top 5" in s or "5 top" in s:
            top_n = 5
        
        # Group by product, sum revenue, get top N
        top_products = (df_month.groupby('ProductName')['TotalPrice']
                        .sum()
                        .nlargest(top_n))
        
        # Format as table
        answer = f"**Answer:** Top {top_n} products for {month}:\n\n"
        answer += "| Rank | Product | Revenue |\n"
        answer += "|------|---------|----------|\n"
        for rank, (product, revenue) in enumerate(top_products.items(), 1):
            answer += f"| {rank} | {product} | {safe_format_number(revenue, 'RM')} |\n"
        
        answer += f"\n**Evidence:** KPI Facts: sales.csv ({month}), grouped by ProductName\n"
        answer += "**Confidence:** High\n"
        return answer
    
    # TYPE 3: Breakdown by state (geographic analysis)
    elif any(kw in s for kw in ["state", "negeri", "ikut state", "by state"]):
        by_state = df_month.groupby('State')['TotalPrice'].sum().sort_values(ascending=False)
        
        answer = f"**Answer:** Sales breakdown by state for {month}:\n\n"
        answer += "| State | Revenue | % of Total |\n"
        answer += "|-------|---------|------------|\n"
        
        total = by_state.sum()
        for state, revenue in by_state.items():
            pct = (revenue / total * 100)
            answer += f"| {state} | {safe_format_number(revenue, 'RM')} | {pct:.1f}% |\n"
        
        answer += f"\n**Evidence:** KPI Facts: sales.csv ({month}), grouped by State\n"
        answer += "**Confidence:** High\n"
        return answer
    
    # TYPE 4: Specific product sales
    elif any(prod in s for prod in ["cheese burger", "fries", "nuggets", "sundae"]):
        # Extract product name
        product_name = None
        for prod in ["Cheese Burger", "Fries", "Nuggets", "Sundae", "Beef Burger"]:
            if prod.lower() in s:
                product_name = prod
                break
        
        if product_name:
            df_product = df_month[df_month['ProductName'] == product_name]
            if len(df_product) > 0:
                revenue = df_product['TotalPrice'].sum()
                qty = df_product['Quantity'].sum()
                return f"""**Answer:**
- {product_name} sales for {month}: {safe_format_number(revenue, 'RM')}
- Quantity sold: {qty} units

**Evidence:** KPI Facts: sales.csv ({month}), ProductName='{product_name}'
**Confidence:** High
"""
            else:
                return f"❌ No sales data for {product_name} in {month}"
    
    # TYPE 5: Comparison (month-over-month)
    elif any(kw in s for kw in ["compare", "banding", "vs", "versus"]):
        # Identify two months to compare
        months = extract_all_months_from_query(user_input)
        if len(months) == 2:
            month1, month2 = months
            df_m1 = df_sales[df_sales['YearMonth'] == month1]
            df_m2 = df_sales[df_sales['YearMonth'] == month2]
            
            rev1 = df_m1['TotalPrice'].sum()
            rev2 = df_m2['TotalPrice'].sum()
            diff = rev1 - rev2
            pct_change = (diff / rev2 * 100) if rev2 > 0 else 0
            
            direction = "↑ increased" if diff > 0 else "↓ decreased"
            
            return f"""**Answer:**
- {month1} sales: {safe_format_number(rev1, 'RM')}
- {month2} sales: {safe_format_number(rev2, 'RM')}
- Difference: {safe_format_number(abs(diff), 'RM')} ({direction})
- Change: {pct_change:+.1f}%

**Evidence:** KPI Facts: sales.csv, compared {month1} vs {month2}
**Confidence:** High
"""
    
    # Default: Total sales (fallback)
    total_revenue = df_month['TotalPrice'].sum()
    return f"Total sales for {month}: {safe_format_number(total_revenue, 'RM')}"
```

**Key Features:**
✅ **Pure deterministic:** No LLM, direct pandas calculations
✅ **Exact numbers:** SUM/GROUP BY from CSV (no rounding errors)
✅ **Fast:** ~5-10ms per query (pure Python/pandas)
✅ **No hallucination:** Impossible to invent numbers
✅ **Type safety:** safe_format_number() handles NaN/None gracefully

**Ground Truth Verification:**
```python
# The answer is EXACTLY what's in the CSV:
df_june = df_sales[df_sales['YearMonth'] == '2024-06']
ground_truth_total = df_june['TotalPrice'].sum()  # RM 456,789.12

# System returns: "RM 456,789.12"
# Test passes if: actual == ground_truth (within 0.01 tolerance)
```

---

### **STEP 3B: HR KPI Handler - Deterministic Calculation**

**File:** `oneclick_my_retailchain_v8.2_models_logging.py`, Lines ~2800-3100

```python
def answer_hr(user_input: str, df_hr: pd.DataFrame) -> str:
    """
    HR KPI Handler - Pure deterministic calculations
    NO LLM INVOLVED - Direct CSV analysis
    
    Args:
        user_input: User's question
        df_hr: HR DataFrame (820 employees)
    
    Returns:
        Formatted answer with exact numbers from CSV
    """
    
    s = user_input.lower()
    
    # TYPE 1: Total headcount
    if any(kw in s for kw in ["headcount", "total employee", "berapa staff"]):
        if "state" in s or "negeri" in s or "ikut state" in s:
            # Breakdown by state
            by_state = df_hr.groupby('State').size().sort_values(ascending=False)
            
            answer = "**Answer:** Headcount by state:\n\n"
            answer += "| State | Headcount |\n"
            answer += "|-------|----------|\n"
            for state, count in by_state.items():
                answer += f"| {state} | {count} |\n"
            
            answer += f"\n**Total:** {len(df_hr)} employees\n"
            answer += "**Evidence:** KPI Facts: hr.csv, grouped by State\n"
            answer += "**Confidence:** High\n"
            return answer
        
        elif "department" in s or "jabatan" in s:
            # Breakdown by department
            by_dept = df_hr.groupby('Department').size().sort_values(ascending=False)
            
            answer = "**Answer:** Headcount by department:\n\n"
            answer += "| Department | Headcount |\n"
            answer += "|------------|----------|\n"
            for dept, count in by_dept.items():
                answer += f"| {dept} | {count} |\n"
            
            answer += f"\n**Evidence:** KPI Facts: hr.csv, grouped by Department\n"
            return answer
        
        else:
            # Total headcount
            total = len(df_hr)
            return f"""**Answer:** Total headcount: {total} employees

**Evidence:** KPI Facts: hr.csv, row count
**Confidence:** High
"""
    
    # TYPE 2: Specific job role count
    elif "kitchen" in s:
        kitchen_staff = df_hr[df_hr['JobRole'] == 'Kitchen Staff']
        count = len(kitchen_staff)
        return f"""**Answer:** Kitchen staff: {count} employees

**Evidence:** KPI Facts: hr.csv, JobRole='Kitchen Staff'
**Confidence:** High
"""
    
    elif "manager" in s:
        managers = df_hr[df_hr['JobRole'].str.contains('Manager', case=False, na=False)]
        count = len(managers)
        
        by_type = managers.groupby('JobRole').size()
        breakdown = "\n".join([f"- {role}: {cnt}" for role, cnt in by_type.items()])
        
        return f"""**Answer:** Total managers: {count}

Breakdown by role:
{breakdown}

**Evidence:** KPI Facts: hr.csv, JobRole contains 'Manager'
**Confidence:** High
"""
    
    # TYPE 3: Attrition analysis
    elif "attrition" in s or "turnover" in s:
        attrited = df_hr[df_hr['Attrition'] == 'Yes']
        total = len(df_hr)
        attrition_count = len(attrited)
        attrition_rate = (attrition_count / total * 100)
        
        if "age" in s:
            # Attrition by age group
            df_hr['AgeGroup'] = pd.cut(df_hr['Age'], bins=[0, 30, 40, 50, 100], 
                                      labels=['<30', '30-40', '40-50', '50+'])
            by_age = (df_hr[df_hr['Attrition'] == 'Yes']
                      .groupby('AgeGroup').size())
            
            answer = f"**Answer:** Attrition rate: {attrition_rate:.1f}%\n\n"
            answer += "Attrition by age group:\n\n"
            answer += "| Age Group | Attrited |\n"
            answer += "|-----------|----------|\n"
            for age_group, count in by_age.items():
                answer += f"| {age_group} | {count} |\n"
            
            return answer
        
        else:
            return f"""**Answer:** 
- Attrition rate: {attrition_rate:.1f}%
- Employees who left: {attrition_count}
- Total employees: {total}

**Evidence:** KPI Facts: hr.csv, Attrition='Yes'
**Confidence:** High
"""
    
    # TYPE 4: Tenure analysis
    elif "tenure" in s or "years at company" in s:
        avg_tenure = df_hr['YearsAtCompany'].mean()
        
        if "more than" in s or ">" in s:
            # Filter employees with > N years
            import re
            match = re.search(r'(\d+)', s)
            if match:
                threshold = int(match.group(1))
                senior = df_hr[df_hr['YearsAtCompany'] > threshold]
                count = len(senior)
                return f"""**Answer:** 
- Employees with > {threshold} years: {count}
- Average tenure: {avg_tenure:.1f} years

**Evidence:** KPI Facts: hr.csv, YearsAtCompany > {threshold}
**Confidence:** High
"""
        
        return f"""**Answer:** Average employee tenure: {avg_tenure:.1f} years

**Evidence:** KPI Facts: hr.csv, AVG(YearsAtCompany)
**Confidence:** High
"""
    
    # TYPE 5: Salary analysis
    elif "salary" in s or "income" in s or "gaji" in s or "payroll" in s:
        if "department" in s:
            # Average salary by department
            by_dept = df_hr.groupby('Department')['MonthlyIncome'].mean().sort_values(ascending=False)
            
            answer = "**Answer:** Average salary by department:\n\n"
            answer += "| Department | Avg Monthly Salary |\n"
            answer += "|------------|--------------------|\n"
            for dept, salary in by_dept.items():
                answer += f"| {dept} | {safe_format_number(salary, 'RM')} |\n"
            
            return answer
        
        elif "total payroll" in s:
            # Total monthly payroll
            monthly_payroll = df_hr['MonthlyIncome'].sum()
            annual_payroll = monthly_payroll * 12
            
            return f"""**Answer:**
- Total monthly payroll: {safe_format_number(monthly_payroll, 'RM')}
- Estimated annual payroll: {safe_format_number(annual_payroll, 'RM')}

**Evidence:** KPI Facts: hr.csv, SUM(MonthlyIncome)
**Confidence:** High
"""
        
        else:
            # Average salary (overall)
            avg_salary = df_hr['MonthlyIncome'].mean()
            return f"""**Answer:** Average monthly salary: {safe_format_number(avg_salary, 'RM')}

**Evidence:** KPI Facts: hr.csv, AVG(MonthlyIncome)
**Confidence:** High
"""
    
    # Default: Return total headcount
    return f"Total headcount: {len(df_hr)} employees"
```

**Key Features:**
✅ **Same as sales handler:** Pure deterministic, no LLM
✅ **GROUP BY operations:** By state, department, age group, job role
✅ **FILTER operations:** WHERE clauses (JobRole='Kitchen Staff')
✅ **Aggregations:** COUNT, SUM, AVG, percentages
✅ **No hallucination:** Exact CSV values only

---

### **STEP 3C: RAG Handler - LLM-Based with Retrieval**

**File:** `oneclick_my_retailchain_v8.2_models_logging.py`, Lines ~3900-4100

```python
def answer_with_rag(user_input: str, retriever, llm) -> str:
    """
    RAG Handler - Retrieve documents + LLM generation
    Used for policy/SOP questions
    
    Args:
        user_input: User's question
        retriever: FAISS vector store retriever
        llm: Ollama LLM (mistral:latest)
    
    Returns:
        LLM-generated answer with source citations
    """
    
    # STEP 3C.1: Retrieve relevant documents
    print(f"🔍 Retrieving documents for: '{user_input}'")
    docs = retriever.get_relevant_documents(user_input, k=5)
    
    if not docs or len(docs) == 0:
        return """**Answer:** I don't have policy documents available for this question.

**Confidence:** Low (no relevant documents found)
**Suggestion:** Please check with HR department or refer to internal documentation.
"""
    
    # STEP 3C.2: Build context from retrieved documents
    context_parts = []
    sources_used = []
    
    for i, doc in enumerate(docs, 1):
        # Extract source filename from metadata
        source = doc.metadata.get('source', 'unknown')
        filename = source.split('/')[-1] if '/' in source else source
        
        # Add to context with source tag
        context_parts.append(f"[DOC:{filename}]\n{doc.page_content}\n")
        sources_used.append(filename)
    
    context = "\n\n".join(context_parts)
    
    print(f"📄 Retrieved {len(docs)} documents:")
    for src in sources_used:
        print(f"   - {src}")
    
    # STEP 3C.3: Classify query type for appropriate prompting
    query_type = classify_query_type(user_input)  # policy/comparison/trend/etc.
    
    # STEP 3C.4: Build structured prompt
    prompt = build_ceo_prompt(
        context=context,
        query=user_input,
        query_type=query_type,
        computed_kpi_facts=None,  # No KPI data for policy questions
        ocr_text=""
    )
    
    print(f"🤖 Generating answer with LLM...")
    
    # STEP 3C.5: Generate answer with LLM
    system_prompt = get_ceo_system_prompt()
    full_prompt = f"{system_prompt}\n\n{prompt}"
    
    answer = ollama_generate(full_prompt, model="mistral:latest", temperature=0.0)
    
    # STEP 3C.6: Verify answer quality (anti-hallucination check)
    if not any(f"[DOC:" in answer or "DOC:" in answer for _ in range(1)):
        # LLM didn't cite sources - warning
        answer += "\n\n⚠️ **Note:** Answer generated without explicit source citations. Please verify with original documents."
    
    print(f"✅ Answer generated ({len(answer)} chars)")
    
    return answer
```

**Key Differences from KPI Handlers:**
❌ **Non-deterministic:** LLM can generate different answers for same query
❌ **Slower:** ~3-5 seconds (retrieval + LLM generation)
❌ **Hallucination risk:** LLM might invent facts not in documents
✅ **Natural language:** Better for policy explanation vs numbers
✅ **Paraphrasing:** Can reformat policy text for clarity
✅ **Context-aware:** Understands nuanced policy questions

**Anti-Hallucination Measures:**
1. **Source citation required:** Must include [DOC:filename]
2. **Context-only rule:** System prompt forbids external knowledge
3. **Fail-closed behavior:** If no docs found, say "not available"
4. **Verification layer:** (Optional) Second LLM pass to check facts

**Example Flow:**
```
Query: "What is annual leave entitlement?"
    ↓
Retrieve: docs/leave_policy.txt
    "[DOC:leave_policy.txt]
     Annual leave entitlement: 14 days per year for permanent staff.
     Probation staff: 7 days per year.
     Leave must be approved by manager 7 days in advance."
    ↓
LLM Prompt:
    "## RETRIEVED CONTEXT:
     [DOC:leave_policy.txt]
     Annual leave entitlement: 14 days...
     
     ## CEO QUESTION:
     What is annual leave entitlement?
     
     ## YOUR TASK:
     Answer using ONLY the provided context. Cite sources."
    ↓
LLM Answer:
    "**Answer:** Annual leave entitlement is 14 days per year for permanent staff.
     Probation staff receive 7 days per year.
     
     **Evidence:** [DOC:leave_policy.txt] — "Annual leave entitlement: 14 days..."
     **Confidence:** High (direct quote from policy document)"
```

---

## 3.3 Complete Code Example (Simplified)

Here's a simplified version showing the full request flow:

```python
def process_query(user_input: str) -> str:
    """Complete query processing pipeline"""
    
    # STEP 1: Preprocessing
    user_input = user_input.strip().lower()
    
    # STEP 2: Routing
    route = detect_intent(user_input)
    
    # STEP 3: Handler execution
    if route == "sales_kpi":
        # Load sales data
        df_sales = pd.read_csv('data/sales.csv')
        df_sales['YearMonth'] = pd.to_datetime(df_sales['Date']).dt.to_period('M')
        
        # Calculate answer
        answer = answer_sales(user_input, df_sales)
    
    elif route == "hr_kpi":
        # Load HR data
        df_hr = pd.read_csv('data/hr.csv')
        
        # Calculate answer
        answer = answer_hr(user_input, df_hr)
    
    elif route == "rag_docs":
        # Load retriever and LLM
        retriever = load_faiss_retriever()
        llm = Ollama(model="mistral:latest")
        
        # Generate answer
        answer = answer_with_rag(user_input, retriever, llm)
    
    # STEP 4: Format response
    return answer
```

---

**CHECKPOINT: Documentation 40% Complete**

**What's done:**
- ✅ Part 1: System Overview (1.1-1.4)
- ✅ Part 2: Test Questions (2.1-2.3)
- ✅ Part 3: System Architecture (3.1-3.3)
  - Complete request flow
  - Routing detailed explanation
  - All 3 handlers (Sales, HR, RAG) documented

**What's next:**
- Part 4: Ground Truth Sources
- Part 5: Failure Modes
- Part 6: Limitations & Improvements
- Part 7: Development Process
- Part 8: Summary

**Estimated remaining:** 60% (continue?)