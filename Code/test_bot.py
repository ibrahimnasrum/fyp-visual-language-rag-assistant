"""
FYP Evaluation Script - Tests routing accuracy and answer quality
"""
import requests
import json
import time
from datetime import datetime
from typing import Dict, List
import csv

# Test cases organized by category
TEST_CASES = {
    "SALES": [
        {
            "query": "sales bulan 2024-06",
            "expected_route": "sales_kpi",
            "difficulty": "EASY",
            "note": "Basic sales query"
        },
        {
            "query": "salse bulan 2024-06",
            "expected_route": "sales_kpi",
            "difficulty": "MEDIUM",
            "note": "Typo: salse → sales"
        },
        {
            "query": "top 3 produk dengan highest revenue",
            "expected_route": "sales_kpi",
            "difficulty": "MEDIUM",
            "note": "Mixed language + ranking"
        },
        {
            "query": "banding sales bulan ni vs bulan lepas",
            "expected_route": "sales_kpi",
            "difficulty": "HARD",
            "note": "Comparison query in Malay"
        },
        {
            "query": "sales ikut stat bulan 2024-06",
            "expected_route": "sales_kpi",
            "difficulty": "MEDIUM",
            "note": "Typo: stat → state"
        }
    ],
    "HR": [
        {
            "query": "total headcount",
            "expected_route": "hr_kpi",
            "difficulty": "EASY",
            "note": "Basic HR query"
        },
        {
            "query": "staff",
            "expected_route": "hr_kpi",
            "difficulty": "MEDIUM",
            "note": "Ambiguous single-word query"
        },
        {
            "query": "headcont ikut state",
            "expected_route": "hr_kpi",
            "difficulty": "MEDIUM",
            "note": "Typo: headcont → headcount"
        },
        {
            "query": "attrition by age group",
            "expected_route": "hr_kpi",
            "difficulty": "EASY",
            "note": "Standard HR metric"
        },
        {
            "query": "average income by jabatan",
            "expected_route": "hr_kpi",
            "difficulty": "MEDIUM",
            "note": "Mixed language (jabatan)"
        }
    ],
    "RAG": [
        {
            "query": "What is the annual leave policy?",
            "expected_route": "rag_docs",
            "difficulty": "EASY",
            "note": "Policy question"
        },
        {
            "query": "How do I submit a medical claim?",
            "expected_route": "rag_docs",
            "difficulty": "EASY",
            "note": "Procedural question"
        },
        {
            "query": "What's the weather today?",
            "expected_route": "rag_docs",
            "difficulty": "LOW",
            "note": "Out of scope"
        }
    ],
    "ROBUSTNESS": [
        {
            "query": "berapa sales for Cheese Burger in Mei 2024?",
            "expected_route": "sales_kpi",
            "difficulty": "MEDIUM",
            "note": "Complex mixed language"
        },
        {
            "query": "Can you book a meeting?",
            "expected_route": "rag_docs",
            "difficulty": "LOW",
            "note": "Not a query function"
        }
    ]
}

def evaluate_routing(actual: str, expected: str) -> float:
    """Score routing accuracy."""
    if actual == expected:
        return 1.0
    # Partial credit for acceptable alternatives
    acceptable = {
        "hr_kpi": ["rag_docs"],  # RAG can answer HR questions (less ideal)
        "sales_kpi": ["rag_docs"]
    }
    if actual in acceptable.get(expected, []):
        return 0.7
    return 0.0

def evaluate_answer_quality(answer: str) -> Dict[str, float]:
    """
    Evaluate answer quality on multiple dimensions.
    
    Returns:
        dict: {
            'length_score': 0-1,
            'structure_score': 0-1,
            'completeness': 0-1,
            'overall': 0-1
        }
    """
    scores = {}
    
    # Length score (300+ chars is good)
    answer_len = len(answer)
    if answer_len >= 400:
        scores['length_score'] = 1.0
    elif answer_len >= 300:
        scores['length_score'] = 0.8
    elif answer_len >= 200:
        scores['length_score'] = 0.6
    else:
        scores['length_score'] = 0.4
    
    # Structure score (has headers/sections)
    has_headers = any(marker in answer for marker in ['##', '###', '**'])
    has_sections = answer.count('\n\n') >= 2
    scores['structure_score'] = 1.0 if (has_headers and has_sections) else 0.5
    
    # Completeness (has key components)
    components = ['Summary', 'Evidence', 'Next', 'RM', 'rows', 'Data']
    found = sum(1 for comp in components if comp.lower() in answer.lower())
    scores['completeness'] = found / len(components)
    
    # Overall score (weighted average)
    scores['overall'] = (
        scores['length_score'] * 0.3 +
        scores['structure_score'] * 0.3 +
        scores['completeness'] * 0.4
    )
    
    return scores

