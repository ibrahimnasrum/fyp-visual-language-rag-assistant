import os
import re

import faiss
import gradio as gr
import ollama
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer

# Try to import BLIP-2 + PIL (for images)
try:
    from transformers import Blip2Processor, Blip2ForConditionalGeneration
    from PIL import Image
    BLIP2_AVAILABLE = True
except ImportError:
    BLIP2_AVAILABLE = False
    print("⚠️ transformers or Pillow not installed - BLIP-2 image captioning disabled.")

# =========================
# 1. Device detection
# =========================
if torch.cuda.is_available():
    device = "cuda"
    print(f"✅ Success: NVIDIA GPU detected. Using device: {device}")
else:
    device = "cpu"
    print("⚠️ Warning: GPU not detected. Using CPU (slower).")

# =========================
# 2. Load CSV data
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SALES_CSV_PATH = os.path.join(BASE_DIR, "retail_burger_sales.csv")  # adjust if needed
HR_CSV_PATH = os.path.join(BASE_DIR, "HR.csv")                      # HR dataset

if not os.path.exists(SALES_CSV_PATH):
    raise FileNotFoundError(f"Sales CSV file not found at: {SALES_CSV_PATH}")
if not os.path.exists(HR_CSV_PATH):
    raise FileNotFoundError(f"HR CSV file not found at: {HR_CSV_PATH}")

# Sales data (burger)
df_sales = pd.read_csv(SALES_CSV_PATH)
print("📄 Loaded SALES CSV with shape:", df_sales.shape)
print("Sales Columns:", list(df_sales.columns))
# ---- Sales normalization for KPI queries ----
df_sales["Date"] = pd.to_datetime(df_sales["Date"], errors="coerce")
df_sales["DateStr"] = df_sales["Date"].dt.strftime("%Y-%m-%d")
df_sales["YearMonth"] = df_sales["Date"].dt.to_period("M")

# Ensure numeric columns are numeric (safer for sums)
for _c in ["Quantity", "Unit Price", "Total Sale"]:
    df_sales[_c] = pd.to_numeric(df_sales[_c], errors="coerce")

AVAILABLE_SALES_MONTHS = sorted(df_sales["YearMonth"].dropna().unique().tolist())
LATEST_SALES_MONTH = max(AVAILABLE_SALES_MONTHS) if AVAILABLE_SALES_MONTHS else None

# HR data
df_hr = pd.read_csv(HR_CSV_PATH)
print("📄 Loaded HR CSV with shape:", df_hr.shape)
print("HR Columns:", list(df_hr.columns))

# =========================
# 3. Precompute metadata (Sales + HR)
# =========================
# Sales-specific metadata
EMPLOYEES = sorted(df_sales["Employee"].dropna().unique().tolist())
PRODUCTS = sorted(df_sales["Product"].dropna().unique().tolist())
REGIONS = sorted(df_sales["Region"].dropna().unique().tolist())
print("Sales Employees:", EMPLOYEES)
print("Sales Products:", PRODUCTS)
print("Sales Regions:", REGIONS)

# HR-specific metadata (useful for parsing)
HR_DEPARTMENTS = sorted(df_hr["Department"].dropna().unique().tolist())
HR_ATTRITION_VALUES = sorted(df_hr["Attrition"].dropna().unique().tolist())
HR_AGEGROUPS = sorted(df_hr["AgeGroup"].dropna().unique().tolist())
print("HR Departments:", HR_DEPARTMENTS)
print("HR AgeGroups:", HR_AGEGROUPS)
print("HR Attrition values:", HR_ATTRITION_VALUES)

# =========================
# 4. Build summaries (Sales + HR) and embeddings for RAG
# =========================

# ---- 4a. Sales row summaries ----
sales_summaries = []
for _, row in df_sales.iterrows():
    summary = (
        f"[SALES] "
        f"Date={row['DateStr']}; "
        f"Region={row['Region']}; "
        f"Product={row['Product']}; "
        f"Employee={row['Employee']}; "
        f"Qty={row['Quantity']}; "
        f"UnitPrice={row['Unit Price']}; "
        f"TotalSale={row['Total Sale']}"
    )
    sales_summaries.append(summary)

