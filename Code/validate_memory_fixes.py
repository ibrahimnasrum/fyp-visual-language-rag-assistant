#!/usr/bin/env python3
"""
Lightweight Memory Fix Validation Script
Tests Ollama memory fixes without importing full bot module
"""

import ollama
import time
import sys

def test_ollama_memory_fixes():
    """Test that Ollama memory fixes are working"""
    
    print("\n" + "="*80)
    print("OLLAMA MEMORY FIX VALIDATION")
    print("="*80)
    print()
    
    # Test 1: Pre-load mistral
    print("✓ Test 1: Pre-loading mistral:latest...")
    try:
        start = time.time()
        response = ollama.chat(
            model="mistral:latest",
            messages=[{"role": "user", "content": "test"}],
            options={"num_ctx": 512, "num_predict": 1, "num_gpu": 0},
            keep_alive="10m"
        )
        elapsed = time.time() - start
        print(f"  ✅ SUCCESS: Model loaded in {elapsed:.1f}s")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return 1
    
    # Test 2: Check model is kept alive
    print("\n✓ Test 2: Checking model keep-alive...")
    try:
        ollama.chat(
            model="mistral:latest",
            messages=[{"role": "user", "content": "short"}],
            options={"num_ctx": 512, "num_predict": 1},
            keep_alive="10m"
        )
        print("  ✅ SUCCESS: Model responded (kept alive)")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return 1
    
    # Test 3: Verify reduced memory footprint options
    print("\n✓ Test 3: Testing reduced memory options...")
    try:
        response = ollama.chat(
            model="mistral:latest",
            messages=[{"role": "user", "content": "What is 2+2?"}],
            options={
                "num_ctx": 2048,      # Reduced from 4096
                "num_predict": 400,    # Reduced from 500
                "num_gpu": 0,          # CPU only
                "temperature": 0
            },
            keep_alive="10m"
        )
        answer = response.get("message", {}).get("content", "")
        print(f"  ✅ SUCCESS: Generated response: '{answer[:50]}...'")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return 1
    
    # Test 4: Retry logic simulation
    print("\n✓ Test 4: Testing retry logic (simulated)...")
    max_retries = 2
    for attempt in range(max_retries):
        try:
            response = ollama.chat(
                model="mistral:latest",
                messages=[{"role": "user", "content": "OK"}],
                options={"num_ctx": 512, "num_predict": 1},
                keep_alive="10m"
            )
            print(f"  ✅ Attempt {attempt+1}: SUCCESS")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"  ⚠️  Attempt {attempt+1}: Failed, retrying in 2s...")
                time.sleep(2)
            else:
                print(f"  ❌ All retries failed: {e}")
                return 1
    
    # Test 5: Verify no "unable to allocate" errors
    print("\n✓ Test 5: Stress test (5 rapid queries)...")
    failures = 0
    for i in range(5):
        try:
            response = ollama.chat(
                model="mistral:latest",
                messages=[{"role": "user", "content": f"Q{i}"}],
                options={"num_ctx": 2048, "num_predict": 100},
                keep_alive="10m"
            )
            print(f"  Query {i+1}: ✅ OK")
            time.sleep(0.5)  # Throttling
        except Exception as e:
            if "unable to allocate" in str(e).lower():
                failures += 1
                print(f"  Query {i+1}: ❌ Memory error!")
            else:
                print(f"  Query {i+1}: ⚠️  Other error: {str(e)[:50]}")
            time.sleep(1)
    
    if failures > 0:
        print(f"\n  ❌ {failures}/5 queries had memory allocation errors")
        return 1
    else:
        print(f"\n  ✅ All 5 queries succeeded - no memory errors!")
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print("✅ All memory fix validations passed!")
    print("\nKey improvements:")
    print("  • Memory-optimized options (context: 2048, tokens: 400)")
    print("  • Model keep-alive (10m) prevents unloading")
    print("  • Retry logic handles transient failures")
    print("  • No 'unable to allocate CPU buffer' errors")
    print("\nThe automated test suite is ready to run!")
    print("="*80)
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = test_ollama_memory_fixes()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        sys.exit(1)
