import os
import re
import glob
import time
import csv
import subprocess
import cv2
import pytesseract
import time

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
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")
DOCS_DIR = os.path.join(os.path.dirname(BASE_DIR), "docs")

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

print("📁 DOCS_DIR =", DOCS_DIR)

if not os.path.isdir(DOCS_DIR):
    print("⚠️ docs folder not found.")
else:
    doc_files = sorted(glob.glob(os.path.join(DOCS_DIR, "*.txt")))
    print("📄 Docs files found =", doc_files)

    for fp in doc_files:
        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read().strip()

        # split by blank lines (paragraph chunks)
        parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        title = os.path.basename(fp)

        for p in parts:
            doc_chunks.append(f"[DOC:{title}] {p}")

print("📄 Docs chunks loaded =", len(doc_chunks))
if len(doc_chunks) > 0:
    print("📄 Sample doc chunk =", doc_chunks[0][:200])


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

def extract_named_month_range(q: str):
    s = (q or "").lower()

    # year (optional). If missing, use latest dataset year
    m_year = re.search(r"\b(20\d{2})\b", s)
    year = int(m_year.group(1)) if m_year else int(str(LATEST_SALES_MONTH)[:4])

    # find month words in text order
    words = re.findall(r"[a-zA-Z]+", s)
    months = []
    for w in words:
        w = w.lower()
        if w in MONTH_ALIASES:
            months.append(MONTH_ALIASES[w])

    if len(months) >= 2:
        m1, m2 = months[0], months[1]
        p1 = pd.Period(f"{year:04d}-{m1:02d}", freq="M")
        p2 = pd.Period(f"{year:04d}-{m2:02d}", freq="M")
        start_m, end_m = (p1, p2) if p1 <= p2 else (p2, p1)
        return start_m, end_m

    return None



def extract_month_from_query(q: str):
    if LATEST_SALES_MONTH is None:
        return None

    s = (q or "").lower()

    if any(k in s for k in ["bulan ni", "bulan ini", "this month", "current month", "mtd"]):
        return LATEST_SALES_MONTH
    if any(k in s for k in ["bulan lepas", "last month", "previous month"]):
        return LATEST_SALES_MONTH - 1

    # explicit yyyy-mm or yyyy/m
    m = re.search(r"\b(20\d{2})[-/](0?[1-9]|1[0-2])\b", s)
    if m:
        y = int(m.group(1))
        mo = int(m.group(2))
        return pd.Period(f"{y:04d}-{mo:02d}", freq="M")

    # text month (mac 2024 / march 2024)
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

    # fallback latest
    return LATEST_SALES_MONTH


def extract_two_months_from_query(q: str):
    """Return up to 2 explicit months found in query like 2024-03 vs 2024-05."""
    s = (q or "").lower()
    matches = re.findall(r"\b(20\d{2})[-/](0?[1-9]|1[0-2])\b", s)

    months = []
    for y, m in matches:
        months.append(pd.Period(f"{int(y):04d}-{int(m):02d}", freq="M"))

    uniq = []
    for x in months:
        if x not in uniq:
            uniq.append(x)

    return uniq[:2]


def detect_sales_metric(q: str) -> str:
    s = (q or "").lower()
    if any(k in s for k in ["quantity", "qty", "jumlah", "terjual", "units"]):
        return "quantity"
    return "revenue"


def detect_sales_dimension(q: str) -> str:
    s = (q or "").lower()
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
    s = (q or "").lower()
    state = next((x for x in STATES if x.lower() in s), None)
    branch = next((x for x in sorted(BRANCHES, key=len, reverse=True) if x.lower() in s), None)
    product = next((x for x in sorted(PRODUCTS, key=len, reverse=True) if x.lower() in s), None)
    employee = next((x for x in SALES_REPS if x.lower() in s), None)
    channel = next((x for x in CHANNELS if x.lower() in s), None)
    return state, branch, product, employee, channel


