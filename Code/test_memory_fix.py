"""
Quick test script to validate Ollama memory fixes
Tests a few RAG questions to ensure no "unable to allocate CPU buffer" errors
"""

import sys
import time
from pathlib import Path

# Import bot module using importlib
import importlib.util
spec = importlib.util.spec_from_file_location(
    "bot_module",
    str(Path(__file__).parent / "oneclick_my_retailchain_v8.2_models_logging.py")
)
bot_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bot_module)

rag_query_ui = bot_module.rag_query_ui
preload_ollama_model = bot_module.preload_ollama_model

# Test questions (RAG-only)
TEST_QUESTIONS = [
    "What is the annual leave entitlement per year?",
    "What is the refund policy?",
    "How to request emergency leave?",
]

def test_rag_questions():
    """Test RAG questions to validate memory fixes"""
    print("\n" + "="*80)
    print("OLLAMA MEMORY FIX VALIDATION TEST")
    print("="*80)
    print(f"Testing {len(TEST_QUESTIONS)} RAG questions to check for memory errors\n")
    
    # Pre-load model
    print("🔄 Pre-loading mistral:latest...")
    success = preload_ollama_model("mistral:latest", keep_alive="10m")
    if success:
        print("✅ Model loaded successfully!\n")
    else:
        print("⚠️  Pre-load failed, but continuing...\n")
    
    time.sleep(2)
    
    # Test each question
    results = []
    for i, question in enumerate(TEST_QUESTIONS, 1):
        print(f"\n[{i}/{len(TEST_QUESTIONS)}] Testing: {question}")
        print("-" * 80)
        
        start = time.time()
        error_found = False
        final_answer = ""
        
        try:
            outputs = list(rag_query_ui(
                user_input=question,
                model_name="mistral:latest",
                has_image=False,
                chat_id="",
                conversation_history=[]
            ))
            
            if outputs:
                final_output = outputs[-1]
                answer_md = final_output[1] if len(final_output) > 1 else ""
                final_answer = answer_md
                
                # Check for error
                if "unable to allocate CPU buffer" in answer_md.lower():
                    error_found = True
                    print("❌ FAILED: Memory allocation error found!")
                elif "error loading model" in answer_md.lower():
                    error_found = True
                    print("❌ FAILED: Model loading error found!")
                elif "status code: 500" in answer_md.lower():
                    error_found = True
                    print("❌ FAILED: Status 500 error found!")
                else:
                    print("✅ PASSED: No memory errors")
                
        except Exception as e:
            error_found = True
            final_answer = str(e)
            print(f"❌ FAILED: Exception: {e}")
        
        elapsed = time.time() - start
        results.append({
            'question': question,
            'success': not error_found,
            'time': elapsed,
            'answer_preview': final_answer[:150]
        })
        
        print(f"   Time: {elapsed:.2f}s")
        print(f"   Answer preview: {final_answer[:100]}...")
        
        # Delay between tests
        time.sleep(2)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    passed = sum(1 for r in results if r['success'])
    failed = len(results) - passed
    
    print(f"Total: {len(results)} questions")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 SUCCESS! All tests passed - memory fixes are working!")
        return 0
    else:
        print("\n⚠️  Some tests failed - memory issues may still exist")
        print("\nFailed questions:")
        for r in results:
            if not r['success']:
                print(f"  - {r['question']}")
                print(f"    Answer: {r['answer_preview']}")
        return 1

if __name__ == "__main__":
    sys.exit(test_rag_questions())
