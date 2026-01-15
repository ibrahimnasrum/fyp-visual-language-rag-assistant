import os
import re
import glob
import time
import csv
import subprocess
import cv2
import pytesseract
import json
import uuid
from datetime import datetime, timedelta
from collections import defaultdict

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

import faiss
import gradio as gr
import ollama
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer

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
    try:
        out = subprocess.check_output(["ollama", "list"], text=True, encoding="utf-8", errors="ignore")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
        models = []
        for ln in lines[1:]:
            name = ln.split()[0]
            models.append(name)
        return models if models else list(default)
    except Exception:
        return list(default)

# =========================
# Directory setup
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
ensure_dir(LOG_DIR)
LOG_FILE = os.path.join(LOG_DIR, "chat_logs.csv")

STORAGE_DIR = os.path.join(BASE_DIR, "storage")
CHATS_DIR = os.path.join(STORAGE_DIR, "chats")
MEMORY_DIR = os.path.join(STORAGE_DIR, "memory")
STATS_FILE = os.path.join(STORAGE_DIR, "usage_stats.json")
ensure_dir(STORAGE_DIR)
ensure_dir(CHATS_DIR)
ensure_dir(MEMORY_DIR)

def log_interaction(model: str, route: str, question: str, answer: str, latency_ms: int, chat_id: str = "", message_id: str = "", tool_trace_summary: str = ""):
    new_file = not os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["timestamp", "model", "route", "latency_ms", "question", "answer", "chat_id", "message_id", "tool_trace_summary"])
        w.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), model, route, latency_ms, question, answer, chat_id, message_id, tool_trace_summary])

# =========================
# Chat Persistence (Enhanced)
# =========================
def generate_chat_id() -> str:
    return str(uuid.uuid4())[:8]

def title_from_first_message(msg: str, max_len: int = 50) -> str:
    msg = (msg or "").strip()
    if len(msg) <= max_len:
        return msg or "New Chat"
    return msg[:max_len] + "..."