def extract_month_range_from_query(q: str):
    """
    Detects queries like:
      - from 2024-01 until 2024-06
      - 2024-01 to 2024-06
    Returns (start_period, end_period) or None
    """
    s = (q or "").lower()
    matches = re.findall(r"\b(20\d{2})[-/](0?[1-9]|1[0-2])\b", s)
    if len(matches) >= 2:
        p1 = pd.Period(f"{int(matches[0][0]):04d}-{int(matches[0][1]):02d}", freq="M")
        p2 = pd.Period(f"{int(matches[1][0]):04d}-{int(matches[1][1]):02d}", freq="M")
        start_m, end_m = (p1, p2) if p1 <= p2 else (p2, p1)
        return start_m, end_m
    return None


def answer_sales_ceo_kpi(q: str):
    if LATEST_SALES_MONTH is None:
        return "❗ Tiada data sales."

    s = (q or "").lower().strip()

    metric = detect_sales_metric(q)
    value_col = "Total Sale" if metric == "revenue" else "Quantity"
    metric_label = "Total Sales (RM)" if metric == "revenue" else "Total Quantity"
    decimals = 2 if metric == "revenue" else 0

    # detect flags
    is_compare = any(k in s for k in ["banding", "compare", "vs", "versus", "mom", "bulan lepas", "last month"])
    is_top = ("top" in s) or ("paling" in s)

    # filters
    state, branch, product, employee, channel = extract_sales_filters(q)

    # =========================================================
    # ✅ RANGE TOP-N (e.g. 2024-01 until 2024-06 OR "Jan until Jun 2024")
    # Trigger when:
    #   - query contains a month range (numeric OR month names)
    #   - user asks top/highest/most
    # Dimension:
    #   - uses detect_sales_dimension(q): Product (default), State, Branch, Channel, Employee
    # =========================================================
    rng = extract_month_range_from_query(q) or extract_named_month_range(q)

    if rng is not None and (is_top or "highest" in s or "most" in s):
        start_m, end_m = rng

        mask = (df_sales["YearMonth"] >= start_m) & (df_sales["YearMonth"] <= end_m)
        sub_range = df_sales[mask].copy()

        # Apply same filters (optional)
        state, branch, product, employee, channel = extract_sales_filters(q)
        if state:
            sub_range = sub_range[sub_range["State"] == state]
        if branch:
            sub_range = sub_range[sub_range["Branch"] == branch]
        if product:
            sub_range = sub_range[sub_range["Product"] == product]
        if employee:
            sub_range = sub_range[sub_range["Employee"] == employee]
        if channel and "Channel" in sub_range.columns:
            sub_range = sub_range[sub_range["Channel"] == channel]

        if sub_range.empty:
            return f"❗ Tiada rekod sales untuk {start_m} → {end_m} dengan filter yang diberi."

        dim = detect_sales_dimension(q)  # default = Product
        grp = sub_range.groupby(dim)[value_col].sum().sort_values(ascending=False)

        top_n = 5 if ("top 5" in s or "top5" in s) else 3
        top_df = grp.head(top_n).reset_index().rename(columns={value_col: metric_label})

        if metric == "revenue":
            top_df[metric_label] = top_df[metric_label].map(lambda x: f"RM {format_num(float(x), 2)}")
        else:
            top_df[metric_label] = top_df[metric_label].astype(int)

        return "\n".join([
            "✅ **Source: structured KPI**",
            f"🏆 **Top {top_n} {dim} by {metric_label} (Range)**",
            f"- Period: **{start_m} → {end_m}**",
            "",
            df_to_markdown_table(top_df),
            "",
            f"Rows used: {len(sub_range):,}",
        ])

    # =========================================================
    # Normal single-month logic starts here
    # =========================================================
    month = extract_month_from_query(q)
    sub = df_sales[df_sales["YearMonth"] == month].copy()

    if state:
        sub = sub[sub["State"] == state]
    if branch:
        sub = sub[sub["Branch"] == branch]
    if product:
        sub = sub[sub["Product"] == product]
    if employee:
        sub = sub[sub["Employee"] == employee]
    if channel and "Channel" in sub.columns:
        sub = sub[sub["Channel"] == channel]

    if sub.empty:
        return f"❗ Tiada rekod untuk {month} dengan filter yang diberi."

    # =========================
    # Compare: explicit month1 vs month2, else MoM
    # =========================
    if is_compare:
        two = extract_two_months_from_query(q)

        if len(two) == 2:
            prev_month, cur_month = two[0], two[1]
        else:
            cur_month = month
            prev_month = month - 1

        cur_df = df_sales[df_sales["YearMonth"] == cur_month].copy()
        prev_df = df_sales[df_sales["YearMonth"] == prev_month].copy()

        # Apply same filters
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
        if channel and "Channel" in cur_df.columns:
            cur_df = cur_df[cur_df["Channel"] == channel]
        if channel and "Channel" in prev_df.columns:
            prev_df = prev_df[prev_df["Channel"] == channel]

        cur_val = float(cur_df[value_col].sum())
        prev_val = float(prev_df[value_col].sum())
        diff = cur_val - prev_val
        pct = (diff / prev_val * 100) if prev_val != 0 else None

        lines = [
            "✅ **Source: structured KPI**",
            f"📊 **{metric_label} (Compare)**",
            f"- {cur_month}: **{format_num(cur_val, decimals)}**",
            f"- {prev_month}: **{format_num(prev_val, decimals)}**",
        ]
        if pct is None:
            lines.append(f"- Change: **{format_num(diff, decimals)}** (previous=0)")
        else:
            lines.append(f"- Change: **{format_num(diff, decimals)}** ({pct:+.2f}%)")
        lines.append(f"- Rows used (current month): {len(cur_df):,}")
        lines.append(f"- Dataset months available: {AVAILABLE_SALES_MONTHS[0]} → {AVAILABLE_SALES_MONTHS[-1]}")
        lines.append(f"- Note: 'bulan ni' = latest month in dataset (**{LATEST_SALES_MONTH}**) untuk demo offline.")
        return "\n".join(lines)

    # =========================
    # Top-N (single month)
    # =========================
    if is_top:
        dim = detect_sales_dimension(q)
        grp = sub.groupby(dim)[value_col].sum().sort_values(ascending=False)

        top_n = 5 if ("top 5" in s or "top5" in s) else 3
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

    # =========================
    # Default total (single month)
    # =========================
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
    s = (q or "").lower().strip()

    # ✅ If question is about HR policy/handbook/SOP, let DOC RAG handle it (NOT HR.csv)
    if any(k in s for k in [
        "policy", "handbook", "guideline", "procedure", "sop",
        "medical claim", "claim", "entitlement",
        "annual leave", "sick leave", "leave", "cuti",
        "overtime approval", "approval",
        "disciplinary", "probation", "grievance", "whistleblowing"
    ]):
        return None

    # Headcount
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

    # Attrition analysis
    if "attrition" in s:
        left = df_hr[df_hr["Attrition"].astype(str).str.lower() == "yes"].copy()
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

    # Average income
    if any(k in s for k in ["average income", "avg income", "gaji purata", "purata gaji", "average salary"]):
        for d in HR_DEPTS:
            if d.lower() in s:
                avg = float(df_hr[df_hr["Department"] == d]["MonthlyIncome"].mean())
                return f"✅ **Source: structured HR**\n💰 Avg MonthlyIncome **{d}**: **RM {format_num(avg, 2)}**"

        avg = float(df_hr["MonthlyIncome"].mean())
        return f"✅ **Source: structured HR**\n💰 Avg MonthlyIncome (all): **RM {format_num(avg, 2)}**"

    return None


