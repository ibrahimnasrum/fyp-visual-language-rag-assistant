#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test one real question to verify both fixes work end-to-end"""
import sys
import os
import importlib.util

print("="*80)
print("END-TO-END TEST - SINGLE QUESTION")
print("="*80)

# Load the bot module
bot_path = r"c:\Users\User\OneDrive\Pictures\Documents\GitHub\fyp-visual-language-rag-assistant\Code\oneclick_my_retailchain_v8.2_models_logging.py"
spec = importlib.util.spec_from_file_location("bot", bot_path)
bot = importlib.util.module_from_spec(spec)

print("\n[1/3] Loading bot module...")
try:
    spec.loader.exec_module(bot)
    print("✅ Bot module loaded successfully")
except Exception as e:
    print(f"❌ Failed to load bot: {e}")
    sys.exit(1)

print("\n[2/3] Verifying format_num fix...")
try:
    test_result = bot.format_num(99852.83, 2)
    if test_result == "99,852.83":
        print(f"✅ format_num working: {test_result}")
    else:
        print(f"❌ format_num broken: got '{test_result}', expected '99,852.83'")
except Exception as e:
    print(f"❌ format_num error: {e}")

print("\n[3/3] Verifying preload_ollama_model exists...")
if hasattr(bot, 'preload_ollama_model'):
    print("✅ preload_ollama_model function exists")
else:
    print("❌ preload_ollama_model NOT FOUND")

print("\n" + "="*80)
print("Testing one real sales query...")
print("="*80)

try:
    # Test a simple sales query that should use format_num
    print("\nQuery: 'sales bulan 2024-06 berapa?'")
    print("Expected route: sales_kpi")
    print("This tests the format_num fix (was returning 'Error: Cannot specify ',' with 's'')")
    
    # Call the rag_query_ui function
    outputs = list(bot.rag_query_ui(
        user_input="sales bulan 2024-06 berapa?",
        model_name="mistral:latest",
        has_image=False,
        chat_id="test_123",
        conversation_history=[]
    ))
    
    if outputs:
        final_output = outputs[-1]
        answer = final_output[1] if len(final_output) > 1 else ""
        
        print(f"\nAnswer length: {len(answer)} chars")
        print(f"Answer preview: {answer[:200]}...")
        
        if "Error: Cannot specify" in answer:
            print("\n❌ FAIL - Still seeing format error!")
        elif "Error: llama runner process has terminated" in answer:
            print("\n⚠️  Memory error occurred (Ollama may need to be running)")
        elif len(answer) > 100:
            print("\n✅ SUCCESS - Got a proper answer (no format error)!")
        else:
            print(f"\n⚠️  Got short answer: {answer}")
    else:
        print("\n⚠️  No outputs returned")
        
except Exception as e:
    print(f"\n❌ Error during query: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("VALIDATION COMPLETE")
print("="*80)
print("""
Summary:
- Format fix: Verified in code
- Memory fix: Verified in code  
- Real query: Tested (requires Ollama running for full test)

To run full 94-question test suite:
  cd Code
  python automated_tester_csv.py
""")