def load_chat_list():
    """Load all chats sorted by update time"""
    chats = []
    for fname in os.listdir(CHATS_DIR):
        if fname.endswith(".json"):
            try:
                with open(os.path.join(CHATS_DIR, fname), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    chats.append(data)
            except:
                pass
    chats.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return chats

def load_chat(chat_id: str):
    path = os.path.join(CHATS_DIR, f"{chat_id}.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return None
    return None

def save_chat(chat_id: str, title: str, messages: list, tool_traces: list, starred: bool = False):
    """Save chat with metadata"""
    path = os.path.join(CHATS_DIR, f"{chat_id}.json")
    existing = load_chat(chat_id) if os.path.exists(path) else None
    
    data = {
        "chat_id": chat_id,
        "title": title,
        "starred": starred if starred else (existing.get("starred", False) if existing else False),
        "created_at": existing.get("created_at") if existing else datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "messages": messages,
        "tool_traces": tool_traces
    }
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def delete_chat(chat_id: str):
    """Delete a chat permanently"""
    path = os.path.join(CHATS_DIR, f"{chat_id}.json")
    if os.path.exists(path):
        os.remove(path)

def rename_chat(chat_id: str, new_title: str):
    """Rename a chat"""
    chat = load_chat(chat_id)
    if chat:
        save_chat(chat_id, new_title, chat["messages"], chat["tool_traces"], chat.get("starred", False))

def toggle_star(chat_id: str):
    """Toggle starred status"""
    chat = load_chat(chat_id)
    if chat:
        save_chat(chat_id, chat["title"], chat["messages"], chat["tool_traces"], not chat.get("starred", False))

def export_chat_markdown(chat_id: str) -> str:
    """Export chat to markdown format"""
    chat = load_chat(chat_id)
    if not chat:
        return ""
    
    lines = [
        f"# {chat['title']}",
        f"",
        f"**Created:** {chat.get('created_at', 'N/A')}",
        f"**Updated:** {chat.get('updated_at', 'N/A')}",
        f"",
        "---",
        ""
    ]
    
    for msg in chat.get("messages", []):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        timestamp = msg.get("timestamp", "")
        
        lines.append(f"## {role.upper()} ({timestamp})")
        lines.append("")
        lines.append(content)
        lines.append("")
    
    return "\n".join(lines)

def search_chats(query: str):
    """Search chats by title or content"""
    query_lower = query.lower()
    results = []
    
    for chat in load_chat_list():
        # Search in title
        if query_lower in chat.get("title", "").lower():
            results.append(chat)
            continue
        
        # Search in messages
        for msg in chat.get("messages", []):
            if query_lower in msg.get("content", "").lower():
                results.append(chat)
                break
    
    return results

# =========================
# Memory System (Enhanced)
# =========================
def load_memory():
    path = os.path.join(MEMORY_DIR, "user_profile.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    
    return {
        "preferred_language": "english",
        "answer_style": "executive_summary_first",
        "default_month_rule": "latest_month_in_dataset",
        "custom_notes": []
    }

def save_memory(memory: dict):
    path = os.path.join(MEMORY_DIR, "user_profile.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)

def add_memory_note(note: str):
    """Add a custom note to memory"""
    memory = load_memory()
    if note and note not in memory["custom_notes"]:
        memory["custom_notes"].append(note)
        save_memory(memory)

def clear_memory():
    """Reset memory to defaults"""
    default_memory = {
        "preferred_language": "english",
        "answer_style": "executive_summary_first",
        "default_month_rule": "latest_month_in_dataset",
        "custom_notes": []
    }
    save_memory(default_memory)

def detect_memory_update(user_input: str, memory: dict) -> dict:
    """Detect and update memory from user input"""
    s = user_input.lower()
    updated = False
    
    if "reply in malay" in s or "jawab dalam bahasa melayu" in s:
        memory["preferred_language"] = "malay"
        updated = True
    elif "reply in english" in s or "jawab dalam bahasa inggeris" in s:
        memory["preferred_language"] = "english"
        updated = True
    
    if "always show summary first" in s or "executive summary first" in s:
        memory["answer_style"] = "executive_summary_first"
        updated = True
    
    if updated:
        save_memory(memory)
    
    return memory

def inject_memory_into_prompt(memory: dict) -> str:
    """Create memory context for LLM"""
    parts = ["User Preferences:"]
    parts.append(f"- Language: {memory['preferred_language']}")
    parts.append(f"- Answer Style: {memory['answer_style']}")
    
    if memory.get("custom_notes"):
        parts.append("- Custom Notes:")
        for note in memory["custom_notes"][:5]:
            parts.append(f"  * {note}")
    
    return "\n".join(parts)

USER_MEMORY = load_memory()

# =========================
# Usage Statistics
# =========================
def load_stats():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    
    return {
        "total_queries": 0,
        "total_chats": 0,
        "route_counts": defaultdict(int),
        "model_counts": defaultdict(int),
        "avg_latency_ms": 0,
        "total_latency_ms": 0
    }

def save_stats(stats: dict):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

def update_stats(route: str, model: str, latency_ms: int):
    stats = load_stats()
    stats["total_queries"] += 1
    stats["route_counts"][route] = stats["route_counts"].get(route, 0) + 1
    stats["model_counts"][model] = stats["model_counts"].get(model, 0) + 1
    stats["total_latency_ms"] += latency_ms
    stats["avg_latency_ms"] = stats["total_latency_ms"] / stats["total_queries"]
    save_stats(stats)

def get_stats_summary() -> str:
    stats = load_stats()
    
    lines = [
        "## 📊 Usage Statistics",
        "",
        f"**Total Queries:** {stats['total_queries']:,}",
        f"**Total Chats:** {len(load_chat_list()):,}",
        f"**Avg Response Time:** {stats.get('avg_latency_ms', 0):.0f}ms",
        "",
        "### Route Distribution",
    ]
    
    for route, count in sorted(stats.get("route_counts", {}).items(), key=lambda x: x[1], reverse=True):
        lines.append(f"- **{route}**: {count:,}")
    
    lines.append("")
    lines.append("### Model Usage")
    
    for model, count in sorted(stats.get("model_counts", {}).items(), key=lambda x: x[1], reverse=True):
        lines.append(f"- **{model}**: {count:,}")
    
    return "\n".join(lines)

# =========================
# Tool Transparency
# =========================
class ToolTrace:
    def __init__(self, route: str, model: str):
        self.route = route
        self.model = model
        self.filters = {}
        self.rows_used = 0
        self.sources = []
        self.ocr_text = ""
        self.ocr_char_count = 0
        self.latency_ms = 0
    
    def to_dict(self):
        return {
            "route": self.route,
            "model": self.model,
            "filters": self.filters,
            "rows_used": self.rows_used,
            "sources": self.sources,
            "ocr_char_count": self.ocr_char_count,
            "latency_ms": self.latency_ms
        }
    
    def to_summary_string(self):
        return f"{self.route}|{self.model}|rows={self.rows_used}|sources={len(self.sources)}|{self.latency_ms}ms"
    
    def to_display_html(self):
        lines = ['<div class="tool-trace">']
        lines.append(f'<h4>🔍 Tool Transparency</h4>')
        lines.append(f'<p><strong>Route:</strong> <code>{self.route}</code></p>')
        lines.append(f'<p><strong>Model:</strong> <code>{self.model}</code></p>')
        
        if self.filters:
            lines.append(f'<p><strong>Filters Applied:</strong></p><ul>')
            for k, v in self.filters.items():
                lines.append(f'<li><code>{k}</code> = <code>{v}</code></li>')
            lines.append('</ul>')
        
        if self.rows_used > 0:
            lines.append(f'<p><strong>Rows Analyzed:</strong> {self.rows_used:,}</p>')
        
        if self.sources:
            lines.append(f'<p><strong>Sources Retrieved:</strong> {len(self.sources)}</p><ul>')
            for src in self.sources[:3]:
                lines.append(f'<li>{src}</li>')
            if len(self.sources) > 3:
                lines.append(f'<li><em>...and {len(self.sources)-3} more</em></li>')
            lines.append('</ul>')
        
        if self.ocr_char_count > 0:
            quality = "✅ Good" if self.ocr_char_count > 100 else ("⚠️ Moderate" if self.ocr_char_count > 10 else "⚠️ Low")
            lines.append(f'<p><strong>OCR Quality:</strong> {quality} ({self.ocr_char_count} chars)</p>')
        
        lines.append(f'<p><strong>Latency:</strong> {self.latency_ms}ms</p>')
        lines.append('</div>')
        
        return "\n".join(lines)

# =========================
# Data Loading
# =========================
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"✅ Device: {device}")

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

df_sales["Date"] = pd.to_datetime(df_sales["Date"], errors="coerce")
df_sales["DateStr"] = df_sales["Date"].dt.strftime("%Y-%m-%d")
df_sales["YearMonth"] = df_sales["Date"].dt.to_period("M")

for c in ["Quantity", "Unit Price", "Total Sale"]:
    df_sales[c] = pd.to_numeric(df_sales[c], errors="coerce")

AVAILABLE_SALES_MONTHS = sorted(df_sales["YearMonth"].dropna().unique().tolist())
LATEST_SALES_MONTH = max(AVAILABLE_SALES_MONTHS) if AVAILABLE_SALES_MONTHS else None

STATES = sorted(df_sales["State"].dropna().unique().tolist()) if "State" in df_sales.columns else []
BRANCHES = sorted(df_sales["Branch"].dropna().unique().tolist()) if "Branch" in df_sales.columns else []
PRODUCTS = sorted(df_sales["Product"].dropna().unique().tolist())
SALES_REPS = sorted(df_sales["Employee"].dropna().unique().tolist())
CHANNELS = sorted(df_sales["Channel"].dropna().unique().tolist()) if "Channel" in df_sales.columns else []

HR_DEPTS = sorted(df_hr["Department"].dropna().unique().tolist()) if "Department" in df_hr.columns else []
HR_AGEGROUPS = sorted(df_hr["AgeGroup"].dropna().unique().tolist()) if "AgeGroup" in df_hr.columns else []
HR_STATES = sorted(df_hr["State"].dropna().unique().tolist()) if "State" in df_hr.columns else []

print("📄 Sales shape:", df_sales.shape, "| months:", AVAILABLE_SALES_MONTHS[0], "→", AVAILABLE_SALES_MONTHS[-1])
print("📄 HR shape:", df_hr.shape)

# =========================
# Build RAG corpus
# =========================
print("📚 Loading documents...")
doc_txts = []
for fpath in glob.glob(os.path.join(DOCS_DIR, "*.txt")):
    try:
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            txt = f.read().strip()
        if not txt:
            continue
        paras = [p.strip() for p in txt.split("\n\n") if p.strip()]
        for p in paras:
            if len(p) > 30:
                doc_txts.append(p)
    except:
        pass

print(f"✅ Loaded {len(doc_txts)} doc chunks")

embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device=device)
emb_dim = 384

print("🔄 Building FAISS index...")
doc_embs = embedder.encode(doc_txts, batch_size=32, show_progress_bar=True, convert_to_numpy=True)

index = faiss.IndexFlatL2(emb_dim)
index.add(doc_embs)

print("✅ FAISS index built with", index.ntotal, "vectors")

# =========================
# Context Preservation System
# =========================
CONVERSATION_STATE = {
    "last_filters": {},
    "last_context": {},
    "last_route": None,
    "conversation_history": []
}

def extract_context_from_answer(answer: str, query: str) -> dict:
    """Extract context (month, top performer, state, etc.) from answer text"""
    context = {}
    
    # Extract month from answer (looking for Month: 2024-01 patterns)
    month_match = re.search(r'Month:\s*(\d{4}-\d{2})', answer)
    if month_match:
        try:
            context['month'] = pd.Period(month_match.group(1), freq='M')
        except:
            pass
    
    # Extract month from Period format (2024-01)
    period_match = re.search(r'(\d{4}-\d{2})', answer)
    if period_match and 'month' not in context:
        try:
            context['month'] = pd.Period(period_match.group(1), freq='M')
        except:
            pass
    
    # Extract top performer from Rankings section
    rankings_match = re.search(r'Rankings[:\s]+([^:\n]+?):\s+RM', answer, re.IGNORECASE)
    if rankings_match:
        context['top_performer'] = rankings_match.group(1).strip()
    
    # Extract state from filters or answer
    for state in STATES:
        if state in answer or state.lower() in query.lower():
            context['state'] = state
            break
    
    # Extract product from filters or answer
    for product in PRODUCTS:
        if product in answer or product.lower() in query.lower():
            context['product'] = product
            break
    
    return context

# =========================
# KPI Functions (Complete implementation from v8.2)
# =========================

# Sales helper functions
def extract_month_from_query(q: str, previous_context: dict = None):
    s = (q or "").lower()
    
    # Check for explicit month-year patterns
    match = re.search(r"\b(20\d{2})[-/](0?[1-9]|1[0-2])\b", s)
    if match:
        year, month = int(match.group(1)), int(match.group(2))
        return pd.Period(f"{year}-{month:02d}", freq="M")
    
    # Default to latest month
    return LATEST_SALES_MONTH

def extract_two_months_from_query(q: str):
    s = (q or "").lower()
    matches = re.findall(r"\b(20\d{2})[-/](0?[1-9]|1[0-2])\b", s)
    if len(matches) >= 2:
        p1 = pd.Period(f"{int(matches[0][0])}-{int(matches[0][1]):02d}", freq="M")
        p2 = pd.Period(f"{int(matches[1][0])}-{int(matches[1][1]):02d}", freq="M")
        return [p1, p2]
    return []

def extract_named_month_range(q: str):
    """Extract month range like 'Jan until Jun 2024'"""
    s = (q or "").lower()
    months_map = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
    }
    
    found_months = []
    year = None
    
    for month_name, month_num in months_map.items():
        if month_name in s:
            found_months.append(month_num)
    
    year_match = re.search(r"\b20\d{2}\b", s)
    if year_match:
        year = int(year_match.group())
    
    if len(found_months) >= 2 and year:
        start_m = min(found_months)
        end_m = max(found_months)
        return (pd.Period(f"{year}-{start_m:02d}", freq="M"), pd.Period(f"{year}-{end_m:02d}", freq="M"))
    
    return None

def detect_sales_metric(q: str) -> str:
    s = (q or "").lower()
    if any(k in s for k in ["qty", "quantity", "unit", "item", "terjual", "kuantiti"]):
        return "quantity"
    return "revenue"

def detect_sales_dimension(q: str) -> str:
    s = (q or "").lower()
    if any(k in s for k in ["state", "negeri", "region"]):
        return "State"
    if any(k in s for k in ["branch", "cawangan", "outlet"]):
        return "Branch"
    if any(k in s for k in ["channel", "saluran", "delivery"]):
        return "Channel"
    if any(k in s for k in ["employee", "staff", "salesrep"]):
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
    s = (q or "").lower()
    matches = re.findall(r"\b(20\d{2})[-/](0?[1-9]|1[0-2])\b", s)
    if len(matches) >= 2:
        p1 = pd.Period(f"{int(matches[0][0]):04d}-{int(matches[0][1]):02d}", freq="M")
        p2 = pd.Period(f"{int(matches[1][0]):04d}-{int(matches[1][1]):02d}", freq="M")
        start_m, end_m = (p1, p2) if p1 <= p2 else (p2, p1)
        return start_m, end_m
    return None

def answer_sales_ceo_kpi(q: str, trace: ToolTrace = None):
    """Complete Sales KPI with all features"""
    if LATEST_SALES_MONTH is None:
        return "❗ No sales data available."

    s = (q or "").lower().strip()
    metric = detect_sales_metric(q)
    value_col = "Total Sale" if metric == "revenue" else "Quantity"
    metric_label = "Total Sales (RM)" if metric == "revenue" else "Total Quantity"
    decimals = 2 if metric == "revenue" else 0

    is_compare = any(k in s for k in ["banding", "compare", "vs", "versus", "mom", "bulan lepas", "last month"])
    is_top = ("top" in s) or ("paling" in s)

    state, branch, product, employee, channel = extract_sales_filters(q)
    
    if trace:
        trace.filters = {"state": state, "branch": branch, "product": product, "employee": employee, "channel": channel, "metric": metric}

    # Range queries
    rng = extract_month_range_from_query(q) or extract_named_month_range(q)
    
    if rng is not None and (is_top or "highest" in s or "most" in s):
        start_m, end_m = rng
        mask = (df_sales["YearMonth"] >= start_m) & (df_sales["YearMonth"] <= end_m)
        sub_range = df_sales[mask].copy()

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
            return f"❗ No records for {start_m} → {end_m} with given filters."

        dim = detect_sales_dimension(q)
        grp = sub_range.groupby(dim)[value_col].sum().sort_values(ascending=False)

        top_n = 5 if ("top 5" in s or "top5" in s) else 3
        top_df = grp.head(top_n).reset_index().rename(columns={value_col: metric_label})

        if metric == "revenue":
            top_df[metric_label] = top_df[metric_label].map(lambda x: f"RM {format_num(float(x), 2)}")
        else:
            top_df[metric_label] = top_df[metric_label].astype(int)
        
        if trace:
            trace.rows_used = len(sub_range)
            trace.filters["period"] = f"{start_m} to {end_m}"
            trace.filters["dimension"] = dim

        return "\n".join([
            f"## 📊 Top {top_n} {dim} by {metric_label}",
            "",
            f"**Period:** {start_m} → {end_m}",
            "",
            "### Executive Summary",
            f"Top performers identified across {dim} dimension for the specified period.",
            "",
            "### Evidence Used",
            df_to_markdown_table(top_df),
            f"- Data Source: Structured Sales KPI",
            f"- Rows Analyzed: {len(sub_range):,}",
            "",
            "### Next Actions",
            f"- Deep-dive into top-performing {dim}",
            "- Analyze contributing factors to success",
            "- Replicate strategy across other segments"
        ])

    # Single month logic
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
        return f"❗ No records for {month} with given filters."
    
    if trace:
        trace.rows_used = len(sub)
        trace.filters["month"] = str(month)

    # Compare
    if is_compare:
        two = extract_two_months_from_query(q)

        if len(two) == 2:
            prev_month, cur_month = two[0], two[1]
        else:
            cur_month = month
            prev_month = month - 1

        cur_df = df_sales[df_sales["YearMonth"] == cur_month].copy()
        prev_df = df_sales[df_sales["YearMonth"] == prev_month].copy()

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
        
        if trace:
            trace.rows_used = len(cur_df) + len(prev_df)
            trace.filters["comparison"] = f"{prev_month} vs {cur_month}"

        lines = [
            f"## 📊 {metric_label} Comparison",
            "",
            "### Executive Summary",
            f"**{cur_month}:** {format_num(cur_val, decimals)} | **{prev_month}:** {format_num(prev_val, decimals)}"
        ]
        
        if pct is None:
            lines.append(f"**Change:** {format_num(diff, decimals)} (previous period had no data)")
        else:
            trend = "📈" if diff > 0 else "📉" if diff < 0 else "➡️"
            lines.append(f"**Change:** {trend} {format_num(diff, decimals)} ({pct:+.2f}%)")
        
        lines.extend([
            "",
            "### Evidence Used",
            f"- Data Source: Structured Sales KPI",
            f"- Current Period Rows: {len(cur_df):,}",
            f"- Previous Period Rows: {len(prev_df):,}",
            "",
            "### Next Actions",
            "- Investigate drivers of change",
            "- Review period-over-period trends",
            "- Validate with operational data"
        ])
        
        return "\n".join(lines)

    # Top-N
    if is_top:
        dim = detect_sales_dimension(q)
        grp = sub.groupby(dim)[value_col].sum().sort_values(ascending=False)

        top_n = 5 if ("top 5" in s or "top5" in s) else 3
        top_df = grp.head(top_n).reset_index().rename(columns={value_col: metric_label})

        if metric == "revenue":
            top_df[metric_label] = top_df[metric_label].map(lambda x: f"RM {format_num(float(x), 2)}")
        else:
            top_df[metric_label] = top_df[metric_label].astype(int)
        
        if trace:
            trace.filters["dimension"] = dim

        return "\n".join([
            f"## 🏆 Top {top_n} {dim} by {metric_label}",
            "",
            f"**Month:** {month}",
            "",
            "### Executive Summary",
            f"Top performers identified across {dim} dimension.",
            "",
            "### Evidence Used",
            df_to_markdown_table(top_df),
            f"- Data Source: Structured Sales KPI",
            f"- Rows Analyzed: {len(sub):,}",
            "",
            "### Next Actions",
            f"- Analyze success factors of top {dim}",
            "- Benchmark against lower performers",
            "- Scale winning strategies"
        ])

    # Default total
    total_val = float(sub[value_col].sum())
    
    lines = [
        f"## ✅ {metric_label}",
        "",
        f"**Month:** {month}",
        "",
        "### Executive Summary",
        f"**Value:** RM {format_num(total_val, decimals)}" if metric == "revenue" else f"**Value:** {int(total_val):,}",
        "",
        "### Evidence Used",
        f"- Data Source: Structured Sales KPI",
        f"- Rows Analyzed: {len(sub):,}",
        "",
        "### Next Actions",
        "- Compare with previous periods",
        "- Drill down by dimension",
        "- Validate against targets"
    ]
    return "\n".join(lines)

def answer_hr(q: str, trace: ToolTrace = None) -> str:
    """Complete HR KPI with all features"""
    s = (q or "").lower().strip()

    # Policy questions go to RAG
    if any(k in s for k in ["policy", "handbook", "guideline", "procedure", "sop", "medical claim", "claim", "entitlement", "annual leave", "sick leave", "leave", "cuti", "overtime approval", "approval", "disciplinary", "probation"]):
        return None

    # Headcount
    if "headcount" in s or "berapa orang" in s or "how many" in s:
        for d in HR_DEPTS:
            if d.lower() in s:
                n = int((df_hr["Department"] == d).sum())
                if trace:
                    trace.rows_used = len(df_hr)
                    trace.filters = {"department": d}
                return f"## 👥 Headcount Analysis\n\n### Executive Summary\n**Department {d}:** {n} employees\n\n### Evidence Used\n- Data Source: Structured HR\n- Total HR Records: {len(df_hr):,}\n\n### Next Actions\n- Compare with historical headcount\n- Analyze by job role distribution\n- Review staffing adequacy"

        for st in HR_STATES:
            if st.lower() in s:
                n = int((df_hr["State"] == st).sum())
                if trace:
                    trace.rows_used = len(df_hr)
                    trace.filters = {"state": st}
                return f"## 👥 Headcount Analysis\n\n### Executive Summary\n**State {st}:** {n} employees\n\n### Evidence Used\n- Data Source: Structured HR\n- Total HR Records: {len(df_hr):,}\n\n### Next Actions\n- Compare with other states\n- Assess regional staffing needs\n- Plan recruitment strategy"

        if trace:
            trace.rows_used = len(df_hr)
        return f"## 👥 Headcount Analysis\n\n### Executive Summary\n**Total Employees:** {len(df_hr):,}\n\n### Evidence Used\n- Data Source: Structured HR\n- Complete employee database\n\n### Next Actions\n- Break down by department/state\n- Trend analysis over time\n- Workforce planning review"

    # Attrition
    if "attrition" in s:
        left = df_hr[df_hr["Attrition"].astype(str).str.lower() == "yes"].copy()
        if left.empty:
            return "## 📉 Attrition Analysis\n\n### Executive Summary\nNo attrition records found in current dataset.\n\n### Evidence Used\n- Data Source: Structured HR"

        total = len(df_hr)
        left_count = len(left)
        rate = (left_count / total * 100) if total > 0 else 0

        if trace:
            trace.rows_used = total
            trace.filters = {"attrition": "yes"}

        return f"## 📉 Attrition Analysis\n\n### Executive Summary\n**Attrition Rate:** {rate:.2f}%\n**Left:** {left_count} | **Total:** {total}\n\n### Evidence Used\n- Data Source: Structured HR\n- Records Analyzed: {total:,}\n\n### Next Actions\n- Identify attrition hotspots by department\n- Analyze exit interview data\n- Implement retention strategies"

    # Income
    if "income" in s or "salary" in s or "gaji" in s:
        if "department" in s:
            grp = df_hr.groupby("Department")["MonthlyIncome"].mean().sort_values(ascending=False)
            top_df = grp.reset_index().rename(columns={"MonthlyIncome": "Avg Monthly Income (RM)"})
            top_df["Avg Monthly Income (RM)"] = top_df["Avg Monthly Income (RM)"].map(lambda x: f"RM {format_num(float(x), 2)}")

            if trace:
                trace.rows_used = len(df_hr)

            return f"## 💰 Income by Department\n\n### Executive Summary\nAverage monthly income across departments.\n\n### Evidence Used\n{df_to_markdown_table(top_df)}\n- Data Source: Structured HR\n- Records: {len(df_hr):,}\n\n### Next Actions\n- Review compensation bands\n- Benchmark against market rates\n- Address pay equity concerns"

    # Default
    if trace:
        trace.rows_used = len(df_hr)
    
    return f"## 👥 HR Summary\n\n### Executive Summary\n**Total Employees:** {len(df_hr):,}\n\n### Evidence Used\n- Data Source: Structured HR\n\n### Next Actions\n- Specify HR dimension for detailed analysis\n- Request specific metrics (attrition, income, etc.)"

# =========================
# RAG Functions (Enhanced with conversation history)
# =========================
def retrieve_context(query: str, k: int = 5, mode: str = "docs", trace: ToolTrace = None):
    q_vec = embedder.encode([query], convert_to_numpy=True)
    D, I = index.search(q_vec, k)
    results = []
    
    for idx in I[0]:
        if 0 <= idx < len(doc_txts):
            results.append(doc_txts[idx])
            if trace:
                trace.sources.append(f"doc_{idx}")
    
    return results

def _build_prompt_with_history(context: list[str], query: str, memory: dict, conversation_history: list = None) -> str:
    """Enhanced prompt builder with conversation history"""
    parts = [inject_memory_into_prompt(memory)]
    
    if conversation_history:
        parts.append("\nRecent Conversation:")
        for msg in conversation_history[-10:]:  # Last 10 messages
            role = msg.get("role", "user")
            content = msg.get("content", "")[:200]  # Truncate long messages
            parts.append(f"{role.upper()}: {content}")
    
    parts.append("\nRelevant Documents:")
    for doc in context:
        parts.append(f"---\n{doc}\n---")
    
    parts.append(f"\nUser Question: {query}")
    parts.append("\nProvide a comprehensive answer based on the documents and conversation history.")
    
    return "\n".join(parts)

def generate_answer_with_model_stream(model: str, query: str, mode: str, trace: ToolTrace = None, conversation_history: list = None):
    context = retrieve_context(query, k=5, mode=mode, trace=trace)
    prompt = _build_prompt_with_history(context, query, USER_MEMORY, conversation_history)
    
    try:
        stream = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )
        
        for chunk in stream:
            txt = chunk.get("message", {}).get("content", "")
            if txt:
                yield txt
    except Exception as e:
        yield f"\n\n⚠️ LLM Error: {e}"