# =========================
# 7) RAG answer with selectable model (UPDATED + STREAMING)
# =========================

def retrieve_context(query: str, k: int = 12, mode: str = "all") -> str:
    q_emb = embedder.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(q_emb)

    # Ambil lebih banyak awal supaya boleh filter (docs vs all)
    # k0 minimum 40, tapi jangan lebih dari jumlah index
    k0 = min(max(k * 5, 40), int(index.ntotal) if index is not None else 0)
    if k0 <= 0:
        return ""

    scores, idx = index.search(q_emb, k=k0)

    # idx[0] is list of candidate indices
    candidates = [summaries[i] for i in idx[0] if i != -1]

    if mode == "docs":
        candidates = [c for c in candidates if c.startswith("[DOC:")]

    # limit final
    candidates = candidates[:k]
    return "\n".join(candidates)


def _build_prompt(context: str, query: str) -> str:
    return f"""
You are a helpful analyst for a Malaysia retail chain.
Use ONLY the provided DATA.

DATA:
{context}

QUESTION:
{query}

RULES:
- Use ONLY the provided DATA.
- Do NOT infer "policy" from HR/Sales rows (AgeGroup, OverTime, Attrition are NOT policies).
- If question asks policy/SOP/refund/leave AND there is no [DOC:...] evidence, answer:
  "not available in the provided data (docs)".
- Do not invent numbers.
- Keep answer concise (bullets ok).
""".strip()


