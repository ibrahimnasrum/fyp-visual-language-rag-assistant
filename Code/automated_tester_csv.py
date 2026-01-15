"""
Automated Question Tester with CSV Export
Tests ALL questions automatically and stores results in CSV format
Like a comprehensive test log that you can review in Excel

Usage:
    python automated_tester_csv.py              # Test all questions
    python automated_tester_csv.py --quick      # Test 10 questions only
    python automated_tester_csv.py --category sales  # Test sales only
"""

import sys
import time
import csv
import re
from datetime import datetime
from pathlib import Path

# Import the bot's functions directly (bypass Gradio UI)
sys.path.insert(0, str(Path(__file__).parent))
import importlib.util
spec = importlib.util.spec_from_file_location(
    "bot_module",
    str(Path(__file__).parent / "oneclick_my_retailchain_v8.2_models_logging.py")
)
bot_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bot_module)

# Import functions from module
rag_query_ui = bot_module.rag_query_ui
generate_ceo_followup_questions = bot_module.generate_ceo_followup_questions

# Test question database - ALL 57 questions from MASTER_QUESTION_DATABASE.md
TEST_QUESTIONS = {
    "UI_EXAMPLES": [
        {"id": "UI01", "q": "sales bulan 2024-06 berapa?", "route": "sales_kpi"},
        {"id": "UI02", "q": "banding sales bulan ni vs bulan lepas", "route": "sales_kpi"},
        {"id": "UI03", "q": "top 3 product bulan 2024-06", "route": "sales_kpi"},
        {"id": "UI04", "q": "sales ikut state bulan 2024-06", "route": "sales_kpi"},
        {"id": "UI05", "q": "headcount ikut state", "route": "hr_kpi"},
        {"id": "UI06", "q": "which age group has highest attrition?", "route": "hr_kpi"},
        {"id": "UI07", "q": "What is the annual leave entitlement per year?", "route": "rag_docs"},
    ],
    "SALES": [
        {"id": "S01", "q": "sales bulan 2024-06 berapa?", "route": "sales_kpi"},
        {"id": "S02", "q": "Total sales June 2024", "route": "sales_kpi"},
        {"id": "S03", "q": "revenue bulan 2024-05", "route": "sales_kpi"},
        {"id": "S04", "q": "banding sales bulan 2024-06 vs 2024-05", "route": "sales_kpi"},
        {"id": "S05", "q": "Compare June vs May sales", "route": "sales_kpi"},
        {"id": "S06", "q": "sales trend dari January hingga June 2024", "route": "sales_kpi"},
        {"id": "S07", "q": "top 3 product bulan 2024-06", "route": "sales_kpi"},
        {"id": "S08", "q": "Show top 5 products in June", "route": "sales_kpi"},
        {"id": "S09", "q": "worst performing product bulan 2024-06", "route": "sales_kpi"},
        {"id": "S10", "q": "sales state Selangor bulan 2024-06 berapa?", "route": "sales_kpi"},
        {"id": "S11", "q": "sales ikut state bulan 2024-06", "route": "sales_kpi"},
        {"id": "S12", "q": "Cheese Burger sales in June 2024", "route": "sales_kpi"},
        {"id": "S13", "q": "breakdown sales by product June", "route": "sales_kpi"},
        {"id": "S14", "q": "sales performance by state", "route": "sales_kpi"},
        {"id": "S15", "q": "sales bulan July 2024", "route": "sales_kpi"},
    ],
    "HR": [
        {"id": "H01", "q": "headcount berapa?", "route": "hr_kpi"},
        {"id": "H02", "q": "total employees", "route": "hr_kpi"},
        {"id": "H03", "q": "headcount ikut state", "route": "hr_kpi"},
        {"id": "H04", "q": "How many employees in Selangor?", "route": "hr_kpi"},
        {"id": "H05", "q": "headcount by department", "route": "hr_kpi"},
        {"id": "H06", "q": "berapa staff kitchen?", "route": "hr_kpi"},
        {"id": "H07", "q": "average employee tenure", "route": "hr_kpi"},
        {"id": "H08", "q": "staff with more than 5 years", "route": "hr_kpi"},
        {"id": "H09", "q": "average salary by department", "route": "hr_kpi"},
        {"id": "H10", "q": "total payroll expense", "route": "hr_kpi"},
    ],
    "RAG": [
        {"id": "D01", "q": "What is the annual leave entitlement per year?", "route": "rag_docs"},
        {"id": "D02", "q": "refund policy apa?", "route": "rag_docs"},
        {"id": "D03", "q": "how to request emergency leave", "route": "rag_docs"},
        {"id": "D04", "q": "maternity leave duration", "route": "rag_docs"},
        {"id": "D05", "q": "company profile", "route": "rag_docs"},
        {"id": "D06", "q": "how many branches we have?", "route": "rag_docs"},
        {"id": "D07", "q": "what products do we sell?", "route": "rag_docs"},
        {"id": "D08", "q": "what is the SOP for handling customer complaints?", "route": "rag_docs"},
        {"id": "D09", "q": "opening hours for KL branch", "route": "rag_docs"},
        {"id": "D10", "q": "Penang branch manager siapa?", "route": "rag_docs"},
        {"id": "D11", "q": "how to escalate an incident", "route": "rag_docs"},
        {"id": "D12", "q": "performance review process", "route": "rag_docs"},
        {"id": "D13", "q": "Why did sales drop in Selangor?", "route": "rag_docs"},
        {"id": "D14", "q": "How can we improve Cheese Burger sales?", "route": "rag_docs"},
        {"id": "D15", "q": "What happened on June 15, 2024?", "route": "rag_docs"},
        {"id": "D16", "q": "Tell me about competitor pricing", "route": "rag_docs"},
    ],
    "ROBUSTNESS": [
        {"id": "R01", "q": "top products", "route": "sales_kpi"},
        {"id": "R02", "q": "sales", "route": "sales_kpi"},
        {"id": "R03", "q": "staff", "route": "hr_kpi"},
        {"id": "R04", "q": "salse bulan 2024-06", "route": "sales_kpi"},
        {"id": "R05", "q": "headcont by stat", "route": "hr_kpi"},
        {"id": "R06", "q": "What's the weather today?", "route": "rag_docs"},
        {"id": "R07", "q": "Can you book a meeting?", "route": "rag_docs"},
        {"id": "R08", "q": "berapa sales for Cheese Burger in Mei 2024?", "route": "sales_kpi"},
        {"id": "R09", "q": "top 3 produk dengan highest revenue", "route": "sales_kpi"},
    ],
    "CEO_STRATEGIC": [
        # GROWTH & TRENDS (6 questions)
        {"id": "CEO01", "q": "Show me monthly revenue growth from January to June 2024", "route": "sales_kpi"},
        {"id": "CEO02", "q": "Which month had the highest sales in 2024?", "route": "sales_kpi"},
        {"id": "CEO03", "q": "What drove our revenue change from May to June?", "route": "sales_kpi"},
        {"id": "CEO04", "q": "Compare Q1 vs Q2 2024 total sales", "route": "sales_kpi"},
        {"id": "CEO05", "q": "Are we growing or declining overall from Jan to June?", "route": "sales_kpi"},
        {"id": "CEO06", "q": "Which product is growing fastest in recent months?", "route": "sales_kpi"},
        
        # EFFICIENCY & PRODUCTIVITY (5 questions)
        {"id": "CEO07", "q": "What's the average sales per employee?", "route": "sales_kpi"},
        {"id": "CEO08", "q": "Who is our top performing employee by revenue?", "route": "sales_kpi"},
        {"id": "CEO09", "q": "Which branch generates most revenue per staff member?", "route": "sales_kpi"},
        {"id": "CEO10", "q": "How many employees work overtime by department?", "route": "hr_kpi"},
        {"id": "CEO11", "q": "Which branch has the most employees?", "route": "hr_kpi"},
        
        # RISK IDENTIFICATION (5 questions)
        {"id": "CEO12", "q": "Which products are declining in sales from Q1 to Q2?", "route": "sales_kpi"},
        {"id": "CEO13", "q": "Show me bottom 3 branches by revenue", "route": "sales_kpi"},
        {"id": "CEO14", "q": "Which department has the highest attrition rate?", "route": "hr_kpi"},
        {"id": "CEO15", "q": "Which state has the lowest sales performance?", "route": "sales_kpi"},
        {"id": "CEO16", "q": "How many managers have left the company?", "route": "hr_kpi"},
        
        # PORTFOLIO MIX (5 questions)
        {"id": "CEO17", "q": "What percentage of our sales come from delivery?", "route": "sales_kpi"},
        {"id": "CEO18", "q": "What percentage of revenue comes from our top 3 products?", "route": "sales_kpi"},
        {"id": "CEO19", "q": "Show me revenue breakdown by state as percentages", "route": "sales_kpi"},
        {"id": "CEO20", "q": "What's our payment method distribution?", "route": "sales_kpi"},
        {"id": "CEO21", "q": "Is delivery growing faster than dine-in?", "route": "sales_kpi"},
        
        # PROFITABILITY (4 questions)
        {"id": "CEO22", "q": "What's our average transaction value by channel?", "route": "sales_kpi"},
        {"id": "CEO23", "q": "Which products have the highest unit price?", "route": "sales_kpi"},
        {"id": "CEO24", "q": "Which channel generates the highest revenue per transaction?", "route": "sales_kpi"},
        {"id": "CEO25", "q": "Show me average unit price trends from Jan to June", "route": "sales_kpi"},
        
        # HR ANALYTICS (5 questions)
        {"id": "CEO26", "q": "What's the average salary by department?", "route": "hr_kpi"},
        {"id": "CEO27", "q": "Show me salary range for kitchen staff", "route": "hr_kpi"},
        {"id": "CEO28", "q": "How many employees have been here for 5+ years?", "route": "hr_kpi"},
        {"id": "CEO29", "q": "What's the age distribution of our workforce?", "route": "hr_kpi"},
        {"id": "CEO30", "q": "What's the average tenure for managers?", "route": "hr_kpi"},
        
        # BENCHMARKING (4 questions)
        {"id": "CEO31", "q": "Which branches perform above the average?", "route": "sales_kpi"},
        {"id": "CEO32", "q": "Compare Selangor vs Penang total sales", "route": "sales_kpi"},
        {"id": "CEO33", "q": "What's the revenue gap between best and worst branch?", "route": "sales_kpi"},
        {"id": "CEO34", "q": "Compare all key metrics: June vs May 2024", "route": "sales_kpi"},
        
        # STRATEGIC PLANNING (3 questions)
        {"id": "CEO35", "q": "Which state shows the highest growth rate?", "route": "sales_kpi"},
        {"id": "CEO36", "q": "Should we focus more on delivery or dine-in based on performance?", "route": "sales_kpi"},
        {"id": "CEO37", "q": "Which product category should we expand?", "route": "sales_kpi"},
    ]
}

