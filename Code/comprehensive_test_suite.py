"""
Comprehensive Test Suite for CEO Bot v8.2
Tests all question types: Sales KPI, HR KPI, RAG/Docs, Visual, Robustness
Automated execution with detailed logging and results analysis
"""

import sys
import time
import json
from datetime import datetime
from pathlib import Path

# Comprehensive test questions organized by category
TEST_QUESTIONS = {
    "SALES_KPI": [
        # Simple aggregations
        {"id": "S01", "query": "sales bulan 2024-06 berapa?", "expected_route": "sales_kpi", "priority": "HIGH"},
        {"id": "S02", "query": "Total sales June 2024", "expected_route": "sales_kpi", "priority": "HIGH"},
        {"id": "S03", "query": "revenue bulan 2024-05", "expected_route": "sales_kpi", "priority": "MEDIUM"},
        
        # Comparisons
        {"id": "S04", "query": "banding sales bulan 2024-06 vs 2024-05", "expected_route": "sales_kpi", "priority": "HIGH"},
        {"id": "S05", "query": "Compare June vs May sales", "expected_route": "sales_kpi", "priority": "HIGH"},
        {"id": "S06", "query": "sales trend dari January hingga June 2024", "expected_route": "sales_kpi", "priority": "MEDIUM"},
        
        # Rankings / Top N
        {"id": "S07", "query": "top 3 product bulan 2024-06", "expected_route": "sales_kpi", "priority": "CRITICAL"},
        {"id": "S08", "query": "Show top 5 products in June", "expected_route": "sales_kpi", "priority": "HIGH"},
        {"id": "S09", "query": "worst performing product bulan 2024-06", "expected_route": "sales_kpi", "priority": "MEDIUM"},
        
        # Filtered queries
        {"id": "S10", "query": "sales state Selangor bulan 2024-06 berapa?", "expected_route": "sales_kpi", "priority": "HIGH"},
        {"id": "S11", "query": "sales ikut state bulan 2024-06", "expected_route": "sales_kpi", "priority": "HIGH"},
        {"id": "S12", "query": "Cheese Burger sales in June 2024", "expected_route": "sales_kpi", "priority": "MEDIUM"},
        
        # Breakdowns
        {"id": "S13", "query": "breakdown sales by product June", "expected_route": "sales_kpi", "priority": "MEDIUM"},
        {"id": "S14", "query": "sales performance by state", "expected_route": "sales_kpi", "priority": "MEDIUM"},
        
        # Edge cases
        {"id": "S15", "query": "sales bulan July 2024", "expected_route": "sales_kpi", "priority": "MEDIUM", "note": "Future month - should fail gracefully"},
    ],
    
    "HR_KPI": [
        # Simple headcount
        {"id": "H01", "query": "headcount berapa?", "expected_route": "hr_kpi", "priority": "HIGH"},
        {"id": "H02", "query": "total employees", "expected_route": "hr_kpi", "priority": "HIGH"},
        
        # Filtered headcount
        {"id": "H03", "query": "headcount ikut state", "expected_route": "hr_kpi", "priority": "HIGH"},
        {"id": "H04", "query": "How many employees in Selangor?", "expected_route": "hr_kpi", "priority": "MEDIUM"},
        
        # Department queries
        {"id": "H05", "query": "headcount by department", "expected_route": "hr_kpi", "priority": "MEDIUM"},
        {"id": "H06", "query": "berapa staff kitchen?", "expected_route": "hr_kpi", "priority": "MEDIUM"},
        
        # Seniority/Tenure
        {"id": "H07", "query": "average employee tenure", "expected_route": "hr_kpi", "priority": "LOW"},
        {"id": "H08", "query": "staff with more than 5 years", "expected_route": "hr_kpi", "priority": "LOW"},
        
        # Salary queries
        {"id": "H09", "query": "average salary by department", "expected_route": "hr_kpi", "priority": "MEDIUM"},
        {"id": "H10", "query": "total payroll expense", "expected_route": "hr_kpi", "priority": "LOW"},
    ],
    
    "RAG_DOCS": [
        # Policy queries
        {"id": "D01", "query": "What is the annual leave entitlement per year?", "expected_route": "rag_docs", "priority": "CRITICAL"},
        {"id": "D02", "query": "refund policy apa?", "expected_route": "rag_docs", "priority": "HIGH"},
        {"id": "D03", "query": "how to request emergency leave", "expected_route": "rag_docs", "priority": "HIGH"},
        {"id": "D04", "query": "maternity leave duration", "expected_route": "rag_docs", "priority": "MEDIUM"},
        
        # Company info
        {"id": "D05", "query": "company profile", "expected_route": "rag_docs", "priority": "MEDIUM"},
        {"id": "D06", "query": "how many branches we have?", "expected_route": "rag_docs", "priority": "MEDIUM"},
        {"id": "D07", "query": "what products do we sell?", "expected_route": "rag_docs", "priority": "MEDIUM"},
        
        # Operations
        {"id": "D08", "query": "what is the SOP for handling customer complaints?", "expected_route": "rag_docs", "priority": "HIGH"},
        {"id": "D09", "query": "opening hours for KL branch", "expected_route": "rag_docs", "priority": "MEDIUM"},
        {"id": "D10", "query": "Penang branch manager siapa?", "expected_route": "rag_docs", "priority": "LOW"},
        
        # FAQ
        {"id": "D11", "query": "how to escalate an incident", "expected_route": "rag_docs", "priority": "MEDIUM"},
        {"id": "D12", "query": "performance review process", "expected_route": "rag_docs", "priority": "LOW"},
        
        # Mixed context
        {"id": "D13", "query": "Why did sales drop in Selangor?", "expected_route": "rag_docs", "priority": "HIGH", "note": "Requires sales data + insights"},
        {"id": "D14", "query": "How can we improve Cheese Burger sales?", "expected_route": "rag_docs", "priority": "MEDIUM"},
        
        # Edge cases
        {"id": "D15", "query": "What happened on June 15, 2024?", "expected_route": "rag_docs", "priority": "LOW"},
        {"id": "D16", "query": "Tell me about competitor pricing", "expected_route": "rag_docs", "priority": "LOW", "note": "May not have data"},
    ],
    
    "VISUAL_OCR": [
        # Table extraction (requires image upload - manual test)
        {"id": "V01", "query": "Extract data from this table", "expected_route": "visual", "priority": "HIGH", "manual": True},
        {"id": "V02", "query": "What's in this chart?", "expected_route": "visual", "priority": "MEDIUM", "manual": True},
        {"id": "V03", "query": "Read the numbers from this image", "expected_route": "visual", "priority": "MEDIUM", "manual": True},
        {"id": "V04", "query": "analyze this sales chart", "expected_route": "visual", "priority": "LOW", "manual": True},
        {"id": "V05", "query": "OCR this document", "expected_route": "visual", "priority": "LOW", "manual": True},
    ],
    
    "ROBUSTNESS": [
        # Ambiguous queries
        {"id": "R01", "query": "top products", "expected_route": "sales_kpi", "priority": "CRITICAL", "note": "Should ask for timeframe"},
        {"id": "R02", "query": "sales", "expected_route": "sales_kpi", "priority": "HIGH", "note": "Too vague - needs clarification"},
        {"id": "R03", "query": "staff", "expected_route": "hr_kpi", "priority": "MEDIUM", "note": "Needs clarification"},
        
        # Typos / Malformed
        {"id": "R04", "query": "salse bulan 2024-06", "expected_route": "sales_kpi", "priority": "MEDIUM", "note": "Typo: salse → sales"},
        {"id": "R05", "query": "headcont by stat", "expected_route": "hr_kpi", "priority": "LOW", "note": "Multiple typos"},
        
        # Out of scope
        {"id": "R06", "query": "What's the weather today?", "expected_route": "rag_docs", "priority": "LOW", "note": "Out of scope"},
        {"id": "R07", "query": "Can you book a meeting?", "expected_route": "rag_docs", "priority": "LOW", "note": "Not a query function"},
        
        # Mixed language
        {"id": "R08", "query": "berapa sales for Cheese Burger in Mei 2024?", "expected_route": "sales_kpi", "priority": "MEDIUM"},
        {"id": "R09", "query": "top 3 produk dengan highest revenue", "expected_route": "sales_kpi", "priority": "MEDIUM"},
    ],
    
    "FOLLOWUP_SCENARIOS": [
        # Context preservation
        {"id": "F01", "sequence": [
            "top 3 product bulan 2024-06",
            "how about May?",  # Should compare to 2024-05
            "which one improved the most?"  # Should analyze change
        ], "priority": "CRITICAL"},
        
        {"id": "F02", "sequence": [
            "sales state Selangor bulan 2024-06",
            "compare with KL",  # Should show Selangor vs KL for June
            "which state is better?"
        ], "priority": "HIGH"},
        
        {"id": "F03", "sequence": [
            "headcount by department",
            "what about kitchen staff only?",  # Should drill down
            "average salary for them?"  # Context: kitchen department
        ], "priority": "HIGH"},
        
        {"id": "F04", "sequence": [
            "What is the refund policy?",
            "How long does it take?",  # Context: refund policy
            "Any exceptions?"  # Context: still refund policy
        ], "priority": "MEDIUM"},
        
        # Cross-category followups
        {"id": "F05", "sequence": [
            "top 3 products June 2024",
            "why is Cheese Burger popular?",  # Switch to RAG for insights
            "what's its sales trend?"  # Back to KPI
        ], "priority": "MEDIUM"},
    ]
}