# ✅ STREAMING VERSION (recommended for UX)
def generate_answer_with_model_stream(model_name: str, query: str, mode: str = "all"):
    context = retrieve_context(query, k=12, mode=mode)
    prompt = _build_prompt(context, query)

    out = ""
    for chunk in ollama.chat(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        options={"num_ctx": 4096, "temperature": 0, "num_predict": 500},
        stream=True,
    ):
        # Ollama streaming biasanya bagi token dekat chunk["message"]["content"]
        token = chunk.get("message", {}).get("content", "")
        if token:
            out += token
            yield out.strip()


# (Optional) NON-STREAMING version (kalau kau masih nak guna)
def generate_answer_with_model(model_name: str, query: str, mode: str = "all") -> str:
    context = retrieve_context(query, k=12, mode=mode)
    prompt = _build_prompt(context, query)

    resp = ollama.chat(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        options={"num_ctx": 4096, "temperature": 0, "num_predict": 500},
    )
    return resp["message"]["content"].strip()

# =========================
# 8) Router with logging + latency
# =========================

HR_KEYWORDS = [
    "hr", "employee", "employees", "staff", "headcount", "department", "jabatan",
    "attrition", "resign", "turnover", "salary", "gaji", "income", "monthlyincome"
]

SALES_KEYWORDS = [
    "sales", "jualan", "revenue", "top", "banding", "compare", "vs", "versus", "mom",
    "bulan", "month", "mtd", "quantity", "qty", "terjual", "state", "negeri", "branch", "cawangan",
    "channel", "saluran"
]

DOC_KEYWORDS = [
    "policy", "polisi", "sop", "guideline", "procedure", "refund", "return",
    "privacy", "complaint", "attendance", "onboarding", "leave", "cuti"
]

HR_POLICY_KEYWORDS = [
    "policy", "handbook", "guideline", "procedure", "sop",
    "medical claim", "claim", "benefit", "benefits", "entitlement",
    "annual leave", "sick leave", "leave", "cuti",
    "overtime approval", "approval", "disciplinary", "probation",
    "grievance", "whistleblowing"
]


def detect_intent(text: str, has_image: bool) -> str:
    """
    Returns: visual | hr_kpi | sales_kpi | rag_docs
    Priority:
      1) If image uploaded => visual
      2) Policy/SOP/Docs keywords => rag_docs
      3) HR KPI keywords => hr_kpi
      4) Sales KPI keywords => sales_kpi
      5) Default => rag_docs
    """
    s = (text or "").lower().strip()

    if has_image:
        return "visual"

    # Policy / SOP should go to docs
    if any(k in s for k in HR_POLICY_KEYWORDS) or any(k in s for k in DOC_KEYWORDS):
        return "rag_docs"

    if any(k in s for k in HR_KEYWORDS):
        return "hr_kpi"

    if any(k in s for k in SALES_KEYWORDS):
        return "sales_kpi"

    return "rag_docs"


