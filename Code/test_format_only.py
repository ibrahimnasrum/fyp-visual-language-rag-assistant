#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Minimal test of the format_num fix"""

def format_num(x: float, decimals: int = 2) -> str:
    """Format number with thousand separators and decimal places"""
    try:
        # Use format() instead of f-string for nested format specs
        format_spec = f",.{decimals}f"
        return format(float(x), format_spec)
    except (ValueError, TypeError):
        return str(x)

# Test the fix
print("="*60)
print("TESTING FORMAT_NUM FIX")
print("="*60)

test_cases = [
    (99852.83, "99,852.83"),
    (20250.99, "20,250.99"),
    (1234567.89, "1,234,567.89"),
]

all_pass = True
for value, expected in test_cases:
    result = format_num(value, 2)
    status = "✅ PASS" if result == expected else "❌ FAIL"
    print(f"{status} format_num({value}, 2) = {result} (expected: {expected})")
    if result != expected:
        all_pass = False

if all_pass:
    print("\n✅ ALL TESTS PASSED - Format fix is working!")
    print("   The 'Cannot specify ',' with 's'' error is FIXED")
else:
    print("\n❌ SOME TESTS FAILED")
