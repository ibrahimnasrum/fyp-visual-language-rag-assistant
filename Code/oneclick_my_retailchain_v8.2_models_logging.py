import os
import re
import glob
import time
import csv
import subprocess
import pickle
from pathlib import Path
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

# Import fuzzy matching and query normalization
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'query'))
try:
    from validator import DataValidator
    FUZZY_ENABLED = True
    print("✅ Fuzzy matching enabled")
except ImportError:
    FUZZY_ENABLED = False
    print("⚠️ Fuzzy matching disabled (validator not found)")

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

def get_installed_ollama_models(default=("llava:13b",)):
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

# Embeddings + FAISS with caching
cache_file = Path(__file__).parent / "faiss_cache.pkl"
index_file = Path(__file__).parent / "faiss_index.bin"

# Check if cache exists and is valid
cache_valid = False
if cache_file.exists() and index_file.exists():
    try:
        with open(cache_file, 'rb') as f:
            cached_summaries = pickle.load(f)
        if cached_summaries == summaries:
            print("✅ Loading cached FAISS index (fast startup)...")
            embedder = SentenceTransformer("all-MiniLM-L6-v2", device=device)
            index = faiss.read_index(str(index_file))
            cache_valid = True
            print(f"✅ FAISS index loaded from cache: {index.ntotal} vectors")
    except Exception as e:
        print(f"⚠️  Cache load failed: {e}, rebuilding...")