def run_tests(api_url: str = "http://127.0.0.1:7860") -> Dict:
    """
    Run evaluation tests against the Gradio API.
    
    Args:
        api_url: Base URL of Gradio interface
    
    Returns:
        dict: Test results summary
    """
    results = []
    category_stats = {}
    
    print("=" * 80)
    print("🧪 FYP EVALUATION SUITE - CEO Bot Testing")
    print("=" * 80)
    
    total_tests = sum(len(tests) for tests in TEST_CASES.values())
    current_test = 0
    
    for category, tests in TEST_CASES.items():
        print(f"\n📂 CATEGORY: {category}")
        print("-" * 80)
        
        category_results = {
            'perfect': 0,
            'acceptable': 0,
            'failed': 0,
            'total': len(tests),
            'avg_quality': 0,
            'avg_latency': 0
        }
        
        for test in tests:
            current_test += 1
            print(f"\n[{current_test}/{total_tests}] Testing: {test['query'][:50]}...")
            
            # Submit query
            start_time = time.time()
            try:
                # Note: Adjust this based on your actual Gradio API endpoint
                response = requests.post(
                    f"{api_url}/api/predict",
                    json={"data": [test['query'], None]},  # [query, image]
                    timeout=30
                )
                latency = (time.time() - start_time) * 1000  # ms
                
                if response.status_code == 200:
                    result_data = response.json()
                    answer = result_data.get('data', [''])[0]
                    
                    # Extract route from answer (assuming it's logged)
                    # This may need adjustment based on your actual response format
                    actual_route = "unknown"
                    if "sales_kpi" in answer.lower():
                        actual_route = "sales_kpi"
                    elif "hr_kpi" in answer.lower():
                        actual_route = "hr_kpi"
                    elif "rag_docs" in answer.lower():
                        actual_route = "rag_docs"
                    
                    # Evaluate
                    routing_score = evaluate_routing(actual_route, test['expected_route'])
                    quality_scores = evaluate_answer_quality(answer)
                    
                    # Combined score
                    combined_score = (routing_score * 0.4) + (quality_scores['overall'] * 0.6)
                    
                    # Classify result
                    if combined_score >= 0.9:
                        status = "PERFECT"
                        category_results['perfect'] += 1
                    elif combined_score >= 0.75:
                        status = "ACCEPTABLE"
                        category_results['acceptable'] += 1
                    else:
                        status = "FAILED"
                        category_results['failed'] += 1
                    
                    category_results['avg_quality'] += quality_scores['overall']
                    category_results['avg_latency'] += latency
                    
                    # Store result
                    results.append({
                        'category': category,
                        'query': test['query'],
                        'expected_route': test['expected_route'],
                        'actual_route': actual_route,
                        'routing_score': routing_score,
                        'quality_overall': quality_scores['overall'],
                        'combined_score': combined_score,
                        'status': status,
                        'latency_ms': latency,
                        'answer_length': len(answer),
                        'difficulty': test['difficulty'],
                        'note': test['note']
                    })
                    
                    print(f"  ✓ Route: {actual_route} (Expected: {test['expected_route']})")
                    print(f"  ✓ Routing Score: {routing_score:.2f}")
                    print(f"  ✓ Quality Score: {quality_scores['overall']:.2f}")
                    print(f"  ✓ Combined Score: {combined_score:.2f}")
                    print(f"  ✓ Status: {status}")
                    print(f"  ✓ Latency: {latency:.0f}ms")
                    
                else:
                    print(f"  ✗ HTTP Error: {response.status_code}")
                    results.append({
                        'category': category,
                        'query': test['query'],
                        'status': 'ERROR',
                        'error': f"HTTP {response.status_code}"
                    })
                    category_results['failed'] += 1
                    
            except Exception as e:
                print(f"  ✗ Exception: {str(e)}")
                results.append({
                    'category': category,
                    'query': test['query'],
                    'status': 'ERROR',
                    'error': str(e)
                })
                category_results['failed'] += 1
        
        # Calculate category averages
        if category_results['total'] > 0:
            category_results['avg_quality'] /= category_results['total']
            category_results['avg_latency'] /= category_results['total']
        
        category_stats[category] = category_results
        
        # Print category summary
        print(f"\n📊 {category} Summary:")
        print(f"  Perfect: {category_results['perfect']} ({category_results['perfect']/category_results['total']*100:.1f}%)")
        print(f"  Acceptable: {category_results['acceptable']} ({category_results['acceptable']/category_results['total']*100:.1f}%)")
        print(f"  Failed: {category_results['failed']} ({category_results['failed']/category_results['total']*100:.1f}%)")
        print(f"  Success Rate: {(category_results['perfect'] + category_results['acceptable'])/category_results['total']*100:.1f}%")
        print(f"  Avg Quality: {category_results['avg_quality']:.3f}")
        print(f"  Avg Latency: {category_results['avg_latency']:.0f}ms")
    
    # Overall summary
    print("\n" + "=" * 80)
    print("📈 OVERALL SUMMARY")
    print("=" * 80)
    
    total_perfect = sum(stats['perfect'] for stats in category_stats.values())
    total_acceptable = sum(stats['acceptable'] for stats in category_stats.values())
    total_failed = sum(stats['failed'] for stats in category_stats.values())
    
    print(f"Total Tests: {total_tests}")
    print(f"Perfect: {total_perfect} ({total_perfect/total_tests*100:.1f}%)")
    print(f"Acceptable: {total_acceptable} ({total_acceptable/total_tests*100:.1f}%)")
    print(f"Failed: {total_failed} ({total_failed/total_tests*100:.1f}%)")
    print(f"Success Rate: {(total_perfect + total_acceptable)/total_tests*100:.1f}%")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON
    json_file = f"test_results_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': timestamp,
            'summary': category_stats,
            'results': results
        }, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Results saved to: {json_file}")
    
    # CSV
    csv_file = f"test_results_{timestamp}.csv"
    if results:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"💾 CSV saved to: {csv_file}")
    
    return {
        'summary': category_stats,
        'results': results,
        'success_rate': (total_perfect + total_acceptable) / total_tests
    }

if __name__ == "__main__":
    print("\n⚠️  IMPORTANT: Make sure your Gradio app is running first!")
    print("   Run: python oneclick_my_retailchain_v8.2_models_logging.py\n")
    
    input("Press Enter when ready to start testing...")
    
    results = run_tests()
    
    print("\n✅ Evaluation complete!")
    print(f"   Success Rate: {results['success_rate']*100:.1f}%")
