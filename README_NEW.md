# 🧠 FYP AI Personal Assistant Using Visual Language RAG (CEO Bot) — ChatGPT-Style UX

A **CEO-style AI Personal Assistant** for a Malaysia retail chain featuring **ChatGPT-like UX** with:

- ✅ **Persistent Chat Sessions** *(multi-turn conversations saved to disk)*
- ✅ **Memory System** *(remembers user preferences and context)*
- ✅ **Tool Transparency** *(shows which tools/data sources were used)*
- ✅ **Executive Answer Format** *(structured: Summary → Evidence → Next Actions)*
- ✅ **Deterministic KPI** *(Sales & HR analytics with zero hallucination)*
- ✅ **Document RAG** *(Policy/SOP answers grounded in company docs)*
- ✅ **Visual OCR** *(Extract and analyze tables/charts from images)*

Built with **Gradio UI + Ollama (local LLM) + FAISS + SentenceTransformers + Tesseract OCR**.

---

## 🆕 What's New in v8.2 (ChatGPT-Style Upgrade)

### 1) **Persistent Chat Sessions (Threads)**
- Each conversation is saved as `storage/chats/<chat_id>.json`
- Sidebar shows recent chats with titles and timestamps
- "New Chat" button creates fresh sessions
- Chat history includes messages, timestamps, and tool traces

### 2) **Lightweight Memory System**
- User preferences stored in `storage/memory/user_profile.json`
- Remembers: preferred language, answer style, default month rules
- Auto-detects updates: "reply in Malay" → saves language preference
- Memory is injected into LLM prompts for context

### 3) **Tool Transparency Panel**
- Every answer shows which route was taken (KPI/RAG/OCR)
- Displays filters applied, rows analyzed, sources retrieved
- OCR quality indicators and character counts
- Full trace saved in chat history and logs

### 4) **Executive Answer Format**
All answers now follow a consistent structure:
1. **Executive Summary** (2-6 lines)
2. **Evidence Used** (data sources, rows, filters)
3. **Assumptions/Limits** (if applicable)
4. **Next Actions** (1-3 actionable bullets)

### 5) **Enhanced Logging**
- Logs now include: `chat_id`, `message_id`, `tool_trace_summary`
- Full audit trail for evaluation and debugging

---

## ✨ Core Features

### 1) Deterministic KPI (No hallucination for numbers)
For **Sales** & **HR** KPI queries, the system **does not rely on the LLM to compute numbers**.
It uses **pandas calculations** (filter / groupby / sum) so outputs are **repeatable**:

> Same dataset + same query → same numeric output (deterministic)

### 2) RAG for policy/docs (Grounded answers)
For policy/SOP questions, the system retrieves the most relevant chunks from `docs/*.txt` using **FAISS** similarity search, then the LLM answers using **ONLY retrieved context**.

### 3) OCR for table/chart image questions
Upload an image (table/chart screenshot), the system extracts text using **pytesseract**, appends it to the query, and answers using **RAG/LLM**.

**New:** OCR quality indicators show if text extraction was successful or noisy.

### 4) Intent routing (Hybrid decision engine)
A routing function selects the correct path:
- `sales_kpi` → deterministic Sales KPI
- `hr_kpi` → deterministic HR KPI
- `rag_docs` → RAG (docs)
- `visual` → OCR + RAG/LLM

This improves accuracy and reduces hallucination.

### 5) Streaming answers + comprehensive logging
- **Streaming output** in UI (better UX)
- Every interaction logs to: `logs/chat_logs.csv` with:
  - timestamp, model, route, latency_ms, question, answer, chat_id, message_id, tool_trace_summary

---

## 🧱 System Architecture (High Level)

**User (Text/Image)** → **Router** → One of:
1. **Sales KPI Engine** (pandas)
2. **HR KPI Engine** (pandas)
3. **RAG Docs** (FAISS + Embeddings + LLM)
4. **Visual OCR** (Tesseract) → RAG/LLM

Then → **Executive Format Answer** + **Tool Transparency** + **Chat Persistence**

---

## 📁 Project Structure

