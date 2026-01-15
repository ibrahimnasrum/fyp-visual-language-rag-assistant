#!/usr/bin/env python3
"""Test the fixed format_num function"""

import importlib.util
from pathlib import Path

# Load the module
spec = importlib.util.spec_from_file_location(
    "bot",
    str(Path(__file__).parent / "oneclick_my_retailchain_v8.2_models_logging.py")
)
bot = importlib.util.module_from_spec(spec)

try:
    spec.loader.exec_module(bot)
    print("✅ Module loaded successfully\n")
except Exception as e:
    print(f"❌ Module load failed: {e}")
    exit(1)

# Test format_num function
print("="*60)
print("Testing format_num() function")
print("="*60)

test_cases = [
    (99852.8348, 2, "99,852.83"),
    (1234567.89, 2, "1,234,567.89"),
    (42.1, 1, "42.1"),
    (0.005, 2, "0.00"),
    (999999.999, 2, "1,000,000.00"),
]

all_pass = True
for value, decimals, expected in test_cases:
    result = bot.format_num(value, decimals)
    status = "✅" if result == expected else "❌"
    print(f"{status} format_num({value}, {decimals})")
    print(f"   Expected: {expected}")
    print(f"   Got:      {result}")
    if result != expected:
        all_pass = False
    print()

if all_pass:
    print("\n" + "="*60)
    print("🎉 ALL TESTS PASSED - format_num is fixed!")
    print("="*60)
    exit(0)
else:
    print("\n" + "="*60)
    print("❌ SOME TESTS FAILED")
    print("="*60)
    exit(1)