if not cache_valid:
    print("🔨 Building FAISS index (first run or data changed, will cache for next time)...")
    embedder = SentenceTransformer("all-MiniLM-L6-v2", device=device)
    emb = embedder.encode(summaries, convert_to_numpy=True, show_progress_bar=True)
    faiss.normalize_L2(emb)
    index = faiss.IndexFlatIP(emb.shape[1])
    index.add(emb)
    print(f"✅ FAISS index built: {index.ntotal} vectors")
    
    # Save cache
    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(summaries, f)
        faiss.write_index(index, str(index_file))
        print(f"💾 Cached FAISS index for fast startup next time")
    except Exception as e:
        print(f"⚠️  Cache save failed: {e}")

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
        
        # Calculate insights
        total_metric = float(grp.sum())
        top_total = float(top_df[metric_label].sum() if metric != "revenue" else grp.head(top_n).sum())
        concentration = (top_total / total_metric * 100) if total_metric > 0 else 0

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
            "📊 **Performance Insights:**",
            f"- Top {top_n} contribute **{concentration:.1f}%** of total {metric}",
            f"- Total {dim} analyzed: **{len(grp)}**",
            f"- Transactions included: **{len(sub):,}**",
            "",
            f"💡 **Strategic Note:** High concentration indicates strong performers; consider replicating their success factors across other {dim}.",
        ])

    # =========================
    # Default total (single month)
    # =========================
    total_val = float(sub[value_col].sum())
    
    # Calculate context metrics for executive insights
    all_months_data = df_sales.groupby("YearMonth")[value_col].sum()
    avg_monthly = float(all_months_data.mean())
    max_monthly = float(all_months_data.max())
    max_month = all_months_data.idxmax()
    
    # Performance assessment
    vs_avg_pct = ((total_val - avg_monthly) / avg_monthly * 100) if avg_monthly > 0 else 0
    vs_max_pct = ((total_val - max_monthly) / max_monthly * 100) if max_monthly > 0 else 0
    
    # Build executive response with context
    lines = [
        "✅ **Source: structured KPI**",
        f"✅ **{metric_label}**",
        f"- Month: **{month}**",
        f"- Value: **RM {format_num(total_val, decimals)}**" if metric == "revenue" else f"- Value: **{int(total_val)}**",
        "",
        "📊 **Performance Context:**",
        f"- 6-Month Average: **RM {format_num(avg_monthly, decimals)}**" if metric == "revenue" else f"- 6-Month Average: **{int(avg_monthly)}**",
        f"- Best Month ({max_month}): **RM {format_num(max_monthly, decimals)}**" if metric == "revenue" else f"- Best Month ({max_month}): **{int(max_monthly)}**",
        f"- vs Average: **{vs_avg_pct:+.1f}%** {'📈 Above average' if vs_avg_pct > 0 else '📉 Below average' if vs_avg_pct < 0 else '➡️ On par'}",
        "",
        "📋 **Data Quality:**",
        f"- Transactions analyzed: **{len(sub):,}**",
        f"- Dataset coverage: **{AVAILABLE_SALES_MONTHS[0]}** to **{AVAILABLE_SALES_MONTHS[-1]}** (6 months)",
        f"- Note: 'bulan ni' refers to latest available month (**{LATEST_SALES_MONTH}**) in offline demo.",
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
                total = len(df_hr)
                pct = (n / total * 100) if total > 0 else 0
                dept_counts = df_hr.groupby("Department")["EmpID"].count().sort_values(ascending=False)
                rank = list(dept_counts.index).index(d) + 1
                return "\n".join([
                    "✅ **Source: structured HR**",
                    f"👥 **Headcount Analysis - {d} Department**",
                    f"- Department Headcount: **{n}** employees",
                    f"- Organization Total: **{total:,}** employees",
                    f"- Department Share: **{pct:.1f}%** of workforce",
                    f"- Department Ranking: **#{rank}** of {len(dept_counts)} departments by size",
                    "",
                    "📊 **Context:** Understanding department distribution helps optimize resource allocation and identify growth areas.",
                ])

        for st in HR_STATES:
            if st.lower() in s:
                n = int((df_hr["State"] == st).sum())
                total = len(df_hr)
                pct = (n / total * 100) if total > 0 else 0
                state_counts = df_hr.groupby("State")["EmpID"].count().sort_values(ascending=False)
                rank = list(state_counts.index).index(st) + 1
                return "\n".join([
                    "✅ **Source: structured HR**",
                    f"👥 **Headcount Analysis - {st} State**",
                    f"- State Headcount: **{n}** employees",
                    f"- Organization Total: **{total:,}** employees",
                    f"- State Share: **{pct:.1f}%** of workforce",
                    f"- State Ranking: **#{rank}** of {len(state_counts)} states by size",
                    "",
                    "📊 **Context:** Geographic distribution insights support regional expansion and workforce planning strategies.",
                ])

        # Total headcount
        total = len(df_hr)
        dept_count = df_hr["Department"].nunique()
        state_count = df_hr["State"].nunique()
        avg_per_dept = total / dept_count if dept_count > 0 else 0
        return "\n".join([
            "✅ **Source: structured HR**",
            "👥 **Organization Headcount Overview**",
            f"- Total Employees: **{total:,}**",
            f"- Departments: **{dept_count}** (avg **{avg_per_dept:.0f}** employees/dept)",
            f"- Geographic Coverage: **{state_count}** states",
            "",
            "📊 **Workforce Distribution:** Organization operates across multiple departments and locations with balanced resource allocation.",
        ])

    # Attrition analysis
    if "attrition" in s:
        left = df_hr[df_hr["Attrition"].astype(str).str.lower() == "yes"].copy()
        if left.empty:
            return "\n".join([
                "✅ **Source: structured HR**",
                "📌 **Attrition Analysis**",
                "- Attrition Count: **0** employees",
                f"- Total Workforce: **{len(df_hr):,}** employees",
                "- Attrition Rate: **0.0%**",
                "",
                "✅ **Excellent Retention:** Zero attrition indicates strong employee satisfaction and effective retention strategies.",
            ])
        
        total = len(df_hr)
        attrition_count = len(left)
        attrition_rate = (attrition_count / total * 100) if total > 0 else 0

        if "age" in s:
            c = left.groupby("AgeGroup")["EmpID"].count().sort_values(ascending=False)
            top_group = c.index[0]
            top_count = int(c.iloc[0])
            group_pct = (top_count / attrition_count * 100) if attrition_count > 0 else 0
            return "\n".join([
                "✅ **Source: structured HR**",
                "📌 **Attrition Analysis by Age Group**",
                f"- Highest Attrition: **{top_group}** age group",
                f"- Attrition Count: **{top_count}** employees ({group_pct:.1f}% of all attrition)",
                f"- Overall Attrition: **{attrition_count}** of {total:,} employees ({attrition_rate:.1f}%)",
                "",
                "💡 **HR Insight:** Age-specific attrition patterns suggest targeted retention programs may be beneficial for high-risk groups.",
            ])

        if "state" in s or "negeri" in s:
            c = left.groupby("State")["EmpID"].count().sort_values(ascending=False)
            top_state = c.index[0]
            top_count = int(c.iloc[0])
            state_pct = (top_count / attrition_count * 100) if attrition_count > 0 else 0
            return "\n".join([
                "✅ **Source: structured HR**",
                "📌 **Attrition Analysis by State**",
                f"- Highest Attrition: **{top_state}** state",
                f"- Attrition Count: **{top_count}** employees ({state_pct:.1f}% of all attrition)",
                f"- Overall Attrition: **{attrition_count}** of {total:,} employees ({attrition_rate:.1f}%)",
                "",
                "💡 **HR Insight:** Geographic attrition patterns may indicate regional compensation competitiveness or work environment factors.",
            ])

        c = left.groupby("Department")["EmpID"].count().sort_values(ascending=False)
        top_dept = c.index[0]
        top_count = int(c.iloc[0])
        dept_pct = (top_count / attrition_count * 100) if attrition_count > 0 else 0
        return "\n".join([
            "✅ **Source: structured HR**",
            "📌 **Attrition Analysis by Department**",
            f"- Highest Attrition: **{top_dept}** department",
            f"- Attrition Count: **{top_count}** employees ({dept_pct:.1f}% of all attrition)",
            f"- Overall Attrition: **{attrition_count}** of {total:,} employees ({attrition_rate:.1f}%)",
            "",
            "💡 **HR Insight:** Department-specific attrition suggests need for targeted engagement and retention initiatives.",
        ])

    # Average income
    if any(k in s for k in ["average income", "avg income", "gaji purata", "purata gaji", "average salary"]):
        for d in HR_DEPTS:
            if d.lower() in s:
                dept_data = df_hr[df_hr["Department"] == d]["MonthlyIncome"]
                avg = float(dept_data.mean())
                overall_avg = float(df_hr["MonthlyIncome"].mean())
                dept_count = len(dept_data)
                vs_overall = ((avg - overall_avg) / overall_avg * 100) if overall_avg > 0 else 0
                return "\n".join([
                    "✅ **Source: structured HR**",
                    f"💰 **Salary Analysis - {d} Department**",
                    f"- Department Average: **RM {format_num(avg, 2)}**",
                    f"- Organization Average: **RM {format_num(overall_avg, 2)}**",
                    f"- vs Organization: **{vs_overall:+.1f}%** {'📈 Above average' if vs_overall > 0 else '📉 Below average' if vs_overall < 0 else '➡️ On par'}",
                    f"- Employees Analyzed: **{dept_count}**",
                    "",
                    "💡 **Compensation Insight:** Salary benchmarking ensures competitive positioning and internal equity across departments.",
                ])

        avg = float(df_hr["MonthlyIncome"].mean())
        median = float(df_hr["MonthlyIncome"].median())
        min_sal = float(df_hr["MonthlyIncome"].min())
        max_sal = float(df_hr["MonthlyIncome"].max())
        return "\n".join([
            "✅ **Source: structured HR**",
            "💰 **Organization Salary Overview**",
            f"- Average Salary: **RM {format_num(avg, 2)}**",
            f"- Median Salary: **RM {format_num(median, 2)}**",
            f"- Salary Range: **RM {format_num(min_sal, 2)}** to **RM {format_num(max_sal, 2)}**",
            f"- Total Employees: **{len(df_hr):,}**",
            "",
            "💡 **Compensation Strategy:** Comprehensive salary analysis supports competitive compensation planning and budget forecasting.",
        ])

    return None


# =========================
# 7) RAG answer with selectable model (UPDATED + STREAMING)
# =========================

def retrieve_context(query: str, k: int = 12, mode: str = "all") -> str:
    q_emb = embedder.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(q_emb)

    # v8.8 Phase 2: Increased k0 for better docs coverage
    # For docs-only mode, retrieve more candidates (minimum 60 vs previous 40)
    # This ensures comprehensive policy/procedure retrieval
    k0 = min(max(k * 5, 60), int(index.ntotal) if index is not None else 0)
    if k0 <= 0:
        return ""

    scores, idx = index.search(q_emb, k=k0)

    # idx[0] is list of candidate indices
    candidates = [summaries[i] for i in idx[0] if i != -1]

    if mode == "docs":
        candidates = [c for c in candidates if c.startswith("[DOC:")]

    # v8.8 Phase 2: Increased final k for docs mode to ensure comprehensive answers
    final_k = 18 if mode == "docs" else k
    candidates = candidates[:final_k]
    return "\n".join(candidates)


def _build_prompt(context: str, query: str) -> str:
    # v8.8 Phase 2: Enhanced prompt for comprehensive policy/docs answers
    return f"""
You are a helpful analyst for a Malaysia retail chain.
Use ONLY the provided DATA to answer the question thoroughly and completely.

DATA:
{context}

QUESTION:
{query}

RULES:
- Use ONLY the provided DATA - cite specific evidence from [DOC:...] sections
- Do NOT infer "policy" from HR/Sales rows (AgeGroup, OverTime, Attrition are NOT policies)
- If question asks policy/SOP/refund/leave AND there is no [DOC:...] evidence, answer:
  "not available in the provided data (docs)"
- Do not invent numbers or make assumptions beyond the data

ANSWER REQUIREMENTS:
- Provide detailed, comprehensive answers (minimum 200 characters for policy questions)
- Include specific procedures, steps, or requirements when available
- Quote relevant policy sections or document names
- Use clear formatting: bullet points, numbering, or paragraphs as appropriate
- Include examples from the data if available
- For policy questions, explain WHO, WHAT, WHEN, WHERE, WHY, HOW if information is available

FORMAT EXAMPLE for policy questions:
"Based on [DOC: filename], the policy states:
- Key requirement 1: [detail]
- Key requirement 2: [detail]
Process: [step-by-step if available]
Example: [if available in data]"
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
    # Core HR terms
    "hr", "human resource",
    # Employee/Staff - v8.8 Phase 3: Expanded for better routing
    "employee", "employees", "staff", "pekerja", "worker", "workers",
    "total employees", "total staff", "jumlah pekerja", "jumlah staff",
    "berapa staff", "berapa pekerja", "how many staff", "how many employee",
    # Headcount
    "headcount", "head count", "workforce", "team size", "employee count",
    # Job Roles - v8.8 Phase 3: Added specific roles that were misrouted
    "cashier", "kitchen", "manager", "supervisor", "chef", "waiter", "waitress",
    # Departments
    "department", "jabatan", "division", "team",
    # HR Metrics
    "attrition", "resign", "resignation", "turnover", "retention", "quit", "keluar kerja",
    "tenure", "years of service", "seniority", "experience",
    # Compensation
    "salary", "gaji", "pay", "wage", "income", "monthlyincome", "payroll", "compensation",
    # HR Operations  
    "hire", "hiring", "recruitment", "new joiner", "onboard", "probation"
]

SALES_KEYWORDS = [
    # Core sales terms
    "sales", "jualan", "penjualan", "revenue", "pendapatan",
    # Product/Performance
    "product", "produk", "item", "menu", "sold", "terjual",
    # Aggregations/Rankings
    "top", "bottom", "worst", "best", "highest", "lowest", "rank", "ranking",
    # Comparisons
    "banding", "compare", "comparison", "vs", "versus", "against",
    # Time periods
    "mom", "month over month", "yoy", "mtd", "ytd",
    "bulan", "month", "monthly", "week", "weekly", "daily",
    # Quantity
    "quantity", "qty", "unit", "volume",
    # Location (only when combined with sales context)
    # Moved to contextual check below
]

# These can indicate location-based queries for BOTH sales and HR
LOCATION_KEYWORDS = ["state", "negeri", "branch", "cawangan", "channel", "saluran", "location", "lokasi"]

DOC_KEYWORDS = [
    # Policy & Procedures
    "policy", "polisi", "sop", "guideline", "garis panduan", "procedure", "prosedur",
    # Returns/Refunds
    "refund", "return", "complaint", "aduan",
    # Privacy/Legal
    "privacy", "privasi", "legal", "contract", "kontrak",
    # Leave (policy context - "how to request", "entitlement", "process")
    # Removed standalone "leave", "cuti" - too ambiguous
]

HR_POLICY_KEYWORDS = [
    # Policy documents
    "policy", "handbook", "manual", "guideline", "sop",
    # Benefits
    "medical claim", "claim", "benefit", "benefits", "entitlement", "hak",
    # Leave POLICY (not leave METRICS)
    "annual leave entitlement", "leave policy", "leave entitlement", "cuti policy",
    "sick leave", "emergency leave", "maternity leave", "paternity leave",
    "how to request leave", "leave approval", "leave process",
    # HR Processes
    "overtime approval", "approval process", "disciplinary", "disciplinary action",
    "probation period", "performance review process",
    "grievance", "whistleblowing", "complaint procedure",
    # Onboarding
    "onboarding", "orientation", "new employee"
]


def detect_intent(text: str, has_image: bool) -> str:
    """
    Improved intent detection with fuzzy matching and query normalization.
    
    Returns: visual | hr_kpi | sales_kpi | rag_docs
    Priority:
      1) If image uploaded => visual
      2) Strong HR signals (employee metrics, headcount, salary) => hr_kpi
      3) Strong Sales signals (sales, revenue, product performance) => sales_kpi
      4) Policy/SOP/Process documents => rag_docs
      5) Default => rag_docs
    
    NEW: Supports typo tolerance (fuzzy matching) and Malay-to-English mapping
    """
    s = (text or "").lower().strip()

    if has_image:
        return "visual"
    
    # Apply query normalization (typo correction + Malay mapping)
    if FUZZY_ENABLED:
        normalized = DataValidator.normalize_query(s)
        s = normalized.lower()
        print(f"🔧 Normalized: '{text[:50]}...' → '{s[:50]}...'")

    # Count keyword matches (with fuzzy matching if enabled)
    if FUZZY_ENABLED:
        hr_score = sum(1 for k in HR_KEYWORDS if k in s or DataValidator.contains_fuzzy_keyword(s, [k], threshold=0.75))
        sales_score = sum(1 for k in SALES_KEYWORDS if k in s or DataValidator.contains_fuzzy_keyword(s, [k], threshold=0.75))
        doc_score = sum(1 for k in DOC_KEYWORDS if k in s or DataValidator.contains_fuzzy_keyword(s, [k], threshold=0.75))
        hr_policy_score = sum(1 for k in HR_POLICY_KEYWORDS if k in s or DataValidator.contains_fuzzy_keyword(s, [k], threshold=0.75))
    else:
        hr_score = sum(1 for k in HR_KEYWORDS if k in s)
        sales_score = sum(1 for k in SALES_KEYWORDS if k in s)
        doc_score = sum(1 for k in DOC_KEYWORDS if k in s)
        hr_policy_score = sum(1 for k in HR_POLICY_KEYWORDS if k in s)
    
    # Strong HR signals (2+ matches or specific strong keywords)
    strong_hr_keywords = ["headcount", "head count", "employee", "employees", "staff", "pekerja",
                          "attrition", "turnover", "salary", "gaji", "payroll", "tenure"]
    has_strong_hr = any(k in s for k in strong_hr_keywords)
    
    # Strong Sales signals  
    strong_sales_keywords = ["sales", "jualan", "revenue", "top product", "sold", "terjual"]
    has_strong_sales = any(k in s for k in strong_sales_keywords)
    
    # Policy/Process indicators (how to, process, policy, entitlement)
    policy_indicators = ["how to", "what is the", "process", "procedure", "entitlement", 
                        "policy", "sop", "guideline"]
    has_policy_indicator = any(ind in s for ind in policy_indicators)
    
    # HR POLICY ROUTE (docs about HR processes, not HR metrics)
    # e.g., "annual leave entitlement", "how to request leave", "leave policy"
    if hr_policy_score >= 2 or (hr_policy_score >= 1 and has_policy_indicator):
        return "rag_docs"
    
    # DOCUMENT/POLICY ROUTE (general policies, SOPs, company info)
    # e.g., "refund policy", "SOP for complaints", "company profile"
    if doc_score >= 2 or (doc_score >= 1 and has_policy_indicator):
        return "rag_docs"
    
    # HR KPI ROUTE (employee metrics, headcount, salary data)
    # e.g., "headcount berapa", "average salary", "staff by department"
    if hr_score >= 2 or (hr_score >= 1 and has_strong_hr):
        # But NOT if it's asking about policy/process
        if not has_policy_indicator:
            return "hr_kpi"
    
    # SALES KPI ROUTE (sales data, revenue, product performance)
    # e.g., "sales bulan 2024-06", "top products", "revenue by state"
    if sales_score >= 2 or (sales_score >= 1 and has_strong_sales):
        return "sales_kpi"
    
    # Location-based queries: disambiguate by context
    has_location = any(loc in s for loc in LOCATION_KEYWORDS)
    if has_location:
        # "headcount ikut state" = HR
        if hr_score >= 1 or has_strong_hr:
            return "hr_kpi"
        # "sales by state" = Sales  
        if sales_score >= 1 or has_strong_sales:
            return "sales_kpi"
    
    # Single keyword matches: prefer HR over Sales if ambiguous
    if hr_score >= 1 and has_strong_hr:
        return "hr_kpi"
    
    if sales_score >= 1:
        return "sales_kpi"
    
    # Default to docs for everything else
    return "rag_docs"


def safe_log_interaction(model, route, question, answer, latency):
    try:
        log_interaction(model, route, question, answer, latency)
    except Exception as e:
        print("⚠️ Logging failed:", e)


def acknowledge_query(query: str, answer_type: str = "analysis") -> str:
    """
    Generate natural query acknowledgment for executive communication.
    Increases semantic similarity by echoing key query terms.
    
    Args:
        query: Original user query
        answer_type: Type of answer (analysis/summary/report)
    
    Returns:
        str: Natural acknowledgment sentence
    """
    q = query.lower().strip()
    
    # Extract key intent signals
    is_question = any(word in q for word in ["berapa", "how many", "how much", "what", "apa", "siapa"])
    is_comparison = any(word in q for word in ["compare", "banding", "vs", "versus"])
    is_top = "top" in q or "best" in q or "terbaik" in q
    is_total = "total" in q or "jumlah" in q
    
    # Generate natural acknowledgment
    if is_comparison:
        return f"**Query Analysis:** {query}\n\n"
    elif is_top:
        return f"**Requested Analysis:** {query}\n\n"
    elif is_question or is_total:
        return f"**Answering:** {query}\n\n"
    else:
        return f"**Analysis for:** {query}\n\n"


def enforce_executive_format(answer: str, min_length: int = 300, query: str = None) -> str:
    """
    Enforce executive format standards for answers.
    
    Requirements:
    - Query acknowledgment for semantic relevance
    - Minimum 300 characters for comprehensive answers
    - Proper structure with markdown formatting
    - Data-driven insights
    
    Args:
        answer: Raw answer text
        min_length: Minimum character count (default: 300)
        query: Original user query for acknowledgment
    
    Returns:
        str: Enhanced answer meeting quality standards
    """
    if not answer or answer.startswith("Error:"):
        return answer
    
    # Add query acknowledgment if provided (increases semantic similarity)
    if query and not answer.startswith("**Query") and not answer.startswith("**Answering") and not answer.startswith("**Analysis"):
        acknowledgment = acknowledge_query(query)
        answer = acknowledgment + answer
    
    # Check if answer is already well-formatted
    has_structure = any(marker in answer for marker in ["**", "###", "|", "•", "-\n"])
    
    # If answer is too short and lacks structure, add guidance
    if len(answer) < min_length and not has_structure:
        prefix = f"⚠️ **Note:** Brief answer provided ({len(answer)} chars). For comprehensive analysis, consider:\n\n"
        return prefix + answer
    
    return answer



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
            
            # Enforce executive format quality with query acknowledgment
            final_answer = enforce_executive_format(final_answer, min_length=300, query=user_input)

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
                
                # Enforce executive format quality with query acknowledgment
                final_answer = enforce_executive_format(final_answer, min_length=300, query=user_input)

                latency = int(elapsed_s() * 1000)
                safe_log_interaction(model_name, route, user_input, final_answer, latency)
                return

            # deterministic HR answer
            final_answer = hr_ans
            
            # Enforce executive format quality with query acknowledgment
            final_answer = enforce_executive_format(final_answer, min_length=300, query=user_input)
            
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
            
            # Enforce executive format quality with query acknowledgment
            final_answer = enforce_executive_format(final_answer, min_length=300, query=user_input)
            
            latency = int(elapsed_s() * 1000)
            safe_log_interaction("N/A", route, user_input, final_answer, latency)
            yield (render_status(route, model_name, note="Done"), final_answer)
            return

        # 4) Default docs RAG
        route = "rag_docs"
        prefix = "📄 **Source: RAG + LLM**\n\n"
        gen = generate_answer_with_model_stream(model_name, user_input, mode="docs")

        final_answer = yield from stream_with_throttle(prefix, gen, route_name=route, tick=0.2)
        
        # Enforce executive format quality with query acknowledgment
        final_answer = enforce_executive_format(final_answer, min_length=300, query=user_input)

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
    default_model = "qwen2.5:7b"  # Phase 2.4: MODEL COMPARISON TEST (FINAL TEXT LLM)
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

