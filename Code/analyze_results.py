"""
Comprehensive Test Results Analysis
Compares baseline (112123) vs latest (133721) results
"""
import pandas as pd

# Load data
baseline = pd.read_csv('test_results_20260115_112123.csv')
latest = pd.read_csv('test_results_20260115_133721.csv')

print("="*80)
print("CHUNK 1: OVERALL METRICS COMPARISON")
print("="*80)

print("\n=== BASELINE (112123) ===")
print(baseline['status'].value_counts())
print(f"\nTotal: {len(baseline)}")
print(f"Pass Rate: {(baseline['status'] == 'PASS').sum() / len(baseline) * 100:.1f}%")

print("\n=== LATEST (133721) ===")
print(latest['status'].value_counts())
print(f"\nTotal: {len(latest)}")
print(f"Pass Rate: {(latest['status'] == 'PASS').sum() / len(latest) * 100:.1f}%")

print("\n=== IMPROVEMENT ===")
pass_delta = (latest['status'] == 'PASS').sum() - (baseline['status'] == 'PASS').sum()
route_fail_delta = (latest['status'] == 'ROUTE_FAIL').sum() - (baseline['status'] == 'ROUTE_FAIL').sum()
answer_fail_delta = (latest['status'] == 'ANSWER_FAIL').sum() - (baseline['status'] == 'ANSWER_FAIL').sum()

print(f"Pass: {pass_delta:+d} ({pass_delta/len(baseline)*100:+.1f}%)")
print(f"Route Fail: {route_fail_delta:+d}")
print(f"Answer Fail: {answer_fail_delta:+d}")

# Merge and find changes
merged = pd.merge(
    baseline[['test_id', 'question', 'expected_route', 'actual_route', 'status', 'answer_preview']],
    latest[['test_id', 'actual_route', 'status', 'answer_preview']],
    on='test_id',
    suffixes=('_before', '_after')
)

changed = merged[
    (merged['status_before'] != merged['status_after']) |
    (merged['actual_route_before'] != merged['actual_route_after'])
]

print("\n" + "="*80)
print("CHUNK 2: CHANGED TESTS SUMMARY")
print("="*80)
print(f"\nTotal changed: {len(changed)}")

improved = changed[(changed['status_before'] != 'PASS') & (changed['status_after'] == 'PASS')]
degraded = changed[(changed['status_before'] == 'PASS') & (changed['status_after'] != 'PASS')]
route_only = changed[
    (changed['status_before'] == changed['status_after']) &
    (changed['actual_route_before'] != changed['actual_route_after'])
]

print(f"Improved (FAIL→PASS): {len(improved)}")
print(f"Degraded (PASS→FAIL): {len(degraded)}")
print(f"Changed route only: {len(route_only)}")

print("\n" + "="*80)
print("CHUNK 3: DETAILED CHANGES")
print("="*80)

print("\n### IMPROVED TESTS (FAIL→PASS) ###")
if len(improved) > 0:
    for _, row in improved.iterrows():
        print(f"\n{row['test_id']}: {row['question'][:60]}")
        print(f"  Expected: {row['expected_route']}")
        print(f"  Route: {row['actual_route_before']} → {row['actual_route_after']}")
        print(f"  Status: {row['status_before']} → {row['status_after']}")
else:
    print("None")

print("\n### DEGRADED TESTS (PASS→FAIL) ###")
if len(degraded) > 0:
    for _, row in degraded.iterrows():
        print(f"\n{row['test_id']}: {row['question'][:60]}")
        print(f"  Expected: {row['expected_route']}")
        print(f"  Route: {row['actual_route_before']} → {row['actual_route_after']}")
        print(f"  Status: {row['status_before']} → {row['status_after']}")
else:
    print("None")

# Analyze routing accuracy by expected route
print("\n" + "="*80)
print("CHUNK 4: ROUTING ACCURACY BY TYPE")
print("="*80)

for route_type in ['hr_kpi', 'sales_kpi', 'rag_docs']:
    baseline_subset = baseline[baseline['expected_route'] == route_type]
    latest_subset = latest[latest['expected_route'] == route_type]
    
    baseline_correct = (baseline_subset['actual_route'] == baseline_subset['expected_route']).sum()
    latest_correct = (latest_subset['actual_route'] == latest_subset['expected_route']).sum()
    
    print(f"\n{route_type.upper()}:")
    print(f"  Baseline: {baseline_correct}/{len(baseline_subset)} correct ({baseline_correct/len(baseline_subset)*100:.1f}%)")
    print(f"  Latest:   {latest_correct}/{len(latest_subset)} correct ({latest_correct/len(latest_subset)*100:.1f}%)")
    print(f"  Change:   {latest_correct - baseline_correct:+d} ({(latest_correct/len(latest_subset) - baseline_correct/len(baseline_subset))*100:+.1f}%)")

# Save detailed changes to CSV
changed.to_csv('analysis_changed_tests.csv', index=False)
print("\n" + "="*80)
print(f"✅ Detailed changes saved to: analysis_changed_tests.csv")
print("="*80)
