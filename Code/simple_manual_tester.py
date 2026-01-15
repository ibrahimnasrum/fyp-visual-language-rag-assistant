"""
Simple Question Tester - Manual Browser-Based Testing
Copy questions from here, paste into CEO Bot UI, record results manually

This is SIMPLER than automated testing - just use your browser!
"""

print("""
================================================================================
          CEO BOT v8.2 - COMPREHENSIVE QUESTION TEST GUIDE                 
                                                                           
  INSTRUCTIONS:                                                            
  1. Open http://127.0.0.1:7866 in your browser                          
  2. Copy each question below                                             
  3. Paste into chatbox and click Submit                                  
  4. Record: Route badge, Answer quality, Follow-ups generated            
  5. Check mark: [PASS] Accurate / [REVIEW] Needs review / [FAIL] Inaccurate          
================================================================================

""")

# Test categories with expected results
tests = {
    "*** CRITICAL TESTS (Must Pass) ***": [
        {
            "id": "UI01",
            "question": "sales bulan 2024-06 berapa?",
            "expected_route": "sales_kpi",
            "expected_answer": "Total sales for June 2024 with specific RM amount",
            "expected_followups": ["Compare with previous month", "Break down by state", "Show top 5 products"]
        },
        {
            "id": "UI03",
            "question": "top 3 product bulan 2024-06",
            "expected_route": "sales_kpi",
            "expected_answer": "Ranked list of top 3 products with sales amounts",
            "expected_followups": ["What's different about top performers?", "Compare top vs bottom"]
        },
        {
            "id": "UI07",
            "question": "What is the annual leave entitlement per year?",
            "expected_route": "rag_docs",
            "expected_answer": "Policy details from HR_Policy_MY.txt document",
            "expected_followups": ["What's the leave approval process?", "Any restrictions on leave timing?"]
        },
        {
            "id": "S07",
            "question": "Show top 5 products in June",
            "expected_route": "sales_kpi",
            "expected_answer": "Top 5 products ranked by sales (NOT top 3 - Bug #3 test)",
            "expected_followups": ["Product-related follow-ups"]
        },
    ],
    
    "*** SALES KPI TESTS ***": [
        {
            "id": "S01",
            "question": "sales bulan 2024-06 berapa?",
            "expected_route": "sales_kpi",
            "expected_answer": "Total sales amount in RM",
        },
        {
            "id": "S02",
            "question": "Total sales June 2024",
            "expected_route": "sales_kpi",
            "expected_answer": "Same as S01 (English version)",
        },
        {
            "id": "S04",
            "question": "banding sales bulan 2024-06 vs 2024-05",
            "expected_route": "sales_kpi",
            "expected_answer": "Comparison table with June vs May, difference, % change",
        },
        {
            "id": "S10",
            "question": "sales state Selangor bulan 2024-06 berapa?",
            "expected_route": "sales_kpi",
            "expected_answer": "Selangor-only sales for June 2024",
        },
        {
            "id": "S11",
            "question": "sales ikut state bulan 2024-06",
            "expected_route": "sales_kpi",
            "expected_answer": "Breakdown by all states for June 2024",
        },
        {
            "id": "S15",
            "question": "sales bulan July 2024",
            "expected_route": "sales_kpi",
            "expected_answer": "Should say 'No data for July 2024' or similar (future month test)",
        },
    ],
    
    "*** HR KPI TESTS ***": [
        {
            "id": "H01",
            "question": "headcount berapa?",
            "expected_route": "hr_kpi",
            "expected_answer": "Total employee count: 820",
        },
        {
            "id": "H02",
            "question": "total employees",
            "expected_route": "hr_kpi",
            "expected_answer": "Same as H01 (English version)",
        },
        {
            "id": "H03",
            "question": "headcount ikut state",
            "expected_route": "hr_kpi",
            "expected_answer": "Employee count breakdown by state",
        },
        {
            "id": "H06",
            "question": "berapa staff kitchen?",
            "expected_route": "hr_kpi",
            "expected_answer": "Kitchen department employee count",
        },
    ],
    
    "*** RAG/DOCUMENT TESTS ***": [
        {
            "id": "D01",
            "question": "What is the annual leave entitlement per year?",
            "expected_route": "rag_docs",
            "expected_answer": "Policy from HR_Policy_MY.txt (check if grounded in document)",
        },
        {
            "id": "D02",
            "question": "refund policy apa?",
            "expected_route": "rag_docs",
            "expected_answer": "Refund policy from company documents",
        },
        {
            "id": "D03",
            "question": "how to request emergency leave",
            "expected_route": "rag_docs",
            "expected_answer": "Emergency leave process/steps from policy",
        },
        {
            "id": "D08",
            "question": "what is the SOP for handling customer complaints?",
            "expected_route": "rag_docs",
            "expected_answer": "SOP from Sales_SOP_MY.txt",
        },
        {
            "id": "D13",
            "question": "Why did sales drop in Selangor?",
            "expected_route": "rag_docs",
            "expected_answer": "Analysis/insights (may say 'no specific data available' - that's OK)",
        },
    ],
    
    "*** ROBUSTNESS TESTS (Edge Cases) ***": [
        {
            "id": "R01",
            "question": "top products",
            "expected_route": "sales_kpi",
            "expected_answer": "Should ask for clarification OR use latest month (ambiguous query test)",
        },
        {
            "id": "R02",
            "question": "sales",
            "expected_route": "sales_kpi",
            "expected_answer": "Should ask for clarification (too vague test)",
        },
        {
            "id": "R04",
            "question": "salse bulan 2024-06",
            "expected_route": "sales_kpi",
            "expected_answer": "Should handle typo 'salse' → 'sales' gracefully",
        },
        {
            "id": "R08",
            "question": "berapa sales for Cheese Burger in Mei 2024?",
            "expected_route": "sales_kpi",
            "expected_answer": "Cheese Burger sales for May 2024 (mixed language test)",
        },
    ],
}