print(f"🔢 Built {len(sales_summaries)} SALES row summaries.")

# ---- 4b. HR row summaries ----
hr_summaries = []
for _, row in df_hr.iterrows():
    # Use key HR columns to describe each employee
    summary = (
        f"[HR] "
        f"EmpID={row['EmpID']}; "
        f"Age={row['Age']}; "
        f"AgeGroup={row['AgeGroup']}; "
        f"Attrition={row['Attrition']}; "
        f"BusinessTravel={row['BusinessTravel']}; "
        f"DailyRate={row['DailyRate']}; "
        f"Department={row['Department']}; "
        f"DistanceFromHome={row['DistanceFromHome']}; "
        f"Education={row['Education']}; "
        f"EducationField={row['EducationField']}; "
        f"EmployeeCount={row['EmployeeCount']}; "
        f"EmployeeNumber={row['EmployeeNumber']}; "
        f"EnvironmentSatisfaction={row['EnvironmentSatisfaction']}; "
        f"Gender={row['Gender']}; "
        f"HourlyRate={row['HourlyRate']}; "
        f"JobInvolvement={row['JobInvolvement']}; "
        f"JobLevel={row['JobLevel']}; "
        f"JobRole={row['JobRole']}; "
        f"JobSatisfaction={row['JobSatisfaction']}; "
        f"MaritalStatus={row['MaritalStatus']}; "
        f"MonthlyIncome={row['MonthlyIncome']}; "
        f"MonthlyRate={row['MonthlyRate']}; "
        f"NumCompaniesWorked={row['NumCompaniesWorked']}; "
        f"OverTime={row['OverTime']}; "
        f"PercentSalaryHike={row['PercentSalaryHike']}; "
        f"PerformanceRating={row['PerformanceRating']}; "
        f"TotalWorkingYears={row['TotalWorkingYears']}; "
        f"TrainingTimesLastYear={row['TrainingTimesLastYear']}; "
        f"WorkLifeBalance={row['WorkLifeBalance']}; "
        f"YearsAtCompany={row['YearsAtCompany']}; "
        f"YearsInCurrentRole={row['YearsInCurrentRole']}; "
        f"YearsSinceLastPromotion={row['YearsSinceLastPromotion']}; "
        f"YearsWithCurrManager={row['YearsWithCurrManager']}"
    )
    hr_summaries.append(summary)

print(f"🔢 Built {len(hr_summaries)} HR row summaries.")

# ---- 4c. Combine for one big RAG corpus ----
summaries = sales_summaries + hr_summaries
print(f"📚 Total RAG summaries (Sales + HR): {len(summaries)}")

# Load embedding model
embedder = SentenceTransformer("all-MiniLM-L6-v2", device=device)

print("📦 Encoding all summaries into embeddings (Sales + HR)...")
emb_matrix = embedder.encode(
    summaries,
    convert_to_numpy=True,
    show_progress_bar=True,
)

# Normalize for cosine similarity
faiss.normalize_L2(emb_matrix)

# Build FAISS index (combined)
d = emb_matrix.shape[1]
index = faiss.IndexFlatIP(d)
index.add(emb_matrix)
print("✅ FAISS index built with", index.ntotal, "vectors (Sales + HR).")

# =========================
# 5. Question type detectors
# =========================

# ---- Sales detectors ----
def is_sales_quantity_question(query: str) -> bool:
    q = query.lower()
    return (
        ("how many" in q or "quantity" in q)
        and "burger" in q
    )


def is_sales_amount_question(query: str) -> bool:
    q = query.lower()
    return (
        "total sale" in q
        or "total amount" in q
        or "sale amount" in q
        or "how much revenue" in q
        or ("how much" in q and "sell" in q)
    )

# ---- HR detectors ----
def is_hr_department_count_question(query: str) -> bool:
    """
    e.g. 'How many employees work in the Sales department?'
    """
    q = query.lower()
    if "how many" not in q:
        return False
    if "department" in q:
        return True
    for dept in HR_DEPARTMENTS:
        if dept.lower() in q:
            return True
    return False