```
Code/
  ├── oneclick_my_retailchain_v8.2_models_logging.py  # Main application
  ├── storage/                                         # NEW: Persistent data
  │   ├── chats/                                      # Chat sessions (JSON)
  │   └── memory/                                     # User preferences (JSON)
  └── logs/
      └── chat_logs.csv                               # Interaction logs

data/
  ├── MY_Retail_Sales_2024H1.csv                      # Sales data
  └── MY_Retail_HR_Employees.csv                      # HR data

docs/
  ├── Company_Profile_MY.txt                          # Company info
  ├── FAQ_MY.txt                                      # FAQs
  ├── HR_Policy_MY.txt                                # HR policies
  ├── Ops_Incident_Report_MY.txt                      # Operational docs
  └── Sales_SOP_MY.txt                                # Sales procedures
```

---

## 💾 How Chat Storage Works

### Chat Sessions (`storage/chats/<chat_id>.json`)
Each chat file contains:
```json
{
  "chat_id": "a1b2c3d4",
  "title": "Sales analysis for June 2024",
  "created_at": "2026-01-13T10:30:00",
  "updated_at": "2026-01-13T10:45:00",
  "messages": [
    {
      "role": "user",
      "content": "sales bulan 2024-06?",
      "timestamp": "2026-01-13T10:30:15"
    },
    {
      "role": "assistant",
      "content": "## ✅ Total Sales (RM)...",
      "timestamp": "2026-01-13T10:30:18"
    }
  ],
  "tool_traces": [
    {
      "route": "sales_kpi",
      "model": "N/A",
      "filters": {"month": "2024-06"},
      "rows_used": 4981,
      "latency_ms": 125
    }
  ]
}
```

### Memory (`storage/memory/user_profile.json`)
User preferences:
```json
{
  "preferred_language": "malay",
  "answer_style": "executive_summary_first",
  "default_month_rule": "latest_month_in_dataset",
  "custom_notes": []
}
```

**Privacy Note:** All data is stored locally. No external APIs or cloud services are used.

---

## ✅ Prerequisites

### 1) Python
- Python **3.9+** recommended

### 2) Ollama (Local LLM runtime)
Install Ollama, then pull at least one model:

```bash
ollama pull llama3:latest
```

### 3) Tesseract OCR (Required for image OCR)

Install **Tesseract OCR** and ensure `tesseract` is available in your system **PATH**.

**Windows note:** If PATH is not set, you can set the Tesseract executable path in code:

