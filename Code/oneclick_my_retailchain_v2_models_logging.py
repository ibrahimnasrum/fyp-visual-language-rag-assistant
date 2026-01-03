import os
import re
import glob
import time
import csv
import subprocess
import cv2
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

import faiss
import gradio as gr
import ollama
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer

# =========================
# Tabulate check (for to_markdown)
# =========================
try:
    import tabulate  # noqa: F401
except ImportError:
    raise ImportError("Missing dependency 'tabulate'. Install: pip install tabulate")

# =========================
# Helpers
# =========================
def df_to_markdown_table(df: pd.DataFrame, max_rows: int = 20) -> str:
    if df is None or df.empty:
        return "_(no rows)_"
    df2 = df.copy()
    if len(df2) > max_rows:
        df2 = df2.head(max_rows)
    return df2.to_markdown(index=False)

def format_num(x: float, decimals: int = 2) -> str:
    try:
        return f"{x:,.{decimals}f}"
    except Exception:
        return str(x)

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def get_installed_ollama_models(default=("llama3:latest",)):
    """
    Try parse `ollama list`. If fails, return default.
    """
    try:
        out = subprocess.check_output(["ollama", "list"], text=True, encoding="utf-8", errors="ignore")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
        # Expect header: NAME ID SIZE MODIFIED
        models = []
        for ln in lines[1:]:
            # split by spaces; first token is model name
            name = ln.split()[0]
            if ":" not in name:
                # some outputs may omit tag -> keep anyway
                models.append(name)
            else:
                models.append(name)
        return models if models else list(default)
    except Exception:
        return list(default)

# =========================
# Logging
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
ensure_dir(LOG_DIR)
LOG_FILE = os.path.join(LOG_DIR, "chat_logs.csv")

def log_interaction(model: str, route: str, question: str, answer: str, latency_ms: int):
    new_file = not os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["timestamp", "model", "route", "latency_ms", "question", "answer"])
        w.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), model, route, latency_ms, question, answer])

# =========================
# 1) Device
# =========================
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"✅ Device: {device}")

# =========================
# 2) Load Malaysia RetailChain datasets
# =========================
DATA_DIR = os.path.join(BASE_DIR, "data")
DOCS_DIR = os.path.join(BASE_DIR, "docs")

SALES_CSV = os.path.join(DATA_DIR, "MY_Retail_Sales_2024H1.csv")
HR_CSV = os.path.join(DATA_DIR, "MY_Retail_HR_Employees.csv")

if not os.path.exists(SALES_CSV):
    raise FileNotFoundError(f"Sales CSV not found: {SALES_CSV}")
if not os.path.exists(HR_CSV):
    raise FileNotFoundError(f"HR CSV not found: {HR_CSV}")

df_sales = pd.read_csv(SALES_CSV)
df_hr = pd.read_csv(HR_CSV)

# Normalize Sales dates
df_sales["Date"] = pd.to_datetime(df_sales["Date"], errors="coerce")
df_sales["DateStr"] = df_sales["Date"].dt.strftime("%Y-%m-%d")
df_sales["YearMonth"] = df_sales["Date"].dt.to_period("M")

for c in ["Quantity", "Unit Price", "Total Sale"]:
    df_sales[c] = pd.to_numeric(df_sales[c], errors="coerce")

AVAILABLE_SALES_MONTHS = sorted(df_sales["YearMonth"].dropna().unique().tolist())
LATEST_SALES_MONTH = max(AVAILABLE_SALES_MONTHS) if AVAILABLE_SALES_MONTHS else None

# Metadata (Sales)
STATES = sorted(df_sales["State"].dropna().unique().tolist()) if "State" in df_sales.columns else []
BRANCHES = sorted(df_sales["Branch"].dropna().unique().tolist()) if "Branch" in df_sales.columns else []
PRODUCTS = sorted(df_sales["Product"].dropna().unique().tolist())
SALES_REPS = sorted(df_sales["Employee"].dropna().unique().tolist())
CHANNELS = sorted(df_sales["Channel"].dropna().unique().tolist()) if "Channel" in df_sales.columns else []

# Metadata (HR)
HR_DEPTS = sorted(df_hr["Department"].dropna().unique().tolist()) if "Department" in df_hr.columns else []
HR_AGEGROUPS = sorted(df_hr["AgeGroup"].dropna().unique().tolist()) if "AgeGroup" in df_hr.columns else []
HR_STATES = sorted(df_hr["State"].dropna().unique().tolist()) if "State" in df_hr.columns else []

