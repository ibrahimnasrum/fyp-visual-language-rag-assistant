"""
Phase 3: Visual Language Model Testing

Tests llava:13b and llava:latest on chart interpretation tasks.
Validates FYP Objective 1: Vision-language multimodal understanding.

Usage:
    python test_visual_models.py
"""

import ollama
import json
from pathlib import Path
from datetime import datetime

TEST_IMAGES_DIR = Path(__file__).parent / 'test_images'
RESULTS_DIR = Path(__file__).parent / 'model_comparison_results'

# Visual test cases
VISUAL_TESTS = [
    {
        'id': 'V01',
        'image': 'V01_sales_trend.png',
        'query': 'Analyze the sales trend shown in this chart. What is the overall pattern from January to June 2024?',
        'expected_keywords': ['trend', 'increase', 'decrease', 'pattern', 'month']
    },
    {
        'id': 'V02',
        'image': 'V02_product_table.png',
        'query': 'List all products shown in this table with their exact sales values in RM.',
        'expected_keywords': ['product', 'RM', 'sales', 'table']
    },
    {
        'id': 'V03',
        'image': 'V03_category_bar.png',
        'query': 'Which product category has the highest sales according to this bar chart?',
        'expected_keywords': ['category', 'highest', 'sales', 'bar']
    },
    {
        'id': 'V04',
        'image': 'V04_region_pie.png',
        'query': 'What percentage of sales comes from each region shown in this pie chart?',
        'expected_keywords': ['region', 'percentage', '%', 'pie']
    },
    {
        'id': 'V05',
        'image': 'V05_multilingual.png',
        'query': 'Read the text from this document and summarize the key points (includes Chinese/Malay text).',
        'expected_keywords': ['text', 'document', 'summary']
    }
]


def test_visual_model(model_name: str, image_path: Path, query: str) -> dict:
    """Test a visual model on one image"""
    try:
        # Read image as base64
        import base64
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()
        
        start_time = datetime.now()
        
        # Call ollama with image
        response = ollama.chat(
            model=model_name,
            messages=[{
                'role': 'user',
                'content': query,
                'images': [image_data]
            }]
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        return {
            'success': True,
            'answer': response['message']['content'],
            'response_time': elapsed
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'response_time': 0
        }


def evaluate_visual_answer(answer: str, expected_keywords: list) -> dict:
    """Simple evaluation based on keyword presence"""
    answer_lower = answer.lower()
    
    keywords_found = sum(1 for kw in expected_keywords if kw.lower() in answer_lower)
    keyword_score = keywords_found / len(expected_keywords) if expected_keywords else 0
    
    return {
        'keyword_coverage': keyword_score * 100,
        'keywords_found': keywords_found,
        'total_keywords': len(expected_keywords),
        'answer_length': len(answer)
    }


def run_visual_tests(model_name: str):
    """Run all visual tests for one model"""
    
    print(f"\n{'='*80}")
    print(f"Testing Visual Model: {model_name}")
    print(f"{'='*80}\n")
    
    results = {
        'model': model_name,
        'timestamp': datetime.now().isoformat(),
        'tests': []
    }
    
    for test_case in VISUAL_TESTS:
        test_id = test_case['id']
        image_file = TEST_IMAGES_DIR / test_case['image']
        
        print(f"📊 {test_id}: {test_case['image']}")
        
        if not image_file.exists():
            print(f"   ⚠️  Image not found: {test_case['image']}")
            results['tests'].append({
                'id': test_id,
                'status': 'SKIPPED',
                'reason': 'Image file not found'
            })
            continue
        
        # Test the model
        result = test_visual_model(model_name, image_file, test_case['query'])
        
        if not result['success']:
            print(f"   ❌ Error: {result['error']}")
            results['tests'].append({
                'id': test_id,
                'status': 'ERROR',
                'error': result['error']
            })
            continue
        
        # Evaluate answer
        evaluation = evaluate_visual_answer(result['answer'], test_case['expected_keywords'])
        
        print(f"   ✅ Completed in {result['response_time']:.2f}s")
        print(f"   📝 Keyword coverage: {evaluation['keyword_coverage']:.1f}%")
        print(f"   📏 Answer length: {evaluation['answer_length']} chars")
        
        results['tests'].append({
            'id': test_id,
            'image': test_case['image'],
            'query': test_case['query'],
            'answer': result['answer'],
            'response_time': result['response_time'],
            'evaluation': evaluation,
            'status': 'PASS' if evaluation['keyword_coverage'] >= 50 else 'PARTIAL'
        })
    
    # Calculate summary statistics
    completed = [t for t in results['tests'] if t['status'] in ['PASS', 'PARTIAL']]
    
    if completed:
        avg_keyword_coverage = sum(t['evaluation']['keyword_coverage'] for t in completed) / len(completed)
        avg_response_time = sum(t['response_time'] for t in completed) / len(completed)
        pass_count = sum(1 for t in completed if t['status'] == 'PASS')
        
        results['summary'] = {
            'total_tests': len(VISUAL_TESTS),
            'completed': len(completed),
            'passed': pass_count,
            'avg_keyword_coverage': avg_keyword_coverage,
            'avg_response_time': avg_response_time
        }
        
        print(f"\n📊 Summary:")
        print(f"   Tests completed: {len(completed)}/{len(VISUAL_TESTS)}")
        print(f"   Pass rate: {pass_count}/{len(completed)} ({pass_count/len(completed)*100:.1f}%)")
        print(f"   Avg keyword coverage: {avg_keyword_coverage:.1f}%")
        print(f"   Avg response time: {avg_response_time:.2f}s")
    
    # Save results
    output_file = RESULTS_DIR / f"{model_name.replace(':', '_')}_visual_tests.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Results saved: {output_file.name}\n")
    
    return results


if __name__ == "__main__":
    print("\n" + "="*80)
    print("VISUAL LANGUAGE MODEL TESTING - FYP Objective 1")
    print("="*80)
    
    # Test both visual models
    models_to_test = [
        'llava:13b',
        'llava:latest'
    ]
    
    all_results = {}
    
    for model in models_to_test:
        try:
            results = run_visual_tests(model)
            all_results[model] = results
        except Exception as e:
            print(f"\n❌ Error testing {model}: {e}\n")
    
    # Comparison summary
    if len(all_results) >= 2:
        print("\n" + "="*80)
        print("VISUAL MODEL COMPARISON")
        print("="*80 + "\n")
        
        for model, results in all_results.items():
            if 'summary' in results:
                print(f"{model}:")
                print(f"  Coverage: {results['summary']['avg_keyword_coverage']:.1f}%")
                print(f"  Speed: {results['summary']['avg_response_time']:.2f}s")
                print()
    
    print("="*80)
    print("✅ Visual testing complete!")
    print("="*80)
