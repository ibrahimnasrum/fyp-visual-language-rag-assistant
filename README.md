# 🧠 FYP AI Personal Assistant (CEO Bot) — Hybrid KPI + RAG + OCR (Malaysia Retail Chain)

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

If you have GPU + CUDA properly installed, PyTorch may use CUDA automatically. Otherwise CPU is fine.

