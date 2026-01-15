# 📊 How to View Test Results in CSV

## CSV File Locations

All test result CSV files are saved in the **workspace root folder**:
```
fyp-visual-language-rag-assistant/test_results_YYYYMMDD_HHMMSS.csv
```

---

## Current Test Files

### Previous Tests:
1. **test_results_20260115_004039.csv** - 57 original questions
2. **test_results_20260115_005042.csv** - 37 CEO strategic questions

### Running Now:
3. **test_results_20260115_XXXXXX.csv** - ALL 94 questions (57 + 37)
   - ⏳ Testing in progress (~20-30 minutes)
   - Will appear in workspace root when done

---

## CSV File Structure

Each CSV contains these columns:

| Column | Description |
|--------|-------------|
| `test_id` | Question ID (e.g., S01, CEO01) |
| `question` | The actual question text |
| `expected_route` | Where question should go (sales_kpi, hr_kpi, rag_docs) |
| `actual_route` | Where it actually went |
| `route_match` | YES if routing correct, NO if wrong |
| `status` | PASS, ROUTE_FAIL, ANSWER_FAIL, ERROR |
| `response_time_sec` | How long it took to answer |
| `answer_length` | Length of answer in characters |
| `answer_preview` | First 200 chars of answer |
| `followup_count` | Number of follow-up questions generated |
| `followup_preview` | Preview of follow-up questions |
| `timestamp` | When test ran |
| `error` | Error message if failed |

---

## How to Open and Analyze

### Option 1: Excel (Easiest)
1. Navigate to: `C:\Users\User\OneDrive\Pictures\Documents\GitHub\fyp-visual-language-rag-assistant\`
2. Double-click `test_results_YYYYMMDD_HHMMSS.csv`
3. Opens in Excel with all columns

**Excel Tips:**
- **Filter by status**: Click status column → Filter → Show only "PASS" or "ROUTE_FAIL"
- **Sort by test_id**: Sort A→Z to group by category (CEO01-CEO37, S01-S15, etc.)
- **Search questions**: Ctrl+F to find specific question text
- **Freeze top row**: View → Freeze Panes → Freeze Top Row

### Option 2: View in Terminal (Quick Check)
```powershell
# View summary
python Code/view_results.py

# Or open specific file
Import-Csv test_results_20260115_004039.csv | Format-Table test_id, question, status, route_match
```

### Option 3: VS Code
1. Right-click CSV file → "Open With" → "Text Editor"
2. Install extension "Excel Viewer" for better view
3. Or "Rainbow CSV" extension for colored columns

---

## Quick Analysis Commands

### Count by Status
```powershell
# PowerShell
Import-Csv test_results_YYYYMMDD_HHMMSS.csv | Group-Object status | Select Count, Name
```

### Show Only Failures
```powershell
Import-Csv test_results_YYYYMMDD_HHMMSS.csv | Where-Object {$_.status -ne "PASS"} | Format-Table test_id, question, status
```

### Find Specific Question
```powershell
Import-Csv test_results_YYYYMMDD_HHMMSS.csv | Where-Object {$_.question -like "*salary*"} | Format-Table test_id, question, answer_preview
```

---

## What to Look For

### ✅ Good Results (PASS)
- `status` = PASS
- `route_match` = YES
- `answer_preview` has real content (not empty)
- `followup_count` > 0

### ⚠️ Issues to Check

**ROUTE_FAIL:**
- Question went to wrong route (e.g., HR question → rag_docs)
- Check `expected_route` vs `actual_route`
- May still have answer, but wrong processing

**ANSWER_FAIL:**
- Routing correct but no answer generated
- `answer_preview` is empty or very short
- Check `error` column for details

**ERROR:**
- System error during processing
- Check `error` column for stack trace

---

## Current Test Categories

### Original 57 Questions:
- **UI_EXAMPLES** (7): UI01-UI07
- **SALES** (15): S01-S15
- **HR** (10): H01-H10
- **RAG** (16): D01-D16
- **ROBUSTNESS** (9): R01-R09

### New CEO Strategic 37 Questions:
- **CEO_STRATEGIC** (37): CEO01-CEO37
  - Growth & Trends: CEO01-CEO06
  - Efficiency: CEO07-CEO11
  - Risk: CEO12-CEO16
  - Portfolio Mix: CEO17-CEO21
  - Profitability: CEO22-CEO25
  - HR Analytics: CEO26-CEO30
  - Benchmarking: CEO31-CEO34
  - Strategic Planning: CEO35-CEO37

---

## Example: Viewing in Excel

**Step-by-step:**

1. **Open File:**
   - Go to workspace folder
   - Double-click `test_results_20260115_XXXXXX.csv`

2. **Filter to See Only CEO Questions:**
   - Click on `test_id` column header
   - Filter → Text Filters → "Begins With" → Type "CEO"
   - Shows only 37 CEO strategic questions

3. **Check Pass Rate:**
   - Click on `status` column header
   - Look at bottom of Excel: Shows count of each status

4. **Review Failed Questions:**
   - Filter `status` column → Uncheck "PASS"
   - Review `answer_preview` and `error` columns

5. **Copy for Analysis:**
   - Select rows → Ctrl+C
   - Paste into new sheet or document

---

## File Naming Convention

Format: `test_results_YYYYMMDD_HHMMSS.csv`

Example: `test_results_20260115_153045.csv`
- Date: 2026-01-15
- Time: 15:30:45 (3:30:45 PM)

**Latest file = Most recent test**

---

## Current Test Status

### Running Now:
```bash
# Check if done
dir test_results_*.csv | sort LastWriteTime -Descending | select -First 1

# When done, it will show new file with current date/time
```

### When Complete:
- New CSV file appears in workspace root
- Contains ALL 94 questions (57 original + 37 CEO strategic)
- Ready to open in Excel

**Estimated completion:** ~20-30 minutes from start time

---

## Quick Reference

**CSV Location:** `fyp-visual-language-rag-assistant\` (workspace root)

**Total Questions:** 94 (57 original + 37 CEO strategic)

**Open in Excel:** Double-click the CSV file

**View Summary:** `python Code\view_results.py`

**Check Progress:** Look for newest `test_results_*.csv` file

---

## Need Help?

**Question not found?** Search in `question` column (Ctrl+F in Excel)

**Want specific category?** Filter by `test_id` (e.g., CEO* for CEO questions)

**Need raw data?** All answers in `answer_preview` column (may be truncated to 200 chars)

**Want full answers?** Check the logs or re-run specific questions manually
