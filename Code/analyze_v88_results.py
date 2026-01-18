import json

# Load v8.8 results
with open('test_results_20260117_145126.json', 'r', encoding='utf-8') as f:
    v88_data = json.load(f)

print("\n" + "="*60)
print("v8.8 TEST RESULTS (Final Optimization)")
print("="*60)
print(f"Timestamp: {v88_data['timestamp']}")
print(f"Tests Executed: {v88_data['total_tests']}")
print(f"\nUser Satisfaction: {v88_data['user_satisfaction_rate']*100:.1f}%")
print(f"  Perfect: {v88_data['perfect']}")
print(f"  Acceptable: {v88_data['acceptable']}")
print(f"  Failed: {v88_data['failed']}")
print(f"  Errors: {v88_data['errors']}")

# Calculate category breakdown from results
results = v88_data['results']
categories = {}
for test_data in results:
    test_id = test_data.get('id', 'Unknown')
    # Determine category from test ID
    if test_id.startswith('S'):
        cat = 'Sales'
    elif test_id.startswith('H'):
        cat = 'HR'
    elif test_id.startswith('D'):
        cat = 'Docs'
    elif test_id.startswith('R'):
        cat = 'Robustness'
    elif test_id.startswith('V'):
        cat = 'Visual'
    else:
        cat = 'Unknown'
    
    if cat not in categories:
        categories[cat] = {'total': 0, 'satisfied': 0}
    
    categories[cat]['total'] += 1
    if test_data['status'] in ['ACCEPTABLE', 'PERFECT']:
        categories[cat]['satisfied'] += 1

print(f"\nCategory Breakdown:")
print("-"*60)
for cat in sorted(categories.keys()):
    data = categories[cat]
    rate = (data['satisfied'] / data['total'] * 100) if data['total'] > 0 else 0
    print(f"  {cat:15s}: {rate:5.1f}% ({data['satisfied']:2d}/{data['total']:2d} tests)")

# Load v8.7 results for comparison
with open('test_results_20260117_142905.json', 'r', encoding='utf-8') as f:
    v87_data = json.load(f)

print(f"\n" + "="*60)
print("COMPARISON: v8.7 → v8.8")
print("="*60)

v87_sat = v87_data['user_satisfaction_rate'] * 100
v88_sat = v88_data['user_satisfaction_rate'] * 100
sat_change = v88_sat - v87_sat
sat_rel_change = ((v88_sat / v87_sat) - 1) * 100 if v87_sat > 0 else 0

print(f"Overall Satisfaction:")
print(f"  v8.7: {v87_sat:.1f}% → v8.8: {v88_sat:.1f}%")
print(f"  Change: {sat_change:+.1f}% absolute ({sat_rel_change:+.1f}% relative)")

# Calculate v8.7 categories
v87_results = v87_data['results']
v87_categories = {}
for test_data in v87_results:
    test_id = test_data.get('id', 'Unknown')
    # Determine category from test ID
    if test_id.startswith('S'):
        cat = 'Sales'
    elif test_id.startswith('H'):
        cat = 'HR'
    elif test_id.startswith('D'):
        cat = 'Docs'
    elif test_id.startswith('R'):
        cat = 'Robustness'
    elif test_id.startswith('V'):
        cat = 'Visual'
    else:
        cat = 'Unknown'
    
    if cat not in v87_categories:
        v87_categories[cat] = {'total': 0, 'satisfied': 0}
    
    v87_categories[cat]['total'] += 1
    if test_data['status'] in ['ACCEPTABLE', 'PERFECT']:
        v87_categories[cat]['satisfied'] += 1

print(f"\nCategory Changes:")
print("-"*60)
for cat in sorted(categories.keys()):
    v87_rate = (v87_categories[cat]['satisfied'] / v87_categories[cat]['total'] * 100) if cat in v87_categories and v87_categories[cat]['total'] > 0 else 0
    v88_rate = (categories[cat]['satisfied'] / categories[cat]['total'] * 100) if categories[cat]['total'] > 0 else 0
    change = v88_rate - v87_rate
    rel_change = ((v88_rate / v87_rate) - 1) * 100 if v87_rate > 0 else 0
    
    print(f"  {cat:15s}: {v87_rate:5.1f}% → {v88_rate:5.1f}% ({change:+5.1f}%, {rel_change:+5.1f}% rel)")

# Load v8.6 results for complete comparison
with open('test_results_20260117_133556.json', 'r', encoding='utf-8') as f:
    v86_data = json.load(f)

print(f"\n" + "="*60)
print("COMPLETE JOURNEY: v8.6 → v8.7 → v8.8")
print("="*60)

v86_sat = v86_data['user_satisfaction_rate'] * 100
v86_passed = v86_data['perfect'] + v86_data['acceptable']
v87_passed = v87_data['perfect'] + v87_data['acceptable']
v88_passed = v88_data['perfect'] + v88_data['acceptable']

print(f"Overall Satisfaction:")
print(f"  v8.6 (Baseline):     {v86_sat:.1f}% ({v86_passed}/{v86_data['total_tests']})")
print(f"  v8.7 (Route-Aware):  {v87_sat:.1f}% ({v87_passed}/{v87_data['total_tests']}) [+{v87_sat-v86_sat:.1f}%, +{((v87_sat/v86_sat)-1)*100:.1f}% rel]")
print(f"  v8.8 (Optimized):    {v88_sat:.1f}% ({v88_passed}/{v88_data['total_tests']}) [+{v88_sat-v86_sat:.1f}%, +{((v88_sat/v86_sat)-1)*100:.1f}% rel]")

print(f"\nTotal Improvement: {v86_sat:.1f}% → {v88_sat:.1f}% (+{v88_sat-v86_sat:.1f}% absolute, +{((v88_sat/v86_sat)-1)*100:.1f}% relative)")

# Check if target achieved
if v88_sat >= 70:
    print(f"\n✅ TARGET ACHIEVED: {v88_sat:.1f}% ≥ 70% (FYP2 standard)")
else:
    print(f"\n⚠️  TARGET MISSED: {v88_sat:.1f}% < 70% (gap: {70-v88_sat:.1f}%)")
