#!/usr/bin/env python
"""Quick test of ONE failing query"""
import sys
sys.path.insert(0, r"c:\Users\User\OneDrive\Pictures\Documents\GitHub\fyp-visual-language-rag-assistant\Code")

# Simple import
from automated_tester_csv import AutomatedTester

print("Testing ONE query that previously failed...")
print("="*60)

tester = AutomatedTester()

# Test UI01 - the first failing query
test_q = {
    'id': 'TEST01',
    'question': 'sales bulan 2024-06 berapa?',
    'expected_route': 'sales_kpi',
    'route': 'sales_kpi'
}

print(f"\nQuery: {test_q['question']}")
print("Expected route: sales_kpi\n")

tester.test_question(test_q)

result = tester.results[-1]

print(f"\nResult:")
print(f"- Status: {result['status']}")
print(f"- Route match: {result['route_match']}")
print(f"- Answer preview: {result['answer_preview'][:200]}")

if "Error: Cannot specify" in result['answer_preview']:
    print("\n❌ FORMAT ERROR STILL OCCURRING!")
else:
    print("\n✅ NO FORMAT ERROR - Fix is working!")