def is_hr_attrition_by_agegroup_question(query: str) -> bool:
    """
    e.g. 'Which age group has the highest attrition?'
    """
    q = query.lower()
    return "attrition" in q and ("age group" in q or "agegroup" in q)

# =========================
# 6. Date + filter extraction (Sales)
# =========================
MONTH_PATTERN = (
    r"(Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|"
    r"Aug|August|Sep|September|Oct|October|Nov|November|Dec|December)"
)

def extract_date_from_query(query: str):
    """
    Try to find a date in formats:
    - 2024-01-01
    - Jan 1, 2024 / January 1, 2024
    - 1 Jan 2024
    Return 'YYYY-MM-DD' or None.
    """
    # 1) ISO format
    m_iso = re.search(r"\d{4}-\d{2}-\d{2}", query)
    if m_iso:
        return m_iso.group(0)

    # 2) 'Jan 1, 2024' or 'January 1 2024'
    m_long = re.search(
        rf"{MONTH_PATTERN}\s+\d{{1,2}},?\s+\d{{4}}",
        query,
        flags=re.IGNORECASE,
    )
    # 3) '1 Jan 2024'
    m_reverse = re.search(
        rf"\d{{1,2}}\s+{MONTH_PATTERN}\s+\d{{4}}",
        query,
        flags=re.IGNORECASE,
    )

    date_str = None
    if m_long:
        date_str = m_long.group(0)
    elif m_reverse:
        date_str = m_reverse.group(0)

    if date_str is None:
        return None

    try:
        dt = pd.to_datetime(date_str, dayfirst=False)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None


def extract_sales_filters_from_question(query: str):
    """
    Simple rule-based parser (for Sales dataset):
    - Date in various formats -> normalized to 'YYYY-MM-DD'
    - Region (from known regions)
    - Employee (from known employees)
    - Product (from known products)
    """
    q_lower = query.lower()

    # Date
    date = extract_date_from_query(query)

    # Region
    region = None
    for r in REGIONS:
        if r.lower() in q_lower:
            region = r
            break

    # Employee
    employee = None
    for emp in EMPLOYEES:
        if emp.lower() in q_lower:
            employee = emp
            break

    # Product (longest names first)
    product = None
    for prod in sorted(PRODUCTS, key=len, reverse=True):
        if prod.lower() in q_lower:
            product = prod
            break

    return {
        "date": date,
        "region": region,
        "employee": employee,
        "product": product,
    }

# =========================
# 7. Deterministic numeric answers
# =========================

# ---- Sales deterministic ----
def apply_sales_filters(filters):
    sub = df_sales.copy()

    if filters["date"] is not None:
        sub = sub[sub["DateStr"] == filters["date"]]
    if filters["region"] is not None:
        sub = sub[sub["Region"] == filters["region"]]
    if filters["employee"] is not None:
        sub = sub[sub["Employee"] == filters["employee"]]
    if filters["product"] is not None:
        sub = sub[sub["Product"] == filters["product"]]

    return sub


def answer_sales_quantity(query: str) -> str:
    filters = extract_sales_filters_from_question(query)
    sub = apply_sales_filters(filters)
    total_qty = int(sub["Quantity"].sum())
    return str(total_qty)


def answer_sales_amount(query: str) -> str:
    filters = extract_sales_filters_from_question(query)
    sub = apply_sales_filters(filters)
    total_sale = float(sub["Total Sale"].sum())
    return f"{total_sale:.2f}"


# ---- HR deterministic ----
def answer_hr_department_count(query: str) -> str:
    """
    Count employees in a specific department.
    Returns just the number as a string, e.g. "57".
    """
    q_lower = query.lower()
    department = None
    for dept in HR_DEPARTMENTS:
        if dept.lower() in q_lower:
            department = dept
            break

    # If no specific department detected, return total employees
    if department is None:
        count = int(df_hr.shape[0])
        return str(count)

    sub = df_hr[df_hr["Department"] == department]
    count = int(sub.shape[0])
    return str(count)