print("📄 Sales shape:", df_sales.shape, "| months:", AVAILABLE_SALES_MONTHS[0], "→", AVAILABLE_SALES_MONTHS[-1])
print("📄 HR shape:", df_hr.shape)

# =========================
# 3) Build RAG corpus (Sales + HR rows + docs)
# =========================
sales_summaries = []
for _, r in df_sales.iterrows():
    sales_summaries.append(
        "[SALES] "
        f"Date={r.get('DateStr','')}; State={r.get('State','')}; Branch={r.get('Branch','')}; "
        f"Product={r.get('Product','')}; Qty={r.get('Quantity','')}; UnitPrice={r.get('Unit Price','')}; "
        f"TotalSale={r.get('Total Sale','')}; Channel={r.get('Channel','')}; Payment={r.get('PaymentMethod','')}; "
        f"Employee={r.get('Employee','')}"
    )

hr_summaries = []
for _, r in df_hr.iterrows():
    hr_summaries.append(
        "[HR] "
        f"EmpID={r.get('EmpID','')}; State={r.get('State','')}; Branch={r.get('Branch','')}; "
        f"Department={r.get('Department','')}; JobRole={r.get('JobRole','')}; Age={r.get('Age','')}; "
        f"AgeGroup={r.get('AgeGroup','')}; MonthlyIncome={r.get('MonthlyIncome','')}; "
        f"OverTime={r.get('OverTime','')}; Attrition={r.get('Attrition','')}; YearsAtCompany={r.get('YearsAtCompany','')}"
    )

doc_chunks = []
if os.path.isdir(DOCS_DIR):
    for fp in sorted(glob.glob(os.path.join(DOCS_DIR, "*.txt"))):
        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read().strip()
        parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        title = os.path.basename(fp)
        for p in parts:
            doc_chunks.append(f"[DOC:{title}] {p}")

summaries = sales_summaries + hr_summaries + doc_chunks
print(f"📚 RAG corpus size: {len(summaries)} (Sales={len(sales_summaries)}, HR={len(hr_summaries)}, Docs={len(doc_chunks)})")

# Embeddings + FAISS
embedder = SentenceTransformer("all-MiniLM-L6-v2", device=device)
emb = embedder.encode(summaries, convert_to_numpy=True, show_progress_bar=True)
faiss.normalize_L2(emb)
index = faiss.IndexFlatIP(emb.shape[1])
index.add(emb)
print("✅ FAISS index vectors:", index.ntotal)

# =========================
# 4) Optional BLIP-2
# =========================


def caption_image(image_path: str) -> str:
    try:
        img = cv2.imread(image_path)
        if img is None:
            return "Unable to read image file."

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        text = pytesseract.image_to_string(th, config="--oem 3 --psm 6")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{2,}", "\n", text).strip()

        if len(text) < 10:
            return "No readable text detected in the image."

        return "OCR Extracted Text:\n" + text[:2000]
    except Exception as e:
        return f"OCR failed: {e}"

# =========================
# 5) Sales KPI engine (Malaysia version)
# =========================
MONTH_ALIASES = {
    "jan": 1, "january": 1, "januari": 1,
    "feb": 2, "february": 2, "februari": 2,
    "mar": 3, "march": 3, "mac": 3,
    "apr": 4, "april": 4,
    "may": 5, "mei": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7, "julai": 7,
    "aug": 8, "august": 8, "ogos": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "okt": 10, "oktober": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12, "dis": 12, "disember": 12,
}

def extract_month_from_query(q: str):
    if LATEST_SALES_MONTH is None:
        return None
    s = q.lower()

    if any(k in s for k in ["bulan ni", "bulan ini", "this month", "current month", "mtd"]):
        return LATEST_SALES_MONTH
    if any(k in s for k in ["bulan lepas", "last month", "previous month"]):
        return LATEST_SALES_MONTH - 1

    m = re.search(r"\b(20\d{2})[-/](0?[1-9]|1[0-2])\b", s)
    if m:
        y = int(m.group(1))
        mo = int(m.group(2))
        return pd.Period(f"{y:04d}-{mo:02d}", freq="M")

    tokens = re.findall(r"[a-zA-Z]+|\d{4}", s)
    year = None
    for t in tokens:
        if re.fullmatch(r"20\d{2}", t):
            year = int(t)
            break
    month_num = None
    for t in tokens:
        t2 = t.lower()
        if t2 in MONTH_ALIASES:
            month_num = MONTH_ALIASES[t2]
            break
    if month_num is not None:
        if year is None:
            year = int(str(LATEST_SALES_MONTH)[:4])
        return pd.Period(f"{year:04d}-{month_num:02d}", freq="M")

    return LATEST_SALES_MONTH