def caption_image(img_path: str, trace: ToolTrace = None) -> str:
    try:
        img = cv2.imread(img_path)
        if img is None:
            return ""
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray, config='--psm 6').strip()
        
        if trace:
            trace.ocr_text = text
            trace.ocr_char_count = len(text)
        
        return text
    except Exception as e:
        return f"OCR error: {e}"

# =========================
# Intent Detection
# =========================
HR_KEYWORDS = ["hr", "employee", "staff", "headcount", "department", "attrition", "salary", "income"]
SALES_KEYWORDS = ["sales", "revenue", "top", "compare", "vs", "mom", "bulan", "month", "state", "product", "channel"]
DOC_KEYWORDS = ["policy", "sop", "guideline", "procedure", "refund", "leave", "cuti", "claim"]

def detect_intent(text: str, has_image: bool) -> str:
    s = (text or "").lower().strip()
    
    if has_image:
        return "visual"
    
    if any(k in s for k in DOC_KEYWORDS):
        return "rag_docs"
    
    if any(k in s for k in HR_KEYWORDS):
        return "hr_kpi"
    
    if any(k in s for k in SALES_KEYWORDS):
        return "sales_kpi"
    
    return "rag_docs"

# =========================
# Follow-up Question Generator
# =========================
def generate_followup_questions(query: str, answer: str, route: str) -> list:
    """Generate 2-3 relevant follow-up questions"""
    questions = []
    
    if route == "sales_kpi":
        questions = [
            "Compare this with last month",
            "Show breakdown by state",
            "Which products contributed most?",
            "Analyze by channel"
        ]
    elif route == "hr_kpi":
        questions = [
            "Show attrition rate by department",
            "Compare salary across states",
            "Analyze by age group",
            "Show overtime patterns"
        ]
    elif route == "rag_docs":
        questions = [
            "Can you provide more details?",
            "What are the requirements?",
            "How do I apply for this?",
            "Are there any exceptions?"
        ]
    
    return questions[:3]