def answer_hr_attrition_by_agegroup(query: str) -> str:
    """
    Finds the age group with the highest attrition (Attrition == 'Yes').
    Returns short text, but built from exact pandas calculation.
    """
    left = df_hr[df_hr["Attrition"] == "Yes"].copy()
    if left.empty:
        return "No attrition records found."

    counts = left.groupby("AgeGroup")["EmpID"].count()
    top_group = counts.idxmax()
    top_value = int(counts.max())

    return f"{top_group} ({top_value})"

# =========================
# 8. BLIP-2 Vision-Language (image captioning)
# =========================
if BLIP2_AVAILABLE:
    try:
        blip2_device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🔍 Loading BLIP-2 model on {blip2_device} ...")
        blip2_processor = Blip2Processor.from_pretrained("Salesforce/blip2-flan-t5-small")
        blip2_model = Blip2ForConditionalGeneration.from_pretrained(
            "Salesforce/blip2-flan-t5-small",
            torch_dtype=torch.float16 if blip2_device == "cuda" else torch.float32,
        ).to(blip2_device)
        print("✅ BLIP-2 loaded successfully.")
    except Exception as e:
        print(f"⚠️ Failed to load BLIP-2: {e}")
        BLIP2_AVAILABLE = False


def caption_image(image_path: str) -> str:
    """
    Use BLIP-2 to generate a caption for the given image file path.
    """
    if not BLIP2_AVAILABLE:
        return "Image provided, but BLIP-2 is not available."

    try:
        img = Image.open(image_path).convert("RGB")
    except Exception as e:
        return f"Error opening image: {e}"

    inputs = blip2_processor(images=img, return_tensors="pt").to(blip2_device)
    with torch.no_grad():
        out = blip2_model.generate(**inputs, max_new_tokens=50)
    caption = blip2_processor.tokenizer.decode(out[0], skip_special_tokens=True)
    return caption

# =========================
# 9. RAG-style answer with Llama 3 (Sales + HR)
# =========================
def generate_answer_with_llama3(query: str) -> str:
    query_embedding = embedder.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(query_embedding)

    k = min(80, index.ntotal)
    scores, indices = index.search(query_embedding, k=k)

    context_rows = [summaries[i] for i in indices[0]]
    context = "\n".join(context_rows)

    print("\n--- DEBUG: CONTEXT SENT TO LLAMA 3 (first 500 chars) ---")
    print(context[:500] + "...")
    print("--------------------------------------------------------\n")

    prompt = f"""
You are a helpful data analyst for a company.

You are given several data rows in this format:

[SALES] Date=YYYY-MM-DD; Region=...; Product=...; Employee=...; Qty=...; UnitPrice=...; TotalSale=...
[HR]    EmpID=...; Age=...; AgeGroup=...; Attrition=...; BusinessTravel=...; DailyRate=...; Department=...; etc.

DATA:
{context}

QUESTION:
{query}

INSTRUCTIONS:
- Use SALES rows when the question is about sales, revenue, products, employees selling burgers, dates, or regions.
- Use HR rows when the question is about employees as people, departments, attrition, age, salary, HR metrics.
- Use only the information from DATA to answer the question.
- If you need to count or sum, do the math step by step.
- If the answer cannot be found from DATA, say that it is not available.
- Keep your answer concise (max 4 sentences or bullet points).

Now answer the QUESTION.
"""

    response = ollama.chat(
        model="llama3",
        messages=[{"role": "user", "content": prompt}],
        options={"num_ctx": 4096},
    )

    return response["message"]["content"].strip()

# =========================
# 9.5 Sales CEO KPI engine (structured answers, no hallucination)
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


def looks_like_sales_query(query: str) -> bool:
    q = query.lower()
    # Strong signals
    if "department" in q or "jabatan" in q:
        return False

    if any(prod.lower() in q for prod in PRODUCTS):
        return True
    if any(r.lower() in q for r in REGIONS):
        return True

    if any(k in q for k in ["sales", "sale", "revenue", "jualan", "jual", "pendapatan", "total sale"]):
        return True
    if any(k in q for k in ["burger", "product", "produk", "unit price", "harga"]):
        return True
    if any(k in q for k in ["quantity", "qty", "jumlah", "terjual", "units"]):
        return True

    return False