def detect_sales_metric(q: str) -> str:
    s = q.lower()
    if any(k in s for k in ["quantity", "qty", "jumlah", "terjual", "units"]):
        return "quantity"
    return "revenue"

def detect_sales_dimension(q: str) -> str:
    s = q.lower()
    if any(k in s for k in ["state", "negeri", "region", "kawasan"]):
        return "State"
    if any(k in s for k in ["branch", "cawangan", "outlet", "kedai"]):
        return "Branch"
    if any(k in s for k in ["channel", "saluran", "delivery", "takeaway", "dine"]):
        return "Channel"
    if any(k in s for k in ["employee", "staff", "salesrep", "sales rep", "pekerja"]):
        return "Employee"
    return "Product"

def extract_sales_filters(q: str):
    s = q.lower()
    state = next((x for x in STATES if x.lower() in s), None)
    branch = next((x for x in sorted(BRANCHES, key=len, reverse=True) if x.lower() in s), None)
    product = next((x for x in sorted(PRODUCTS, key=len, reverse=True) if x.lower() in s), None)
    employee = next((x for x in SALES_REPS if x.lower() in s), None)
    channel = next((x for x in CHANNELS if x.lower() in s), None)
    return state, branch, product, employee, channel

def answer_sales_ceo_kpi(q: str):
    if LATEST_SALES_MONTH is None:
        return "❗ Tiada data sales."

    s = q.lower()
    month = extract_month_from_query(q)
    sub = df_sales[df_sales["YearMonth"] == month].copy()

    state, branch, product, employee, channel = extract_sales_filters(q)
    if state: sub = sub[sub["State"] == state]
    if branch: sub = sub[sub["Branch"] == branch]
    if product: sub = sub[sub["Product"] == product]
    if employee: sub = sub[sub["Employee"] == employee]
    if channel and "Channel" in sub.columns: sub = sub[sub["Channel"] == channel]

    if sub.empty:
        return f"❗ Tiada rekod untuk {month} dengan filter yang diberi."

    metric = detect_sales_metric(q)
    value_col = "Total Sale" if metric == "revenue" else "Quantity"
    metric_label = "Total Sales (RM)" if metric == "revenue" else "Total Quantity"
    decimals = 2 if metric == "revenue" else 0

    is_compare = any(k in s for k in ["banding", "compare", "vs", "versus", "mom", "bulan lepas", "last month"])
    is_top = "top" in s or "paling" in s

    if is_compare:
        prev = month - 1
        cur_df = df_sales[df_sales["YearMonth"] == month].copy()
        prev_df = df_sales[df_sales["YearMonth"] == prev].copy()

        if state:
            cur_df = cur_df[cur_df["State"] == state]
            prev_df = prev_df[prev_df["State"] == state]
        if branch:
            cur_df = cur_df[cur_df["Branch"] == branch]
            prev_df = prev_df[prev_df["Branch"] == branch]
        if product:
            cur_df = cur_df[cur_df["Product"] == product]
            prev_df = prev_df[prev_df["Product"] == product]
        if employee:
            cur_df = cur_df[cur_df["Employee"] == employee]
            prev_df = prev_df[prev_df["Employee"] == employee]
        if channel:
            cur_df = cur_df[cur_df["Channel"] == channel]
            prev_df = prev_df[prev_df["Channel"] == channel]

        cur_val = float(cur_df[value_col].sum())
        prev_val = float(prev_df[value_col].sum())
        diff = cur_val - prev_val
        pct = (diff / prev_val * 100) if prev_val != 0 else None

        lines = [
            "✅ **Source: structured KPI**",
            f"📊 **{metric_label} (MoM)**",
            f"- {month}: **{format_num(cur_val, decimals)}**",
            f"- {prev}: **{format_num(prev_val, decimals)}**",
        ]
        if pct is None:
            lines.append(f"- Change: **{format_num(diff, decimals)}** (previous=0)")
        else:
            lines.append(f"- Change: **{format_num(diff, decimals)}** ({pct:+.2f}%)")
        lines.append(f"- Rows used (current month): {len(cur_df):,}")
        lines.append(f"- Dataset months available: {AVAILABLE_SALES_MONTHS[0]} → {AVAILABLE_SALES_MONTHS[-1]}")
        lines.append(f"- Note: 'bulan ni' = latest month in dataset (**{LATEST_SALES_MONTH}**) untuk demo offline.")
        return "\n".join(lines)

    if is_top:
        dim = detect_sales_dimension(q)
        grp = sub.groupby(dim)[value_col].sum().sort_values(ascending=False)
        top_n = 3
        if "top 5" in s or "top5" in s:
            top_n = 5

        top_df = grp.head(top_n).reset_index().rename(columns={value_col: metric_label})
        if metric == "revenue":
            top_df[metric_label] = top_df[metric_label].map(lambda x: f"RM {format_num(float(x), 2)}")
        else:
            top_df[metric_label] = top_df[metric_label].astype(int)

        return "\n".join([
            "✅ **Source: structured KPI**",
            f"🏆 **Top {top_n} {dim} by {metric_label}**",
            f"- Month: **{month}**",
            "",
            df_to_markdown_table(top_df),
            "",
            f"Rows used: {len(sub):,}",
        ])

    total_val = float(sub[value_col].sum())
    lines = [
        "✅ **Source: structured KPI**",
        f"✅ **{metric_label}**",
        f"- Month: **{month}**",
        f"- Value: **RM {format_num(total_val, decimals)}**" if metric == "revenue" else f"- Value: **{int(total_val)}**",
        f"- Rows used: {len(sub):,}",
        f"- Note: 'bulan ni' = latest month in dataset (**{LATEST_SALES_MONTH}**) untuk demo offline.",
    ]
    return "\n".join(lines)

