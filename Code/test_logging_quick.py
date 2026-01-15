"""Quick logging verification - tests individual functions"""
import sys
import importlib.util

# Load module
spec = importlib.util.spec_from_file_location(
    "oneclick", 
    r"c:\Users\User\OneDrive\Pictures\Documents\GitHub\fyp-visual-language-rag-assistant\Code\oneclick_my_retailchain_v8.2_models_logging.py"
)
oneclick = importlib.util.module_from_spec(spec)
sys.modules['oneclick'] = oneclick
spec.loader.exec_module(oneclick)

print("="*80)
print("QUICK LOGGING TEST - Verifying GAP-001 to GAP-004")
print("="*80)

# Test 1: Route logging
print("\n[TEST 1] Route Detection (GAP-002)")
print("-"*80)
route = oneclick.detect_intent("Top 5 products by revenue", False)
print(f"✓ Route returned: {route}")

# Test 2: Filter extraction (need to check if function exists first)
print("\n[TEST 2] Filter Extraction (GAP-001)")
print("-"*80)
if hasattr(oneclick, 'extract_sales_filters'):
    filters = oneclick.extract_sales_filters("Sales in Selangor for Samsung")
    print(f"✓ Filters returned: {filters}")
else:
    print("⚠ extract_sales_filters not found")

# Test 3: Follow-up generation
print("\n[TEST 3] Follow-up Generation (GAP-003)")
print("-"*80)
if hasattr(oneclick, 'generate_ceo_followup_questions'):
    answer = "Total sales in January was RM 2.4M"
    followups = oneclick.generate_ceo_followup_questions(
        "What were sales in January?", 
        answer, 
        "sales_kpi"
    )
    print(f"✓ Follow-ups returned: {len(followups)} questions")
else:
    print("⚠ generate_ceo_followup_questions not found")

print("\n" + "="*80)
print("✅ LOGGING VERIFICATION COMPLETE")
print("Check above for emoji-prefixed log messages:")
print("  🔀 ROUTE: ... (GAP-002)")
print("  🔍 FILTER EXTRACTION: ... (GAP-001)")
print("  📝 FOLLOW-UP GENERATION: ... (GAP-003)")
print("  📊 CONVERSATION_HISTORY: ... (GAP-004 - appears during full runs)")
print("="*80)
