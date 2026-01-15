"""
Test script to verify logging infrastructure (GAP-001 to GAP-004)
Run a few queries and check if logging appears correctly
"""

print("=" * 80)
print("LOGGING VERIFICATION TEST")
print("Testing: Route logging, Filter logging, Follow-up logging, Conversation logging")
print("=" * 80)

# Import the main module
import sys
import importlib.util
sys.path.insert(0, r"c:\Users\User\OneDrive\Pictures\Documents\GitHub\fyp-visual-language-rag-assistant\Code")

# Load the module with dots in its name
spec = importlib.util.spec_from_file_location(
    "oneclick", 
    r"c:\Users\User\OneDrive\Pictures\Documents\GitHub\fyp-visual-language-rag-assistant\Code\oneclick_my_retailchain_v8.2_models_logging.py"
)
oneclick = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oneclick)

detect_intent = oneclick.detect_intent
extract_sales_filters = oneclick.extract_sales_filters
generate_ceo_followup_questions = oneclick.generate_ceo_followup_questions

print("\n\n" + "="*80)
print("TEST 1: Route Detection Logging (GAP-002)")
print("="*80)

test_queries = [
    ("Top 5 products by revenue in January", False),
    ("What is our leave policy?", False),
    ("Show employee headcount", False),
]

for query, has_image in test_queries:
    print(f"\nQuery: '{query}'")
    route = detect_intent(query, has_image)
    print(f"Expected route to be logged above with matched keywords")

print("\n\n" + "="*80)
print("TEST 2: Filter Extraction Logging (GAP-001)")
print("="*80)

filter_queries = [
    "Total sales in Selangor for January",
    "Revenue for Samsung products",
    "Sales by Ali in KL branch",
]

for query in filter_queries:
    print(f"\nQuery: '{query}'")
    state, branch, product, employee, channel = extract_sales_filters(query)
    print(f"Extracted: State={state}, Branch={branch}, Product={product}, Employee={employee}, Channel={channel}")

print("\n\n" + "="*80)
print("TEST 3: Follow-up Generation Logging (GAP-003)")
print("="*80)

test_answer = """
Total sales for Selangor in January 2024 was RM 2,450,000.
This represents a 15% increase from December 2023.
Top performing products were Samsung Galaxy and iPhone 14.
"""

test_query = "What were the sales in Selangor for January?"
route = "sales_kpi"

print(f"\nGenerating follow-ups for: '{test_query}'")
print(f"Route: {route}")
followups = generate_ceo_followup_questions(test_query, test_answer, route)
print(f"\nReturned follow-ups: {followups}")

print("\n\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
print("\n✅ Check above output for:")
print("   1. 🔀 ROUTE: messages (showing route + matched keywords)")
print("   2. 🔍 FILTER EXTRACTION: messages (showing extracted filters)")
print("   3. 📝 FOLLOW-UP GENERATION: messages (showing generated questions)")
print("   4. 📊 CONVERSATION_HISTORY: (will appear in full runs with chat)")
print("\nIf all logs appear with emojis and structured format, gaps are FILLED!")