# Generate formatted test checklist
for category, questions in tests.items():
    print(f"\n{'='*80}")
    print(f"{category}")
    print(f"{'='*80}\n")
    
    for i, test in enumerate(questions, 1):
        print(f"[{test['id']}] TEST {i}/{len(questions)}")
        print("-" * 80)
        print(f"QUESTION:")
        print(f"   {test['question']}")
        print(f"\nEXPECTED:")
        print(f"   Route: {test['expected_route']}")
        print(f"   Answer: {test['expected_answer']}")
        if 'expected_followups' in test:
            print(f"   Follow-ups: {test['expected_followups']}")
        print(f"\nACTUAL RESULTS:")
        print(f"   Route: _____________")
        print(f"   Answer Accurate: [ ] YES  [ ] NO  [ ] PARTIAL")
        print(f"   Follow-ups Count: _____")
        print(f"   Notes: _________________________________________________")
        print(f"\nStatus: [ ] PASS  [ ] FAIL  [ ] NEEDS_REVIEW")
        print()

print(f"\n{'='*80}")
print("TESTING COMPLETE!")
print(f"{'='*80}\n")
print("SUMMARY CHECKLIST:")
print("  [ ] All CRITICAL tests passed")
print("  [ ] Sales KPI routing correct")
print("  [ ] HR KPI routing correct")
print("  [ ] RAG/Docs routing correct")
print("  [ ] Ambiguous queries handled gracefully")
print("  [ ] Follow-ups generated for all questions")
print("  [ ] Timer updated continuously (never stuck at 0.0s)")
print("  [ ] Stop button works when tested")
print()
print("SAVE THIS OUTPUT:")
print("   Copy results to: test_results_manual_[date].txt")
print()
print("NEXT STEPS:")
print("   1. Review any FAIL results")
print("   2. Compare actual vs expected answers")
print("   3. Identify patterns in failures")
print("   4. Create improvement plan for inaccurate answers")
print()
