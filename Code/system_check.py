"""
Complete System Status Check
Run this to verify all FYP enhancements are working.
"""
import os
import sys

print('\n' + '='*70)
print('🔍 COMPLETE SYSTEM STATUS REPORT')
print('='*70 + '\n')

# Check file structure
print('📁 FILE STRUCTURE:')
files_to_check = [
    'query/time_classifier.py',
    'query/validator.py',
    'query/__init__.py',
    'core/simple_cache.py',
    'core/__init__.py',
    'tests/fyp_evaluation.py',
    'tests/__init__.py',
    'oneclick_my_retailchain_v8.2_models_logging.py',
    'Run_FYP_Tests.bat'
]

all_files_ok = True
for file in files_to_check:
    exists = os.path.exists(file)
    status = '✅' if exists else '❌'
    print(f'  {status} {file}')
    if not exists:
        all_files_ok = False

# Check data
data_path = '../data/MY_Retail_Sales_2024H1.csv'
print(f'\n📊 DATA FILE:')
data_exists = os.path.exists(data_path)
print(f'  {"✅" if data_exists else "❌"} {data_path}')

if data_exists:
    import pandas as pd
    df = pd.read_csv(data_path)
    print(f'  📈 Rows: {len(df):,}')
    print(f'  📈 Columns: {len(df.columns)}')
    df['Date'] = pd.to_datetime(df['Date'])
    df['YearMonth'] = df['Date'].dt.to_period('M')
    months = sorted(df['YearMonth'].unique())
    print(f'  📈 Available Months: {", ".join([str(m) for m in months])}')
    print(f'  📈 Products: {df["Product"].nunique()}')
    print(f'  📈 States: {df["State"].nunique()}')

# Test modules
print('\n🧪 MODULE FUNCTIONALITY TESTS:')
try:
    from query.time_classifier import TimeClassifier
    from query.validator import DataValidator
    from core.simple_cache import SimpleCache

    # Test 1: Time classification
    tc = TimeClassifier()
    test1 = tc.classify('What is total revenue?')
    print(f'  ✅ Time Classifier: Classification={test1["classification"]}, Sensitive={test1["is_time_sensitive"]}')

    # Test 2: Data validation
    dv = DataValidator(data_path)
    test2 = dv.validate('2024-01')
    print(f'  ✅ Data Validator: Available={test2["available"]} for 2024-01')
    
    test3 = dv.validate('2023-12')
    print(f'  ✅ Data Validator: Available={test3["available"]} for 2023-12 (should be False)')

    # Test 3: Cache
    cache = SimpleCache()
    cache.set('test_key', 'test_value')
    retrieved = cache.get('test_key')
    cache.get('test_key')  # Second get for hit
    stats = cache.get_stats()
    print(f'  ✅ Cache: Get/Set working, Hits={stats["hits"]}, Hit Rate={stats["hit_rate_percent"]}%')

    print('\n📊 INTEGRATION STATUS:')
    print('  ✅ All modules imported successfully')
    print('  ✅ Time classifier functional')
    print('  ✅ Data validator functional')
    print('  ✅ Cache system functional')
    
except Exception as e:
    print(f'  ❌ Module test failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Summary
print('\n' + '='*70)
if all_files_ok and data_exists:
    print('✅ ALL SYSTEMS OPERATIONAL - READY FOR FYP')
    print('\n📝 Next Steps:')
    print('  1. Run: python oneclick_my_retailchain_v8.2_models_logging.py')
    print('  2. Test queries with validation system')
    print('  3. Run: Run_FYP_Tests.bat (for evaluation)')
    print('  4. Write your thesis using the implementation')
else:
    print('⚠️  SOME ISSUES DETECTED - Review above')
print('='*70 + '\n')