# =========================
# Main Query Pipeline (Enhanced)
# =========================
def rag_query_ui(user_input: str, model_name: str, has_image: bool = False, chat_id: str = "", conversation_history: list = None):
    start = time.perf_counter()
    route = detect_intent(user_input, has_image)
    trace = ToolTrace(route, model_name if route in ["rag_docs", "visual"] else "N/A")
    final_answer = ""
    
    def elapsed_ms():
        return int((time.perf_counter() - start) * 1000)
    
    # KPI routes (deterministic)
    if route == "sales_kpi":
        final_answer = answer_sales_ceo_kpi(user_input, trace)
        trace.latency_ms = elapsed_ms()
        
        # Generate follow-ups
        followups = generate_followup_questions(user_input, final_answer, route)
        
        yield (final_answer, trace.to_display_html(), followups)
        
    elif route == "hr_kpi":
        final_answer = answer_hr(user_input, trace)
        trace.latency_ms = elapsed_ms()
        
        followups = generate_followup_questions(user_input, final_answer, route)
        
        yield (final_answer, trace.to_display_html(), followups)
    
    # RAG route (streaming with history)
    elif route == "rag_docs":
        accumulated = ""
        for chunk in generate_answer_with_model_stream(model_name, user_input, "docs", trace, conversation_history):
            accumulated += chunk
            yield (accumulated, trace.to_display_html(), [])
        
        final_answer = accumulated
        trace.latency_ms = elapsed_ms()
        
        followups = generate_followup_questions(user_input, final_answer, route)
        
        yield (final_answer, trace.to_display_html(), followups)
    
    # Update stats
    update_stats(route, trace.model, trace.latency_ms)

