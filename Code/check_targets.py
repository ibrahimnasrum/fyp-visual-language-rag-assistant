"""Check target test IDs"""
import pandas as pd

df = pd.read_csv('test_results_20260115_133721.csv')
target_ids = ['H06', 'H07', 'H08', 'H10', 'CEO23', 'CEO31', 'CEO27', 'CEO29', 'CEO30', 'R03', 'R05', 'CEO11']

print('=== CHECKING TARGET TEST IDS ===\n')
for tid in target_ids:
    if tid in df['test_id'].values:
        row = df[df['test_id'] == tid].iloc[0]
        print(f'{tid}: {row["question"][:60]}')
        print(f'  Expected: {row["expected_route"]} | Actual: {row["actual_route"]} | Status: {row["status"]}')
        if row["status"] != "PASS":
            print(f'  ❌ STILL FAILING')
        else:
            print(f'  ✅ PASSING')
    else:
        print(f'{tid}: ❌ NOT FOUND in latest CSV')
    print()
