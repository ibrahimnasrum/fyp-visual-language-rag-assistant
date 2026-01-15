#!/usr/bin/env python
"""Test the exact failing query to understand the error"""
import sys
import importlib.util

# Load bot module
spec = importlib.util.spec_from_file_location(
    "bot", 
    r"c:\Users\User\OneDrive\Pictures\Documents\GitHub\fyp-visual-language-rag-assistant\Code\oneclick_my_retailchain_v8.2_models_logging.py"
)
bot = importlib.util.module_from_spec(spec)
print("Loading bot module...")
spec.loader.exec_module(bot)
print("✅ Bot module loaded\n")

# Test the exact failing query
test_query = "sales bulan 2024-06 berapa?"

print(f"Testing query: {test_query}")
print("="*60)

try:
    # Call the direct function
    result = bot.answer_sales_ceo_kpi(test_query, trace=None)
    
    print(f"\nResult type: {type(result)}")
    print(f"Result length: {len(str(result))} chars")
    print(f"\nResult preview:")
    print(result[:500] if result else "None")
    
    if "Error:" in str(result):
        print("\n❌ ERROR FOUND IN RESULT")
        print(f"Error message: {result}")
    else:
        print("\n✅ NO ERROR - Query executed successfully")
        
except Exception as e:
    print(f"\n❌ EXCEPTION OCCURRED")
    print(f"Exception type: {type(e).__name__}")
    print(f"Exception message: {e}")
    
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()