def safe_log_interaction(model, route, question, answer, latency):
    try:
        log_interaction(model, route, question, answer, latency)
    except Exception as e:
        print("⚠️ Logging failed:", e)



# =========================
# RAG QUERY UI (Blocks: 2 outputs)
# returns: (status_html, answer_markdown)
#
# Features:
# - Auto badge by route: KPI / RAG / OCR
# - Streaming (throttled) for LLM answers
# - Deterministic KPI answers (no LLM)
# - Logging kept (1 row per query)
# =========================
import time

def rag_query_ui(user_input: str, model_name: str, has_image: bool = False):
    start = time.perf_counter()
    route = "rag_docs"
    final_answer = ""

    def elapsed_s() -> float:
        return time.perf_counter() - start

    def render_status(route_name: str, model: str, note: str = "Processing") -> str:
        # route badge
        if route_name in ("sales_kpi", "hr_kpi"):
            r = '<span class="badge kpi">KPI</span>'
        elif route_name == "visual":
            r = '<span class="badge ocr">OCR</span>'
        elif route_name == "validation":
            r = '<span class="badge note">VALIDATION</span>'
        else:
            r = '<span class="badge rag">RAG</span>'

        m = f'<span class="badge model">Model: {model}</span>'
        t = f'<span class="badge time">⏳ {elapsed_s():.1f}s</span>'
        n = f'<span class="badge note">{note}</span>' if note else ""

        return f'<div class="badges">{r}{m}{t}{n}</div>'

    def stream_with_throttle(prefix_md: str, stream_gen, route_name: str, tick: float = 0.2) -> str:
        """
        Stream answer with UI updates at most every `tick` seconds.
        Yields (status_html, answer_md).
        Returns final answer markdown.
        """
        out = ""
        last = time.perf_counter()

        # show prefix immediately
        yield (render_status(route_name, model_name, note="Processing"), prefix_md)

        for partial in stream_gen:
            out = partial
            now = time.perf_counter()
            if (now - last) >= tick:
                last = now
                yield (render_status(route_name, model_name, note="Processing"), prefix_md + out)

        final_md = (prefix_md + out).strip()
        yield (render_status(route_name, model_name, note="Done"), final_md)
        return final_md

    try:
        user_input = (user_input or "").strip()

        # Validation
        if len(user_input) < 3:
            route = "validation"
            final_answer = "Sila tanya soalan yang lebih jelas."
            latency = int(elapsed_s() * 1000)
            safe_log_interaction(model_name, route, user_input, final_answer, latency)
            yield (render_status(route, model_name, note="Validation"), final_answer)
            return

        intent = detect_intent(user_input, has_image=has_image)
        print("DEBUG intent=", intent, "model=", model_name, "len=", len(user_input), "has_image=", has_image)

        # 1) Visual (OCR text already appended in multimodal_query)
        if intent == "visual":
            route = "visual"
            prefix = "📷 **Source: OCR + RAG + LLM**\n\n"
            gen = generate_answer_with_model_stream(model_name, user_input, mode="all")

            final_answer = yield from stream_with_throttle(prefix, gen, route_name=route, tick=0.2)

            latency = int(elapsed_s() * 1000)
            safe_log_interaction(model_name, route, user_input, final_answer, latency)
            return

        # 2) HR KPI path (structured HR.csv)
        if intent == "hr_kpi":
            route = "hr_kpi"
            hr_ans = answer_hr(user_input)

            # If HR returns None (policy-like), fallback to docs RAG
            if hr_ans is None:
                route = "rag_docs"
                prefix = "📄 **Source: RAG + LLM**\n\n"
                gen = generate_answer_with_model_stream(model_name, user_input, mode="docs")

                final_answer = yield from stream_with_throttle(prefix, gen, route_name=route, tick=0.2)

                latency = int(elapsed_s() * 1000)
                safe_log_interaction(model_name, route, user_input, final_answer, latency)
                return

            # deterministic HR answer
            final_answer = hr_ans
            latency = int(elapsed_s() * 1000)
            safe_log_interaction("N/A", route, user_input, final_answer, latency)
            yield (render_status(route, model_name, note="Done"), final_answer)
            return

        # 3) Sales KPI path (structured Sales.csv)
        if intent == "sales_kpi":
            route = "sales_kpi"
            ans = answer_sales_ceo_kpi(user_input)
            if ans is None:
                ans = "Error: sales_kpi returned None (check answer_sales_ceo_kpi return paths)."

            final_answer = ans
            latency = int(elapsed_s() * 1000)
            safe_log_interaction("N/A", route, user_input, final_answer, latency)
            yield (render_status(route, model_name, note="Done"), final_answer)
            return

        # 4) Default docs RAG
        route = "rag_docs"
        prefix = "📄 **Source: RAG + LLM**\n\n"
        gen = generate_answer_with_model_stream(model_name, user_input, mode="docs")

        final_answer = yield from stream_with_throttle(prefix, gen, route_name=route, tick=0.2)

        latency = int(elapsed_s() * 1000)
        safe_log_interaction(model_name, route, user_input, final_answer, latency)
        return

    except Exception as e:
        final_answer = f"Error: {e}"
        latency = int(elapsed_s() * 1000)
        safe_log_interaction(model_name, route, user_input, final_answer, latency)
        yield (render_status(route, model_name, note="Error"), final_answer)
        return
