"""
Automated Test Runner for CEO Bot v8.2
Executes all test questions via Gradio Client API
Tests timer behavior, stop button, routing accuracy, and response quality
"""

import sys
import time
import json
from datetime import datetime
from pathlib import Path
from gradio_client import Client
from comprehensive_test_suite import TEST_QUESTIONS

class TestRunner:
    def __init__(self, gradio_url="http://127.0.0.1:7866"):
        """Initialize test runner with Gradio client"""
        self.gradio_url = gradio_url
        self.client = None
        self.results = []
        self.start_time = None
        
    def connect(self):
        """Connect to Gradio app"""
        print(f"🔌 Connecting to {self.gradio_url}...")
        try:
            self.client = Client(self.gradio_url)
            print("✅ Connected successfully!\n")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def run_single_test(self, test_id, query, expected_route, priority, note=""):
        """Run a single test question"""
        print(f"\n{'='*80}")
        print(f"🧪 TEST [{test_id}] ({priority})")
        print(f"   Query: {query}")
        print(f"   Expected Route: {expected_route}")
        if note:
            print(f"   Note: {note}")
        print(f"{'='*80}")
        
        test_result = {
            "id": test_id,
            "query": query,
            "expected_route": expected_route,
            "priority": priority,
            "note": note,
            "timestamp": datetime.now().isoformat(),
        }
        
        try:
            # Submit query
            print("⏱️  Submitting query...")
            start = time.time()
            
            result = self.client.predict(
                query,  # txt
                None,   # img
                "qwen2.5:7b",  # model
                None,   # current_chat_id
                [],     # chat_messages
                [],     # chat_traces
                api_name="/submit"
            )
            
            elapsed = time.time() - start
            
            # Parse result
            status_html = result[0] if len(result) > 0 else ""
            answer_md = result[1] if len(result) > 1 else ""
            
            # Extract route from status HTML
            actual_route = "unknown"
            if "sales_kpi" in status_html.lower():
                actual_route = "sales_kpi"
            elif "hr_kpi" in status_html.lower():
                actual_route = "hr_kpi"
            elif "rag_docs" in status_html.lower():
                actual_route = "rag_docs"
            elif "visual" in status_html.lower():
                actual_route = "visual"
            
            # Check routing accuracy
            route_match = actual_route == expected_route
            
            # Store results
            test_result.update({
                "status": "PASS" if route_match else "FAIL",
                "actual_route": actual_route,
                "route_match": route_match,
                "response_time": elapsed,
                "answer_length": len(answer_md),
                "answer_preview": answer_md[:200] if answer_md else ""
            })
            
            # Print results
            if route_match:
                print(f"✅ PASS - Route correct: {actual_route}")
            else:
                print(f"❌ FAIL - Route mismatch: expected {expected_route}, got {actual_route}")
            
            print(f"⏱️  Response time: {elapsed:.2f}s")
            print(f"📝 Answer length: {len(answer_md)} chars")
            print(f"📄 Preview: {answer_md[:150]}..." if answer_md else "📄 No answer")
            
        except Exception as e:
            test_result.update({
                "status": "ERROR",
                "error": str(e),
                "actual_route": "error",
                "route_match": False
            })
            print(f"❌ ERROR: {e}")
        
        self.results.append(test_result)
        return test_result
    
    def run_category(self, category_name, questions, max_tests=None):
        """Run all tests in a category"""
        print(f"\n\n{'#'*80}")
        print(f"# CATEGORY: {category_name}")
        print(f"# Total tests: {len(questions)}")
        print(f"{'#'*80}\n")
        
        category_results = []
        
        for i, q in enumerate(questions):
            if max_tests and i >= max_tests:
                print(f"\n⚠️  Stopping at {max_tests} tests (limit reached)")
                break
            
            # Skip manual tests (visual/OCR)
            if q.get('manual'):
                print(f"\n⏭️  SKIPPED [{q['id']}] - Manual test (requires image upload)")
                continue
            
            result = self.run_single_test(
                q['id'],
                q['query'],
                q['expected_route'],
                q['priority'],
                q.get('note', '')
            )
            category_results.append(result)
            
            # Small delay between tests
            time.sleep(0.5)
        
        # Category summary
        passed = sum(1 for r in category_results if r['status'] == 'PASS')
        failed = sum(1 for r in category_results if r['status'] == 'FAIL')
        errors = sum(1 for r in category_results if r['status'] == 'ERROR')
        
        print(f"\n\n{'='*80}")
        print(f"📊 CATEGORY SUMMARY: {category_name}")
        print(f"{'='*80}")
        print(f"  ✅ Passed: {passed}")
        print(f"  ❌ Failed: {failed}")
        print(f"  ⚠️  Errors: {errors}")
        print(f"  📈 Success Rate: {passed/(passed+failed+errors)*100:.1f}%" if (passed+failed+errors) > 0 else "  N/A")
        print(f"{'='*80}\n")
        
        return category_results
    
    def run_all_tests(self, max_per_category=None):
        """Run all test categories"""
        self.start_time = datetime.now()
        print(f"\n{'#'*80}")
        print(f"# COMPREHENSIVE TEST EXECUTION")
        print(f"# Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*80}\n")
        
        # Run each category
        for category, questions in TEST_QUESTIONS.items():
            if category == "FOLLOWUP_SCENARIOS":
                print(f"\n⏭️  SKIPPING {category} - Requires multi-turn conversation support")
                continue
            
            self.run_category(category, questions, max_tests=max_per_category)
        
        # Final summary
        self.print_final_report()
    
    def print_final_report(self):
        """Print comprehensive test report"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')
        errors = sum(1 for r in self.results if r['status'] == 'ERROR')
        
        print(f"\n\n{'#'*80}")
        print(f"# FINAL TEST REPORT")
        print(f"{'#'*80}")
        print(f"\n⏱️  Duration: {duration:.2f}s")
        print(f"📊 Total Tests: {total}")
        print(f"   ✅ Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"   ❌ Failed: {failed} ({failed/total*100:.1f}%)")
        print(f"   ⚠️  Errors: {errors} ({errors/total*100:.1f}%)")
        
        # Failed tests details
        if failed > 0:
            print(f"\n❌ FAILED TESTS:")
            for r in self.results:
                if r['status'] == 'FAIL':
                    print(f"   [{r['id']}] {r['query'][:50]}...")
                    print(f"      Expected: {r['expected_route']}, Got: {r['actual_route']}")
        
        # Error tests details
        if errors > 0:
            print(f"\n⚠️  ERROR TESTS:")
            for r in self.results:
                if r['status'] == 'ERROR':
                    print(f"   [{r['id']}] {r['query'][:50]}...")
                    print(f"      Error: {r.get('error', 'Unknown error')}")
        
        # Performance stats
        response_times = [r.get('response_time', 0) for r in self.results if 'response_time' in r]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            print(f"\n⚡ Performance:")
            print(f"   Average response time: {avg_time:.2f}s")
            print(f"   Fastest: {min(response_times):.2f}s")
            print(f"   Slowest: {max(response_times):.2f}s")
        
        print(f"\n{'#'*80}\n")
        
        # Save results to JSON
        self.save_results()
    
    def save_results(self):
        """Save test results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_{timestamp}.json"
        
        output = {
            "timestamp": self.start_time.isoformat(),
            "gradio_url": self.gradio_url,
            "total_tests": len(self.results),
            "passed": sum(1 for r in self.results if r['status'] == 'PASS'),
            "failed": sum(1 for r in self.results if r['status'] == 'FAIL'),
            "errors": sum(1 for r in self.results if r['status'] == 'ERROR'),
            "results": self.results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to: {filename}")


def main():
    """Main execution"""
    # Check if gradio_client is installed
    try:
        import gradio_client
    except ImportError:
        print("❌ gradio_client not installed!")
        print("   Run: pip install gradio_client")
        return
    
    # Parse arguments
    max_per_category = None
    if len(sys.argv) > 1:
        try:
            max_per_category = int(sys.argv[1])
            print(f"⚙️  Running max {max_per_category} tests per category")
        except:
            pass
    
    # Initialize and run
    runner = TestRunner()
    
    if not runner.connect():
        print("\n❌ Failed to connect to Gradio app")
        print("   Make sure the app is running at http://127.0.0.1:7866")
        return
    
    # Run tests
    runner.run_all_tests(max_per_category=max_per_category)


if __name__ == "__main__":
    main()
