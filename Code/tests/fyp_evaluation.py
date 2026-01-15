"""
FYP Evaluation Framework
30-scenario test suite for thesis Chapter 5 results.
Tests validation, caching, and decision-making accuracy.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from query.time_classifier import TimeClassifier
from query.validator import DataValidator
from core.simple_cache import SimpleCache
import pandas as pd
import json
from datetime import datetime


class FYPEvaluator:
    """Evaluation framework for FYP thesis results."""
    
    def __init__(self, sales_csv_path: str):
        """Initialize evaluator with data path."""
        self.sales_csv_path = sales_csv_path
        self.classifier = TimeClassifier()
        self.validator = DataValidator(sales_csv_path)
        self.cache = SimpleCache(ttl_seconds=3600)
        self.results = []
    
    def run_all_tests(self):
        """Run all 30 test scenarios."""
        print("\n" + "="*80)
        print("🧪 FYP EVALUATION FRAMEWORK - 30 Test Scenarios")
        print("="*80 + "\n")
        
        # Category 1: Time Classification (10 scenarios)
        print("📋 Category 1: Time Sensitivity Classification")
        self._test_time_classification()
        
        # Category 2: Data Validation (10 scenarios)
        print("\n📋 Category 2: Data Availability Validation")
        self._test_data_validation()
        
        # Category 3: Cache Performance (10 scenarios)
        print("\n📋 Category 3: Cache Performance")
        self._test_cache_performance()
        
        # Generate summary
        self._generate_summary()
    
    def _test_time_classification(self):
        """Test time sensitivity classification accuracy."""
        test_cases = [
            # Static queries (should NOT be time-sensitive)
            ("What products are available?", False, "static"),
            ("List all states", False, "static"),
            ("Show me all branches", False, "static"),
            
            # Dynamic queries with explicit timeframe (should NOT need clarification)
            ("Total revenue in January 2024", True, "dynamic"),
            ("Sales in 2024-01", True, "dynamic"),
            ("Revenue for H1 2024", True, "dynamic"),
            
            # Dynamic queries WITHOUT timeframe (NEEDS clarification)
            ("What is the total revenue?", True, "dynamic"),
            ("Show me sales performance", True, "dynamic"),
            ("Top 5 products", True, "hybrid"),
            ("Total transactions", True, "dynamic"),
        ]
        
        correct = 0
        for i, (query, expected_sensitive, expected_class) in enumerate(test_cases, 1):
            result = self.classifier.classify(query)
            is_correct = (result['is_time_sensitive'] == expected_sensitive and 
                         result['classification'] == expected_class)
            
            status = "✅ PASS" if is_correct else "❌ FAIL"
            print(f"  TC-CLASS-{i:02d}: {status} | '{query[:50]}...'")
            print(f"     Expected: sensitive={expected_sensitive}, class={expected_class}")
            print(f"     Got: sensitive={result['is_time_sensitive']}, class={result['classification']}")
            
            if is_correct:
                correct += 1
            
            self.results.append({
                'test_id': f'TC-CLASS-{i:02d}',
                'category': 'time_classification',
                'query': query,
                'expected': {'sensitive': expected_sensitive, 'class': expected_class},
                'actual': result,
                'passed': is_correct
            })
        
        accuracy = (correct / len(test_cases)) * 100
        print(f"\n  📊 Classification Accuracy: {correct}/{len(test_cases)} ({accuracy:.1f}%)\n")
    
    def _test_data_validation(self):
        """Test data availability validation."""
        test_cases = [
            # Available months (should PASS)
            ("2024-01", True, "Data available"),
            ("2024-02", True, "Data available"),
            ("January 2024", True, "Data available"),
            
            # Unavailable months (should FAIL with helpful message)
            ("2023-12", False, "Data not available"),
            ("2024-07", False, "Data not available"),
            ("December 2023", False, "Data not available"),
            
            # No month specified (should PASS with all data message)
            (None, True, "Using all available data"),
            
            # Invalid formats (should FAIL with parse error)
            ("invalid-month", False, "Could not parse"),
            ("xyz", False, "Could not parse"),
            ("2024-13", False, "Could not parse"),
        ]
        
        correct = 0
        for i, (month_str, expected_available, expected_msg_contains) in enumerate(test_cases, 1):
            result = self.validator.validate(month_str)
            is_correct = (result['available'] == expected_available and 
                         expected_msg_contains.lower() in result['message'].lower())
            
            status = "✅ PASS" if is_correct else "❌ FAIL"
            print(f"  TC-VALID-{i:02d}: {status} | Month: {month_str}")
            print(f"     Expected: available={expected_available}, contains='{expected_msg_contains}'")
            print(f"     Got: available={result['available']}, message='{result['message'][:50]}...'")
            
            if is_correct:
                correct += 1
            
            self.results.append({
                'test_id': f'TC-VALID-{i:02d}',
                'category': 'data_validation',
                'month': month_str,
                'expected': {'available': expected_available, 'message_contains': expected_msg_contains},
                'actual': result,
                'passed': is_correct
            })
        
        accuracy = (correct / len(test_cases)) * 100
        print(f"\n  📊 Validation Accuracy: {correct}/{len(test_cases)} ({accuracy:.1f}%)\n")
    
    def _test_cache_performance(self):
        """Test cache hit rates and performance."""
        # Simulate common query patterns
        test_patterns = [
            # Pattern 1: Repeated queries (should hit cache)
            {'state': 'Selangor', 'product': None},
            {'state': 'Selangor', 'product': None},  # Cache hit
            {'state': 'Selangor', 'product': None},  # Cache hit
            
            # Pattern 2: Different filters (cache miss)
            {'state': 'Penang', 'product': None},
            {'state': 'Johor', 'product': None},
            
            # Pattern 3: Product filters
            {'state': None, 'product': 'Nasi Lemak'},
            {'state': None, 'product': 'Nasi Lemak'},  # Cache hit
            
            # Pattern 4: Combined filters
            {'state': 'Selangor', 'product': 'Nasi Lemak'},
            {'state': 'Selangor', 'product': 'Nasi Lemak'},  # Cache hit
            
            # Pattern 5: All data query
            {},
        ]
        
        print("  Testing cache patterns...")
        for i, filters in enumerate(test_patterns, 1):
            cache_key = self._make_cache_key(filters)
            
            # Try to get from cache
            cached = self.cache.get(cache_key)
            
            if cached is None:
                # Simulate data loading
                data = self._simulate_data_load(filters)
                self.cache.set(cache_key, data)
                result = "MISS"
            else:
                result = "HIT"
            
            print(f"     Query {i:02d}: {result} | Filters: {filters}")
        
        stats = self.cache.get_stats()
        print(f"\n  📊 Cache Performance:")
        print(f"     Hits: {stats['hits']}")
        print(f"     Misses: {stats['misses']}")
        print(f"     Hit Rate: {stats['hit_rate_percent']}%")
        print(f"     Cache Size: {stats['cache_size']} entries\n")
        
        # For thesis: Expected hit rate should be > 30% for realistic usage
        expected_hit_rate = 40.0  # With pattern above: 4 hits / 10 queries = 40%
        hit_rate_ok = stats['hit_rate_percent'] >= 30.0
        
        self.results.append({
            'test_id': 'TC-CACHE-01',
            'category': 'cache_performance',
            'expected_hit_rate': expected_hit_rate,
            'actual_hit_rate': stats['hit_rate_percent'],
            'passed': hit_rate_ok,
            'stats': stats
        })
    
    def _make_cache_key(self, filters: dict) -> str:
        """Generate cache key from filters."""
        parts = []
        for k in ['state', 'product', 'branch']:
            if filters.get(k):
                parts.append(f"{k}:{filters[k]}")
        return "|".join(parts) if parts else "all_data"
    
    def _simulate_data_load(self, filters: dict):
        """Simulate loading data (returns filter dict for simplicity)."""
        return filters  # In real scenario, would return DataFrame
    
    def _generate_summary(self):
        """Generate evaluation summary for thesis."""
        print("\n" + "="*80)
        print("📊 EVALUATION SUMMARY (FOR THESIS CHAPTER 5)")
        print("="*80 + "\n")
        
        # Category summaries
        categories = {}
        for result in self.results:
            cat = result['category']
            if cat not in categories:
                categories[cat] = {'total': 0, 'passed': 0}
            categories[cat]['total'] += 1
            if result['passed']:
                categories[cat]['passed'] += 1
        
        print("📋 Results by Category:")
        for cat, stats in categories.items():
            accuracy = (stats['passed'] / stats['total']) * 100
            print(f"  {cat.replace('_', ' ').title()}: {stats['passed']}/{stats['total']} ({accuracy:.1f}%)")
        
        # Overall accuracy
        total_tests = len(self.results)
        total_passed = sum(1 for r in self.results if r['passed'])
        overall_accuracy = (total_passed / total_tests) * 100
        
        print(f"\n📊 Overall Accuracy: {total_passed}/{total_tests} ({overall_accuracy:.1f}%)")
        
        # Save results to JSON for thesis
        output_file = os.path.join(os.path.dirname(__file__), 'fyp_evaluation_results.json')
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_tests': total_tests,
                    'passed': total_passed,
                    'overall_accuracy': overall_accuracy,
                    'by_category': categories
                },
                'detailed_results': self.results
            }, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")
        print("="*80 + "\n")


def main():
    """Run FYP evaluation."""
    # Path to sales data
    sales_csv = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'data', 'MY_Retail_Sales_2024H1.csv'
    )
    
    if not os.path.exists(sales_csv):
        print(f"❌ Sales data not found: {sales_csv}")
        print("Please update the path in the script.")
        return
    
    evaluator = FYPEvaluator(sales_csv)
    evaluator.run_all_tests()


if __name__ == '__main__':
    main()
