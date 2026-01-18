# How to Evaluate Answer Quality - Practical Guide

## 📦 Installation Guide

### Prerequisites
- **Python 3.9+** (Check: `python --version`)
- **pip** package manager
- **Git** (for cloning repository)

### Step 1: Clone Repository
```bash
git clone <repository-url>
cd fyp-visual-language-rag-assistant
```

### Step 2: Create Virtual Environment
**Windows**:
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux**:
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` prefix in your terminal.

### Step 3: Install Dependencies
```bash
pip install -r Code/requirements.txt
```

This installs:
- `gradio-client` - Gradio API communication
- `sentence-transformers` - Semantic similarity
- `scikit-learn` - Classification metrics
- `scipy` - Statistical tests
- `numpy` - Numerical operations
- `pandas` - Data processing
- `matplotlib` - Visualization

**Verify installation**:
```bash
python -c "import sentence_transformers; print('✓ Installed successfully')"
```

### Step 4: Download Sentence Transformer Model
First run will download ~80MB model (one-time):
```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### Step 5: Test Installation
**Run demo**:
```bash
cd Code
python demo_two_tier_evaluation.py
```

Should output:
```
✅ Answer quality evaluator initialized
Example 1 (H08): quality=0.816 → ACCEPTABLE
Example 2 (R03): quality=0.660 → FAILED
Example 3 (H03): quality=0.785 → ACCEPTABLE
```

**Run statistical comparison**:
```bash
python statistical_comparison_demo.py
```

Should show t-test results with p-value < 0.05.

**Run evaluation metrics demo**:
```bash
python evaluation_metrics.py
```

Should generate:
- `demo_confusion_matrix.png`
- `demo_latency_distribution.png`

### Step 6: Start Gradio App (Required for Full Tests)
In a separate terminal:
```bash
python app.py  # Your main Gradio application
```

Verify it's running at: http://127.0.0.1:7866

### Step 7: Run Full Test Suite
```bash
cd Code
python automated_test_runner.py
```

**Optional - Limit tests per category**:
```bash
python automated_test_runner.py 5  # Run only 5 tests per category
```

**Output files**:
- `test_results_TIMESTAMP.json` - Complete results with advanced metrics
- `test_results_TIMESTAMP.csv` - Excel-compatible format
- `confusion_matrix_TIMESTAMP.png` - Routing visualization
- `latency_distribution_TIMESTAMP.png` - Performance visualization

### Troubleshooting

**Issue**: `ModuleNotFoundError: No module named 'gradio_client'`
```bash
pip install gradio-client
```

**Issue**: `Connection refused` when running tests
- Make sure Gradio app is running: `python app.py`
- Check URL matches: `http://127.0.0.1:7866`

**Issue**: Slow first run
- Normal! Downloading sentence-transformers model (~80MB)
- Subsequent runs will be fast (model cached)

**Issue**: `ImportError: DLL load failed` on Windows
```bash
pip install --upgrade torch --index-url https://download.pytorch.org/whl/cu118
```

### Deactivate Virtual Environment
When done:
```bash
deactivate
```

---

## 🎯 Quick Evaluation Checklist

For EACH question you test, check these 3 things:

### 1️⃣ Route Badge (Top of answer)
**Location**: Look at the colored badge at the top of the response

✅ **CORRECT** if badge shows:
- Sales questions → `sales_kpi` badge
- HR questions → `hr_kpi` badge  
- Policy questions → `rag_docs` badge

❌ **WRONG** if:
- "sales bulan 2024-06" shows `rag_docs` (wrong route)
- "What is annual leave policy?" shows `sales_kpi` (wrong route)

---

### 2️⃣ Answer Quality (The main response)
Check if the answer is **complete, accurate, and specific**

#### For SALES Questions:
✅ **GOOD Answer**:
- Shows specific RM amount (e.g., "RM 99,852.83")
- Includes the correct month/period you asked for
- Shows table/breakdown when requested
- Numbers match what you'd calculate from data

❌ **BAD Answer**:
- Vague: "Sales have been increasing..." (no numbers)
- Wrong period: Asked June, got May data
- Hallucinated: Invents products/numbers not in data
- Incomplete: Asked top 5, only shows top 3

**Example - GOOD**:
```
## ✅ Total Sales (RM)
Month: 2024-06
Value: RM 99,852.83
```

