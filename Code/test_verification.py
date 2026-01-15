"""
Test script for verification and deterministic follow-up functionality.
Run this to validate the new features before deploying to production.
"""

import os
import sys

# Add Code directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("Testing Verification & Deterministic Follow-up Features")
print("=" * 60)

# Import functions from main script
try:
    from oneclick_my_retailchain_v8_2_models_logging import (
        extract_numerical_claims,
        compute_ground_truth,
        verify_answer_against_ground_truth,
        format_verification_notice,
        execute_top_products,
        execute_month_comparison,
        execute_state_comparison,
        execute_deterministic_followup,
        df_sales,
        df_hr
    )
    print("✅ Successfully imported all functions\n")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Note: Run this from the Code directory, or adjust the import statement.")
    sys.exit(1)

# =========================
# Test 1: Extract Numerical Claims
# =========================
print("\n" + "=" * 60)
print("TEST 1: Extract Numerical Claims")
print("=" * 60)

test_answer_1 = """
## Sales Analysis

Total Sales: RM 1,234,567.89
Total Quantity: 5,432 units
Average Price: RM 227.25
"""

claims = extract_numerical_claims(test_answer_1)
print("Input:", test_answer_1.strip())
print("\nExtracted Claims:", claims)

expected_keys = ["total_sales", "total_quantity", "avg_price"]
test1_pass = all(key in claims for key in expected_keys)
print("\n✅ PASS" if test1_pass else "\n❌ FAIL")

# =========================
# Test 2: Compute Ground Truth
# =========================
print("\n" + "=" * 60)
print("TEST 2: Compute Ground Truth from Pandas")
print("=" * 60)

query = "What are the total sales for June 2024?"
route = "sales_kpi"
context = {"month": "2024-06"}

ground_truth = compute_ground_truth(query, route, context)
print(f"Query: {query}")
print(f"Context: {context}")
print(f"\nGround Truth: {ground_truth}")

test2_pass = "total_sales" in ground_truth and ground_truth["total_sales"] > 0
print("\n✅ PASS" if test2_pass else "\n❌ FAIL")

# =========================
# Test 3: Verify Answer (Valid)
# =========================
print("\n" + "=" * 60)
print("TEST 3: Verify Answer - Valid Case")
print("=" * 60)

# Get actual total sales for June
june_sales = df_sales[df_sales['DateStr'].str.contains("2024-06", na=False)]['Total Sale'].sum()
print(f"Actual June 2024 Sales: RM {june_sales:,.2f}")

valid_answer = f"## Sales Report\n\nTotal Sales: RM {june_sales:,.2f}\nTotal Quantity: 1000 units"
is_valid, corrections, gt = verify_answer_against_ground_truth(valid_answer, query, route, context)

print(f"\nAnswer: {valid_answer}")
print(f"\nIs Valid: {is_valid}")
print(f"Corrections: {corrections}")

test3_pass = is_valid == True and len(corrections) == 0
print("\n✅ PASS" if test3_pass else "\n❌ FAIL")

# =========================
# Test 4: Verify Answer (Invalid)
# =========================
print("\n" + "=" * 60)
print("TEST 4: Verify Answer - Invalid Case (Hallucination)")
print("=" * 60)

# Intentionally wrong number
wrong_answer = "## Sales Report\n\nTotal Sales: RM 999,999,999.99\nTotal Quantity: 1000 units"
is_valid, corrections, gt = verify_answer_against_ground_truth(wrong_answer, query, route, context)

print(f"Answer: {wrong_answer}")
print(f"\nIs Valid: {is_valid}")
print(f"Corrections: {corrections}")
print(f"\nVerification Notice:")
notice = format_verification_notice(corrections, gt)
print(notice)

test4_pass = is_valid == False and len(corrections) > 0
print("\n✅ PASS" if test4_pass else "\n❌ FAIL")

# =========================
# Test 5: Deterministic Top Products
# =========================
print("\n" + "=" * 60)
print("TEST 5: Deterministic Top Products Execution")
print("=" * 60)

params = {"state": "Selangor", "month": "2024-06"}
answer = execute_top_products(params)

print(f"Parameters: {params}")
print(f"\nAnswer:\n{answer}")

test5_pass = "Top 5 Products" in answer and "✅ Verified" in answer
print("\n✅ PASS" if test5_pass else "\n❌ FAIL")

# =========================
# Test 6: Deterministic Month Comparison
# =========================
print("\n" + "=" * 60)
print("TEST 6: Deterministic Month Comparison")
print("=" * 60)

params = {"month1": "06", "month2": "05", "state": "Selangor"}
answer = execute_month_comparison(params)

print(f"Parameters: {params}")
print(f"\nAnswer:\n{answer}")

test6_pass = "Month Comparison" in answer and "✅ Verified" in answer and "2024-06" in answer
print("\n✅ PASS" if test6_pass else "\n❌ FAIL")

# =========================
# Test 7: Deterministic State Comparison
# =========================
print("\n" + "=" * 60)
print("TEST 7: Deterministic State Comparison")
print("=" * 60)

params = {"month": "2024-06"}
answer = execute_state_comparison(params)

print(f"Parameters: {params}")
print(f"\nAnswer:\n{answer}")

test7_pass = "State Comparison" in answer and "✅ Verified" in answer
print("\n✅ PASS" if test7_pass else "\n❌ FAIL")

# =========================
# Test 8: Execute Deterministic Follow-up Router
# =========================
print("\n" + "=" * 60)
print("TEST 8: Deterministic Follow-up Router")
print("=" * 60)

test_cases = [
    ("Show top products for Selangor", {"state": "Selangor"}),
    ("Compare June vs May", {"month1": "06", "month2": "05"}),
    ("Compare states", {"month": "2024-06"}),
]

test8_results = []
for followup_text, params in test_cases:
    result = execute_deterministic_followup(followup_text, params)
    is_deterministic = result is not None
    test8_results.append(is_deterministic)
    print(f"\nFollow-up: '{followup_text}'")
    print(f"Deterministic: {is_deterministic}")
    if is_deterministic:
        print(f"Answer preview: {result[:100]}...")

test8_pass = all(test8_results)
print("\n✅ PASS" if test8_pass else "\n❌ FAIL")

# =========================
# Summary
# =========================
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

all_tests = [
    ("Extract Numerical Claims", test1_pass),
    ("Compute Ground Truth", test2_pass),
    ("Verify Valid Answer", test3_pass),
    ("Verify Invalid Answer", test4_pass),
    ("Deterministic Top Products", test5_pass),
    ("Deterministic Month Comparison", test6_pass),
    ("Deterministic State Comparison", test7_pass),
    ("Deterministic Router", test8_pass),
]

passed = sum(1 for _, result in all_tests if result)
total = len(all_tests)

print(f"\nTests Passed: {passed}/{total}")
print()

for test_name, result in all_tests:
    status = "✅ PASS" if result else "❌ FAIL"
    print(f"{status} - {test_name}")

if passed == total:
    print("\n🎉 All tests passed! Ready for production.")
else:
    print(f"\n⚠️ {total - passed} test(s) failed. Please review before deploying.")

print("\n" + "=" * 60)
print("Test complete.")
print("=" * 60)