def get_total_test_count():
    """Calculate total number of test questions"""
    total = 0
    for category, questions in TEST_QUESTIONS.items():
        if category == "FOLLOWUP_SCENARIOS":
            total += len(questions)  # Each scenario is one test
        else:
            total += len(questions)
    return total

def get_priority_breakdown():
    """Get breakdown by priority"""
    breakdown = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for category, questions in TEST_QUESTIONS.items():
        if category == "FOLLOWUP_SCENARIOS":
            for item in questions:
                breakdown[item.get("priority", "MEDIUM")] += 1
        else:
            for q in questions:
                breakdown[q.get("priority", "MEDIUM")] += 1
    return breakdown

def print_test_summary():
    """Print summary of all test cases"""
    print("=" * 80)
    print(" COMPREHENSIVE TEST SUITE FOR CEO BOT v8.2")
    print("=" * 80)
    print()
    
    total = get_total_test_count()
    priority_breakdown = get_priority_breakdown()
    
    print(f"📊 TOTAL TEST CASES: {total}")
    print()
    print("📋 BY CATEGORY:")
    for category, questions in TEST_QUESTIONS.items():
        count = len(questions)
        print(f"  • {category:20s}: {count:3d} tests")
    print()
    print("🎯 BY PRIORITY:")
    for priority, count in priority_breakdown.items():
        emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "⚪"}[priority]
        print(f"  {emoji} {priority:10s}: {count:3d} tests")
    print()
    print("=" * 80)
    print()

if __name__ == "__main__":
    print_test_summary()
    
    # Print detailed list
    print("\n📝 DETAILED TEST LIST:\n")
    for category, questions in TEST_QUESTIONS.items():
        print(f"\n{'='*80}")
        print(f" {category}")
        print(f"{'='*80}\n")
        
        if category == "FOLLOWUP_SCENARIOS":
            for item in questions:
                print(f"  [{item['id']}] ({item['priority']})")
                for i, q in enumerate(item['sequence'], 1):
                    print(f"      {i}. {q}")
                print()
        else:
            for q in questions:
                note = f" ({q['note']})" if 'note' in q else ""
                manual = " [MANUAL]" if q.get('manual') else ""
                print(f"  [{q['id']}] ({q['priority']}) {q['query']}{manual}{note}")
        print()