def extract_month_from_query(query: str):
    """Return pd.Period('YYYY-MM') for the month requested.
    If not specified, returns the latest month available in the sales dataset.
    Supports: 'bulan ni', 'bulan lepas', '2024-06', 'June 2024', 'Jun', 'Mei 2024', etc.
    """
    if LATEST_SALES_MONTH is None:
        return None

    q = query.lower()

    # relative
    if any(k in q for k in ["bulan ni", "bulan ini", "this month", "current month", "mtd"]):
        return LATEST_SALES_MONTH
    if any(k in q for k in ["bulan lepas", "last month", "previous month"]):
        return LATEST_SALES_MONTH - 1

    # YYYY-MM
    m = re.search(r"\b(20\d{2})[-/](0?[1-9]|1[0-2])\b", q)
    if m:
        y = int(m.group(1))
        mo = int(m.group(2))
        return pd.Period(f"{y:04d}-{mo:02d}", freq="M")

    # Month name + optional year
    tokens = re.findall(r"[a-zA-Z]+|\d{4}", q)
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

    # fallback
    return LATEST_SALES_MONTH


def detect_sales_metric(query: str) -> str:
    q = query.lower()
    if any(k in q for k in ["quantity", "qty", "jumlah", "terjual", "units", "berapa burger"]):
        # If explicit revenue also mentioned, prefer revenue
        if any(k in q for k in ["sale", "sales", "revenue", "jualan", "pendapatan", "total sale"]):
            return "revenue"
        return "quantity"
    return "revenue"


def detect_sales_dimension(query: str) -> str:
    q = query.lower()
    if any(k in q for k in ["region", "kawasan", "cawangan", "branch"]):
        return "Region"
    if any(k in q for k in ["employee", "salesperson", "staff", "pekerja", "agent"]):
        return "Employee"
    # default product
    return "Product"


def format_num(x: float, decimals: int = 2) -> str:
    try:
        return f"{x:,.{decimals}f}"
    except Exception:
        return str(x)


def extract_sales_dims(query: str):
    q = query.lower()

    region = None
    for r in REGIONS:
        if r.lower() in q:
            region = r
            break

    product = None
    for prod in sorted(PRODUCTS, key=len, reverse=True):
        if prod.lower() in q:
            product = prod
            break

    employee = None
    for emp in EMPLOYEES:
        if emp.lower() in q:
            employee = emp
            break

    return region, product, employee


