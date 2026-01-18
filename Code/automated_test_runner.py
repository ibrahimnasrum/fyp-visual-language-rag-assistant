"""
Automated Test Runner for CEO Bot v8.2 - Two-Tier Evaluation
Executes all test questions via Gradio Client API
Uses two-tier evaluation: routing accuracy (30%) + answer quality (70%)
"""

import sys
import time
import json
from datetime import datetime
from pathlib import Path
from gradio_client import Client
from comprehensive_test_suite import TEST_QUESTIONS
from answer_quality_evaluator import (
    AnswerQualityEvaluator,
    evaluate_route_accuracy,
    compute_overall_evaluation
)
from evaluation_metrics import EvaluationMetrics

class TestRunner:
    def __init__(self, gradio_url="http://127.0.0.1:7860", use_quality_evaluation=True):
        """
        Initialize test runner with Gradio client.
        
        Args:
            gradio_url: Gradio app URL
            use_quality_evaluation: Enable two-tier evaluation (routing + quality)
        """
        self.gradio_url = gradio_url
        self.client = None
        self.results = []
        self.start_time = None
        self.use_quality_evaluation = use_quality_evaluation
        
        # Initialize answer quality evaluator
        if self.use_quality_evaluation:
            try:
                self.quality_evaluator = AnswerQualityEvaluator()
                print("✅ Answer quality evaluator initialized (two-tier evaluation enabled)")
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
        self.api_endpoint = None  # Will be set during connect()
        
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
                
                # Use /on_submit endpoint specifically (it's the main query endpoint)
                if '/on_submit' in api_info.get('named_endpoints', {}):
                    self.api_endpoint = '/on_submit'
                    print(f"   Using endpoint: {self.api_endpoint} ✅")
                elif '/multimodal_query' in api_info.get('named_endpoints', {}):
                    # Simple file uses /multimodal_query
                    self.api_endpoint = '/multimodal_query'
                    print(f"   Using endpoint: {self.api_endpoint} ✅")
                else:
                    # Fallback: find first endpoint with 'submit' or 'query' in name
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
    
    def run_single_test(self, test_id, query, expected_route, priority, note="", test_case=None):
        """
        Run a single test question with two-tier evaluation.
        
        Args:
            test_id: Test question ID
            query: User query
            expected_route: Expected route (legacy, kept for backward compatibility)
            priority: Test priority level
            note: Optional notes
            test_case: Full test case dict (includes acceptable_routes, answer_criteria)
        """
        print(f"\n{'='*80}")
        print(f"🧪 TEST [{test_id}] ({priority})")
        print(f"   Query: {query}")
        
        # Use test_case data if available (two-tier evaluation)
        if test_case and isinstance(test_case, dict):
            preferred_route = test_case.get("preferred_route") or test_case.get("expected_route")
            acceptable_routes = test_case.get("acceptable_routes", [preferred_route])
            print(f"   Preferred Route: {preferred_route}")
            if len(acceptable_routes) > 1:
                print(f"   Acceptable Routes: {', '.join(acceptable_routes)}")
        else:
            preferred_route = expected_route
            acceptable_routes = [expected_route]
            print(f"   Expected Route: {expected_route}")
        
        if note:
            print(f"   Note: {note}")
        print(f"{'='*80}")
        
        test_result = {
            "id": test_id,
            "query": query,
            "expected_route": expected_route,  # Legacy field
            "preferred_route": preferred_route,
            "acceptable_routes": acceptable_routes,
            "priority": priority,
            "note": note,
            "timestamp": datetime.now().isoformat(),
        }
        
        try:
            # Submit query
            print("⏱️  Submitting query...")
            start = time.time()
            
            # Call via API with discovered endpoint
            # Copy file API /on_submit takes 3 parameters: (text, image, model_name)
            # Returns 5 outputs: (status_html, answer_md, trace_html, followup_radio, chat_history_md)
            if self.api_endpoint:
                result = self.client.predict(
                    query,  # text
                    None,   # image
                    "qwen2.5:7b",  # model_name (Phase 2.4: FINAL TEXT LLM)
                    api_name=self.api_endpoint
                )
            else:
                result = self.client.predict(
                    query,  # text
                    None,   # image
                    "llama3:latest",  # model_name (Phase 2.3)
                    fn_index=0
                )
            
            elapsed = time.time() - start
            
            # Parse result - Gradio API returns tuple/list
            # Simple file API returns 2 outputs: (status_html, answer_md)
            # Copy file API /on_submit returns 5 outputs: (status_html, answer_md, trace_html, followup_radio, chat_history_md)
            try:
                # DEBUG: Print raw result
                print(f"🔍 DEBUG: Raw result type: {type(result)}")
                print(f"🔍 DEBUG: Raw result length: {len(result) if isinstance(result, (list, tuple)) else 'N/A'}")
                if isinstance(result, (list, tuple)):
                    for idx, item in enumerate(result):
                        print(f"🔍 DEBUG: result[{idx}] type: {type(item)}, length: {len(str(item)) if item else 0}")
                        if item and len(str(item)) < 200:
                            print(f"🔍 DEBUG: result[{idx}] content: {item}")
                
                if isinstance(result, (list, tuple)) and len(result) >= 2:
                    # Both simple (2 outputs) and copy (5 outputs) have status and answer at index 0,1
                    status_html = str(result[0]) if result[0] else ""
                    answer_md = str(result[1]) if result[1] else ""
                else:
                    # Fallback if unexpected format
                    status_html = str(result) if result else ""
                    answer_md = ""
                
                print(f"🔍 DEBUG: Extracted status_html length: {len(status_html)}")
                print(f"🔍 DEBUG: Extracted answer_md length: {len(answer_md)}")
            except Exception as e:
                print(f"⚠️  Warning: Could not parse result: {e}")
                print(f"   Result type: {type(result)}")
                print(f"   Result length: {len(result) if isinstance(result, (list, tuple)) else 'N/A'}")
                print(f"   Result: {result}")
                status_html = str(result) if result else ""
                answer_md = ""
            
            # Extract route from status HTML and answer content
            # The app returns badge HTML like: <span class="badge kpi">KPI</span>
            # Both sales_kpi and hr_kpi show as "KPI" badge, so we need to infer from answer
            actual_route = "unknown"
            status_lower = status_html.lower()
            answer_lower = answer_md.lower()
            
            # Check for badge classes
            if 'badge kpi' in status_lower or '>kpi<' in status_lower:
                # KPI route - determine if sales or HR from answer content
                sales_keywords = ['sales', 'revenue', 'product', 'rm', 'total penjualan', 'jualan']
                hr_keywords = ['headcount', 'employee', 'staff', 'pekerja', 'attrition', 'turnover', 'hire']
                
                sales_score = sum(1 for kw in sales_keywords if kw in answer_lower)
                hr_score = sum(1 for kw in hr_keywords if kw in answer_lower)
                
                if sales_score > hr_score:
                    actual_route = "sales_kpi"
                elif hr_score > sales_score:
                    actual_route = "hr_kpi"
                else:
                    # Check query as fallback
                    query_lower = query.lower()
                    if any(kw in query_lower for kw in sales_keywords):
                        actual_route = "sales_kpi"
                    elif any(kw in query_lower for kw in hr_keywords):
                        actual_route = "hr_kpi"
                    else:
                        actual_route = "sales_kpi"  # Default to sales
            elif 'badge ocr' in status_lower or '>ocr<' in status_lower:
                actual_route = "visual"
            elif 'badge rag' in status_lower or '>rag<' in status_lower or 'source: rag' in answer_lower:
                actual_route = "rag_docs"
            
            # Fallback: check for explicit route names
            if actual_route == "unknown":
                if "sales" in status_lower or "sales" in answer_lower[:200]:
                    actual_route = "sales_kpi"
                elif "headcount" in answer_lower or "employee" in answer_lower:
                    actual_route = "hr_kpi"
                elif "rag" in status_lower or "📄" in answer_md:
                    actual_route = "rag_docs"
                else:
                    actual_route = "rag_docs"  # Final fallback
            
            # TIER 1: Routing Accuracy Evaluation
            if test_case and isinstance(test_case, dict):
                route_score, route_status = evaluate_route_accuracy(actual_route, test_case)
            else:
                # Legacy: binary route matching
                route_match = actual_route == expected_route
                route_score = 1.0 if route_match else 0.0
                route_status = "PERFECT" if route_match else "WRONG"
            
            # TIER 2: Answer Quality Evaluation (if enabled)
            if self.use_quality_evaluation and test_case and isinstance(test_case, dict) and self.quality_evaluator:
                try:
                    quality_score, quality_breakdown, quality_justification = \
                        self.quality_evaluator.evaluate_answer_quality(
                            query, answer_md, test_case, actual_route
                        )
                    
                    # Compute overall score (weighted combination with route-specific thresholds)
                    overall_score, final_status = compute_overall_evaluation(
                        route_score, quality_score, route_name=actual_route
                    )
                    
                    # Store detailed results
                    test_result.update({
                        # Routing results
                        "actual_route": actual_route,
                        "route_score": route_score,
                        "route_status": route_status,
                        
                        # Quality results
                        "quality_score": quality_score,
                        "quality_breakdown": quality_breakdown,
                        "quality_justification": quality_justification,
                        
                        # Combined results
                        "overall_score": overall_score,
                        "status": final_status,
                        
                        # Metadata
                        "response_time": elapsed,
                        "answer_length": len(answer_md),
                        "answer": answer_md,
                        "answer_preview": answer_md[:200] if answer_md else ""
                    })
                    
                    # Print two-tier results
                    print(f"\n📊 TIER 1: Routing Accuracy")
                    print(f"   Route: {actual_route} (Preferred: {preferred_route})")
                    print(f"   Score: {route_score:.2f} ({route_status})")
                    
                    print(f"\n📊 TIER 2: Answer Quality")
                    print(f"   Score: {quality_score:.3f}")
                    print(f"   • Semantic: {quality_breakdown['semantic_similarity']:.3f}")
                    print(f"   • Completeness: {quality_breakdown['information_completeness']:.3f}")
                    print(f"   • Accuracy: {quality_breakdown['factual_accuracy']:.3f}")
                    print(f"   • Presentation: {quality_breakdown['presentation_quality']:.3f}")
                    
                    print(f"\n📊 COMBINED EVALUATION")
                    print(f"   Overall Score: {overall_score:.3f}")
                    print(f"   Status: {final_status}")
                    
                    if final_status == "PERFECT":
                        print(f"   ✅ PERFECT: Optimal routing + excellent answer quality")
                    elif final_status == "ACCEPTABLE":
                        print(f"   ✅ ACCEPTABLE: User satisfaction threshold met")
                        if route_status != "PERFECT":
                            print(f"      (Note: Non-optimal routing but answer quality compensates)")
                    else:
                        print(f"   ❌ FAILED: Below user satisfaction threshold")
                    
                except Exception as e:
                    print(f"⚠️  Quality evaluation failed: {e}")
                    # Fallback to routing-only
                    test_result.update({
                        "status": "PASS" if route_score == 1.0 else "FAIL",
                        "actual_route": actual_route,
                        "route_score": route_score,
                        "route_status": route_status,
                        "response_time": elapsed,
                        "answer_length": len(answer_md),
                        "answer": answer_md,
                        "answer_preview": answer_md[:200] if answer_md else "",
                        "quality_evaluation_error": str(e)
                    })
                    print(f"   Fallback: {'✅ PASS' if route_score == 1.0 else '❌ FAIL'} (routing only)")
            else:
                # Legacy routing-only evaluation
                route_match = actual_route == expected_route
                test_result.update({
                    "status": "PASS" if route_match else "FAIL",
                    "actual_route": actual_route,
                    "route_match": route_match,
                    "response_time": elapsed,
                    "answer_length": len(answer_md),
                    "answer": answer_md,
                    "answer_preview": answer_md[:200] if answer_md else ""
                })
                
                # Print legacy results
                if route_match:
                    print(f"✅ PASS - Route correct: {actual_route}")
                else:
                    print(f"❌ FAIL - Route mismatch: expected {expected_route}, got {actual_route}")
            
            print(f"⏱️  Response time: {elapsed:.2f}s")
            print(f"📝 Answer length: {len(answer_md)} chars")
            
            # Add to metrics collector
            if test_result.get('status') != 'ERROR':
                # Safely extract category from test_case
                category = 'UNKNOWN'
                if test_case and isinstance(test_case, dict):
                    test_id = test_case.get('id', '')
                    category = test_id[:1] if test_id else 'UNKNOWN'
                
                self.metrics_collector.add_result({
                    'response_time': test_result.get('response_time'),
                    'preferred_route': test_result.get('preferred_route'),
                    'actual_route': test_result.get('actual_route'),
                    'quality_score': test_result.get('quality_score'),
                    'status': test_result.get('status'),
                    'category': category
                })
            
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
                q.get('note', ''),
                test_case=q  # Pass full test case for two-tier evaluation
            )
            category_results.append(result)
            
            # Small delay between tests
            time.sleep(0.5)
        
        # Category summary
        passed = sum(1 for r in category_results if r.get('status') in ['PASS', 'PERFECT', 'ACCEPTABLE'])
        failed = sum(1 for r in category_results if r.get('status') in ['FAIL', 'FAILED'])
        errors = sum(1 for r in category_results if r.get('status') == 'ERROR')
        
        print(f"\n\n{'='*80}")
        print(f"📊 CATEGORY SUMMARY: {category_name}")
        print(f"{'='*80}")
        
        if self.use_quality_evaluation and any('quality_score' in r for r in category_results):
            # Two-tier summary
            perfect = sum(1 for r in category_results if r.get('status') == 'PERFECT')
            acceptable = sum(1 for r in category_results if r.get('status') == 'ACCEPTABLE')
            failed_qual = sum(1 for r in category_results if r.get('status') == 'FAILED')
            
            print(f"  ⭐ Perfect: {perfect} (optimal routing + excellent quality)")
            print(f"  ✅ Acceptable: {acceptable} (user satisfaction met)")
            print(f"  ❌ Failed: {failed_qual} (below threshold)")
            print(f"  ⚠️  Errors: {errors}")
            print(f"  📈 User Satisfaction Rate: {(perfect+acceptable)/(perfect+acceptable+failed_qual+errors)*100:.1f}%" if (perfect+acceptable+failed_qual+errors) > 0 else "  N/A")
            
            # Quality metrics
            quality_scores = [r['quality_score'] for r in category_results if 'quality_score' in r]
            if quality_scores:
                avg_quality = sum(quality_scores) / len(quality_scores)
                print(f"  📊 Average Quality Score: {avg_quality:.3f}")
            
            # Routing metrics
            route_scores = [r['route_score'] for r in category_results if 'route_score' in r]
            if route_scores:
                avg_route = sum(route_scores) / len(route_scores)
                print(f"  🛤️  Average Routing Score: {avg_route:.3f}")
        else:
            # Legacy summary
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
        """Print comprehensive test report with two-tier metrics"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        total = len(self.results)
        
        print(f"\n\n{'#'*80}")
        print(f"# FINAL TEST REPORT")
        print(f"{'#'*80}")
        print(f"\n⏱️  Duration: {duration:.2f}s")
        print(f"📊 Total Tests: {total}")
        
        if self.use_quality_evaluation and any('quality_score' in r for r in self.results):
            # Two-tier report
            perfect = sum(1 for r in self.results if r.get('status') == 'PERFECT')
            acceptable = sum(1 for r in self.results if r.get('status') == 'ACCEPTABLE')
            failed = sum(1 for r in self.results if r.get('status') == 'FAILED')
            errors = sum(1 for r in self.results if r.get('status') == 'ERROR')
            
            print(f"\n🎯 TWO-TIER EVALUATION RESULTS:")
            print(f"   ⭐ Perfect: {perfect} ({perfect/total*100:.1f}%)")
            print(f"      • Optimal routing + excellent answer quality")
            print(f"   ✅ Acceptable: {acceptable} ({acceptable/total*100:.1f}%)")
            print(f"      • User satisfaction threshold met (quality ≥0.70)")
            print(f"   ❌ Failed: {failed} ({failed/total*100:.1f}%)")
            print(f"      • Below user satisfaction threshold")
            print(f"   ⚠️  Errors: {errors} ({errors/total*100:.1f}%)")
            print(f"\n📈 USER SATISFACTION RATE: {(perfect+acceptable)/total*100:.1f}%")
            print(f"   (Perfect + Acceptable cases)")
            
            # Detailed metrics
            quality_scores = [r['quality_score'] for r in self.results if 'quality_score' in r]
            route_scores = [r['route_score'] for r in self.results if 'route_score' in r]
            overall_scores = [r['overall_score'] for r in self.results if 'overall_score' in r]
            
            if quality_scores:
                avg_quality = sum(quality_scores) / len(quality_scores)
                print(f"\n📊 QUALITY METRICS (70% weight):")
                print(f"   Average Quality Score: {avg_quality:.3f}")
                print(f"   Quality ≥0.85 (Excellent): {sum(1 for s in quality_scores if s >= 0.85)} tests")
                print(f"   Quality ≥0.70 (Acceptable): {sum(1 for s in quality_scores if s >= 0.70)} tests")
                print(f"   Quality <0.70 (Poor): {sum(1 for s in quality_scores if s < 0.70)} tests")
            
            if route_scores:
                avg_route = sum(route_scores) / len(route_scores)
                perfect_routing = sum(1 for s in route_scores if s == 1.0)
                acceptable_routing = sum(1 for s in route_scores if s == 0.7)
                wrong_routing = sum(1 for s in route_scores if s == 0.0)
                print(f"\n🛤️  ROUTING METRICS (30% weight):")
                print(f"   Average Routing Score: {avg_route:.3f}")
                print(f"   Perfect Routing: {perfect_routing} ({perfect_routing/len(route_scores)*100:.1f}%)")
                print(f"   Acceptable Alternative: {acceptable_routing} ({acceptable_routing/len(route_scores)*100:.1f}%)")
                print(f"   Wrong Routing: {wrong_routing} ({wrong_routing/len(route_scores)*100:.1f}%)")
            
            if overall_scores:
                avg_overall = sum(overall_scores) / len(overall_scores)
                print(f"\n🎯 COMBINED SCORE:")
                print(f"   Average Overall Score: {avg_overall:.3f}")
                print(f"   (0.3 × routing + 0.7 × quality)")
            
            # Key Insight: Routing vs Quality Analysis
            if quality_scores and route_scores:
                # Cases where routing failed but quality high
                quality_saves = sum(1 for r in self.results 
                                   if r.get('route_score', 1.0) < 1.0 
                                   and r.get('quality_score', 0) >= 0.70
                                   and r.get('status') == 'ACCEPTABLE')
                print(f"\n💡 KEY INSIGHT:")
                print(f"   {quality_saves} cases: Non-optimal routing but ACCEPTABLE answer quality")
                print(f"   → Answer quality compensated for routing inefficiency")
                print(f"   → User satisfied despite routing errors")
            
            # Failed tests details
            if failed > 0:
                print(f"\n❌ FAILED TESTS (quality < 0.70 or unacceptable routing):")
                for r in self.results:
                    if r.get('status') == 'FAILED':
                        q_score = r.get('quality_score', 0)
                        r_score = r.get('route_score', 0)
                        print(f"   [{r['id']}] {r['query'][:50]}...")
                        print(f"      Quality: {q_score:.2f}, Routing: {r_score:.2f}, Route: {r.get('actual_route', 'unknown')}")
        else:
            # Legacy report
            passed = sum(1 for r in self.results if r.get('status') == 'PASS')
            failed = sum(1 for r in self.results if r.get('status') == 'FAIL')
            errors = sum(1 for r in self.results if r.get('status') == 'ERROR')
            
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
        errors = sum(1 for r in self.results if r.get('status') == 'ERROR')
        if errors > 0:
            print(f"\n⚠️  ERROR TESTS:")
            for r in self.results:
                if r.get('status') == 'ERROR':
                    print(f"   [{r['id']}] {r['query'][:50]}...")
                    print(f"      Error: {r.get('error', 'Unknown error')}")
        
        # Performance stats
        response_times = [r.get('response_time', 0) for r in self.results if 'response_time' in r]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            print(f"\n⚡ PERFORMANCE:")
            print(f"   Average response time: {avg_time:.2f}s")
            print(f"   Fastest: {min(response_times):.2f}s")
            print(f"   Slowest: {max(response_times):.2f}s")
        
        print(f"\n{'#'*80}\n")
        
        # Print advanced metrics
        if self.use_quality_evaluation and hasattr(self.metrics_collector, 'results') and len(self.metrics_collector.results) > 0:
            print(f"\n{'='*80}")
            print("📊 ADVANCED EVALUATION METRICS")
            print(f"{'='*80}\n")
            
            try:
                # Compute and print all metrics
                metrics = self.metrics_collector.compute_all_metrics()
                self.metrics_collector.print_all_metrics()
            except Exception as e:
                print(f"⚠️  Could not compute advanced metrics: {e}")
        
        # Save results
        self.save_results()
    
    def save_results(self):
        """Save test results to JSON and CSV files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON (complete data)
        json_filename = f"test_results_{timestamp}.json"
        
        # Compute summary statistics
        total = len(self.results)
        if self.use_quality_evaluation and any('quality_score' in r for r in self.results):
            perfect = sum(1 for r in self.results if r.get('status') == 'PERFECT')
            acceptable = sum(1 for r in self.results if r.get('status') == 'ACCEPTABLE')
            failed = sum(1 for r in self.results if r.get('status') == 'FAILED')
            errors = sum(1 for r in self.results if r.get('status') == 'ERROR')
            
            output = {
                "timestamp": self.start_time.isoformat(),
                "gradio_url": self.gradio_url,
                "evaluation_mode": "two-tier",
                "total_tests": total,
                "perfect": perfect,
                "acceptable": acceptable,
                "failed": failed,
                "errors": errors,
                "user_satisfaction_rate": (perfect + acceptable) / total if total > 0 else 0,
                "results": self.results
            }
            
            # Add advanced metrics if available
            if hasattr(self, 'advanced_metrics'):
                # Convert numpy arrays to lists for JSON serialization
                import numpy as np
                metrics_copy = {}
                for key, value in self.advanced_metrics.items():
                    if isinstance(value, dict):
                        metrics_copy[key] = {}
                        for k, v in value.items():
                            if isinstance(v, np.ndarray):
                                metrics_copy[key][k] = v.tolist()
                            else:
                                metrics_copy[key][k] = v
                    else:
                        metrics_copy[key] = value
                output["advanced_metrics"] = metrics_copy
        else:
            passed = sum(1 for r in self.results if r.get('status') == 'PASS')
            failed = sum(1 for r in self.results if r.get('status') == 'FAIL')
            errors = sum(1 for r in self.results if r.get('status') == 'ERROR')
            
            output = {
                "timestamp": self.start_time.isoformat(),
                "gradio_url": self.gradio_url,
                "evaluation_mode": "routing-only",
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "results": self.results
            }
        
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"💾 JSON results saved to: {json_filename}")
        
        # Save CSV (for easy analysis in Excel)
        csv_filename = f"test_results_{timestamp}.csv"
        try:
            import csv
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                if self.use_quality_evaluation and any('quality_score' in r for r in self.results):
                    # Two-tier CSV format with advanced metrics
                    fieldnames = ['id', 'query', 'actual_route', 'preferred_route', 'acceptable_routes',
                                 'route_score', 'route_status', 'quality_score', 'semantic_similarity',
                                 'information_completeness', 'factual_accuracy', 'presentation_quality',
                                 'overall_score', 'status', 'response_time', 'answer_length', 'note']
                    
                    # Add summary metrics to first row as comment (for Excel analysis)
                    if hasattr(self, 'advanced_metrics'):
                        metrics = self.advanced_metrics
                        f.write(f"# Advanced Metrics Summary\n")
                        f.write(f"# P95 Latency: {metrics['latency']['p95']:.3f}s\n")
                        f.write(f"# Macro F1: {metrics['classification']['macro_f1']:.3f}\n")
                        f.write(f"# Routing Accuracy: {metrics['classification']['accuracy']:.2%}\n")
                        f.write(f"# Quality Saves Routing: {metrics['quality_routing_correlation']['quality_saves_routing']} cases\n")
                        f.write("#\n")
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for r in self.results:
                        row = {
                            'id': r.get('id', ''),
                            'query': r.get('query', ''),
                            'actual_route': r.get('actual_route', ''),
                            'preferred_route': r.get('preferred_route', ''),
                            'acceptable_routes': ','.join(r.get('acceptable_routes', [])),
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
                    # Legacy CSV format
                    fieldnames = ['id', 'query', 'expected_route', 'actual_route', 'route_match',
                                 'status', 'response_time', 'answer_length', 'note']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for r in self.results:
                        row = {k: r.get(k, '') for k in fieldnames}
                        writer.writerow(row)
            
            print(f"💾 CSV results saved to: {csv_filename}")
        except Exception as e:
            print(f"⚠️  Failed to save CSV: {e}")


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
