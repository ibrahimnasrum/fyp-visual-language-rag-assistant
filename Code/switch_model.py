"""
Phase 2 Helper: Quick Model Switcher for Testing

This script helps quickly switch between models in oneclick file for testing.
Run before each test in Phase 2.

Usage:
    python switch_model.py phi3:mini
    python switch_model.py mistral:7b
    python switch_model.py llama3:latest
"""

import sys
from pathlib import Path

MODEL_FILE = Path(__file__).parent / "oneclick_my_retailchain_v8.2_models_logging copy.py"

def switch_model(new_model: str):
    """Switch the default model in oneclick file"""
    
    if not MODEL_FILE.exists():
        print(f"❌ Error: {MODEL_FILE} not found!")
        return False
    
    # Read current content
    content = MODEL_FILE.read_text(encoding='utf-8')
    
    # Find and replace default model line
    lines = content.split('\n')
    modified = False
    
    for i, line in enumerate(lines):
        if 'default_model = models[0]' in line or 'default_model = "' in line:
            old_line = line
            # Replace with new model
            indent = len(line) - len(line.lstrip())
            lines[i] = ' ' * indent + f'default_model = "{new_model}"  # MODEL COMPARISON TEST'
            modified = True
            print(f"✅ Found model assignment at line {i+1}")
            print(f"   OLD: {old_line.strip()}")
            print(f"   NEW: {lines[i].strip()}")
            break
    
    if not modified:
        print("⚠️  Warning: Could not find default_model line")
        print("   You may need to manually edit the file")
        return False
    
    # Write back
    MODEL_FILE.write_text('\n'.join(lines), encoding='utf-8')
    print(f"\n✅ Model switched to: {new_model}")
    print(f"   File: {MODEL_FILE.name}")
    print("\n📝 Next steps:")
    print("   1. Stop current bot (Ctrl+C or kill process)")
    print(f"   2. Start bot: python {MODEL_FILE.name}")
    print("   3. Run tests: python automated_test_runner.py")
    
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python switch_model.py <model_name>")
        print("\nAvailable models:")
        print("  - phi3:mini")
        print("  - mistral:7b")
        print("  - llama3:latest")
        print("  - qwen2.5:7b")
        sys.exit(1)
    
    model = sys.argv[1]
    switch_model(model)