# =========================
# 6) HR deterministic helpers
# =========================
def answer_hr(q: str) -> str:
    s = q.lower()

    if "headcount" in s or "berapa orang" in s or "how many" in s:
        for d in HR_DEPTS:
            if d.lower() in s:
                n = int((df_hr["Department"] == d).sum())
                return f"✅ **Source: structured HR**\n👥 Headcount Department **{d}**: **{n}**"
        for st in HR_STATES:
            if st.lower() in s:
                n = int((df_hr["State"] == st).sum())
                return f"✅ **Source: structured HR**\n👥 Headcount State **{st}**: **{n}**"
        return f"✅ **Source: structured HR**\n👥 Total employees: **{len(df_hr):,}**"

    if "attrition" in s:
        left = df_hr[df_hr["Attrition"].str.lower() == "yes"].copy()
        if left.empty:
            return "✅ **Source: structured HR**\nNo attrition records found."
        if "age" in s:
            c = left.groupby("AgeGroup")["EmpID"].count().sort_values(ascending=False)
            return f"✅ **Source: structured HR**\n📌 Highest attrition by AgeGroup: **{c.index[0]}** (count={int(c.iloc[0])})"
        if "state" in s or "negeri" in s:
            c = left.groupby("State")["EmpID"].count().sort_values(ascending=False)
            return f"✅ **Source: structured HR**\n📌 Highest attrition by State: **{c.index[0]}** (count={int(c.iloc[0])})"
        c = left.groupby("Department")["EmpID"].count().sort_values(ascending=False)
        return f"✅ **Source: structured HR**\n📌 Highest attrition by Department: **{c.index[0]}** (count={int(c.iloc[0])})"

    if any(k in s for k in ["average income", "avg income", "gaji purata", "purata gaji", "average salary"]):
        for d in HR_DEPTS:
            if d.lower() in s:
                avg = float(df_hr[df_hr["Department"] == d]["MonthlyIncome"].mean())
                return f"✅ **Source: structured HR**\n💰 Avg MonthlyIncome **{d}**: **RM {format_num(avg, 2)}**"
        avg = float(df_hr["MonthlyIncome"].mean())
        return f"✅ **Source: structured HR**\n💰 Avg MonthlyIncome (all): **RM {format_num(avg, 2)}**"

    return None

