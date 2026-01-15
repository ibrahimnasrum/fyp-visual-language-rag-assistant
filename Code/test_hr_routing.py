"""
Quick test to diagnose HR routing issue
"""

# Test keyword matching
HR_KEYWORDS = [
    "hr", "employee", "employees", "staff", "headcount", "department", "jabatan",
    "attrition", "resign", "turnover", "salary", "gaji", "income", "monthlyincome"
]

SALES_KEYWORDS = [
    "sales", "jualan", "revenue", "top", "banding", "compare", "vs", "versus", "mom",
    "bulan", "month", "mtd", "quantity", "qty", "terjual", "state", "negeri", "branch", "cawangan",
    "channel", "saluran", "product", "produk", "breakdown", "drove", "difference", "performance"
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

def test_query_routing(query):
    """Test which route a query should take"""
    s = query.lower().strip()
    
    print(f"\n{'='*60}")
    print(f"Query: '{query}'")
    print(f"{'='*60}")
    
    # Check policy/docs (checked first in detect_intent)
    doc_matches = [k for k in HR_POLICY_KEYWORDS + DOC_KEYWORDS if k in s]
    if doc_matches:
        print(f"✅ POLICY/DOCS matched: {doc_matches[:3]}")
        print(f"→ Route: rag_docs")
        return "rag_docs"
    else:
        print(f"❌ No POLICY/DOCS keywords found")
    
    # Check HR KPI
    hr_matches = [k for k in HR_KEYWORDS if k in s]
    if hr_matches:
        print(f"✅ HR_KEYWORDS matched: {hr_matches}")
        print(f"→ Route: hr_kpi")
        return "hr_kpi"
    else:
        print(f"❌ No HR_KEYWORDS found")
    
    # Check Sales KPI
    sales_matches = [k for k in SALES_KEYWORDS if k in s]
    if sales_matches:
        print(f"✅ SALES_KEYWORDS matched: {sales_matches[:3]}")
        print(f"→ Route: sales_kpi")
        return "sales_kpi"
    else:
        print(f"❌ No SALES_KEYWORDS found")
    
    print(f"→ Route: rag_docs (default)")
    return "rag_docs"

def test_answer_hr_keywords(query):
    """Test if query matches answer_hr() patterns"""
    s = query.lower().strip()
    
    print(f"\n{'='*60}")
    print(f"Testing answer_hr() keyword matching")
    print(f"{'='*60}")
    
    # Test total headcount pattern
    headcount_keywords = ["how much employee", "how many employee", "total employee", "number of employee"]
    matches = [k for k in headcount_keywords if k in s]
    
    if matches:
        print(f"✅ Headcount pattern matched: {matches}")
        print(f"→ Should return employee count")
        return True
    else:
        print(f"❌ No headcount pattern matched")
        print(f"→ Will return None (fallback to docs)")
        return False

# Test queries
test_queries = [
    "how much employee in this company?",
    "how many employee",
    "total employee",
    "how many employees",
    "what is the employee count",
    "employee policy",
    "how much employee in this company sales?"
]

print("\n" + "="*80)
print("HR ROUTING DIAGNOSTIC TEST")
print("="*80)

for query in test_queries:
    route = test_query_routing(query)
    if route == "hr_kpi":
        test_answer_hr_keywords(query)

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
