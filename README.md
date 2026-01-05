# 🧠 FYP AI Personal Assistant Using Visual Language Retrieval Augmented Generation(CEO Bot) — Hybrid KPI + RAG + OCR (Malaysia Retail Chain)

A **CEO-style AI Personal Assistant** for a Malaysia retail chain that can answer:

- ✅ **Sales KPI questions** *(deterministic, computed directly from CSV — no hallucination for numbers)*
- ✅ **HR KPI questions** *(deterministic, computed directly from CSV)*
- ✅ **Policy / SOP / company documents questions** *(RAG: FAISS + embeddings + LLM)*
- ✅ **Questions from images** *(OCR → text → RAG/LLM)*

Built with **Gradio UI + Ollama (local LLM) + FAISS vector search + SentenceTransformers embeddings + Tesseract OCR**.

---

## ✨ Key Features

### 1) Deterministic KPI (No hallucination for numbers)
For **Sales** & **HR** KPI queries, the system **does not rely on the LLM to compute numbers**.
It uses **pandas calculations** (filter / groupby / sum) so outputs are **repeatable**:

> Same dataset + same query → same numeric output (deterministic)

### 2) RAG for policy/docs (Grounded answers)
For policy/SOP questions, the system retrieves the most relevant chunks from `docs/*.txt` using **FAISS** similarity search, then the LLM answers using **ONLY retrieved context**.

### 3) OCR for table/chart image questions
Upload an image (table/chart screenshot), the system extracts text using **pytesseract**, appends it to the query, and answers using **RAG/LLM**.

### 4) Intent routing (Hybrid decision engine)
A routing function selects the correct path:
- `sales_kpi` → deterministic Sales KPI
- `hr_kpi` → deterministic HR KPI
- `rag_docs` → RAG (docs)
- `visual` → OCR + RAG/LLM

This improves accuracy and reduces hallucination.

### 5) Streaming answers + logging for evaluation
- **Streaming output** in UI (better UX)
- Every interaction logs to: `logs/chat_logs.csv` with:
  - timestamp, model, route, latency_ms, question, answer

---

## 🧱 System Architecture (High Level)

**User (Text/Image)** → **Router** → One of:
1. **Sales KPI Engine** (pandas)
2. **HR KPI Engine** (pandas)
3. **RAG Docs** (FAISS + Embeddings + LLM)
4. **Visual OCR** (Tesseract) → RAG/LLM

Then → **Gradio UI output** + **CSV logging**

---


✅ Default expected file names:
- `data/MY_Retail_Sales_2024H1.csv`
- `data/MY_Retail_HR_Employees.csv`

✅ Docs loading:
- Reads `docs/*.txt`
- Chunking rule: **blank lines** separate paragraphs

---

## ✅ Prerequisites

### 1) Python
- Python **3.9+** recommended

### 2) Ollama (Local LLM runtime)
Install Ollama, then pull at least one model:

```bash
ollama pull llama3:latest
```

## 3) Tesseract OCR (Required for image OCR)

Install **Tesseract OCR** and ensure `tesseract` is available in your system **PATH**.

**Windows note:** If PATH is not set, you can set the Tesseract executable path in code:

```python
pytesseract.pytesseract.tesseract_cmd = r"PATH_TO_TESSERACT_EXE"
```

## 📦 Python Dependencies
Install required packages:
``` bash
pip install -U gradio pandas numpy faiss-cpu sentence-transformers opencv-python pytesseract ollama torch
```

> If you have GPU + CUDA properly installed, PyTorch may use CUDA automatically. Otherwise CPU is fine.

--- 

## 📊 Dataset Requirements

**Sales CSV (minimum columns)**

Recommended columns used for KPI and summaries:

- Date (parseable date)
- State
- Branch
- Product
- Quantity
- Unit Price
- Total Sale
- Channel
- PaymentMethod
- Employee

The script automatically generates:

- DateStr = YYYY-MM-DD
-YearMonth = YYYY-MM

---

## HR CSV (recommended columns)

Recommended columns used for HR KPI:

- EmpID
- State
- Branch
- Department
- JobRole
- Age
- AgeGroup
- MonthlyIncome
- OverTime
- Attrition
- YearsAtCompany

---

## 🚀 How to Run

From the project root:
🚀 How to Run

