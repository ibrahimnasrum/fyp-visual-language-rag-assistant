"""
Test the improvements: natural language month parsing + new response format
"""
import sys
import importlib.util
import pandas as pd

print("="*70)
print("Testing Improvements")
print("="*70 + "\n")

# Load module
spec = importlib.util.spec_from_file_location(
    "ceo_module",
    "oneclick_my_retailchain_v8.2_models_logging.py"
)
ceo_module = importlib.util.module_from_spec(spec)
print("Loading module (this takes ~30 seconds)...")
spec.loader.exec_module(ceo_module)
print("[OK] Module loaded\n")

# Test 1: Natural language month parsing
print("Test 1: Natural language month parsing")
print("-" * 70)

test_queries = [
    ("January 2024", pd.Period("2024-01", freq="M")),
    ("March 2024", pd.Period("2024-03", freq="M")),
    ("march", pd.Period("2024-03", freq="M")),  # assumes 2024
    ("2024-01", pd.Period("2024-01", freq="M")),
]

extract_month = ceo_module.extract_month_from_query

for query, expected in test_queries:
    result = extract_month(query)
    if result == expected:
        print(f"  [OK] '{query}' -> {result}")
    else:
        print(f"  [FAIL] '{query}' -> Expected: {expected}, Got: {result}")

print()

# Test 2: Response format check
print("Test 2: FYP-grade response format")
print("-" * 70)

answer_sales = ceo_module.answer_sales_ceo_kpi

# Test a simple query
response = answer_sales("What is total revenue for 2024-01?")

required_sections = [
    "**Answer:**",
    "**Evidence/Source:**",
    "**Confidence:**",
    "**Follow-up:**"
]

all_present = True
for section in required_sections:
    if section in response:
        print(f"  [OK] {section} section present")
    else:
        print(f"  [FAIL] {section} section MISSING")
        all_present = False

if all_present:
    print("\n[OK] All required sections present in response")
else:
    print("\n[FAIL] Some sections missing")

# Test 3: Check for proper source citations
print("\nTest 3: Source citation quality")
print("-" * 70)

checks = [
    ("KPI Facts:" in response, "KPI Facts citation"),
    ("Data Source:" in response, "Data Source specified"),
    ("Confidence:" in response, "Confidence level stated"),
]

for check, description in checks:
    if check:
        print(f"  [OK] {description}")
    else:
        print(f"  [FAIL] {description} missing")

print("\n" + "="*70)
print("Testing Complete")
print("="*70)
print("\nNext: Restart the system and test with natural language queries:")
print('  - "What is total revenue for January 2024?"')
print('  - "Compare Selangor vs Penang revenue for March 2024"')
