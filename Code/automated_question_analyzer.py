"""
Automated Question Analyzer for CEO Bot v8.2
Tests ALL questions in the system and captures complete responses
Stores: Question + Full Answer + Follow-ups + Route + Timing + Accuracy

Usage:
    python automated_question_analyzer.py          # Test all questions
    python automated_question_analyzer.py --quick  # Test UI examples only
    python automated_question_analyzer.py --category sales  # Test sales questions only
"""

import sys
import time
import json
import argparse
from datetime import datetime
from pathlib import Path
from gradio_client import Client

# Question database
UI_EXAMPLES = [
    {"id": "UI01", "question": "sales bulan 2024-06 berapa?", "route": "sales_kpi", "priority": "CRITICAL"},
    {"id": "UI02", "question": "banding sales bulan ni vs bulan lepas", "route": "sales_kpi", "priority": "HIGH"},
    {"id": "UI03", "question": "top 3 product bulan 2024-06", "route": "sales_kpi", "priority": "CRITICAL"},
    {"id": "UI04", "question": "sales ikut state bulan 2024-06", "route": "sales_kpi", "priority": "HIGH"},
    {"id": "UI05", "question": "headcount ikut state", "route": "hr_kpi", "priority": "HIGH"},
    {"id": "UI06", "question": "which age group has highest attrition?", "route": "hr_kpi", "priority": "MEDIUM"},
    {"id": "UI07", "question": "What is the annual leave entitlement per year?", "route": "rag_docs", "priority": "CRITICAL"},
]

INVENTORY_SALES = [
    {"id": "S01", "question": "sales bulan 2024-06 berapa?", "route": "sales_kpi", "priority": "HIGH"},
    {"id": "S02", "question": "Total sales June 2024", "route": "sales_kpi", "priority": "HIGH"},
    {"id": "S03", "question": "revenue bulan 2024-05", "route": "sales_kpi", "priority": "MEDIUM"},
    {"id": "S04", "question": "banding sales bulan 2024-06 vs 2024-05", "route": "sales_kpi", "priority": "HIGH"},
    {"id": "S05", "question": "Compare June vs May sales", "route": "sales_kpi", "priority": "HIGH"},
    {"id": "S07", "question": "top 3 product bulan 2024-06", "route": "sales_kpi", "priority": "CRITICAL"},
    {"id": "S08", "question": "Show top 5 products in June", "route": "sales_kpi", "priority": "HIGH"},
    {"id": "S10", "question": "sales state Selangor bulan 2024-06 berapa?", "route": "sales_kpi", "priority": "HIGH"},
    {"id": "S11", "question": "sales ikut state bulan 2024-06", "route": "sales_kpi", "priority": "HIGH"},
    {"id": "S15", "question": "sales bulan July 2024", "route": "sales_kpi", "priority": "MEDIUM"},
]

INVENTORY_HR = [
    {"id": "H01", "question": "headcount berapa?", "route": "hr_kpi", "priority": "HIGH"},
    {"id": "H02", "question": "total employees", "route": "hr_kpi", "priority": "HIGH"},
    {"id": "H03", "question": "headcount ikut state", "route": "hr_kpi", "priority": "HIGH"},
    {"id": "H04", "question": "How many employees in Selangor?", "route": "hr_kpi", "priority": "MEDIUM"},
    {"id": "H06", "question": "berapa staff kitchen?", "route": "hr_kpi", "priority": "MEDIUM"},
]

INVENTORY_RAG = [
    {"id": "D01", "question": "What is the annual leave entitlement per year?", "route": "rag_docs", "priority": "CRITICAL"},
    {"id": "D02", "question": "refund policy apa?", "route": "rag_docs", "priority": "HIGH"},
    {"id": "D03", "question": "how to request emergency leave", "route": "rag_docs", "priority": "HIGH"},
    {"id": "D08", "question": "what is the SOP for handling customer complaints?", "route": "rag_docs", "priority": "HIGH"},
    {"id": "D13", "question": "Why did sales drop in Selangor?", "route": "rag_docs", "priority": "HIGH"},
]