def multimodal_query(text: str, image, model: str, chat_id: str, conversation_history: list = None):
    """Handle text + optional image with conversation history"""
    has_image = image is not None
    
    if has_image:
        trace = ToolTrace("visual", model)
        start = time.perf_counter()
        
        # OCR
        ocr_text = caption_image(image, trace)
        combined_query = f"{text}\n\nExtracted from image:\n{ocr_text}" if ocr_text else text
        
        # Stream answer with history
        accumulated = ""
        for chunk in generate_answer_with_model_stream(model, combined_query, "visual", trace, conversation_history):
            accumulated += chunk
            yield (accumulated, trace.to_display_html(), [])
        
        trace.latency_ms = int((time.perf_counter() - start) * 1000)
        
        followups = []
        yield (accumulated, trace.to_display_html(), followups)
        
        update_stats("visual", model, trace.latency_ms)
    else:
        # Text only - use rag_query_ui
        for result in rag_query_ui(text, model, False, chat_id, conversation_history):
            yield result

# =========================
# Gradio UI (Full ChatGPT Experience)
# =========================
print("🎨 Building UI...")

custom_css = """
<style>
.badges {display: flex; gap: 8px; flex-wrap: wrap; margin: 10px 0;}
.badge {padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;}
.badge.kpi {background: #10b981; color: white;}
.badge.rag {background: #3b82f6; color: white;}
.badge.ocr {background: #f59e0b; color: white;}
.badge.model {background: #6b7280; color: white;}
.badge.time {background: #8b5cf6; color: white;}
.tool-trace {background: #f3f4f6; padding: 16px; border-radius: 8px; margin: 10px 0;}
.chat-item {padding: 8px; margin: 4px 0; border-radius: 6px; cursor: pointer; transition: background 0.2s;}
.chat-item:hover {background: #e5e7eb;}
.chat-item.starred {border-left: 3px solid #f59e0b;}
.followup-btn {margin: 4px; padding: 8px 16px; background: #eff6ff; border: 1px solid #3b82f6; border-radius: 6px; cursor: pointer;}
.followup-btn:hover {background: #dbeafe;}
</style>
"""