def answer_sales_ceo_kpi(query: str):
    """Return a markdown answer if handled, else None."""
    if not looks_like_sales_query(query):
        return None

    q = query.lower()

    # 1) time scope (date has higher priority if explicitly provided)
    date_str = extract_date_from_query(query)  # existing function returns 'YYYY-MM-DD' or None
    if date_str:
        time_mode = "date"
        time_value = pd.to_datetime(date_str)
    else:
        time_mode = "month"
        time_value = extract_month_from_query(query)

    # 2) dimension filters
    region, product, employee = extract_sales_dims(query)

    sub = df_sales.copy()

    if time_mode == "date":
        sub = sub[sub["Date"].dt.normalize() == time_value.normalize()]
        time_label = time_value.strftime("%Y-%m-%d")
    else:
        if time_value is None:
            return "❗ Tiada data sales untuk dijawab."
        sub = sub[sub["YearMonth"] == time_value]
        time_label = str(time_value)

    if region:
        sub = sub[sub["Region"] == region]
    if product:
        sub = sub[sub["Product"] == product]
    if employee:
        sub = sub[sub["Employee"] == employee]

    if sub.empty:
        parts = [f"time={time_label}"]
        if region:
            parts.append(f"region={region}")
        if product:
            parts.append(f"product={product}")
        if employee:
            parts.append(f"employee={employee}")
        return f"❗ Tiada rekod sales untuk {', '.join(parts)} dalam dataset."

    metric = detect_sales_metric(query)
    value_col = "Total Sale" if metric == "revenue" else "Quantity"
    metric_label = "Total Sales" if metric == "revenue" else "Total Quantity"
    decimals = 2 if metric == "revenue" else 0

    # intent flags
    is_compare = any(k in q for k in ["banding", "compare", "vs", "versus", "mom", "month over month", "bulan lepas", "last month"])
    is_top = any(k in q for k in ["top", "paling", "tertinggi", "highest", "best", "paling laris", "most"])
    is_breakdown = any(k in q for k in ["ikut", "by ", "per ", "breakdown", "mengikut"])

    # 3) compare MoM (month only)
    if is_compare and time_mode == "month":
        cur_month = time_value
        prev_month = cur_month - 1

        cur_df = df_sales[df_sales["YearMonth"] == cur_month]
        prev_df = df_sales[df_sales["YearMonth"] == prev_month]

        if region:
            cur_df = cur_df[cur_df["Region"] == region]
            prev_df = prev_df[prev_df["Region"] == region]
        if product:
            cur_df = cur_df[cur_df["Product"] == product]
            prev_df = prev_df[prev_df["Product"] == product]
        if employee:
            cur_df = cur_df[cur_df["Employee"] == employee]
            prev_df = prev_df[prev_df["Employee"] == employee]

        cur_val = cur_df[value_col].sum()
        prev_val = prev_df[value_col].sum()
        diff = cur_val - prev_val
        pct = (diff / prev_val * 100) if prev_val != 0 else None

        lines = []
        lines.append(f"📊 **{metric_label} (MoM)**")
        lines.append(f"- {cur_month}: **{format_num(cur_val, decimals)}**")
        lines.append(f"- {prev_month}: **{format_num(prev_val, decimals)}**")
        if pct is None:
            lines.append(f"- Change: **{format_num(diff, decimals)}** (previous month = 0)")
        else:
            lines.append(f"- Change: **{format_num(diff, decimals)}** ({pct:+.2f}%)")
        lines.append(f"- Rows used (current month): {len(cur_df):,}")
        lines.append(f"- Dataset months available: {AVAILABLE_SALES_MONTHS[0]} → {AVAILABLE_SALES_MONTHS[-1]}")
        return "\n".join(lines)

    # 4) top-N
    if is_top:
        dim = detect_sales_dimension(query)
        grp = sub.groupby(dim)[value_col].sum().sort_values(ascending=False)

        top_n = 3
        if "top 5" in q or "top5" in q:
            top_n = 5

        top_df = grp.head(top_n).reset_index().rename(columns={value_col: metric_label})

        if metric == "revenue":
            top_df[metric_label] = top_df[metric_label].map(lambda x: format_num(x, 2))
        else:
            top_df[metric_label] = top_df[metric_label].astype(int)

        md_table = top_df.to_markdown(index=False)

        lines = []
        lines.append(f"🏆 **Top {top_n} {dim} by {metric_label}**")
        lines.append(f"- Time: **{time_label}**")
        if region and dim != "Region":
            lines.append(f"- Region filter: {region}")
        if product and dim != "Product":
            lines.append(f"- Product filter: {product}")
        if employee and dim != "Employee":
            lines.append(f"- Employee filter: {employee}")
        lines.append("")
        lines.append(md_table)
        lines.append("")
        lines.append(f"Rows used: {len(sub):,}")
        return "\n".join(lines)

    # 5) breakdown
    if is_breakdown:
        dim = detect_sales_dimension(query)
        grp = sub.groupby(dim)[value_col].sum().sort_values(ascending=False)

        out = grp.reset_index().rename(columns={value_col: metric_label})
        total = float(grp.sum())
        out["Share"] = (grp.values / total * 100) if total else 0.0

        if metric == "revenue":
            out[metric_label] = out[metric_label].map(lambda x: format_num(x, 2))
        else:
            out[metric_label] = out[metric_label].astype(int)
        out["Share"] = out["Share"].map(lambda x: f"{x:.1f}%")

        md_table = out.to_markdown(index=False)

        lines = []
        lines.append(f"📌 **{metric_label} breakdown by {dim}**")
        lines.append(f"- Time: **{time_label}**")
        if region and dim != "Region":
            lines.append(f"- Region filter: {region}")
        if product and dim != "Product":
            lines.append(f"- Product filter: {product}")
        if employee and dim != "Employee":
            lines.append(f"- Employee filter: {employee}")
        lines.append("")
        lines.append(md_table)
        lines.append("")
        lines.append(f"Rows used: {len(sub):,}")
        return "\n".join(lines)

    # 6) default: total
    total_val = float(sub[value_col].sum())
    lines = []
    lines.append(f"✅ **{metric_label}**")
    lines.append(f"- Time: **{time_label}**")
    if region:
        lines.append(f"- Region: {region}")
    if product:
        lines.append(f"- Product: {product}")
    if employee:
        lines.append(f"- Employee: {employee}")
    if metric == "revenue":
        lines.append(f"- Value: **{format_num(total_val, 2)}**")
    else:
        lines.append(f"- Value: **{int(total_val)}**")
    lines.append(f"- Rows used: {len(sub):,}")
    if time_mode == "month" and not any(k in q for k in ["bulan", "month", "2024", "2025"]):
        lines.append(f"- Note: bulan tidak dinyatakan, guna bulan terbaru dataset (**{LATEST_SALES_MONTH}**).")

    return "\n".join(lines)