```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

---

## 📦 Python Dependencies

Install required packages:
```bash
pip install -U gradio pandas numpy faiss-cpu sentence-transformers opencv-python pytesseract ollama torch tabulate
```

> If you have GPU + CUDA properly installed, PyTorch may use CUDA automatically. Otherwise CPU is fine.

---

## 📊 Dataset Requirements

**Sales CSV (minimum columns)**
- Date (parseable date)
- State, Branch, Product
- Quantity, Unit Price, Total Sale
- Channel, PaymentMethod, Employee

**HR CSV (minimum columns)**
- EmpID, State, Branch
- Department, JobRole
- Age, AgeGroup
- MonthlyIncome, OverTime, Attrition
- YearsAtCompany

---

## 🚀 How to Run

From the Code directory:

```bash
cd Code
python oneclick_my_retailchain_v8.2_models_logging.py
```

This will:
1. Load Sales + HR CSVs
2. Load docs from `docs/*.txt`
3. Build embeddings + FAISS index
4. **Create storage directories** for chats and memory
5. **Load user memory** from disk (if exists)
6. Launch Gradio web UI with **chat sidebar** and **tool transparency panel**

---

## 🧪 Example Questions

**Sales KPI (deterministic)**
- sales bulan 2024-06 berapa?
- banding sales bulan ni vs bulan lepas
- top 3 product bulan 2024-06
- sales ikut state bulan 2024-06

**HR KPI (deterministic)**
- headcount ikut state
- which age group has highest attrition?
- average income by department

**Docs / Policy (RAG)**
- What is the annual leave entitlement per year?
- What is the refund policy?
- How do I submit a medical claim?

**Image OCR (upload image)**
- summarize table ini (upload gambar table)

**Memory Updates**
- reply in Malay *(saves language preference)*
- reply in English
- always show summary first *(saves answer style preference)*

---

## 🧭 Routing Logic (Why answers are reliable)

The system classifies user intent and routes:

1. If **image uploaded** → `visual` (OCR + RAG)
2. If **policy/SOP keywords** → `rag_docs` (document search)
3. If **HR keywords** → `hr_kpi` (structured HR analytics)
4. If **Sales keywords** → `sales_kpi` (structured sales analytics)
5. Else → default `rag_docs`

**Why this matters:**
- KPI answers use **deterministic calculations** (no LLM hallucination)
- RAG answers are **grounded in retrieved documents**
- OCR enables **multimodal support**
- Tool traces provide **full transparency**

---

## 🔍 Executive Answer Format Example

```markdown
## 📊 Total Sales Comparison

### Executive Summary
**2024-06:** RM 99,852.83 | **2024-05:** RM 87,240.12
**Change:** 📈 RM 12,612.71 (+14.46%)

### Evidence Used
- Data Source: Structured Sales KPI
- Current Period Rows: 4,981
- Previous Period Rows: 4,523
- Dataset Coverage: 2024-01 → 2024-06

### Assumptions
- 'bulan ni' interpreted as latest month in dataset (2024-06)

### Next Actions
- Investigate drivers of change
- Review period-over-period trends
- Validate with operational data
```

---

## 🖼️ OCR Quality Indicators

When an image is uploaded:
- **✅ OCR Quality: Good** - Over 100 characters extracted
- **⚠️ OCR Quality: Moderate** - 10-100 characters extracted
- **⚠️ OCR Quality: Low** - Less than 10 characters (likely unreadable)

The tool transparency panel shows:
- Character count
- Preview of extracted text (first 200 chars)

---

## 🪵 Logging & Evaluation

### Chat Logs (`logs/chat_logs.csv`)
Columns:
- timestamp, model, route, latency_ms
- question, answer
- **chat_id, message_id** *(NEW)*
- **tool_trace_summary** *(NEW)*

### Tool Trace Summary Format
```
sales_kpi|N/A|rows=4981|sources=0|125ms
```

Useful for FYP evaluation:
- KPI correctness vs dataset ground truth
- Route distribution analysis
- Latency comparison by route/model
- Chat session analytics

---

## 🛠 Troubleshooting

**1) "Sales CSV not found" / "HR CSV not found"**
Make sure files exist at:
- `data/MY_Retail_Sales_2024H1.csv`
- `data/MY_Retail_HR_Employees.csv`

**2) Ollama model dropdown empty**
- Check Ollama installed: `ollama --version`
- Pull a model: `ollama pull llama3:latest`

**3) OCR fails / no text detected**
- Install Tesseract and ensure it's in PATH
- Use clearer images (high contrast, not blurred)
- Windows: set `pytesseract.pytesseract.tesseract_cmd` if needed

**4) FAISS installation issues**
```bash
pip install faiss-cpu
```

**5) Chat sessions not saving**
- Check `storage/chats/` directory is created
- Ensure write permissions
- Check console for error messages

---

## 🧩 Customization

### Change Dataset File Names
Edit in the script:
```python
SALES_CSV = os.path.join(DATA_DIR, "YOUR_SALES_FILE.csv")
HR_CSV = os.path.join(DATA_DIR, "YOUR_HR_FILE.csv")
```

### Add More Company Policies/SOPs
Simply add `.txt` files to `docs/` directory. They will be automatically:
- Chunked by blank lines
- Embedded
- Indexed in FAISS
- Available for RAG queries

### Customize Memory Fields
Edit `load_memory()` default structure in the script to add custom fields.

### Customize Executive Format
Update answer functions (`answer_sales_ceo_kpi`, `answer_hr`, etc.) to modify the output structure.

---

## ✅ Conclusion

This FYP project delivers a **ChatGPT-style AI Assistant (CEO Bot)** with enterprise-grade features:

- **🔒 Privacy-First**: All processing and storage is local
- **📊 Accuracy**: Deterministic KPI calculations eliminate hallucination
- **📝 Transparency**: Tool traces show exactly what data was used
- **💬 Persistence**: Chat sessions and preferences survive restarts
- **🎯 Executive-Ready**: Structured answers with evidence and actions
- **🖼️ Multimodal**: Handles text, images, and documents seamlessly

**Perfect for FYP demonstration** showcasing:
- Advanced RAG architecture
- Hybrid deterministic + LLM approach
- Production-ready UX patterns
- Comprehensive evaluation logging

---

## 📚 Further Reading

- [Gradio Documentation](https://gradio.app/)
- [Ollama](https://ollama.ai/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [SentenceTransformers](https://www.sbert.net/)

---

**Built for FYP 2025/2026 | Local-First AI | Zero Cloud Dependencies**