**Example - BAD**:
```
Based on the data, sales performance has been positive.
[No specific numbers, too vague]
```

#### For HR Questions:
✅ **GOOD Answer**:
- Shows specific count (e.g., "820 employees")
- Breakdown by state/department when requested
- Numbers add up correctly

❌ **BAD Answer**:
- Vague: "We have many employees..."
- Wrong calculation
- Missing requested breakdown

#### For RAG/Policy Questions:
✅ **GOOD Answer**:
- Quotes or summarizes from actual document
- Says document name (e.g., "According to HR_Policy_MY.txt")
- Specific details (e.g., "14 days annual leave")
- Says "I don't have this information" if not available

❌ **BAD Answer**:
- Makes up policy details not in documents
- Too vague: "Leave is granted as per policy"
- Doesn't cite document source
- Claims to know things not in your docs

---

### 3️⃣ Follow-up Questions (Below the answer)
Look at the 3 suggested follow-up questions

✅ **GOOD Follow-ups**:
- Relevant to your question
- Preserve context (if you asked about Selangor, follow-ups mention Selangor)
- Actionable (you can click and get useful answer)

❌ **BAD Follow-ups**:
- Generic: "Can you clarify?" (not helpful)
- Lost context: Asked about Selangor, follow-up forgets the state
- Irrelevant: Asked about sales, suggests HR questions

---

## 📝 How to Record Results

### Simple Method: Use Notepad/Text File

Create a file: `test_results_[your_name]_[date].txt`

For each question, copy this template:

```
============================================================
[Test ID: S01] 
Question: sales bulan 2024-06 berapa?
------------------------------------------------------------
ROUTE: sales_kpi ✓        [✓ Correct / ✗ Wrong]
ANSWER: ✓ Accurate        [✓ Accurate / ~ Partial / ✗ Wrong]
  - Shows: RM 99,852.83 for June 2024
  - Specific and complete
FOLLOW-UPS: ✓ Good        [✓ Good / ~ OK / ✗ Poor]
  1. Compare June with previous month
  2. Break down by state
  3. Show top 5 products this month
OVERALL: PASS             [PASS / FAIL / NEEDS_REVIEW]
NOTES: Everything works correctly
============================================================
```

### Quick Marking System:

**For Route**:
- ✓ = Correct route badge
- ✗ = Wrong route badge

**For Answer**:
- ✓ = Accurate, complete, specific
- ~ = Partially correct (has some issues)
- ✗ = Wrong/inaccurate/too vague

**For Follow-ups**:
- ✓ = All 3 relevant and preserve context
- ~ = Some OK, some irrelevant
- ✗ = Not helpful/generic

**Overall Status**:
- **PASS** = Route correct + Answer accurate + Follow-ups good
- **FAIL** = Route wrong OR answer inaccurate
- **NEEDS_REVIEW** = Partial issues, uncertain

---

## 🔍 Detailed Evaluation Examples

### Example 1: PASS
```
Question: top 3 product bulan 2024-06

Route Badge: sales_kpi ✓

Answer:
## 🏆 Top 3 Products by Sales (RM)
Month: 2024-06

1. Cheese Burger: RM 20,250.99 (20.3%)
2. Beef Burger: RM 19,705.96 (19.7%)  
3. Chicken Burger: RM 18,916.92 (18.9%)

Follow-ups:
1. What's different about the top performers?
2. Compare top vs bottom performers
3. Show Cheese Burger sales trend

✅ EVALUATION:
- Route: ✓ Correct (sales_kpi)
- Answer: ✓ Accurate (shows exactly 3 products, specific amounts)
- Follow-ups: ✓ Good (relevant, preserve product context)
- OVERALL: PASS
```

---

### Example 2: FAIL (Wrong Answer)
```
Question: top 3 product bulan 2024-06

Route Badge: sales_kpi ✓

Answer:
## 🏆 Top Products by Sales
1. Cheese Burger: RM 20,250.99
2. Beef Burger: RM 19,705.96
3. Chicken Burger: RM 18,916.92
4. Fish Burger: RM 17,234.50
5. Veggie Burger: RM 15,987.32

Follow-ups: [...]

❌ EVALUATION:
- Route: ✓ Correct (sales_kpi)
- Answer: ✗ WRONG - Shows 5 products when asked for 3! (Bug #3)
- Follow-ups: ✓ Good
- OVERALL: FAIL
- NOTES: Top N bug - shows top 5 instead of top 3
```

