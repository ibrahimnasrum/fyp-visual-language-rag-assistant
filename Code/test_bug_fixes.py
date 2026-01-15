"""Quick validation test for bug fixes v8.2.1"""
import pandas as pd, sys, importlib.util

print("="*60)
print("BUG FIX VALIDATION TEST v8.2.1")
print("="*60)

# Test 1: safe_format_number
print("\n[TEST 1] String Formatting Fix")
print("-"*60)
try:
    sys.path.insert(0, '.')
    spec = importlib.util.spec_from_file_location("bot", "oneclick_my_retailchain_v8.2_models_logging.py")
    bot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bot)
    safe_format_number = bot.safe_format_number
    
    tests = [(1234.56, 2, "1,234.56"), (1234, 0, "1,234"), (None, 0, "N/A"), 
             (float('nan'), 0, "N/A"), ("invalid", 0, "N/A"), (0, 0, "0")]
    
    passed = sum(1 for v, d, exp in tests if safe_format_number(v, d) == exp)
    print(f"  Result: {passed}/{len(tests)} passed")
    if passed == len(tests):
        print("  [OK] All formatting tests passed!")
    else:
        print(f"  [FAIL] {len(tests)-passed} test(s) failed!")
        sys.exit(1)
except Exception as e:
    print(f"  [ERROR] {e}")
    sys.exit(1)

# Test 2: Month parsing
print("\n[TEST 2] Month Parsing Fix")
print("-"*60)
try:
    from query.validator import DataValidator
    validator = DataValidator("../data/MY_Retail_Sales_2024H1.csv")
    
    tests = [("june", True), ("june 2024", True), ("2024-06", True), 
             ("January", True), ("invalid_month", False)]
    
    passed = sum(1 for m, should_parse in tests if (validator._parse_month(m) is not None) == should_parse)
    print(f"  Result: {passed}/{len(tests)} passed")
    if passed == len(tests):
        print("  [OK] All parsing tests passed!")
    else:
        print(f"  [FAIL] {len(tests)-passed} test(s) failed!")
        sys.exit(1)
except Exception as e:
    print(f"  [ERROR] {e}")
    sys.exit(1)

print("\n"+"="*60)
print("[SUCCESS] ALL VALIDATION TESTS PASSED!")
print("="*60)
print("\nReady to run: python automated_tester_csv.py")
print("Expected: 69.1% -> 76-80% accuracy (+7-11%)")
print("="*60)
