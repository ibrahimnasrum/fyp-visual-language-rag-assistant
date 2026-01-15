"""
Test FYP Prompt Engineering Implementation
Verifies that all new functions work correctly
"""
import sys
import os
import importlib.util

# Fix encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

print("="*70)
print("Testing FYP Prompt Engineering Implementation")
print("="*70 + "\n")

# Test 1: Import functions
print("Test 1: Importing enhanced functions...")
try:
    # Load module with dots in filename using importlib
    spec = importlib.util.spec_from_file_location(
        "ceo_module",
        "oneclick_my_retailchain_v8.2_models_logging.py"
    )
    ceo_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ceo_module)
    
    get_ceo_system_prompt = ceo_module.get_ceo_system_prompt
    build_ceo_prompt = ceo_module.build_ceo_prompt
    build_verification_prompt = ceo_module.build_verification_prompt
    build_followup_question_prompt = ceo_module.build_followup_question_prompt
    classify_query_type = ceo_module.classify_query_type
    
    print("All functions imported successfully\n")
except Exception as e:
    print(f"Import failed: {e}\n")
    sys.exit(1)

# Test 2: System prompt generation
print("Test 2: System prompt generation...")
try:
    system_prompt = get_ceo_system_prompt()
    assert "KNOWLEDGE SOURCE HIERARCHY" in system_prompt
    assert "Chain-of-Thought" in system_prompt
    assert "FAIL-CLOSED BEHAVIOR" in system_prompt
    print("[OK] System prompt contains all required sections")
    print(f"   Length: {len(system_prompt)} characters\n")
except Exception as e:
    print(f"[FAIL] System prompt test failed: {e}\n")
    sys.exit(1)

# Test 3: Basic prompt building (backward compatibility)
print("Test 3: Basic prompt building (backward compatibility)...")
try:
    prompt = build_ceo_prompt(
        context="Test context",
        query="What is revenue?",
        query_type="performance"
    )
    assert "Test context" in prompt
    assert "What is revenue?" in prompt
    assert "QUERY TYPE: Performance" in prompt
    print("[OK] Basic prompt building works (backward compatible)\n")
except Exception as e:
    print(f"[FAIL] Basic prompt test failed: {e}\n")
    sys.exit(1)

# Test 4: Advanced prompt building (new parameters)
print("Test 4: Advanced prompt building (new parameters)...")
try:
    prompt = build_ceo_prompt(
        context="Retrieved documents from docs/ folder",
        query="Compare Selangor vs Penang",
        query_type="comparison",
        computed_kpi_facts={
            "Selangor Revenue": "RM 100,000",
            "Penang Revenue": "RM 80,000"
        },
        ocr_text="Invoice data from image"
    )
    assert "COMPUTED KPI FACTS" in prompt
    assert "RM 100,000" in prompt
    assert "OCR TEXT" in prompt or "Invoice data" in prompt
    print("[OK] Advanced prompt building works with new parameters\n")
except Exception as e:
    print(f"[FAIL] Advanced prompt test failed: {e}\n")
    sys.exit(1)

# Test 5: Verification prompt
print("Test 5: Verification prompt generation...")
try:
    verification_prompt = build_verification_prompt(
        original_query="What is revenue?",
        generated_answer="Revenue is RM 500,000",
        sources_used=["Sales KPI 2024-01"]
    )
    assert "fact-checker" in verification_prompt
    assert "Verification Status" in verification_prompt
    assert "PASS / FAIL" in verification_prompt
    print("[OK] Verification prompt generated correctly\n")
except Exception as e:
    print(f"[FAIL] Verification prompt test failed: {e}\n")
    sys.exit(1)

# Test 6: Follow-up question prompt
print("Test 6: Follow-up question prompt generation...")
try:
    followup_prompt = build_followup_question_prompt(
        original_query="What is revenue?",
        partial_answer="Revenue data available",
        missing_info=["time period", "location"]
    )
    assert "follow-up question" in followup_prompt.lower()
    assert "time period" in followup_prompt
    print("[OK] Follow-up question prompt generated correctly\n")
except Exception as e:
    print(f"[FAIL] Follow-up prompt test failed: {e}\n")
    sys.exit(1)

# Test 7: Query type classification (unchanged)
print("Test 7: Query type classification...")
try:
    test_cases = [
        ("What is revenue?", "performance"),
        ("Compare Selangor vs Penang", "comparison"),
        ("What is the trend?", "trend"),
        ("Why did sales decline?", "root_cause"),
        ("What is the leave policy?", "policy")
    ]
    
    for query, expected in test_cases:
        result = classify_query_type(query)
        if result != expected:
            print(f"   [FAIL] '{query}'")
            print(f"      Expected: '{expected}', Got: '{result}'")
            sys.exit(1)
        else:
            print(f"   [OK] '{query}' -> {result}")
    
    print("[OK] Query classification works correctly\n")
except Exception as e:
    print(f"[FAIL] Query classification test failed: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Summary
print("="*70)
print("ALL TESTS PASSED")
print("="*70)
print("\nSummary:")
print("  [OK] Function imports: OK")
print("  [OK] System prompt: Enhanced with hierarchy & CoT")
print("  [OK] Prompt builder: Backward compatible + new features")
print("  [OK] Verification: Working")
print("  [OK] Follow-up: Working")
print("  [OK] Classification: Working")
print("\n🎯 FYP prompt engineering implementation is READY")
print("="*70 + "\n")
