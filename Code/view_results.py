"""
CSV Results Viewer - Analyze test results easily
Reads the CSV file and shows summary, failures, and detailed results

Usage:
    python view_results.py test_results_20260115_123456.csv
    python view_results.py                    # Uses latest CSV file
"""

import sys
import csv
from pathlib import Path
from datetime import datetime

def find_latest_csv():
    """Find the most recent test results CSV file"""
    csv_files = list(Path('.').glob('test_results_*.csv'))
    if not csv_files:
        return None
    return max(csv_files, key=lambda p: p.stat().st_mtime)

def load_results(filename):
    """Load results from CSV"""
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def print_summary(results):
    """Print summary statistics"""
    total = len(results)
    passed = sum(1 for r in results if r['status'] == 'PASS')
    route_fail = sum(1 for r in results if r['status'] == 'ROUTE_FAIL')
    answer_fail = sum(1 for r in results if r['status'] == 'ANSWER_FAIL')
    errors = sum(1 for r in results if r['status'] == 'ERROR')
    
    print(f"\n{'='*80}")
    print(f"TEST RESULTS SUMMARY")
    print(f"{'='*80}\n")
    print(f"📊 Total Tests: {total}")
    print(f"   ✅ PASSED: {passed} ({passed/total*100:.1f}%)")
    print(f"   ⚠️  ROUTE_FAIL: {route_fail} ({route_fail/total*100:.1f}%)")
    print(f"   ⚠️  ANSWER_FAIL: {answer_fail} ({answer_fail/total*100:.1f}%)")
    print(f"   ❌ ERRORS: {errors} ({errors/total*100:.1f}%)")
    
    # Response time stats
    times = [float(r['response_time_sec']) for r in results if r.get('response_time_sec')]
    if times:
        print(f"\n⏱️  Response Times:")
        print(f"   Average: {sum(times)/len(times):.2f}s")
        print(f"   Fastest: {min(times):.2f}s")
        print(f"   Slowest: {max(times):.2f}s")
    
    # Follow-up stats
    followups = [int(r['followup_count']) for r in results if r.get('followup_count') and r['followup_count'].isdigit()]
    if followups:
        print(f"\n💡 Follow-ups:")
        print(f"   Average: {sum(followups)/len(followups):.1f} per question")
        print(f"   With follow-ups: {sum(1 for f in followups if f > 0)}/{len(followups)}")

def print_failures(results):
    """Print all failed tests"""
    failures = [r for r in results if r['status'] != 'PASS']
    
    if not failures:
        print(f"\n{'='*80}")
        print("🎉 NO FAILURES - All tests passed!")
        print(f"{'='*80}\n")
        return
    
    print(f"\n{'='*80}")
    print(f"⚠️  FAILURES DETAIL ({len(failures)} tests)")
    print(f"{'='*80}\n")
    
    for r in failures:
        print(f"[{r['test_id']}] {r['status']}")
        print(f"Question: {r['question']}")
        print(f"Expected Route: {r['expected_route']} → Actual: {r['actual_route']}")
        if r.get('error'):
            print(f"Error: {r['error']}")
        if r.get('answer_preview'):
            print(f"Answer: {r['answer_preview'][:100]}...")
        print("-" * 80)

def print_detailed_results(results, show_all=False):
    """Print detailed results for each test"""
    print(f"\n{'='*80}")
    print(f"DETAILED RESULTS")
    print(f"{'='*80}\n")
    
    display_results = results if show_all else [r for r in results if r['status'] == 'PASS'][:5]
    
    for r in display_results:
        status_emoji = {
            'PASS': '✅',
            'ROUTE_FAIL': '⚠️',
            'ANSWER_FAIL': '⚠️',
            'ERROR': '❌',
            'PARTIAL': '⚠️'
        }.get(r['status'], '❓')
        
        print(f"{status_emoji} [{r['test_id']}] {r['status']}")
        print(f"Q: {r['question']}")
        print(f"Route: {r['expected_route']} → {r['actual_route']} ({r['route_match']})")
        print(f"Time: {r.get('response_time_sec', 0)}s")
        print(f"Answer ({r.get('answer_length', 0)} chars): {r.get('answer_preview', '')[:150]}...")
        if r.get('followup_count') and int(r['followup_count']) > 0:
            print(f"Follow-ups ({r['followup_count']}): {r.get('followup_preview', '')[:150]}...")
        print("-" * 80)
    
    if not show_all and len(results) > 5:
        print(f"\n... and {len(results) - 5} more results (open CSV to see all)\n")

def main():
    """Main viewer"""
    # Get filename
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = find_latest_csv()
        if not filename:
            print("❌ No test results CSV found!")
            print("   Run: python automated_tester_csv.py --quick")
            return 1
        print(f"📂 Using latest file: {filename}\n")
    
    # Check file exists
    if not Path(filename).exists():
        print(f"❌ File not found: {filename}")
        return 1
    
    # Load and display results
    results = load_results(filename)
    
    print(f"\n{'#'*80}")
    print(f"# TEST RESULTS VIEWER")
    print(f"# File: {filename}")
    print(f"# Loaded: {len(results)} test results")
    print(f"{'#'*80}")
    
    # Show summary
    print_summary(results)
    
    # Show failures
    print_failures(results)
    
    # Show sample detailed results
    print_detailed_results(results, show_all=False)
    
    print(f"\n{'='*80}")
    print(f"💡 TIP: Open {filename} in Excel for full analysis")
    print(f"{'='*80}\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
