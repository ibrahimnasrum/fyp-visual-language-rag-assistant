"""
Quick Unit Test for Word Boundary Fix
Tests that keyword_match() correctly handles substring collisions
"""
import re

def keyword_match(keywords: list, text: str) -> tuple:
    """Match keywords with word boundaries to prevent substring collisions."""
    matched_keywords = []
    for k in keywords:
        if ' ' in k:
            # Multi-word phrase: use substring matching
            if k in text:
                matched_keywords.append(k)
        else:
            # Single word: use word boundary to prevent substring matches
            if re.search(rf'\b{re.escape(k)}\b', text):
                matched_keywords.append(k)
    return (len(matched_keywords) > 0, matched_keywords)

# Test cases
print("=" * 80)
print("WORD BOUNDARY MATCHING TESTS")
print("=" * 80)

# Test 1: "age" should NOT match "percentage" or "average"
test_cases = [
    ("what percentage of sales?", ["age"], False, "percentage should NOT match 'age'"),
    ("what is the average?", ["age"], False, "average should NOT match 'age'"),
    ("show me age distribution", ["age"], True, "'age' should match 'age'"),
    ("age group analysis", ["age"], True, "'age' should match 'age'"),
    ("what's the age?", ["age"], True, "'age' should match 'age'"),
]

print("\n1. Testing 'age' keyword (single word):")
for text, keywords, expected, description in test_cases:
    matched, matched_kw = keyword_match(keywords, text.lower())
    status = "✅ PASS" if matched == expected else "❌ FAIL"
    print(f"  {status} | '{text}' | matched={matched} | {description}")

# Test 2: Multi-word phrases should use substring matching
print("\n2. Testing multi-word phrases:")
multi_word_tests = [
    ("age group by department", ["age group"], True, "multi-word 'age group' should match"),
    ("what's the employee age grouped?", ["age group"], True, "'age group' substring in 'grouped'"),
    ("show me ages", ["age group"], False, "'ages' should NOT match 'age group'"),
]

for text, keywords, expected, description in multi_word_tests:
    matched, matched_kw = keyword_match(keywords, text.lower())
    status = "✅ PASS" if matched == expected else "❌ FAIL"
    print(f"  {status} | '{text}' | matched={matched} | {description}")

# Test 3: Real-world regression cases
print("\n3. Testing actual regression queries:")
HR_KEYWORDS = ["age", "age group", "managers", "manager", "payroll", "tenure"]
SALES_KEYWORDS = ["sales", "revenue", "percentage", "average", "branch", "product"]

regression_tests = [
    ("What percentage of our sales come from delivery?", HR_KEYWORDS, False, "CEO17: should NOT match HR"),
    ("What percentage of revenue from top 3 products?", HR_KEYWORDS, False, "CEO18: should NOT match HR"),
    ("Show me revenue breakdown by state as percentages", HR_KEYWORDS, False, "CEO19: should NOT match HR"),
    ("What's our average transaction value by channel?", HR_KEYWORDS, False, "CEO22: should NOT match HR"),
    ("Which branches perform above the average?", HR_KEYWORDS, False, "CEO31: should NOT match HR"),
    ("How many managers have left the company?", HR_KEYWORDS, True, "CEO16: should match HR (managers)"),
    ("What's the age distribution of our workforce?", HR_KEYWORDS, True, "CEO29: should match HR (age)"),
]

for text, keywords, expected, description in regression_tests:
    matched, matched_kw = keyword_match(keywords, text.lower())
    status = "✅ PASS" if matched == expected else "❌ FAIL"
    matched_list = matched_kw if matched else "none"
    print(f"  {status} | {description}")
    print(f"         Query: '{text[:60]}...'")
    print(f"         Matched keywords: {matched_list}")

# Test 4: Sales keywords should still match correctly
print("\n4. Testing sales keyword matching:")
sales_tests = [
    ("What percentage of our sales come from delivery?", SALES_KEYWORDS, True, "should match 'sales'"),
    ("Show me revenue breakdown", SALES_KEYWORDS, True, "should match 'revenue'"),
    ("Which branches perform above average?", SALES_KEYWORDS, True, "should match 'branch', 'average'"),
]

for text, keywords, expected, description in sales_tests:
    matched, matched_kw = keyword_match(keywords, text.lower())
    status = "✅ PASS" if matched == expected else "❌ FAIL"
    print(f"  {status} | '{text}' | matched: {matched_kw[:3]} | {description}")

print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print("If all tests show ✅ PASS, the word boundary fix is working correctly!")
print("=" * 80)
