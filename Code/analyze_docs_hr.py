import json

# Load v8.8 results
with open('test_results_20260117_145126.json', 'r', encoding='utf-8') as f:
    v88_data = json.load(f)

# Load v8.7 results
with open('test_results_20260117_142905.json', 'r', encoding='utf-8') as f:
    v87_data = json.load(f)

print("\n" + "="*70)
print("DOCS CATEGORY ANALYSIS (Why Phase 2 didn't work)")
print("="*70)

docs_v88 = [t for t in v88_data['results'] if t['id'].startswith('D')]
docs_v87 = [t for t in v87_data['results'] if t['id'].startswith('D')]

print(f"\nDocs tests v8.7 vs v8.8:")
print(f"{'ID':<6} {'v8.7 Status':<12} {'v8.7 Q':<8} {'v8.8 Status':<12} {'v8.8 Q':<8} {'Length':<8} {'Route':<12}")
print("-"*70)

for v88_test in docs_v88[:10]:
    test_id = v88_test['id']
    v87_test = next((t for t in docs_v87 if t['id'] == test_id), None)
    if v87_test:
        print(f"{test_id:<6} {v87_test['status']:<12} {v87_test['quality_score']:.3f}    "
              f"{v88_test['status']:<12} {v88_test['quality_score']:.3f}    "
              f"{v88_test['answer_length']:<8} {v88_test['actual_route']:<12}")

print("\n" + "="*70)
print("HR CATEGORY ANALYSIS (Why Phase 3 didn't work)")
print("="*70)

hr_v88 = [t for t in v88_data['results'] if t['id'].startswith('H')]
hr_v87 = [t for t in v87_data['results'] if t['id'].startswith('H')]

print(f"\nHR tests v8.7 vs v8.8:")
print(f"{'ID':<6} {'Query':<30} {'v8.7 Route':<12} {'v8.8 Route':<12} {'v8.7 Status':<12} {'v8.8 Status':<12}")
print("-"*70)

for v88_test in hr_v88:
    test_id = v88_test['id']
    v87_test = next((t for t in hr_v87 if t['id'] == test_id), None)
    if v87_test:
        print(f"{test_id:<6} {v88_test['query'][:28]:<30} {v87_test['actual_route']:<12} "
              f"{v88_test['actual_route']:<12} {v87_test['status']:<12} {v88_test['status']:<12}")

print("\n" + "="*70)
print("KEY FINDINGS")
print("="*70)

# Check if answers got longer
docs_v87_avg_len = sum(t['answer_length'] for t in docs_v87) / len(docs_v87)
docs_v88_avg_len = sum(t['answer_length'] for t in docs_v88) / len(docs_v88)

print(f"\nDocs Answer Length:")
print(f"  v8.7: {docs_v87_avg_len:.1f} chars (avg)")
print(f"  v8.8: {docs_v88_avg_len:.1f} chars (avg)")
print(f"  Change: {docs_v88_avg_len - docs_v87_avg_len:+.1f} chars")

# Check if routing changed for HR
hr_routing_changed = sum(1 for i, v88 in enumerate(hr_v88) 
                         if hr_v87[i]['actual_route'] != v88['actual_route'])
print(f"\nHR Routing Changes:")
print(f"  Tests with different routing: {hr_routing_changed}/{len(hr_v88)}")

# Check quality scores
docs_v87_avg_q = sum(t['quality_score'] for t in docs_v87) / len(docs_v87)
docs_v88_avg_q = sum(t['quality_score'] for t in docs_v88) / len(docs_v88)

print(f"\nDocs Quality Score:")
print(f"  v8.7: {docs_v87_avg_q:.3f} (avg)")
print(f"  v8.8: {docs_v88_avg_q:.3f} (avg)")
print(f"  Change: {docs_v88_avg_q - docs_v87_avg_q:+.3f}")

# Check if threshold would help
docs_passing_at_68 = sum(1 for t in docs_v88 if t['quality_score'] >= 0.68)
docs_total = len(docs_v88)

print(f"\nDocs tests that would pass at 0.68 threshold:")
print(f"  {docs_passing_at_68}/{docs_total} tests ({docs_passing_at_68/docs_total*100:.1f}%)")