class AutomatedTester:
    """Automated testing with CSV export"""
    
    def __init__(self, output_file="test_results.csv"):
        self.output_file = output_file
        self.results = []
        self.session_start = datetime.now()
        
    def test_question(self, test_data):
        """Test a single question and return results"""
        qid = test_data['id']
        question = test_data['q']
        expected_route = test_data['route']
        
        print(f"\n[{qid}] Testing: {question[:60]}...")
        
        result = {
            'test_id': qid,
            'question': question,
            'expected_route': expected_route,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            start_time = time.time()
            
            # Call the UI function to get full response
            # rag_query_ui yields (status_html, answer_md, trace_html, followup_list)
            # Use mistral:latest which is slightly smaller (4.4GB vs 4.7GB)
            outputs = list(rag_query_ui(
                user_input=question,
                model_name="mistral:latest",  # Using mistral for better memory stability
                has_image=False,
                chat_id="",
                conversation_history=[]
            ))
            
            # Get final output (last yield)
            if outputs:
                final_output = outputs[-1]
                status_html = final_output[0] if len(final_output) > 0 else ""
                answer_md = final_output[1] if len(final_output) > 1 else ""
                tool_trace = final_output[2] if len(final_output) > 2 else ""
                followups = final_output[3] if len(final_output) > 3 else []
                
                elapsed = time.time() - start_time
                
                # Extract actual route from status_html (contains route badges)
                actual_route = "unknown"
                if "sales_kpi" in status_html or "KPI" in status_html:
                    actual_route = "sales_kpi" if "sales" in answer_md.lower() or "revenue" in answer_md.lower() else "hr_kpi"
                elif "RAG" in status_html or "Document" in status_html:
                    actual_route = "rag_docs"
                elif "OCR" in status_html:
                    actual_route = "visual"
                
                # Try to extract route from trace_html if available
                if "sales_kpi" in tool_trace.lower():
                    actual_route = "sales_kpi"
                elif "hr_kpi" in tool_trace.lower():
                    actual_route = "hr_kpi"
                elif "rag_docs" in tool_trace.lower():
                    actual_route = "rag_docs"
                    
                route_match = actual_route == expected_route
                
                # Extract answer preview (first 200 chars, no HTML)
                # Extract answer preview (first 200 chars)
                answer_preview = re.sub(r'\s+', ' ', answer_md[:200]).strip()
                
                # Get follow-up count
                followup_count = len(followups) if followups else 0
                followup_text = " | ".join(followups[:3]) if followups else ""
                
                # Determine status
                if route_match and answer_md and len(answer_md) > 50:
                    status = "PASS"
                elif not route_match:
                    status = "ROUTE_FAIL"
                elif not answer_md or len(answer_md) < 50:
                    status = "ANSWER_FAIL"
                else:
                    status = "PARTIAL"
                
                result.update({
                    'status': status,
                    'actual_route': actual_route,
                    'route_match': 'YES' if route_match else 'NO',
                    'response_time_sec': round(elapsed, 2),
                    'answer_length': len(answer_md),
                    'answer_preview': answer_preview,
                    'followup_count': followup_count,
                    'followup_preview': followup_text,
                    'error': ''
                })
                
                # Print summary
                status_emoji = "✅" if status == "PASS" else "⚠️" if status == "PARTIAL" else "❌"
                print(f"  {status_emoji} {status} - Route: {actual_route} - {elapsed:.1f}s - {followup_count} follow-ups")
                
            else:
                result.update({
                    'status': 'ERROR',
                    'actual_route': actual_route,
                    'route_match': 'YES' if route_match else 'NO',
                    'response_time_sec': time.time() - start_time,
                    'error': 'No output generated'
                })
                print(f"  ❌ ERROR - No output")
                
        except Exception as e:
            result.update({
                'status': 'ERROR',
                'actual_route': 'error',
                'route_match': 'NO',
                'response_time_sec': 0,
                'error': str(e)
            })
            print(f"  ❌ ERROR: {e}")
        
        self.results.append(result)
        return result
    
    def test_category(self, category_name, questions):
        """Test all questions in a category"""
        print(f"\n{'='*80}")
        print(f"TESTING CATEGORY: {category_name} ({len(questions)} questions)")
        print(f"{'='*80}")
        
        for i, q in enumerate(questions, 1):
            print(f"\nProgress: {i}/{len(questions)}")
            self.test_question(q)
            # ✅ Add delay between tests to prevent memory overload
            # Longer delay for RAG queries (model loading)
            if q.get('route') == 'rag_docs':
                time.sleep(1.5)  # 1.5s delay after RAG queries
            else:
                time.sleep(0.5)  # 0.5s delay for KPI queries
        
        # Category summary
        cat_results = [r for r in self.results if any(q['id'] == r['test_id'] for q in questions)]
        passed = sum(1 for r in cat_results if r['status'] == 'PASS')
        print(f"\n{category_name} Summary: {passed}/{len(cat_results)} passed")
    
    def test_all(self, categories=None):
        """Test all categories"""
        if categories:
            # Test specific categories
            for cat in categories:
                if cat.upper() in TEST_QUESTIONS:
                    self.test_category(cat.upper(), TEST_QUESTIONS[cat.upper()])
        else:
            # Test everything - ALL 57 questions
            for cat_name, questions in TEST_QUESTIONS.items():
                self.test_category(cat_name, questions)
    
    def save_to_csv(self):
        """Save results to CSV file"""
        if not self.results:
            print("No results to save")
            return
        
        # Define CSV columns
        fieldnames = [
            'test_id', 'question', 'expected_route', 'actual_route', 'route_match',
            'status', 'response_time_sec', 'answer_length', 'answer_preview',
            'followup_count', 'followup_preview', 'timestamp', 'error'
        ]
        
        with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.results)
        
        print(f"\n{'='*80}")
        print(f"✅ Results saved to: {self.output_file}")
        print(f"{'='*80}")
        print(f"📊 Open in Excel to review all answers and follow-ups")
        print(f"   - Total tests: {len(self.results)}")
        print(f"   - Passed: {sum(1 for r in self.results if r['status'] == 'PASS')}")
        print(f"   - Failed: {sum(1 for r in self.results if r['status'] in ['ROUTE_FAIL', 'ANSWER_FAIL', 'ERROR'])}")
        print(f"{'='*80}\n")
    
    def print_summary(self):
        """Print summary statistics"""
        duration = (datetime.now() - self.session_start).total_seconds()
        total = len(self.results)
        
        if total == 0:
            print("\nNo tests were run")
            return
        
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        route_fail = sum(1 for r in self.results if r['status'] == 'ROUTE_FAIL')
        answer_fail = sum(1 for r in self.results if r['status'] == 'ANSWER_FAIL')
        errors = sum(1 for r in self.results if r['status'] == 'ERROR')
        
        print(f"\n{'#'*80}")
        print(f"# FINAL SUMMARY")
        print(f"{'#'*80}")
        print(f"Duration: {duration:.1f}s")
        print(f"Total Tests: {total}")
        print(f"  ✅ PASSED: {passed} ({passed/total*100:.1f}%)")
        print(f"  ⚠️  ROUTE_FAIL: {route_fail} ({route_fail/total*100:.1f}%)")
        print(f"  ⚠️  ANSWER_FAIL: {answer_fail} ({answer_fail/total*100:.1f}%)")
        print(f"  ❌ ERRORS: {errors} ({errors/total*100:.1f}%)")
        
        # Average response time
        times = [r.get('response_time_sec', 0) for r in self.results if r.get('response_time_sec')]
        if times:
            print(f"\n⏱️  Response Times:")
            print(f"  Average: {sum(times)/len(times):.2f}s")
            print(f"  Fastest: {min(times):.2f}s")
            print(f"  Slowest: {max(times):.2f}s")
        
        # Follow-up stats
        followup_counts = [r.get('followup_count', 0) for r in self.results if 'followup_count' in r]
        if followup_counts:
            print(f"\n💡 Follow-ups:")
            print(f"  Average per question: {sum(followup_counts)/len(followup_counts):.1f}")
            print(f"  Questions with follow-ups: {sum(1 for c in followup_counts if c > 0)}/{len(followup_counts)}")
        
        print(f"\n{'#'*80}\n")


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Automated testing with CSV export')
    parser.add_argument('--category', choices=['ui_examples', 'sales', 'hr', 'rag', 'robustness', 'ceo_strategic'],
                       help='Test specific category')
    parser.add_argument('--output', default='test_results.csv', help='Output CSV filename')
    
    args = parser.parse_args()
    
    # Create output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"test_results_{timestamp}.csv"
    
    # Count total questions
    total_questions = sum(len(qs) for qs in TEST_QUESTIONS.values())
    
    print(f"\n{'#'*80}")
    print(f"# AUTOMATED QUESTION TESTER - ALL {total_questions} QUESTIONS")
    print(f"# Output: {output_file}")
    print(f"{'#'*80}\n")
    
    if args.category:
        cat_count = len(TEST_QUESTIONS[args.category.upper()])
        print(f"📋 CATEGORY MODE: Testing {args.category.upper()} ({cat_count} questions)\n")
    else:
        print(f"📋 FULL MODE: Testing ALL {total_questions} questions\n")
        print("   - UI Examples: 7 questions")
        print("   - Sales KPI: 15 questions")
        print("   - HR KPI: 10 questions")
        print("   - RAG/Docs: 16 questions")
        print("   - Robustness: 9 questions")
        print("   - CEO Strategic: 37 questions (NEW - Advanced executive analysis)")
        print(f"\n⏱️  Estimated time: ~25-35 minutes (depends on LLM speed)\n")
        print("⚠️  Press Ctrl+C to cancel.\n")
        time.sleep(3)
    
    # ✅ PRE-LOAD MODEL BEFORE BATCH TESTING
    print("\n" + "="*80)
    print("🔄 PRE-LOADING OLLAMA MODEL FOR BATCH TESTING")
    print("="*80)
    print("This ensures the model stays in memory and prevents loading errors...\n")
    
    # Import preload function from bot module
    model_loaded = False
    
    # Try loading mistral first (4.4GB - more likely to succeed with limited RAM)
    print("Attempting to load mistral:latest (4.4GB)...")
    preload_success = bot_module.preload_ollama_model("mistral:latest", keep_alive="30m")
    
    if preload_success:
        print("✅ Model mistral:latest pre-loaded successfully! Starting tests...\n")
        model_loaded = True
        time.sleep(1)
    else:
        # Try llama3 as fallback
        print("⚠️  mistral failed to load. Trying llama3:latest...")
        preload_success = bot_module.preload_ollama_model("llama3:latest", keep_alive="30m")
        if preload_success:
            print("✅ Model mistral:latest pre-loaded successfully! Starting tests...\n")
            model_loaded = True
            time.sleep(1)
        else:
            # Last resort: try llama3
            print("⚠️  mistral failed to load. Trying llama3:latest...")
            preload_success = bot_module.preload_ollama_model("llama3:latest", keep_alive="30m")
            if preload_success:
                print("✅ Model llama3:latest pre-loaded successfully! Starting tests...\n")
                model_loaded = True
                time.sleep(1)
    
    if not model_loaded:
        print("\n" + "="*80)
        print("⚠️  WARNING: Could not pre-load any model!")
        print("="*80)
        print("This may be due to low memory. Recommendations:")
        print("  1. Close other applications to free up RAM")
        print("  2. Restart Ollama: Run 'ollama serve' in a new terminal")
        print("  3. Check available memory: Should have >5GB free")
        print("  4. Test with smaller batches: --category flag")
        print("\nContinuing tests anyway... (expect some errors)\n")
        time.sleep(3)
    
    # Initialize tester
    tester = AutomatedTester(output_file)
    
    # Run tests
    try:
        if args.category:
            tester.test_all(categories=[args.category])
        else:
            tester.test_all()
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
    
    # Save results
    tester.save_to_csv()
    tester.print_summary()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