---

### Example 3: FAIL (Wrong Route)
```
Question: sales bulan 2024-06 berapa?

Route Badge: rag_docs ✗

Answer:
Based on available documents, sales have been performing well
in recent months. The company has seen growth...
[Vague, no specific numbers]

Follow-ups: [...]

❌ EVALUATION:
- Route: ✗ WRONG - Should be sales_kpi, not rag_docs
- Answer: ✗ WRONG - No specific amount, too vague
- Follow-ups: ~ OK but not great
- OVERALL: FAIL
- NOTES: Routing error - sales query went to RAG instead of KPI
```

---

### Example 4: NEEDS_REVIEW (Partial)
```
Question: Why did sales drop in Selangor?

Route Badge: rag_docs ✓

Answer:
I don't have specific information about why sales dropped in 
Selangor. Based on available documents, there may be various 
operational factors. Would you like me to show the actual 
sales numbers for Selangor to analyze the trend?

Follow-ups:
1. Show Selangor sales trend over 6 months
2. Compare Selangor vs other states
3. What are the operational challenges in Selangor?

~ EVALUATION:
- Route: ✓ Correct (rag_docs)
- Answer: ~ Partial - Admits no specific info (good), but could be more helpful
- Follow-ups: ✓ Good - Preserve Selangor context
- OVERALL: NEEDS_REVIEW
- NOTES: Acceptable - at least doesn't hallucinate, but could provide data-driven insights
```

---

## 🎯 Priority Checks

### CRITICAL Issues (Must report immediately):
1. **Wrong route** - Question goes to wrong category
2. **Hallucinated numbers** - Makes up sales figures
3. **Wrong calculations** - Math errors
4. **Context loss** - Follow-up forgets state/product/month
5. **Top N bug** - Shows wrong count (top 5 when asked top 3)

### Medium Issues (Note for improvement):
1. **Vague answers** - No specific numbers
2. **Missing breakdown** - Asked for table, got text
3. **Generic follow-ups** - Not context-aware

### Minor Issues (OK to ignore):
1. **Formatting differences** - Table vs list
2. **Wording differences** - "RM" vs "Ringgit Malaysia"

---

## 📊 Summary Template

After testing all questions, create a summary:

```
========================================
TESTING SUMMARY
Date: [Date]
Tested by: [Your name]
========================================

STATISTICS:
- Total questions tested: ____ / 30
- Passed: ____ (___%)
- Failed: ____ (___%)
- Needs Review: ____ (___%)

CRITICAL FAILURES:
1. [Test ID] - [Brief issue]
2. [Test ID] - [Brief issue]

PATTERNS NOTICED:
- [ ] All sales questions work correctly
- [ ] All HR questions work correctly
- [ ] RAG queries sometimes hallucinate
- [ ] Top N rankings show wrong count
- [ ] Follow-ups lose context
- [ ] Timer froze at 0.0s (if applicable)
- [ ] Stop button didn't work (if applicable)

RECOMMENDATIONS:
1. Fix: [Specific issue]
2. Improve: [Specific area]
3. Investigate: [Unclear case]
========================================
```

---

## 💡 Pro Tips

1. **Test in order** - Start with CRITICAL tests first
2. **Take screenshots** - For failed tests, screenshot the answer
3. **Compare similar questions** - Does "sales bulan 2024-06" give same result as "Total sales June 2024"?
4. **Test follow-ups** - Click a follow-up question to see if context preserved
5. **Note timing** - If query takes unusually long (>60s), note it
6. **Check console** - If app running in terminal, watch for error messages

---

## 🚀 Ready to Start?

1. Open browser to http://127.0.0.1:7866
2. Open notepad/text editor for recording results
3. Run: `python simple_manual_tester.py` to get question list
4. Start with first question, follow evaluation guide above
5. Mark ✓ / ✗ / ~ for each aspect
6. Note overall PASS/FAIL/NEEDS_REVIEW
7. Continue with remaining questions

**Time estimate**: 
- 5 questions: ~10 minutes
- Full 30 questions: ~45 minutes

Good luck! 🎯
