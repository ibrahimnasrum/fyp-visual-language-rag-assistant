"""
Run tests with improved intent detection and compare with baseline
Shows Before vs After improvement metrics
"""

import json
from pathlib import Path
import subprocess
import sys

print("="*80)
print("IMPROVEMENT VALIDATION - Before vs After Comparison")
print("="*80)

# Load baseline results
baseline_file = Path(__file__).parent / 'test_results_20260117_043810.json'
with open(baseline_file, 'r', encoding='utf-8') as f:
    baseline = json.load(f)

print(f"\n📊 BASELINE RESULTS (Before Improvements):")
print(f"   File: {baseline_file.name}")
print(f"   Total Tests: {baseline['total_tests']}")
print(f"   User Satisfaction: {baseline['user_satisfaction_rate']*100:.1f}%")
print(f"   - Perfect: {baseline['perfect']}")
print(f"   - Acceptable: {baseline['acceptable']}")
print(f"   - Failed: {baseline['failed']}")

print(f"\n🔧 Running tests with IMPROVED intent detection...")
print(f"   (This will take 5-10 minutes for 50 tests)\n")

# Run the automated test runner
result = subprocess.run(
    [sys.executable, 'automated_test_runner.py'],
    cwd=Path(__file__).parent,
    capture_output=False
)

if result.returncode != 0:
    print(f"\n❌ Test run failed with code {result.returncode}")
    sys.exit(1)

# Find the latest results file
results_dir = Path(__file__).parent
latest_file = max(results_dir.glob('test_results_*.json'), key=lambda p: p.stat().st_mtime)

with open(latest_file, 'r', encoding='utf-8') as f:
    improved = json.load(f)

print(f"\n")
print("="*80)
print("📈 IMPROVEMENT ANALYSIS")
print("="*80)

print(f"\n📊 IMPROVED RESULTS (After Changes):")
print(f"   File: {latest_file.name}")
print(f"   Total Tests: {improved['total_tests']}")
print(f"   User Satisfaction: {improved['user_satisfaction_rate']*100:.1f}%")
print(f"   - Perfect: {improved['perfect']}")
print(f"   - Acceptable: {improved['acceptable']}")
print(f"   - Failed: {improved['failed']}")

# Calculate improvements
satisfaction_improvement = (improved['user_satisfaction_rate'] - baseline['user_satisfaction_rate']) * 100
perfect_improvement = improved['perfect'] - baseline['perfect']
acceptable_improvement = improved['acceptable'] - baseline['acceptable']

print(f"\n🎯 IMPROVEMENT METRICS:")
print(f"   User Satisfaction: {baseline['user_satisfaction_rate']*100:.1f}% → {improved['user_satisfaction_rate']*100:.1f}%")
if satisfaction_improvement > 0:
    print(f"   ✅ IMPROVED by {satisfaction_improvement:.1f} percentage points!")
elif satisfaction_improvement < 0:
    print(f"   ⚠️  DECLINED by {abs(satisfaction_improvement):.1f} percentage points")
else:
    print(f"   ➡️  No change")

print(f"\n   Perfect Cases: {baseline['perfect']} → {improved['perfect']} ({perfect_improvement:+d})")
print(f"   Acceptable Cases: {baseline['acceptable']} → {improved['acceptable']} ({acceptable_improvement:+d})")

# Detailed routing analysis
print(f"\n🛤️  ROUTING ACCURACY ANALYSIS:")
baseline_routing = {}
improved_routing = {}

for test in baseline['results']:
    route = test.get('preferred_route', 'unknown')
    if route not in baseline_routing:
        baseline_routing[route] = {'correct': 0, 'total': 0}
    baseline_routing[route]['total'] += 1
    if test.get('route_score', 0) >= 0.7:  # Perfect or acceptable routing
        baseline_routing[route]['correct'] += 1

for test in improved['results']:
    route = test.get('preferred_route', 'unknown')
    if route not in improved_routing:
        improved_routing[route] = {'correct': 0, 'total': 0}
    improved_routing[route]['total'] += 1
    if test.get('route_score', 0) >= 0.7:  # Perfect or acceptable routing
        improved_routing[route]['correct'] += 1

for route in sorted(set(list(baseline_routing.keys()) + list(improved_routing.keys()))):
    if route == 'unknown':
        continue
    
    baseline_acc = (baseline_routing.get(route, {}).get('correct', 0) / 
                   baseline_routing.get(route, {}).get('total', 1)) * 100
    improved_acc = (improved_routing.get(route, {}).get('correct', 0) / 
                   improved_routing.get(route, {}).get('total', 1)) * 100
    
    improvement = improved_acc - baseline_acc
    symbol = "✅" if improvement > 5 else "➡️" if abs(improvement) <= 5 else "⚠️"
    
    print(f"   {symbol} {route:15s}: {baseline_acc:5.1f}% → {improved_acc:5.1f}% ({improvement:+.1f}%)")

print(f"\n" + "="*80)
print(f"💾 Full results saved to: {latest_file}")
print("="*80)
