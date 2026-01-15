# ✅ AUTOMATED TESTING - Quick Start Guide

## YES! Automated testing is MUCH better than manual!

I've created a fully automated system that:
- Tests all questions automatically
- Stores everything in CSV (like logs)
- You can review in Excel
- Much faster than manual testing

---

## 🚀 How to Use (3 Simple Steps)

### Step 1: Run Quick Test (5 critical questions, ~2 minutes)
```bash
cd Code
python automated_tester_csv.py --quick
```

**What happens:**
- Tests 5 critical questions automatically
- Shows progress in real-time
- Saves to: `test_results_20260115_HHMMSS.csv`

### Step 2: View Results Summary
```bash
python view_results.py
```

**Shows:**
- ✅ Pass/Fail statistics
- ⚠️ Which tests failed
- ⏱️ Response times
- 💡 Follow-up counts

### Step 3: Open CSV in Excel
```bash
# Just double-click: test_results_20260115_HHMMSS.csv
```

**CSV Contains:**
- `test_id` - Question ID (S01, H01, etc.)
- `question` - The actual question text
- `expected_route` - Where it should go
- `actual_route` - Where it actually went
- `route_match` - YES/NO
- `status` - PASS/FAIL/ERROR
- `response_time_sec` - How long it took
- `answer_preview` - First 200 chars of answer
- `followup_count` - How many follow-ups generated
- `followup_preview` - What follow-ups were suggested

---

## 📊 Test Options

### Option 1: Quick Test (Recommended first)
```bash
python automated_tester_csv.py --quick
```
- Tests: 5 critical questions
- Time: ~2 minutes
- Good for: First check

### Option 2: Test Specific Category
```bash
# Sales questions only
python automated_tester_csv.py --category sales

# HR questions only
python automated_tester_csv.py --category hr

# RAG/Document questions only
python automated_tester_csv.py --category rag
```
- Tests: 5-10 questions per category
- Time: ~3-5 minutes
- Good for: Focused testing

### Option 3: Full Test (All questions)
```bash
python automated_tester_csv.py
```
- Tests: ~30 questions
- Time: ~10 minutes
- Good for: Complete validation

---

## 📁 Output Files

### CSV File Format:
```
test_results_20260115_143022.csv
                ^^^^^^^^ ^^^^^^
                Date     Time
```

**Open in Excel to see:**
- Sort by status to see all failures
- Filter by route to check sales/hr/rag separately
- See full answers in answer_preview column
- See all follow-ups in followup_preview column

---

## 🔍 Example Output

### Console Output:
```
================================================================================
TESTING CATEGORY: CRITICAL (5 questions)
================================================================================

Progress: 1/5
[UI01] Testing: sales bulan 2024-06 berapa?...
  ✅ PASS - Route: sales_kpi - 2.3s - 3 follow-ups

Progress: 2/5
[UI03] Testing: top 3 product bulan 2024-06...
  ❌ ROUTE_FAIL - Route: rag_docs - 5.1s - 2 follow-ups

...

CRITICAL Summary: 4/5 passed

================================================================================
✅ Results saved to: test_results_20260115_143022.csv
================================================================================
📊 Open in Excel to review all answers and follow-ups
   - Total tests: 5
   - Passed: 4
   - Failed: 1
================================================================================
```

### CSV Content (in Excel):
```
test_id | question              | expected_route | actual_route | route_match | status | answer_preview
--------|----------------------|----------------|--------------|-------------|--------|----------------
UI01    | sales bulan 2024-06  | sales_kpi      | sales_kpi    | YES         | PASS   | ## ✅ Total Sales (RM) Value: RM 99,852.83...
UI03    | top 3 product        | sales_kpi      | rag_docs     | NO          | FAIL   | Based on documents, the top products...
...
```

---

## ✅ Advantages Over Manual Testing

| Manual Testing | Automated Testing |
|---------------|------------------|
| ❌ 1 hour for 30 questions | ✅ 10 minutes for 30 questions |
| ❌ Easy to miss details | ✅ Captures everything |
| ❌ Need to type notes | ✅ Auto-saves to CSV |
| ❌ Hard to compare | ✅ Open in Excel, sort, filter |
| ❌ Tedious and boring | ✅ Just run and review |

---

## 🎯 What to Check in CSV

After running tests, open CSV and check:

### 1. Route Accuracy
- Filter `route_match` column
- Look for "NO" values
- These are routing errors

### 2. Status Column
- Filter by "FAIL" or "ERROR"
- These need investigation
- Check `answer_preview` to see what went wrong

### 3. Answer Preview
- Read first 200 chars of each answer
- Check if it's specific or vague
- Check if it has numbers or just text

### 4. Follow-up Quality
- Check `followup_count` (should be 2-3)
- Read `followup_preview` to see if relevant

---

## 🔧 Troubleshooting

### Error: "Cannot import from oneclick_my_retailchain_v8.2_models_logging"
**Solution**: The script imports functions directly from your bot code. Make sure:
1. You're in the `Code/` directory
2. The bot file exists: `oneclick_my_retailchain_v8.2_models_logging.py`

### Error: No CSV file generated
**Solution**: Check console for errors. The test might have crashed. Run with `--quick` first.

### Want to test custom questions?
**Solution**: Edit `automated_tester_csv.py`, add your questions to `TEST_QUESTIONS` dict.

---

## 📈 Next Steps After Testing

1. **Run quick test first**:
   ```bash
   python automated_tester_csv.py --quick
   ```

2. **View results**:
   ```bash
   python view_results.py
   ```

3. **Open CSV in Excel** - Review details

4. **If issues found**:
   - Note which test IDs failed (S01, H03, etc.)
   - Check answer_preview column
   - Tell me the failures, I'll help fix

5. **Run full test** when ready:
   ```bash
   python automated_tester_csv.py
   ```

---

## 💡 Pro Tips

1. **Test incrementally**: Start with --quick, then category by category
2. **Compare results**: Run before/after code changes to verify improvements
3. **Keep CSV files**: Name them with version numbers to track progress
4. **Use Excel filters**: Sort by status, filter by category
5. **Share CSV**: Send me the CSV file if you need help analyzing failures

---

**Ready to start?**

```bash
cd Code
python automated_tester_csv.py --quick
```

Takes 2 minutes, saves everything to CSV automatically! 🚀