INVENTORY_ROBUSTNESS = [
    {"id": "R01", "question": "top products", "route": "sales_kpi", "priority": "CRITICAL", "note": "Ambiguous"},
    {"id": "R02", "question": "sales", "route": "sales_kpi", "priority": "HIGH", "note": "Too vague"},
    {"id": "R04", "question": "salse bulan 2024-06", "route": "sales_kpi", "priority": "MEDIUM", "note": "Typo"},
    {"id": "R08", "question": "berapa sales for Cheese Burger in Mei 2024?", "route": "sales_kpi", "priority": "MEDIUM"},
]


class QuestionAnalyzer:
    """Comprehensive question testing and analysis"""
    
    def __init__(self, gradio_url="http://127.0.0.1:7866"):
        self.gradio_url = gradio_url
        self.client = None
        self.results = []
        self.session_start = datetime.now()
        
    def connect(self):
        """Connect to Gradio app"""
        print(f"\n{'='*80}")
        print(f"🔌 CONNECTING TO CEO BOT")
        print(f"{'='*80}")
        print(f"URL: {self.gradio_url}")
        print(f"Time: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")
        
        try:
            self.client = Client(self.gradio_url)
            print("✅ Connected successfully!")
            
            # List available API endpoints
            print("\n📋 Available API Endpoints:")
            try:
                info = self.client.view_api()
                print(f"   {info}\n")
            except:
                pass
            
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            print("\n💡 Make sure CEO Bot is running:")
            print("   python oneclick_my_retailchain_v8.2_models_logging.py\n")
            return False
    
    def test_question(self, question_data):
        """Test a single question and capture complete response"""
        qid = question_data['id']
        question = question_data['question']
        expected_route = question_data['route']
        priority = question_data.get('priority', 'MEDIUM')
        note = question_data.get('note', '')
        
        print(f"\n{'='*80}")
        print(f"🧪 TEST [{qid}] - {priority}")
        print(f"{'='*80}")
        print(f"Question: {question}")
        print(f"Expected Route: {expected_route}")
        if note:
            print(f"Note: {note}")
        print(f"{'='*80}")
        
        result = {
            "id": qid,
            "question": question,
            "expected_route": expected_route,
            "priority": priority,
            "note": note,
            "timestamp": datetime.now().isoformat(),
        }
        
        try:
            # Submit query and measure time
            print("⏱️  Submitting...")
            start_time = time.time()
            
            response = self.client.predict(
                question,  # txt
                None,      # img
                "qwen2.5:7b",  # model
                None,      # current_chat_id
                [],        # chat_messages
                [],        # chat_traces
                api_name="/submit"
            )
            
            elapsed = time.time() - start_time
            
            # Parse response components
            status_html = response[0] if len(response) > 0 else ""
            answer_md = response[1] if len(response) > 1 else ""
            tool_trace = response[2] if len(response) > 2 else ""
            followups_list = response[3] if len(response) > 3 else []
            
            # Extract actual route from status HTML
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
            route_correct = actual_route == expected_route
            
            # Store comprehensive results
            result.update({
                "status": "PASS" if route_correct else "ROUTE_MISMATCH",
                "actual_route": actual_route,
                "route_correct": route_correct,
                "response_time_sec": round(elapsed, 2),
                "answer_full": answer_md,
                "answer_length": len(answer_md),
                "answer_preview": answer_md[:300] + "..." if len(answer_md) > 300 else answer_md,
                "followups_generated": followups_list,
                "followup_count": len(followups_list) if followups_list else 0,
                "tool_trace": tool_trace,
            })
            
            # Display results
            if route_correct:
                print(f"✅ ROUTE CORRECT: {actual_route}")
            else:
                print(f"❌ ROUTE MISMATCH: expected {expected_route}, got {actual_route}")
            
            print(f"⏱️  Response Time: {elapsed:.2f}s")
            print(f"📝 Answer Length: {len(answer_md)} chars")
            
            if followups_list:
                print(f"\n💡 Follow-ups Generated ({len(followups_list)}):")
                for i, fq in enumerate(followups_list, 1):
                    print(f"   {i}. {fq}")
            else:
                print(f"\n⚠️  No follow-ups generated")
            
            print(f"\n📄 Answer Preview:")
            preview = answer_md[:200].replace('\n', ' ')
            print(f"   {preview}...")
            
        except Exception as e:
            result.update({
                "status": "ERROR",
                "error": str(e),
                "error_type": type(e).__name__,
                "actual_route": "error",
                "route_correct": False
            })
            print(f"❌ ERROR: {e}")
        
        self.results.append(result)
        return result
    
    def test_category(self, category_name, questions):
        """Test all questions in a category"""
        print(f"\n\n{'#'*80}")
        print(f"# CATEGORY: {category_name}")
        print(f"# Questions: {len(questions)}")
        print(f"{'#'*80}\n")
        
        for i, q in enumerate(questions, 1):
            print(f"\nProgress: {i}/{len(questions)}")
            self.test_question(q)
            
            # Small delay between tests to avoid overwhelming the system
            if i < len(questions):
                time.sleep(0.5)
        
        # Category summary
        self.print_category_summary(category_name)
    
    def print_category_summary(self, category_name):
        """Print summary for completed category"""
        category_results = [r for r in self.results if r['id'].startswith(category_name[0])]
        
        if not category_results:
            return
        
        total = len(category_results)
        passed = sum(1 for r in category_results if r['status'] == 'PASS')
        route_mismatch = sum(1 for r in category_results if r['status'] == 'ROUTE_MISMATCH')
        errors = sum(1 for r in category_results if r['status'] == 'ERROR')
        
        avg_time = sum(r.get('response_time_sec', 0) for r in category_results) / total
        
        print(f"\n{'='*80}")
        print(f"📊 CATEGORY SUMMARY: {category_name}")
        print(f"{'='*80}")
        print(f"Total Tests: {total}")
        print(f"  ✅ Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"  ⚠️  Route Mismatch: {route_mismatch} ({route_mismatch/total*100:.1f}%)")
        print(f"  ❌ Errors: {errors} ({errors/total*100:.1f}%)")
        print(f"  ⏱️  Avg Response Time: {avg_time:.2f}s")
        print(f"{'='*80}\n")
    
    def test_all(self, categories=None):
        """Test all question categories"""
        test_plan = {
            "UI_EXAMPLES": UI_EXAMPLES,
            "SALES": INVENTORY_SALES,
            "HR": INVENTORY_HR,
            "RAG": INVENTORY_RAG,
            "ROBUSTNESS": INVENTORY_ROBUSTNESS
        }
        
        if categories:
            test_plan = {k: v for k, v in test_plan.items() if k in categories}
        
        for category, questions in test_plan.items():
            self.test_category(category, questions)
        
        self.print_final_report()
    
    def print_final_report(self):
        """Generate comprehensive final report"""
        duration = (datetime.now() - self.session_start).total_seconds()
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        route_mismatch = sum(1 for r in self.results if r['status'] == 'ROUTE_MISMATCH')
        errors = sum(1 for r in self.results if r['status'] == 'ERROR')
        
        print(f"\n\n{'#'*80}")
        print(f"# FINAL ANALYSIS REPORT")
        print(f"{'#'*80}\n")
        print(f"Session Duration: {duration:.1f}s")
        print(f"Total Questions Tested: {total}")
        print(f"\n📊 Results Breakdown:")
        print(f"  ✅ PASSED: {passed} ({passed/total*100:.1f}%)")
        print(f"  ⚠️  ROUTE MISMATCH: {route_mismatch} ({route_mismatch/total*100:.1f}%)")
        print(f"  ❌ ERRORS: {errors} ({errors/total*100:.1f}%)")
        
        # Performance stats
        response_times = [r.get('response_time_sec', 0) for r in self.results if 'response_time_sec' in r]
        if response_times:
            print(f"\n⚡ Performance:")
            print(f"  Average: {sum(response_times)/len(response_times):.2f}s")
            print(f"  Fastest: {min(response_times):.2f}s")
            print(f"  Slowest: {max(response_times):.2f}s")
        
        # Follow-up stats
        with_followups = sum(1 for r in self.results if r.get('followup_count', 0) > 0)
        total_followups = sum(r.get('followup_count', 0) for r in self.results)
        print(f"\n💡 Follow-ups:")
        print(f"  Questions with follow-ups: {with_followups}/{total} ({with_followups/total*100:.1f}%)")
        print(f"  Total follow-ups generated: {total_followups}")
        print(f"  Average per question: {total_followups/total:.1f}")
        
        # Route mismatch details
        if route_mismatch > 0:
            print(f"\n⚠️  ROUTE MISMATCHES:")
            for r in self.results:
                if r['status'] == 'ROUTE_MISMATCH':
                    print(f"   [{r['id']}] {r['question'][:50]}")
                    print(f"       Expected: {r['expected_route']}, Got: {r['actual_route']}")
        
        # Errors details
        if errors > 0:
            print(f"\n❌ ERRORS:")
            for r in self.results:
                if r['status'] == 'ERROR':
                    print(f"   [{r['id']}] {r['question'][:50]}")
                    print(f"       Error: {r.get('error', 'Unknown error')}")
        
        print(f"\n{'#'*80}\n")
        
        # Save results
        self.save_results()
    
    def save_results(self):
        """Save comprehensive results to JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"question_analysis_{timestamp}.json"
        
        output = {
            "session_info": {
                "start_time": self.session_start.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_seconds": (datetime.now() - self.session_start).total_seconds(),
                "gradio_url": self.gradio_url
            },
            "summary": {
                "total_questions": len(self.results),
                "passed": sum(1 for r in self.results if r['status'] == 'PASS'),
                "route_mismatch": sum(1 for r in self.results if r['status'] == 'ROUTE_MISMATCH'),
                "errors": sum(1 for r in self.results if r['status'] == 'ERROR'),
            },
            "detailed_results": self.results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to: {filename}")
        print(f"📊 Review the file to see full answers and follow-ups for each question\n")


def main():
    """Main execution with argument parsing"""
    parser = argparse.ArgumentParser(description='Analyze all questions in CEO Bot system')
    parser.add_argument('--quick', action='store_true', help='Test UI examples only (fast)')
    parser.add_argument('--category', choices=['sales', 'hr', 'rag', 'robustness', 'ui'], 
                       help='Test specific category only')
    parser.add_argument('--url', default='http://127.0.0.1:7866', help='Gradio URL')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = QuestionAnalyzer(gradio_url=args.url)
    
    if not analyzer.connect():
        return 1
    
    # Determine what to test
    if args.quick:
        print("📋 Quick Mode: Testing UI Examples only\n")
        analyzer.test_category("UI_EXAMPLES", UI_EXAMPLES)
        analyzer.print_final_report()
    elif args.category:
        category_map = {
            'sales': ('SALES', INVENTORY_SALES),
            'hr': ('HR', INVENTORY_HR),
            'rag': ('RAG', INVENTORY_RAG),
            'robustness': ('ROBUSTNESS', INVENTORY_ROBUSTNESS),
            'ui': ('UI_EXAMPLES', UI_EXAMPLES)
        }
        cat_name, cat_questions = category_map[args.category]
        print(f"📋 Testing {cat_name} category only\n")
        analyzer.test_category(cat_name, cat_questions)
        analyzer.print_final_report()
    else:
        print("📋 Full Mode: Testing ALL questions\n")
        print("⚠️  This will take approximately 5-10 minutes")
        print("⚠️  Each question takes 1-60 seconds depending on complexity\n")
        input("Press ENTER to start...")
        analyzer.test_all()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
