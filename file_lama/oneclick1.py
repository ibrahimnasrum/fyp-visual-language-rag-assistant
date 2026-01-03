import os
import re

import faiss
import gradio as gr
import ollama
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer

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
CSV_PATH = "retail_burger_sales.csv"  # adjust if needed

if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(f"CSV file not found at: {CSV_PATH}")

df = pd.read_csv(CSV_PATH)

print("📄 Loaded CSV with shape:", df.shape)
print("Columns:", list(df.columns))

# =========================
# 3. Precompute metadata
# =========================
EMPLOYEES = sorted(df["Employee"].dropna().unique().tolist())
PRODUCTS = sorted(df["Product"].dropna().unique().tolist())
REGIONS = sorted(df["Region"].dropna().unique().tolist())

print("Employees:", EMPLOYEES)
print("Products:", PRODUCTS)
print("Regions:", REGIONS)

# =========================
# 4. Build summaries + embeddings for RAG (fallback)
# =========================
summaries = []
for _, row in df.iterrows():
    summary = (
        f"Date={row['Date']}; "
        f"Region={row['Region']}; "
        f"Product={row['Product']}; "
        f"Employee={row['Employee']}; "
        f"Qty={row['Quantity']}; "
        f"UnitPrice={row['Unit Price']}; "
        f"TotalSale={row['Total Sale']}"
    )
    summaries.append(summary)

print(f"🔢 Built {len(summaries)} row summaries.")

embedder = SentenceTransformer("all-MiniLM-L6-v2", device=device)

print("📦 Encoding all rows into embeddings...")
emb_matrix = embedder.encode(
    summaries,
    convert_to_numpy=True,
    show_progress_bar=True,
)

faiss.normalize_L2(emb_matrix)

d = emb_matrix.shape[1]
index = faiss.IndexFlatIP(d)
index.add(emb_matrix)
print("✅ FAISS index built with", index.ntotal, "vectors.")

# =========================
# 5. Question type detectors
# =========================
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

# =========================
# 6. Date + filter extraction
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


def extract_filters_from_question(query: str):
    """
    Simple rule-based parser:
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
def apply_filters(filters):
    sub = df.copy()

    if filters["date"] is not None:
        sub = sub[sub["Date"] == filters["date"]]
    if filters["region"] is not None:
        sub = sub[sub["Region"] == filters["region"]]
    if filters["employee"] is not None:
        sub = sub[sub["Employee"] == filters["employee"]]
    if filters["product"] is not None:
        sub = sub[sub["Product"] == filters["product"]]

    return sub


def answer_sales_quantity(query: str) -> str:
    filters = extract_filters_from_question(query)
    sub = apply_filters(filters)
    total_qty = int(sub["Quantity"].sum())
    return str(total_qty)


def answer_sales_amount(query: str) -> str:
    filters = extract_filters_from_question(query)
    sub = apply_filters(filters)
    total_sale = float(sub["Total Sale"].sum())
    # just number (good for evaluation)
    return f"{total_sale:.2f}"

# =========================
# 8. RAG-style answer with Llama 3 (fallback)
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
You are a helpful data analyst for a burger restaurant.

You are given several data rows in this format:
Date=YYYY-MM-DD; Region=...; Product=...; Employee=...; Qty=...; UnitPrice=...; TotalSale=...

DATA:
{context}

QUESTION:
{query}

INSTRUCTIONS:
- Carefully read ALL the rows in DATA.
- Use only the information from DATA to answer the question.
- If you need to count or sum, do the math step by step.
- If the answer cannot be found from DATA, say that it is not available.

Now answer in a concise way.
"""

    response = ollama.chat(
        model="llama3",
        messages=[{"role": "user", "content": prompt}],
        options={"num_ctx": 4096},
    )

    return response["message"]["content"].strip()

# =========================
# 9. Main UI function
# =========================
def rag_query_ui(user_input: str) -> str:
    try:
        if is_sales_quantity_question(user_input):
            return answer_sales_quantity(user_input)

        if is_sales_amount_question(user_input):
            return answer_sales_amount(user_input)

        # fallback for general analysis/explanation questions
        return generate_answer_with_llama3(user_input)
    except Exception as e:
        return f"Error: {e}"

# =========================
# 10. Launch Gradio app
# =========================
if __name__ == "__main__":
    print("🚀 Launching Assistant...")
    gr.Interface(
        fn=rag_query_ui,
        inputs="text",
        outputs="text",
        title="Burger Sales Q&A Assistant (GPU/CPU)",
        description=(
            "Examples:\n"
            "- 'How many Cheese Burgers did Diana sell on 2024-01-01?'\n"
            "- 'What was the total sale amount for Charlie's Double Patty Burger transaction on Jan 1, 2024?'\n"
            "- 'Who sold the most burgers in Uptown in January?' (RAG + Llama 3)"
        ),
    ).launch(inbrowser=True)