# =========================
# 7) RAG answer with selectable model
# =========================
def retrieve_context(query: str, k: int = 12) -> str:
    q_emb = embedder.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(q_emb)
    k = min(k, index.ntotal)
    scores, idx = index.search(q_emb, k=k)
    return "\n".join(summaries[i] for i in idx[0])

def generate_answer_with_model(model_name: str, query: str) -> str:
    context = retrieve_context(query, k=12)

    prompt = f"""
You are a helpful analyst for a Malaysia retail chain.
Use ONLY the provided DATA.

DATA:
{context}

QUESTION:
{query}

RULES:
- Do not invent numbers.
- If not found in DATA, say "not available in the provided data".
- Keep answer concise (bullets ok).
"""

    resp = ollama.chat(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        options={"num_ctx": 4096, "temperature": 0},
    )
    return resp["message"]["content"].strip()

# =========================
# 8) Router with logging + latency
# =========================
def rag_query_ui(user_input: str, model_name: str) -> str:
    start = time.perf_counter()
    route = "rag"
    try:
        user_input = (user_input or "").strip()
        if len(user_input) < 3:
            ans = "Sila tanya soalan yang lebih jelas."
            latency = int((time.perf_counter() - start) * 1000)
            log_interaction(model_name, "validation", user_input, ans, latency)
            return ans

        s = user_input.lower()

        # Sales KPI first (deterministic)
        if any(k in s for k in ["sales", "jualan", "revenue", "top", "banding", "vs", "bulan", "state", "branch", "channel"]):
            route = "sales_kpi"
            ans = answer_sales_ceo_kpi(user_input)
            latency = int((time.perf_counter() - start) * 1000)
            log_interaction("N/A", route, user_input, ans, latency)
            return ans

        # HR deterministic
        hr_ans = answer_hr(user_input)
        if hr_ans is not None:
            route = "hr_kpi"
            ans = hr_ans
            latency = int((time.perf_counter() - start) * 1000)
            log_interaction("N/A", route, user_input, ans, latency)
            return ans

        # Else: RAG + LLM
        route = "rag_docs"
        ans = "📄 **Source: RAG + LLM**\n" + generate_answer_with_model(model_name, user_input)
        latency = int((time.perf_counter() - start) * 1000)
        log_interaction(model_name, route, user_input, ans, latency)
        return ans

    except Exception as e:
        ans = f"Error: {e}"
        latency = int((time.perf_counter() - start) * 1000)
        log_interaction(model_name, route, user_input, ans, latency)
        return ans

# =========================
# 9) Multimodal wrapper (image + text)
# =========================
def multimodal_query(text_input, image_input, model_name):
    query = (text_input or "").strip()
    if image_input is not None:
        cap = caption_image(image_input)
        print("🖼️ Image caption:", cap)
        if query:
            query = query + f" | Image: {cap}"
        else:
            query = f"Based on the image: {cap}"

    if not query:
        return "Please provide a question, an image, or both."
    return rag_query_ui(query, model_name)

# =========================
# 10) Launch UI
# =========================
if __name__ == "__main__":
    models = get_installed_ollama_models()
    default_model = models[0] if models else "llama3:latest"
    print("✅ Ollama models found:", models)

    print("🚀 Launching MY RetailChain Assistant (FAISS + Model Compare + Logging)...")
    gr.Interface(
        fn=multimodal_query,
        inputs=[
            gr.Textbox(lines=2, label="Soalan (optional)"),
            gr.Image(type="filepath", label="Upload table/chart image (optional)"),
            gr.Dropdown(choices=models, value=default_model, label="Choose LLM model (RAG only)"),
        ],
        outputs=gr.Markdown(),
        title="MY Retail Chain VL-RAG Assistant (Sales + HR + Docs) — Compare LLM",
        description=(
            "Structured KPI (Sales/HR) is deterministic (no LLM).\n"
            "RAG uses selected LLM model.\n\n"
            "Contoh soalan:\n"
            "- sales bulan ni berapa?\n"
            "- banding sales bulan ni vs bulan lepas\n"
            "- top 3 product bulan 2024-06\n"
            "- sales ikut state bulan 2024-06\n"
            "- headcount ikut state\n"
            "- which age group has highest attrition?\n"
            "- upload table image dan tanya: summarize table ini\n\n"
            "Logs saved to: logs/chat_logs.csv"
        ),
    ).launch(inbrowser=True, debug=True, show_error=True)
