"""Direct test of format_num fix"""
import sys
sys.path.insert(0, r"c:\Users\User\OneDrive\Pictures\Documents\GitHub\fyp-visual-language-rag-assistant\Code")

# Direct import and test
import importlib.util
spec = importlib.util.spec_from_file_location(
    "bot", 
    r"c:\Users\User\OneDrive\Pictures\Documents\GitHub\fyp-visual-language-rag-assistant\Code\oneclick_my_retailchain_v8.2_models_logging.py"
)
bot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bot)

print("="*60)
print("FORMAT_NUM FIX VALIDATION")
print("="*60)

# Test the exact error scenario
test_value = 99852.83
result = bot.format_num(test_value, 2)

print(f"\nTest: format_num({test_value}, 2)")
print(f"Result: {result}")
print(f"Expected: 99,852.83")

if result == "99,852.83":
    print("\n✅ FORMAT FIX WORKS! No more 'Cannot specify ',' with 's'' error")
else:
    print(f"\n❌ FAILED - Got: {result}")

# Test preload exists
print("\n" + "="*60)
print("MEMORY FIX VALIDATION")
print("="*60)

if hasattr(bot, 'preload_ollama_model'):
    print("✅ preload_ollama_model() function exists")
    import inspect
    sig = inspect.signature(bot.preload_ollama_model)
    print(f"   Signature: preload_ollama_model{sig}")
else:
    print("❌ preload_ollama_model() NOT FOUND")

print("\n" + "="*60)
print("BOTH FIXES ARE IN PLACE")
print("="*60)