From the project root:
```bash
python oneclick_my_retailchain_v8.2_models_logging.py
```

This will:

1. Load Sales + HR CSVs
2. Load docs from docs/*.txt (if exists)
3. Build embeddings + FAISS index (Sales rows + HR rows + doc chunks)
4. Launch Gradio web UI in your browser

--- 

## 🧪 Example Questions (for demo & testing)

**Sales KPI (deterministic)**
- sales bulan 2024-06 berapa?
- banding sales bulan ni vs bulan lepas
- top 3 product bulan 2024-06
- sales ikut state bulan 2024-06

**HR KPI (deterministic)**
- headcount ikut state
- which age group has highest attrition?

**Docs / Policy (RAG)**
- What is the annual leave entitlement per year?

**Image OCR (upload image)**
- summarize table ini (upload gambar table)

🧭 **Routing Logic (Why answers are reliable)**  
The system classifies user intent and routes:

- If image uploaded → visual
- If policy/SOP keywords → rag_docs
- If HR keywords → hr_kpi
- If Sales keywords → sales_kpi
- Else → default rag_docs

Why this matters:
- KPI answers must be correct numbers (LLM can hallucinate)
- RAG answers must be grounded on documents
- OCR enables multimodal support

## 🧾 Output Style (Deterministic KPI)

Deterministic KPI answers are formatted consistently (example):
```Bash
✅ Source: structured KPI
✅ Total Sales (RM)

Month: 2024-06
Value: RM 99,852.83
Rows used: 4,981
Note: 'bulan ni' = latest month in dataset (2024-06) untuk demo offline.
```

---

## 🔍 RAG Prompt Rules (to reduce hallucination)
The RAG prompt enforces:
- Use ONLY provided DATA (retrieved context)
- Do NOT invent numbers
- Do NOT treat HR/Sales rows as policies
- If a policy question has no [DOC:...] evidence → answer “not available in the provided data (docs)”


## 🖼️ OCR (Image Processing)
OCR pipeline steps:

1. Read image → grayscale
2. Gaussian blur + Otsu threshold
3. pytesseract.image_to_string(...)
4. Clean whitespace
5. Append OCR text to query

If OCR detects too little text, it returns:

> “No readable text detected in the image.”

## 🪵 Logging & Evaluation

All chat interactions are saved to:
```text
logs/chat_logs.csv
```

Columns:
- timestamp
- model
- route
- latency_ms
- question
- answer

Useful for FYP evaluation:
- KPI correctness vs dataset ground truth (expected values)
- Route distribution (sales/hr/docs/visual)
- Latency comparison by route/model

---
## 🛠 Troubleshooting

**1) “Sales CSV not found” / “HR CSV not found”**
Make sure files exist exactly at:
- data/MY_Retail_Sales_2024H1.csv
- data/MY_Retail_HR_Employees.csv

**2) Ollama model dropdown empty**
- Check Ollama installed
- Ensure you pulled a model:

   ```bash
  ollama pull llama3:latest
  ```

**3) OCR fails / no text detected**

- Install Tesseract and ensure tesseract is in PATH
- Use clearer image (high contrast, not blurred)
-Windows: set pytesseract.pytesseract.tesseract_cmd if needed

**4) FAISS installation issues**
```bash
pip install faiss-cpu
```

---
## 🧩 Customization
**Change dataset file names**
Edit inside the script:
```python
SALES_CSV = os.path.join(DATA_DIR, "MY_Retail_Sales_2024H1.csv")
HR_CSV    = os.path.join(DATA_DIR, "MY_Retail_HR_Employees.csv")
```
**Add more company policies / SOP**

Add more .txt files into:
```text
docs/
```

---

## ✅ Conclusion

This FYP project delivers a **hybrid AI Personal Assistant (CEO Bot)** that supports real-world retail decision making by combining:

- **Deterministic KPI analytics (Sales + HR)** for **accurate and repeatable numeric answers**
- **RAG (FAISS + Embeddings + LLM)** for **document-grounded policy/SOP responses**
- **OCR (Tesseract)** to enable **multimodal Q&A from tables/images**
- **Intent routing + logging** to improve **reliability, evaluation, and performance tracking**

Overall, the system reduces hallucination risk for KPI queries, improves trust through evidence-based document retrieval, and provides a practical end-to-end assistant ready for FYP demonstration and evaluation.