# =========================
# 9) Multimodal wrapper (image + text) — STREAMING (Blocks: 2 outputs)
# returns: (status_md, answer_md)
# =========================
import time

def multimodal_query(text_input, image_input, model_name):
    start = time.perf_counter()

    def elapsed_s():
        return time.perf_counter() - start

    # Build query
    query = (text_input or "").strip()
    has_image = image_input is not None

    # If image uploaded, OCR/caption + append into query
    if has_image:
        # show early status (so user nampak running)
        yield (
            f'<div class="badges">'
            f'<span class="badge ocr">OCR</span>'
            f'<span class="badge model">Model: {model_name}</span>'
            f'<span class="badge time">⏳ {elapsed_s():.1f}s</span>'
            f'<span class="badge note">Reading image</span>'
            f'</div>',
            ""
        )

        cap = caption_image(image_input)
        print("🖼️ OCR:", cap[:300])

        if query:
            query = f"{query}\n\n{cap}"
        else:
            query = f"Please summarize the image.\n\n{cap}"

    if not query:
        yield ("", "Please provide a question, an image, or both.")
        return

    # initial status (general)
    yield (
        f'<div class="badges">'
        f'<span class="badge model">Model: {model_name}</span>'
        f'<span class="badge time">⏳ {elapsed_s():.1f}s</span>'
        f'<span class="badge note">Processing</span>'
        f'</div>',
        ""
    )

    # Stream from rag_query_ui (which yields (status_html, answer_md))
    for status_html, answer_md in rag_query_ui(query, model_name, has_image=has_image):
        # ensure time badge always updates even if status_html empty
        if not status_html:
            status_html = (
                f'<div class="badges">'
                f'<span class="badge model">Model: {model_name}</span>'
                f'<span class="badge time">⏳ {elapsed_s():.1f}s</span>'
                f'</div>'
            )
        yield (status_html, answer_md)



# =========================
# 10) Launch UI — CEO Bot Header (POLISHED + COMPATIBLE)
# =========================
import gradio as gr

