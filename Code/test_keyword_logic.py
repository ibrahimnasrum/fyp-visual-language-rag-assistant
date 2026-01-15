"""Test keyword matching logic directly"""
import re

# Copy the keyword_match function from the bot
def keyword_match(keywords: list, text: str) -> tuple:
    """Match keywords with word boundaries to prevent substring collisions."""
    matched_keywords = []
    for k in keywords:
        if ' ' in k:
            # Multi-word phrase: use substring matching
            if k in text:
                matched_keywords.append(k)
        else:
            # Single word: use word boundary to prevent substring matches
            if re.search(rf'\b{re.escape(k)}\b', text):
                matched_keywords.append(k)
    return (len(matched_keywords) > 0, matched_keywords)

# Test with actual keywords from the bot
HR_KEYWORDS = [
    # Core HR terms
    "hr", "employee", "employees", "staff", "headcount", "department", "jabatan",
    "attrition", "resign", "turnover", "salary", "gaji", "income", "monthlyincome",
    
    # Granular HR terms (IMPROVEMENT #1)
    "tenure", "years of service", "seniority",
    "kitchen staff", "kitchen", "chef", "cook",
    "managers", "manager", "supervisor",
    "age", "age group", "age distribution", "workforce",
    "payroll", "total compensation", "payroll expense",
    "orang", "berapa orang",
    "by role", "by position", "by title", "by job",
    "5+ years", "more than", "less than", "over", "under",
    "veteran", "new hire", "experienced"
]

SALES_KEYWORDS = [
    "sales", "jualan", "revenue", "top", "banding", "compare", "vs", "versus", "mom",
    "bulan", "month", "mtd", "quantity", "qty", "terjual", "state", "negeri", "branch", "cawangan",
    "channel", "saluran", "product", "produk", "breakdown", "drove", "difference", "performance"
]

# Test failing queries
test_queries = [
    ("H06", "berapa staff kitchen?"),
    ("H07", "average employee tenure"),
    ("H08", "staff with more than 5 years"),
    ("H10", "total payroll expense"),
    ("CEO27", "Show me salary range for kitchen staff"),
    ("CEO29", "What's the age distribution of our workforce?"),
    ("CEO30", "What's the average tenure for managers?"),
    ("CEO23", "Which products have the highest unit price?"),
    ("CEO31", "Which branches perform above the average?"),
]

print("="*80)
print("KEYWORD MATCHING TEST")
print("="*80)

for test_id, query in test_queries:
    query_lower = query.lower()
    
    hr_match, hr_keywords = keyword_match(HR_KEYWORDS, query_lower)
    sales_match, sales_keywords = keyword_match(SALES_KEYWORDS, query_lower)
    
    print(f"\n{test_id}: {query}")
    print(f"  HR Match: {hr_match} → {hr_keywords[:5] if hr_keywords else 'None'}")
    print(f"  Sales Match: {sales_match} → {sales_keywords[:5] if sales_keywords else 'None'}")
    
    if hr_match:
        print(f"  ✅ Should route to HR_KPI")
    elif sales_match:
        print(f"  ✅ Should route to SALES_KPI")
    else:
        print(f"  ❌ No match → defaults to RAG_DOCS")
