"""
FYP Test Suite - Quick Start
Run this to execute all tests and see results.
"""
import os
import sys

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

print("="*80)
print("🧪 FYP TEST SUITE - QUICK START")
print("="*80)
print("\nThis will run 30 evaluation scenarios to generate thesis results.\n")

# Import and run
try:
    from fyp_evaluation import main
    main()
    
    print("\n" + "="*80)
    print("✅ TESTS COMPLETE")
    print("="*80)
    print("\n📝 Next steps:")
    print("  1. Check fyp_evaluation_results.json for detailed results")
    print("  2. Use accuracy metrics in thesis Chapter 5")
    print("  3. Include cache stats in performance analysis")
    print("\n💡 To show cache stats in main system:")
    print("     from oneclick_my_retailchain_v8.2_models_logging import show_cache_stats")
    print("     show_cache_stats()")
    print("\n")
    
except Exception as e:
    print(f"\n❌ Error running tests: {e}")
    print("\nTroubleshooting:")
    print("  1. Check sales data path in fyp_evaluation.py")
    print("  2. Ensure all modules are in correct directories")
    print("  3. Run from Code/tests/ directory")