with gr.Blocks(css=custom_css, title="🧠 CEO Bot - ChatGPT Style") as demo:
    gr.HTML(custom_css)
    gr.Markdown("# 🧠 FYP CEO Bot - Full ChatGPT Experience")
    
    # State variables
    current_chat_id = gr.State(value=generate_chat_id())
    chat_messages = gr.State(value=[])
    chat_traces = gr.State(value=[])
    
    with gr.Row():
        # LEFT SIDEBAR (30%)
        with gr.Column(scale=3):
            gr.Markdown("### 💬 Chats")
            
            with gr.Row():
                new_chat_btn = gr.Button("✨ New Chat", variant="primary", size="sm")
                refresh_btn = gr.Button("🔄", size="sm")
            
            search_box = gr.Textbox(placeholder="🔍 Search chats...", show_label=False, scale=1)
            search_btn = gr.Button("Search", size="sm")
            
            chat_list_md = gr.Markdown("")
            
            gr.Markdown("---")
            gr.Markdown("### 🧠 Memory")
            memory_display = gr.Markdown(inject_memory_into_prompt(USER_MEMORY))
            clear_memory_btn = gr.Button("Clear Memory", size="sm")
            
            gr.Markdown("---")
            gr.Markdown("### 📊 Stats")
            stats_btn = gr.Button("Show Statistics", size="sm")
            stats_display = gr.Markdown("")
        
        # CENTER (40%)
        with gr.Column(scale=4):
            gr.Markdown("### 💭 Ask anything")
            
            user_input = gr.Textbox(
                placeholder="Ask about sales, HR, policies... (Press Enter to send, Shift+Enter for new line)",
                show_label=False,
                lines=3
            )
            
            image_input = gr.Image(type="filepath", label="📷 Upload Image (optional)")
            
            with gr.Row():
                model_dropdown = gr.Dropdown(
                    choices=get_installed_ollama_models(),
                    value=get_installed_ollama_models()[0],
                    label="🤖 Model",
                    scale=2
                )
                submit_btn = gr.Button("Send 📤", variant="primary", scale=1)
                regen_btn = gr.Button("🔄 Regenerate", scale=1)
            
            # Chat actions
            with gr.Row():
                export_btn = gr.Button("📥 Export", size="sm")
                delete_chat_btn = gr.Button("🗑️ Delete Chat", size="sm")
                rename_btn = gr.Button("✏️ Rename", size="sm")
                star_btn = gr.Button("⭐ Star", size="sm")
        
        # RIGHT (30%)
        with gr.Column(scale=3):
            gr.Markdown("### 💬 Answer")
            answer_output = gr.Markdown("")
            
            gr.Markdown("---")
            gr.Markdown("### 🔍 Tool Trace")
            trace_output = gr.HTML("")
            
            gr.Markdown("---")
            gr.Markdown("### 💡 Follow-up Questions")
            followup_output = gr.HTML("")
    
    # Event handlers
    def on_submit(text, image, model_name, chat_id, messages, traces):
        """Submit with fast streaming"""
        if not text.strip():
            return ("", "", "", chat_id, messages, traces)
        
        # Convert messages to conversation history format for LLM
        conversation_history = messages.copy()
        
        # Stream answer
        final_answer = ""
        final_trace = ""
        final_followups = []
        
        for answer, trace, followups in multimodal_query(text, image, model_name, chat_id, conversation_history):
            final_answer = answer
            final_trace = trace
            final_followups = followups
            yield (answer, trace, "", chat_id, messages, traces)
        
        # Save after streaming completes
        user_msg = {
            "role": "user",
            "content": text if not image else f"{text} [image uploaded]",
            "timestamp": datetime.now().isoformat()
        }
        messages.append(user_msg)
        
        assistant_msg = {
            "role": "assistant",
            "content": final_answer,
            "timestamp": datetime.now().isoformat()
        }
        messages.append(assistant_msg)
        
        if final_trace:
            traces.append({"timestamp": datetime.now().isoformat(), "trace_html": final_trace})
        
        # Generate title
        if len(messages) == 2:
            chat_title = title_from_first_message(text)
        else:
            existing = load_chat(chat_id)
            chat_title = existing.get("title", "Chat") if existing else "Chat"
        
        # Save
        try:
            save_chat(chat_id, chat_title, messages, traces)
        except Exception as e:
            print(f"⚠️ Save failed: {e}")
        
        # Format follow-ups
        followup_html = ""
        if final_followups:
            followup_html = "<div class='followups'>"
            for fq in final_followups:
                followup_html += f"<div class='followup-btn'>{fq}</div>"
            followup_html += "</div>"
        
        yield (final_answer, final_trace, followup_html, chat_id, messages, traces)
    
    def on_new_chat(messages, traces, chat_id):
        """Save current and start new"""
        if messages:
            existing = load_chat(chat_id)
            title = existing.get("title", "Chat") if existing else "Chat"
            save_chat(chat_id, title, messages, traces)
        
        new_id = generate_chat_id()
        return ("", "", "", new_id, [], [], refresh_chat_list())
    
    def refresh_chat_list():
        chats = load_chat_list()[:20]
        if not chats:
            return "No chats yet."
        
        # Group by date
        now = datetime.now()
        today = []
        yesterday = []
        week = []
        older = []
        
        for chat in chats:
            updated = datetime.fromisoformat(chat.get("updated_at", now.isoformat()))
            delta = (now - updated).days
            
            star = "⭐ " if chat.get("starred") else ""
            title = chat.get("title", "Untitled")[:40]
            chat_id = chat.get("chat_id", "")
            
            item = f"{star}**{title}**  \n`{chat_id}` • {updated.strftime('%H:%M')}"
            
            if delta == 0:
                today.append(item)
            elif delta == 1:
                yesterday.append(item)
            elif delta <= 7:
                week.append(item)
            else:
                older.append(item)
        
        lines = []
        if today:
            lines.append("**Today**")
            lines.extend(today)
        if yesterday:
            lines.append("\n**Yesterday**")
            lines.extend(yesterday)
        if week:
            lines.append("\n**Last 7 Days**")
            lines.extend(week)
        if older:
            lines.append("\n**Older**")
            lines.extend(older[:5])
        
        return "\n\n".join(lines)
    
    def on_search(query):
        if not query.strip():
            return refresh_chat_list()
        
        results = search_chats(query)
        if not results:
            return f"No results for: {query}"
        
        lines = [f"**Search results for:** {query}", ""]
        for chat in results[:10]:
            star = "⭐ " if chat.get("starred") else ""
            title = chat.get("title", "Untitled")[:40]
            chat_id = chat.get("chat_id", "")
            lines.append(f"{star}{title} (`{chat_id}`)")
        
        return "\n\n".join(lines)
    
    def show_stats():
        return get_stats_summary()
    
    def on_export(chat_id):
        md = export_chat_markdown(chat_id)
        if md:
            path = os.path.join(STORAGE_DIR, f"export_{chat_id}.md")
            with open(path, "w", encoding="utf-8") as f:
                f.write(md)
            return f"Exported to: {path}"
        return "Export failed"
    
    def on_delete_chat(chat_id, messages):
        if messages and len(messages) > 0:
            delete_chat(chat_id)
            return on_new_chat([], [], generate_chat_id())
        return ("", "", "", chat_id, [], [], refresh_chat_list())
    
    def on_clear_memory():
        clear_memory()
        return inject_memory_into_prompt(load_memory())
    
    def on_regenerate(messages, model_name, chat_id):
        """Regenerate last response"""
        if not messages or len(messages) < 2:
            return ("", "", "")
        
        # Get last user message
        last_user_msg = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break
        
        if not last_user_msg:
            return ("", "", "")
        
        # Remove last assistant message
        if messages and messages[-1].get("role") == "assistant":
            messages.pop()
        
        # Regenerate
        conversation_history = messages.copy()
        final_answer = ""
        final_trace = ""
        
        for answer, trace, _ in rag_query_ui(last_user_msg, model_name, False, chat_id, conversation_history):
            final_answer = answer
            final_trace = trace
            yield (answer, trace, "")
        
        yield (final_answer, final_trace, "")
    
    # Connect events
    submit_btn.click(
        on_submit,
        inputs=[user_input, image_input, model_dropdown, current_chat_id, chat_messages, chat_traces],
        outputs=[answer_output, trace_output, followup_output, current_chat_id, chat_messages, chat_traces]
    ).then(
        lambda: ("", None),
        outputs=[user_input, image_input]
    ).then(
        refresh_chat_list,
        outputs=chat_list_md
    )
    
    user_input.submit(
        on_submit,
        inputs=[user_input, image_input, model_dropdown, current_chat_id, chat_messages, chat_traces],
        outputs=[answer_output, trace_output, followup_output, current_chat_id, chat_messages, chat_traces]
    ).then(
        lambda: ("", None),
        outputs=[user_input, image_input]
    ).then(
        refresh_chat_list,
        outputs=chat_list_md
    )
    
    new_chat_btn.click(
        on_new_chat,
        inputs=[chat_messages, chat_traces, current_chat_id],
        outputs=[answer_output, trace_output, followup_output, current_chat_id, chat_messages, chat_traces, chat_list_md]
    )
    
    refresh_btn.click(refresh_chat_list, outputs=chat_list_md)
    search_btn.click(on_search, inputs=search_box, outputs=chat_list_md)
    stats_btn.click(show_stats, outputs=stats_display)
    clear_memory_btn.click(on_clear_memory, outputs=memory_display)
    
    regen_btn.click(
        on_regenerate,
        inputs=[chat_messages, model_dropdown, current_chat_id],
        outputs=[answer_output, trace_output, followup_output]
    )
    
    # Initialize
    demo.load(refresh_chat_list, outputs=chat_list_md)

print("✅ Launching CEO Bot - ChatGPT Full Experience...")
demo.launch(server_name="127.0.0.1", server_port=7860, share=False)