if __name__ == "__main__":
    models = get_installed_ollama_models()
    default_model = models[0] if models else "llama3:latest"
    print("✅ Ollama models found:", models)
    print("🚀 Launching CEO Bot (FAISS + OCR + RAG + LLM)...")

    with gr.Blocks(title="CEO Bot") as demo:
        gr.HTML("""
        <style>
            body { background: #f6f7fb; }

              .container {
                 max-width: 1120px;
                 margin: 0 auto;
                 padding: 10px 10px 26px 10px;
             }

         /* ===== HEADER ===== */
            .topbar {
                display:flex;
                align-items:center;
                justify-content:space-between;
                gap:18px;
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 18px;
                padding: 16px 18px;
                background: radial-gradient(1200px 400px at 20% 50%, rgba(249,115,22,0.18), transparent 55%),
                linear-gradient(180deg, #0b1220 0%, #0f172a 100%);
                box-shadow: 0 18px 40px rgba(2,6,23,0.45);
                margin-bottom: 18px;
             }

            .brand { display:flex; gap:14px; align-items:center; }

            .logo {
                width: 48px; height: 48px;
                border-radius: 16px;
                background: linear-gradient(135deg, #f97316, #fb923c);
                box-shadow: 0 14px 28px rgba(249,115,22,0.45);
                display:flex; align-items:center; justify-content:center;
                color: #111827;
                font-weight: 900; font-size: 16px;
                letter-spacing: -0.2px;
                flex: 0 0 auto;
            }
                
                /* 🔥 ADD HERE (TEXT FIX) */
            #brand_title {
                color: #ffffff !important;
                font-size: 26px;
                font-weight: 900;
             }

            #brand_subtitle {
                
                color: rgba(255,255,255,0.75) !important;
                font-size: 14px;
                margin-top: 4px;
             }


            .title { font-size: 26px; font-weight: 900; margin: 0; color:#ffffff; letter-spacing: -0.3px; }
            .subtitle { font-size: 14px; margin-top: 4px;  color: rgba(255,255,255,0.72); }

                /* ===== RIGHT INFO PANEL (clean, not button-like) ===== */
            .meta {
                display:grid;
                grid-template-columns: 1fr 1fr;
                gap: 8px 10px;
                padding: 10px;
                border-radius: 14px;
                border: 1px solid rgba(255,255,255,0.10);
                color: rgba(255,255,255,0.88) !important; 
                background: rgba(255,255,255,0.06);
                min-width: 300px;
            
            }

            .chip {
                font-size: 12px;
                padding: 7px 10px;
                border-radius: 10px;
                border: 1px solid rgba(255,255,255,0.12);
                background: rgba(255,255,255,0.08);0
                color: rgba(255,255,255,0.88) !important; 
                white-space: nowrap;
            }
            .chip b { font-weight: 800; color: rgba(255,255,255,0.88) !important;  }; }

            /* ===== Cards ===== */
            .card {
                border: 1px solid #e6e8ef;
                border-radius: 18px;
                padding: 16px;
                background: #ffffff;
                box-shadow: 0 10px 26px rgba(16,24,40,0.05);
            }
            .section-title { letter-spacing: -0.2px; font-size: 15px; font-weight: 800; margin: 8px 0 10px 2px; color:#0f172a; }

            /* Output */
            #status_box { min-height: 30px; }
            #answer_box {
                height: 380px;
                overflow: auto;
                border: 1px solid #e6e8ef;
                border-radius: 16px;
                padding: 14px;
                background: #ffffff;
            }

            .btnrow button { height: 44px; border-radius: 14px !important; font-weight: 800; }

            /* Status badges (dynamic) */
            .badges { display:flex; gap:8px; flex-wrap:wrap; margin: 2px 0 10px 0; }
            .badge { font-size:12px; padding:6px 10px; border-radius:999px; border:1px solid #e6e8ef; background:white; }
            .badge.kpi   { background:#ecfdf5; border-color:#10b981; color:#065f46; }
            .badge.rag   { background:#fff7ed; border-color:#f97316; color:#9a3412; }
            .badge.ocr   { background:#eff6ff; border-color:#3b82f6; color:#1e3a8a; }
            .badge.model { background:#f5f3ff; border-color:#a78bfa; color:#4c1d95; }
            .badge.time  { background:#f8fafc; border-color:#e6e8ef; color:#111827; }
            .badge.note  { background:#ffffff; border-color:#e6e8ef; color:#64748b; }

             /* ===== FORCE READABILITY IN DARK HEADER ===== */
.topbar, .topbar * {
  color: rgba(255,255,255,0.86) !important;
}

/* Title lebih terang sikit */
#brand_title, #brand_title * {
  color: rgba(255,255,255,0.95) !important;
  text-shadow: 0 1px 2px rgba(0,0,0,0.40);
}

/* Subtitle putih lembut, bukan seputih title */
#brand_subtitle, #brand_subtitle * {
  color: rgba(255,255,255,0.72) !important;
  text-shadow: 0 1px 2px rgba(0,0,0,0.40);
}

/* Chips: pastikan text dalam chip pun ikut */
.meta, .meta * , .chip, .chip * {
  color: rgba(255,255,255,0.88) !important;
}     

        </style>
        """)

        with gr.Column(elem_classes=["container"]):
            # ✅ NEW HEADER (CEO Bot)
            gr.HTML("""
                    
             <div class="topbar">
                <!-- LEFT BRAND -->
                <div class="brand">
                   <div class="logo">CB</div>
                   <div>
                      <div class="title" id="brand_title">CEO Bot</div>
                      <div class="subtitle">
                         Retail Intelligence & Decision Support System (FAISS + OCR + RAG + LLM)
                      </div>
                   </div>
                </div>

              <!-- RIGHT INFO -->
              <div class="meta">
                  <div class="chip"><b>KPI</b> Deterministic</div>
                  <div class="chip"><b>Docs</b> RAG Search</div>
                  <div class="chip"><b>Image</b> OCR → RAG</div>
                  <div class="chip"><b>UX</b> Streaming + Timer</div>
               </div>
             </div>
            """)

            with gr.Row():
                # LEFT: Inputs
                with gr.Column(scale=5):
                    gr.Markdown("### Inputs", elem_classes=["section-title"])
                    with gr.Group(elem_classes=["card"]):
                        txt = gr.Textbox(lines=3, label="Soalan", placeholder="Contoh: sales ikut state bulan 2024-06")
                        img = gr.Image(type="filepath", label="Upload table/chart image (optional)")
                        model = gr.Dropdown(choices=models, value=default_model, label="LLM model (RAG only)")

                        with gr.Row(elem_classes=["btnrow"]):
                            submit = gr.Button("Submit", variant="primary")
                            clear = gr.Button("Clear")

                    gr.Markdown("### Examples (klik untuk isi soalan)", elem_classes=["section-title"])
                    gr.Examples(
                        examples=[
                            ["sales bulan 2024-06 berapa?"],
                            ["banding sales bulan ni vs bulan lepas"],
                            ["top 3 product bulan 2024-06"],
                            ["sales ikut state bulan 2024-06"],
                            ["headcount ikut state"],
                            ["which age group has highest attrition?"],
                            ["What is the annual leave entitlement per year?"],
                            ["summarize table ini (upload gambar table)"],
                        ],
                        inputs=[txt],
                    )

                # RIGHT: Outputs
                with gr.Column(scale=6):
                    gr.Markdown("### Output", elem_classes=["section-title"])
                    with gr.Group(elem_classes=["card"]):
                        status_md = gr.HTML("", elem_id="status_box")      # badges HTML
                        answer_md = gr.Markdown("", elem_id="answer_box")  # answer Markdown

            submit.click(
                fn=multimodal_query,
                inputs=[txt, img, model],
                outputs=[status_md, answer_md],
            )

            clear.click(fn=lambda: ("", ""), inputs=[], outputs=[status_md, answer_md])
            clear.click(fn=lambda: ("", None, default_model), inputs=[], outputs=[txt, img, model])

            gr.Markdown("Logs saved to: `logs/chat_logs.csv`")

    demo.queue().launch(inbrowser=True, debug=True, show_error=True)

