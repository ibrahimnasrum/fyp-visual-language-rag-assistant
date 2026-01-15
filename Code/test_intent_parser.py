# Test Query Intent Parser
# Quick test to verify the intent parser works correctly

import sys
sys.path.insert(0, r'c:\Users\User\OneDrive\Pictures\Documents\GitHub\fyp-visual-language-rag-assistant\Code')

# Test cases
test_queries = [
    "What percentage of June sales came from Selangor?",
    "Compare June vs May sales",
    "Top 5 products in Selangor",
    "Total sales for June 2024",
    "Show me sales breakdown by state",
]

print("=" * 80)
print("QUERY INTENT PARSER TEST")
print("=" * 80)

# Note: We can't actually run this yet because it requires the full module to be loaded
# This is just a template for manual testing

for query in test_queries:
    print(f"\n📝 Query: {query}")
    print(f"   Expected:")
    
    if "percentage" in query.lower():
        print(f"   - Intent: percentage")
        print(f"   - Should extract part/whole context")
    elif "compare" in query.lower() or "vs" in query.lower():
        print(f"   - Intent: comparison")
        print(f"   - Should detect what's being compared")
    elif "top" in query.lower() or "breakdown" in query.lower():
        print(f"   - Intent: breakdown")
        print(f"   - Should detect groupby dimension")
    else:
        print(f"   - Intent: total")
        print(f"   - Should extract filters")

print("\n" + "=" * 80)
print("To test manually:")
print("1. Start the app: python oneclick_my_retailchain_v8.2_models_logging.py")
print("2. In Python console, test: parse_query_intent('What percentage of June sales came from Selangor?')")
print("=" * 80)
