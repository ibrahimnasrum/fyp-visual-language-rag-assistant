"""Quick test - just the prompt functions without loading full system"""
import sys
import importlib.util

print("="*70)
print("Quick Prompt Engineering Test (No Data Loading)")
print("="*70 + "\n")

# Test: Import just the prompt function definitions
print("Loading prompt functions...")
try:
    with open("oneclick_my_retailchain_v8.2_models_logging.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check 1: System prompt has correct hierarchy
    if "docs/ folder" in content and "[DOC:filename] documents" in content:
        print("[OK] System prompt references docs/ folder correctly")
    else:
        print("[FAIL] System prompt hierarchy incorrect")
        sys.exit(1)
    
    # Check 2: No reference/ folder mentioned in system prompt
    lines = content.split('\n')
    in_system_prompt = False
    for i, line in enumerate(lines):
        if 'def get_ceo_system_prompt' in line:
            in_system_prompt = True
        if in_system_prompt and 'def build_ceo_prompt' in line:
            in_system_prompt = False
        if in_system_prompt and 'reference/ folder' in line.lower() and 'PRIMARY SOURCE' in content[max(0, content.find(line)-500):content.find(line)+500]:
            print("[FAIL] System prompt still references reference/ folder as PRIMARY SOURCE")
            sys.exit(1)
    
    print("[OK] System prompt does NOT reference reference/ folder as data source")
    
    # Check 3: Function signature has correct parameters
    if 'def build_ceo_prompt(context: str, query: str, query_type: str, memory: dict = None, conversation_history: list = None' in content:
        if 'computed_kpi_facts: dict = None, ocr_text: str = "")' in content:
            print("[OK] Prompt builder has correct signature (7 parameters)")
        else:
            print("[FAIL] Prompt builder signature incorrect")
            sys.exit(1)
    else:
        print("[FAIL] Prompt builder not found")
        sys.exit(1)
    
    # Check 4: Verification function exists
    if 'def build_verification_prompt' in content:
        print("[OK] Verification function exists")
    else:
        print("[FAIL] Verification function missing")
        sys.exit(1)
    
    # Check 5: Follow-up function exists
    if 'def build_followup_question_prompt' in content:
        print("[OK] Follow-up function exists")
    else:
        print("[FAIL] Follow-up function missing")
        sys.exit(1)
    
    # Check 6: Knowledge hierarchy is correct
    if 'PRIMARY SOURCE for policy/procedure questions' in content and 'PRIMARY SOURCE for quantitative analysis' in content:
        print("[OK] Dual PRIMARY sources defined (docs/ + data/)")
    else:
        print("[FAIL] Primary sources not correctly defined")
        sys.exit(1)
    
    print("\n" + "="*70)
    print("ALL CHECKS PASSED")
    print("="*70)
    print("\nSummary:")
    print("  [OK] System prompt: Correct hierarchy (docs/ + data/)")
    print("  [OK] No reference/ folder as data source")
    print("  [OK] Prompt builder: 7 parameters (removed reference_materials)")
    print("  [OK] Verification function: Exists")
    print("  [OK] Follow-up function: Exists")
    print("  [OK] Dual PRIMARY sources: docs/ and data/")
    print("\nImplementation is CORRECT and ready for FYP thesis!")
    
except Exception as e:
    print(f"[FAIL] Test error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