# =========================
# 10. Core text-only entry (used by multimodal wrapper)
# =========================
def rag_query_ui(user_input: str) -> str:
    try:
        user_input = (user_input or "").strip()
        if len(user_input) < 4:
            return "Sila tanya soalan yang lebih jelas (contoh: 'sales bulan ni berapa?')."

        # ✅ Sales KPI (structured) first — accurate & auditable
        kpi = answer_sales_ceo_kpi(user_input)
        if kpi is not None:
            return kpi

        # Sales numeric helpers (exact)
        if is_sales_quantity_question(user_input):
            return answer_sales_quantity(user_input)

        if is_sales_amount_question(user_input):
            return answer_sales_amount(user_input)

        # HR deterministic helpers
        if is_hr_department_count_question(user_input):
            return answer_hr_department_count(user_input)

        if is_hr_attrition_by_agegroup_question(user_input):
            return answer_hr_attrition_by_agegroup(user_input)

        # Everything else (Sales + HR) → RAG + LLaMA 3
        return generate_answer_with_llama3(user_input)

    except Exception as e:
        return f"Error: {e}"


# =========================
# 11. Multimodal wrapper: text + optional image
# =========================
def multimodal_query(text_input, image_input):
    """
    - If only text: behave like before.
    - If image: caption with BLIP-2 and append to the text query.
    """
    query = (text_input or "").strip()

    if image_input is not None:
        caption = caption_image(image_input)
        print(f"🖼️ Image caption: {caption}")
        if query:
            query = query + f" Image description: {caption}"
        else:
            query = f"Based on this image: {caption}"

    if not query:
        return "Please provide a question, an image, or both."

    return rag_query_ui(query)

# =========================
# 12. Launch Gradio app (text + image)
# =========================
if __name__ == "__main__":
    print("🚀 Launching Vision-Language RAG Assistant (Sales + HR + BLIP-2)...")
    gr.Interface(
        fn=multimodal_query,
        inputs=[
            gr.Textbox(lines=2, label="Text question (optional)"),
            gr.Image(type="filepath", label="Upload image (optional)"),
        ],
        outputs=gr.Markdown(),
        title="Company VL-RAG Assistant (Sales + HR + BLIP-2)",
        description=(
            "Ask questions like:\n"
            "- 'How many Cheese Burgers did Diana sell on 2024-01-01?'\n"
            "- 'What was the total sale amount for Charlie's Double Patty Burger transaction on Jan 1, 2024?'\n"
            "- 'How many employees work in the Sales department?'\n"
            "- 'Which age group has the highest attrition?'\n"
            "- Upload a dashboard/chart image and ask: 'Summarise this for me.'"
        ),
    ).launch(inbrowser=True, debug=True, show_error=True)
