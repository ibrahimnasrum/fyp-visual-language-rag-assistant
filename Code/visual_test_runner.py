"""
Visual Language Model Test Runner for CEO Bot v8.2
Executes visual test questions (with images) via Gradio Client API
Uses two-tier evaluation: routing accuracy (30%) + answer quality (70%)
"""

import sys
import time
import json
import csv
import os
from datetime import datetime
from pathlib import Path
from gradio_client import Client
from answer_quality_evaluator import (
    AnswerQualityEvaluator,
    evaluate_route_accuracy,
    compute_overall_evaluation
)
from evaluation_metrics import EvaluationMetrics

class VisualTestRunner:
    def __init__(self, gradio_url="http://127.0.0.1:7860", model_name="llava:13b", use_quality_evaluation=True):
        """
        Initialize visual test runner with Gradio client.
        
        Args:
            gradio_url: Gradio app URL
            model_name: Visual language model to test (llava:13b or llava:latest)
            use_quality_evaluation: Enable two-tier evaluation (routing + quality)
        """
        self.gradio_url = gradio_url
        self.model_name = model_name
        self.client = None
        self.results = []
        self.start_time = None
        self.use_quality_evaluation = use_quality_evaluation
        
        # Initialize answer quality evaluator
        if self.use_quality_evaluation:
            try:
                self.quality_evaluator = AnswerQualityEvaluator()
                print(f"✅ Answer quality evaluator initialized (two-tier evaluation enabled)")
            except Exception as e:
                print(f"⚠️  Failed to initialize quality evaluator: {e}")
                print("   Falling back to routing-only evaluation")
                self.use_quality_evaluation = False
                self.quality_evaluator = None
        else:
            self.quality_evaluator = None
            print("ℹ️  Using routing-only evaluation (legacy mode)")
        
        # Initialize advanced metrics collector
        self.metrics_collector = EvaluationMetrics()
        self.api_endpoint = None
        
    def connect(self):
        """Connect to Gradio app"""
        print(f"🔌 Connecting to {self.gradio_url}...")
        try:
            self.client = Client(self.gradio_url)
            print("✅ Connected successfully!")
            
            # View available API endpoints
            print("\n📋 Available API endpoints:")
            try:
                api_info = self.client.view_api(return_format="dict")
                print(f"   Found {len(api_info.get('named_endpoints', {}))} named endpoints")
                for name, info in api_info.get('named_endpoints', {}).items():
                    print(f"   - {name}")
                
                # Use /on_submit endpoint specifically
                if '/on_submit' in api_info.get('named_endpoints', {}):
                    self.api_endpoint = '/on_submit'
                    print(f"   Using endpoint: {self.api_endpoint} ✅")
                elif '/multimodal_query' in api_info.get('named_endpoints', {}):
                    self.api_endpoint = '/multimodal_query'
                    print(f"   Using endpoint: {self.api_endpoint} ✅")
                else:
                    for name in api_info.get('named_endpoints', {}).keys():
                        if 'submit' in name.lower() or 'query' in name.lower():
                            self.api_endpoint = name
                            print(f"   Using endpoint: {self.api_endpoint} (fallback)")
                            break
                    else:
                        self.api_endpoint = None
                        print(f"   ⚠️  Could not find query endpoint, using fn_index=0")
            except Exception as e:
                print(f"   Could not view API: {e}")
                self.api_endpoint = None
            
            print()
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def load_visual_tests(self, csv_path):
        """Load visual test queries from CSV"""
        tests = []
        print(f"📂 Loading visual tests from: {csv_path}")
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert relative path to absolute path
                    image_path = row['image_path']
                    if not os.path.isabs(image_path):
                        # Assume path is relative to Code directory
                        base_dir = os.path.dirname(csv_path)
                        image_path = os.path.abspath(os.path.join(base_dir, image_path))
                    
                    # Check if image exists
                    if not os.path.exists(image_path):
                        print(f"⚠️  Image not found: {image_path}")
                        continue
                    
                    test = {
                        'id': row['id'],
                        'category': row['category'],
                        'question': row['question'],
                        'image_path': image_path,
                        'preferred_route': row['preferred_route'],
                        'acceptable_routes': row.get('acceptable_routes', '').split(',') if row.get('acceptable_routes') else [row['preferred_route']],
                        'priority': row['priority'],
                        'note': row.get('note', '')
                    }
                    tests.append(test)
            
            print(f"✅ Loaded {len(tests)} visual tests")
            return tests
        except Exception as e:
            print(f"❌ Failed to load visual tests: {e}")
            return []
    
    def run_single_test(self, test):
        """Run a single visual test question with image"""
        test_id = test['id']
        query = test['question']
        image_path = test['image_path']
        preferred_route = test['preferred_route']
        acceptable_routes = test['acceptable_routes']
        priority = test['priority']
        note = test['note']
        
        print(f"\n{'='*80}")
        print(f"🧪 TEST [{test_id}] ({priority})")
        print(f"   Query: {query}")
        print(f"   Image: {os.path.basename(image_path)}")
        print(f"   Preferred Route: {preferred_route}")
        if len(acceptable_routes) > 1:
            print(f"   Acceptable Routes: {', '.join(acceptable_routes)}")
        if note:
            print(f"   Note: {note}")
        print(f"{'='*80}")
        
        test_result = {
            "id": test_id,
            "query": query,
            "image_path": image_path,
            "preferred_route": preferred_route,
            "acceptable_routes": acceptable_routes,
            "priority": priority,
            "note": note,
            "timestamp": datetime.now().isoformat(),
        }
        
        try:
            # Submit query with image
            print(f"⏱️  Submitting query with image to {self.model_name}...")
            start = time.time()
            
            # Call via API with image parameter
            # API signature: (text, image, model_name)
            if self.api_endpoint:
                # Gradio expects file path as handle() format or actual file
                from gradio_client import handle_file
                result = self.client.predict(
                    query,                    # text
                    handle_file(image_path),  # image file (wrapped)
                    self.model_name,          # model_name (llava:13b or llava:latest)
                    api_name=self.api_endpoint
                )
            else:
                result = self.client.predict(
                    query,
                    image_path,
                    self.model_name,
                    fn_index=0
                )
            
            elapsed = time.time() - start
            
            # Parse result
            try:
                if isinstance(result, (list, tuple)) and len(result) >= 2:
                    status_html = str(result[0]) if result[0] else ""
                    answer_md = str(result[1]) if result[1] else ""
                else:
                    status_html = str(result) if result else ""
                    answer_md = ""
            except Exception as e:
                print(f"⚠️  Warning: Could not parse result: {e}")
                status_html = str(result) if result else ""
                answer_md = ""
            
            # Extract route from status HTML
            actual_route = "unknown"
            if "KPI" in status_html or "kpi" in status_html.lower():
                # Infer from answer content
                if "headcount" in answer_md.lower() or "employee" in answer_md.lower() or "attrition" in answer_md.lower():
                    actual_route = "hr_kpi"
                else:
                    actual_route = "sales_kpi"
            elif "RAG" in status_html or "rag" in status_html.lower():
                actual_route = "rag_docs"
            elif "docs" in status_html.lower():
                actual_route = "rag_docs"
            
            # Store basic results
            test_result["actual_route"] = actual_route
            test_result["response_time"] = round(elapsed, 2)
            test_result["answer"] = answer_md
            test_result["answer_length"] = len(answer_md)
            test_result["status_html"] = status_html
            
            # Print response
            print(f"\n✅ Response received in {elapsed:.2f}s")
            print(f"   Route: {actual_route}")
            print(f"   Answer length: {len(answer_md)} chars")
            print(f"\n📝 Answer Preview (first 500 chars):")
            print("-" * 80)
            print(answer_md[:500] + "..." if len(answer_md) > 500 else answer_md)
            print("-" * 80)
            
            # Two-tier evaluation
            if self.use_quality_evaluation and self.quality_evaluator:
                print(f"\n🔍 Two-tier evaluation...")
                
                # Tier 1: Routing accuracy
                route_score, route_status = evaluate_route_accuracy(
                    actual_route, 
                    test  # Pass the full test dict with preferred_route and acceptable_routes
                )
                
                test_result["route_score"] = route_score
                test_result["route_status"] = route_status
                
                print(f"   🛤️  Routing: {route_status} (score: {route_score:.2f})")
                
                # Tier 2: Answer quality
                quality_score, quality_breakdown, quality_justification = self.quality_evaluator.evaluate_answer_quality(
                    query=query,
                    answer=answer_md,
                    test_case=test,  # Pass the full test dict
                    actual_route=actual_route
                )
                
                test_result["quality_score"] = quality_score
                test_result["quality_breakdown"] = quality_breakdown
                
                print(f"   ⭐ Quality: {quality_score:.3f}")
                print(f"      • Semantic: {quality_breakdown.get('semantic_similarity', 0):.3f}")
                print(f"      • Completeness: {quality_breakdown.get('information_completeness', 0):.3f}")
                print(f"      • Accuracy: {quality_breakdown.get('factual_accuracy', 0):.3f}")
                print(f"      • Presentation: {quality_breakdown.get('presentation_quality', 0):.3f}")
                
                # Overall evaluation
                overall_result = compute_overall_evaluation(
                    route_result["route_score"],
                    quality_result["overall_score"],
                    route_result["route_status"]
                )
                
                test_result["overall_score"] = overall_result["overall_score"]
                test_result["status"] = overall_result["status"]
                
                print(f"   🎯 Overall: {overall_result['overall_score']:.3f} → {overall_result['status']}")
                
                # Record for advanced metrics
                self.metrics_collector.record_test(test_result)
            else:
                # Legacy routing-only evaluation
                route_match = (actual_route == preferred_route)
                test_result["route_match"] = route_match
                test_result["status"] = "PASSED" if route_match else "FAILED"
                
                print(f"   Route match: {'✅' if route_match else '❌'}")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            test_result["status"] = "ERROR"
            test_result["error"] = str(e)
            test_result["actual_route"] = "error"
            test_result["response_time"] = 0
            test_result["answer"] = ""
        
        self.results.append(test_result)
        return test_result
    
    def run_all_tests(self, csv_path):
        """Run all visual tests from CSV file"""
        self.start_time = datetime.now()
        print(f"\n{'#'*80}")
        print(f"# VISUAL LANGUAGE MODEL TEST EXECUTION")
        print(f"# Model: {self.model_name}")
        print(f"# Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*80}\n")
        
        # Load tests
        tests = self.load_visual_tests(csv_path)
        if not tests:
            print("❌ No tests to run!")
            return
        
        # Run each test
        for test in tests:
            self.run_single_test(test)
        
        # Final summary
        self.print_final_report()
    
    def print_final_report(self):
        """Print comprehensive test report"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        total = len(self.results)
        
        print(f"\n\n{'#'*80}")
        print(f"# FINAL TEST REPORT - {self.model_name}")
        print(f"{'#'*80}")
        print(f"\n⏱️  Duration: {duration:.2f}s ({duration/total:.2f}s per test)")
        print(f"📊 Total Tests: {total}")
        
        if self.use_quality_evaluation and any('quality_score' in r for r in self.results):
            # Two-tier report
            perfect = sum(1 for r in self.results if r.get('status') == 'PERFECT')
            acceptable = sum(1 for r in self.results if r.get('status') == 'ACCEPTABLE')
            failed = sum(1 for r in self.results if r.get('status') == 'FAILED')
            errors = sum(1 for r in self.results if r.get('status') == 'ERROR')
            
            print(f"\n🎯 TWO-TIER EVALUATION RESULTS:")
            print(f"   ⭐ Perfect: {perfect} ({perfect/total*100:.1f}%)")
            print(f"   ✅ Acceptable: {acceptable} ({acceptable/total*100:.1f}%)")
            print(f"   ❌ Failed: {failed} ({failed/total*100:.1f}%)")
            print(f"   ⚠️  Errors: {errors} ({errors/total*100:.1f}%)")
            print(f"\n📈 USER SATISFACTION RATE: {(perfect+acceptable)/total*100:.1f}%")
            
            # Average scores
            quality_scores = [r['quality_score'] for r in self.results if 'quality_score' in r]
            route_scores = [r['route_score'] for r in self.results if 'route_score' in r]
            overall_scores = [r['overall_score'] for r in self.results if 'overall_score' in r]
            response_times = [r['response_time'] for r in self.results if 'response_time' in r and r['response_time'] > 0]
            
            if quality_scores:
                print(f"\n📊 AVERAGE SCORES:")
                print(f"   Quality: {sum(quality_scores)/len(quality_scores):.3f}")
                print(f"   Routing: {sum(route_scores)/len(route_scores):.3f}")
                print(f"   Overall: {sum(overall_scores)/len(overall_scores):.3f}")
            
            if response_times:
                print(f"\n⏱️  RESPONSE TIME:")
                print(f"   Average: {sum(response_times)/len(response_times):.2f}s")
                print(f"   Min: {min(response_times):.2f}s")
                print(f"   Max: {max(response_times):.2f}s")
        else:
            # Legacy report
            passed = sum(1 for r in self.results if r.get('status') == 'PASSED')
            failed = sum(1 for r in self.results if r.get('status') == 'FAILED')
            errors = sum(1 for r in self.results if r.get('status') == 'ERROR')
            
            print(f"\n📊 RESULTS:")
            print(f"   ✅ Passed: {passed} ({passed/total*100:.1f}%)")
            print(f"   ❌ Failed: {failed} ({failed/total*100:.1f}%)")
            print(f"   ⚠️  Errors: {errors} ({errors/total*100:.1f}%)")
        
        print(f"\n{'#'*80}\n")
        
        # Save results
        self.save_results()
    
    def save_results(self):
        """Save test results to JSON and CSV files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON (complete data)
        json_filename = f"visual_test_results_{self.model_name.replace(':', '_')}_{timestamp}.json"
        
        total = len(self.results)
        if self.use_quality_evaluation and any('quality_score' in r for r in self.results):
            perfect = sum(1 for r in self.results if r.get('status') == 'PERFECT')
            acceptable = sum(1 for r in self.results if r.get('status') == 'ACCEPTABLE')
            failed = sum(1 for r in self.results if r.get('status') == 'FAILED')
            errors = sum(1 for r in self.results if r.get('status') == 'ERROR')
            
            output = {
                "timestamp": self.start_time.isoformat(),
                "gradio_url": self.gradio_url,
                "model_name": self.model_name,
                "evaluation_mode": "two-tier",
                "total_tests": total,
                "perfect": perfect,
                "acceptable": acceptable,
                "failed": failed,
                "errors": errors,
                "user_satisfaction_rate": (perfect + acceptable) / total if total > 0 else 0,
                "results": self.results
            }
        else:
            passed = sum(1 for r in self.results if r.get('status') == 'PASSED')
            failed = sum(1 for r in self.results if r.get('status') == 'FAILED')
            errors = sum(1 for r in self.results if r.get('status') == 'ERROR')
            
            output = {
                "timestamp": self.start_time.isoformat(),
                "gradio_url": self.gradio_url,
                "model_name": self.model_name,
                "evaluation_mode": "routing-only",
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "results": self.results
            }
        
        try:
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            print(f"💾 JSON results saved to: {json_filename}")
        except Exception as e:
            print(f"⚠️  Failed to save JSON: {e}")
        
        # Save CSV (summary)
        csv_filename = f"visual_test_results_{self.model_name.replace(':', '_')}_{timestamp}.csv"
        
        try:
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                if self.use_quality_evaluation and any('quality_score' in r for r in self.results):
                    fieldnames = ['id', 'query', 'image', 'actual_route', 'preferred_route',
                                'route_score', 'route_status', 'quality_score', 
                                'semantic_similarity', 'information_completeness',
                                'factual_accuracy', 'presentation_quality',
                                'overall_score', 'status', 'response_time', 
                                'answer_length', 'note']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for r in self.results:
                        row = {
                            'id': r.get('id', ''),
                            'query': r.get('query', ''),
                            'image': os.path.basename(r.get('image_path', '')),
                            'actual_route': r.get('actual_route', ''),
                            'preferred_route': r.get('preferred_route', ''),
                            'route_score': r.get('route_score', ''),
                            'route_status': r.get('route_status', ''),
                            'quality_score': r.get('quality_score', ''),
                            'semantic_similarity': r.get('quality_breakdown', {}).get('semantic_similarity', ''),
                            'information_completeness': r.get('quality_breakdown', {}).get('information_completeness', ''),
                            'factual_accuracy': r.get('quality_breakdown', {}).get('factual_accuracy', ''),
                            'presentation_quality': r.get('quality_breakdown', {}).get('presentation_quality', ''),
                            'overall_score': r.get('overall_score', ''),
                            'status': r.get('status', ''),
                            'response_time': r.get('response_time', ''),
                            'answer_length': r.get('answer_length', ''),
                            'note': r.get('note', '')
                        }
                        writer.writerow(row)
                else:
                    fieldnames = ['id', 'query', 'image', 'expected_route', 'actual_route',
                                'route_match', 'status', 'response_time', 'answer_length', 'note']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for r in self.results:
                        row = {k: r.get(k, '') for k in fieldnames}
                        row['image'] = os.path.basename(r.get('image_path', ''))
                        writer.writerow(row)
            
            print(f"💾 CSV results saved to: {csv_filename}")
        except Exception as e:
            print(f"⚠️  Failed to save CSV: {e}")


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Visual Language Model Test Runner')
    parser.add_argument('--model', type=str, default='llava:13b',
                      help='Visual language model to test (default: llava:13b)')
    parser.add_argument('--csv', type=str, default='visual_test_queries.csv',
                      help='CSV file with visual test queries (default: visual_test_queries.csv)')
    parser.add_argument('--url', type=str, default='http://127.0.0.1:7860',
                      help='Gradio app URL (default: http://127.0.0.1:7860)')
    
    args = parser.parse_args()
    
    # Initialize and run
    runner = VisualTestRunner(gradio_url=args.url, model_name=args.model)
    
    if not runner.connect():
        print("\n❌ Failed to connect to Gradio app")
        print(f"   Make sure the app is running at {args.url}")
        return
    
    # Run tests
    runner.run_all_tests(args.csv)


if __name__ == "__main__":
    main()
