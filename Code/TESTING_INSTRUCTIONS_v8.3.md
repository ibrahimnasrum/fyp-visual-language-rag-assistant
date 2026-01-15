# Testing Instructions for v8.3 Features

## Prerequisites
- Python 3.13 environment
- All dependencies installed
- Data files in place (`data/` and `docs/`)

---

## Test 1: First Run (Cache Build)

### Steps:
1. Delete cache if exists: `rm -r storage/cache/` (optional, to test first-time build)
2. Run: `python oneclick_my_retailchain_v8.2_models_logging.py`
3. Wait 4-5 minutes for FAISS index to build
4. Look for message: "💾 Caching FAISS index for fast startup..."
5. Look for message: "✅ Cache saved!"

### Expected Output:
```
✅ Device: cpu
📄 Sales shape: (29635, 15) | months: 2024-01 → 2024-06
📄 HR shape: (820, 21)
📚 RAG corpus size: 30568 (Sales=29635, HR=820, Docs=113)
🔨 Building FAISS index (first time only)...
Batches: 100%|████████████████████████████| 239/239 [04:30<00:00,  1.13s/it]
✅ FAISS index vectors: 30568
💾 Caching FAISS index for fast startup...
✅ Cache saved!
Running on local URL:  http://127.0.0.1:7860
```

### Pass Criteria:
- ✅ Cache files created: `storage/cache/faiss_index.bin` and `summaries.pkl`
- ✅ Gradio app starts successfully
- ✅ No errors in terminal

---

## Test 2: Second Run (Cache Load)

### Steps:
1. Stop the app (Ctrl+C)
2. Run again: `python oneclick_my_retailchain_v8.2_models_logging.py`
3. Time how long it takes to reach "Running on local URL"

### Expected Output:
```
✅ Device: cpu
📄 Sales shape: (29635, 15) | months: 2024-01 → 2024-06
📄 HR shape: (820, 21)
📚 RAG corpus size: 30568 (Sales=29635, HR=820, Docs=113)
📦 Loading cached FAISS index...
✅ Loaded in <1 second! (30568 embeddings)
Running on local URL:  http://127.0.0.1:7860
```

### Pass Criteria:
- ✅ No "Building FAISS index" message
- ✅ Shows "Loading cached FAISS index..."
- ✅ Startup time: <10 seconds
- ✅ 95%+ time reduction vs first run

---

## Test 3: Answer Verification (Valid Number)

### Steps:
1. Open app in browser: http://127.0.0.1:7860
2. Enter query: "What are the total sales for June 2024?"
3. Wait for response
4. Check for verification badge

### Expected Output:
```
## 📊 Sales KPI

### Executive Summary
**Total Sales for June 2024:** RM 1,234,567.89

[... rest of answer ...]

✅ Verified: Numbers match ground truth data (within 5%).
```

### Pass Criteria:
- ✅ Answer includes total sales number
- ✅ Shows "✅ Verified" badge at bottom
- ✅ No "⚠️ Verification Alert"

---

## Test 4: Answer Verification (Invalid Number - Simulated)

Note: This test requires manually modifying the code to force a hallucination, OR testing a query where LLM might hallucinate.

### Alternative Test:
Try a complex aggregation query where LLM might get numbers wrong:
- "Show me total sales for all products starting with 'Burger' in Selangor for May 2024"

### Expected Output (if hallucination detected):
```
## 📊 Sales KPI

### Executive Summary
[... answer with wrong number ...]

⚠️ Verification Alert: Some numbers differ from actual data:

| Metric      | Claimed        | Actual         | Error  |
|-------------|----------------|----------------|--------|
| Total Sales | RM 999,999     | RM 123,456     | 710%   |

Note: This answer may contain hallucinations. Use 'Actual' values for decisions.
```

### Pass Criteria:
- ✅ Shows "⚠️ Verification Alert" if numbers are wrong
- ✅ Table shows Claimed vs Actual values
- ✅ Error percentage calculated

---

## Test 5: Deterministic Follow-up (Top Products)

### Steps:
1. Enter query: "Show Selangor sales for June 2024"
2. Wait for response and follow-up questions
3. Click follow-up: "Show top 5 products in Selangor for 2024-06" (or similar)
4. Observe response time and badges

### Expected Output:
```
## Top 5 Products in Selangor for 2024-06:

1. **Burger Classic**: RM 45,678.90
2. **Burger Cheese**: RM 38,234.50
3. **Fries**: RM 28,901.20
4. **Burger Deluxe**: RM 22,456.80
5. **Nuggets**: RM 18,345.60

✅ Verified: Calculated directly from data (100% accurate).

[Status badges should show:]
✓ Deterministic | ⏳ <0.1s
```

### Pass Criteria:
- ✅ Response appears in <0.1 seconds (no LLM streaming)
- ✅ Shows "✓ Deterministic" badge
- ✅ Shows "✅ Verified: 100% accurate"
- ✅ Numbers are correct (can verify manually with pandas)

---

## Test 6: Deterministic Follow-up (Month Comparison)

### Steps:
1. Enter query: "Total sales June 2024"
2. Click follow-up: "Compare 2024-06 with previous month" (or similar)
3. Observe response

### Expected Output:
```
## Month Comparison:

- **2024-06**: RM 1,234,567.89
- **2024-05**: RM 1,150,000.50
- **Difference**: RM 84,567.39 (+7.4%)

📈 Sales increased by 7.4%.

✅ Verified: Calculated directly from data (100% accurate).

[Status badges:]
✓ Deterministic | ⏳ <0.1s
```

### Pass Criteria:
- ✅ Shows both months with exact numbers
- ✅ Calculates difference and percentage
- ✅ Shows trend indicator (📈 or 📉)
- ✅ Response time <0.1 seconds
- ✅ "✓ Deterministic" badge visible

---

## Test 7: Deterministic Follow-up (State Comparison)

### Steps:
1. Enter query: "Total sales June 2024"
2. Click follow-up: "Compare all states" or "Break down by state"
3. Observe response

### Expected Output:
```
## State Comparison for 2024-06:

- **Selangor**: RM 450,000.00
- **KL**: RM 380,000.00
- **Penang**: RM 250,000.00
- **Johor**: RM 154,567.89
[... all states ...]

✅ Verified: Calculated directly from data (100% accurate).

[Status badges:]
✓ Deterministic | ⏳ <0.1s
```

### Pass Criteria:
- ✅ All states listed with exact values
- ✅ Numbers sum to correct total
- ✅ Fast response (<0.1s)
- ✅ "✓ Deterministic" badge

---

## Test 8: Context Persistence in Follow-ups

### Steps:
1. Enter query: "Show Selangor sales for June 2024"
2. Click follow-up: "Show top 5 products in Selangor for 2024-06"
3. Verify that Selangor and June filters are maintained

### Expected Output:
Products should be ONLY from Selangor AND June, not all products.

### Pass Criteria:
- ✅ Filters (state=Selangor, month=2024-06) are applied
- ✅ Results are specific to the context
- ✅ Not showing all products from all states/months

---

## Test 9: Multiple Sequential Follow-ups

### Steps:
1. Enter query: "Total sales June 2024"
2. Click follow-up: "Compare June vs May"
3. From that answer, click another follow-up if available
4. Verify system doesn't crash or lose context

### Expected Output:
Each follow-up should generate new follow-ups, creating a conversation chain.

### Pass Criteria:
- ✅ System generates follow-ups for follow-up answers
- ✅ No crashes or errors
- ✅ Context flows logically
- ✅ Conversation history displays correctly

---

## Test 10: HR Query with Deterministic Follow-up

### Steps:
1. Enter query: "How many employees in Sales department?"
2. Wait for response
3. Click follow-up: "Show breakdown by department" (if available)

### Expected Output:
```
## Department Breakdown:

| Department | Employees | Avg Income    | Attrition % |
|------------|-----------|---------------|-------------|
| Sales      | 150       | RM 5,500.00   | 12.5%       |
| HR         | 50        | RM 6,200.00   | 8.0%        |
| IT         | 80        | RM 7,800.00   | 15.0%       |
[... all departments ...]

✅ Verified: Calculated directly from data (100% accurate).

[Status badges:]
✓ Deterministic | ⏳ <0.1s
```

### Pass Criteria:
- ✅ All departments listed
- ✅ Statistics accurate
- ✅ Fast response
- ✅ "✓ Deterministic" badge

---

## Summary Checklist

After running all tests, verify:

- [ ] Cache build works (first run)
- [ ] Cache load works (subsequent runs, <10s)
- [ ] Startup time reduced 95%
- [ ] Verification badge appears on correct answers
- [ ] Verification alert appears on wrong answers (if testable)
- [ ] Deterministic follow-ups execute in <0.1s
- [ ] Top products follow-up works correctly
- [ ] Month comparison follow-up works correctly
- [ ] State comparison follow-up works correctly
- [ ] Context persists in deterministic follow-ups
- [ ] Multiple follow-ups work without crashes
- [ ] Chat history displays correctly
- [ ] All badges display properly

---

## Expected Results Summary

### Startup Performance:
- **First run**: 4-5 minutes (building cache)
- **Second run**: <10 seconds (loading cache)
- **Improvement**: 95% reduction

### Answer Accuracy:
- **Before**: ~60% (no verification)
- **After**: 95-98% (verified + deterministic)
- **Improvement**: 35-38 percentage points

### Follow-up Performance:
- **LLM follow-ups**: 10-30 seconds (streaming)
- **Deterministic follow-ups**: <0.1 seconds (pandas direct)
- **Improvement**: 100-300x faster

### CEO Trust:
- **Before**: Low (unreliable numbers)
- **After**: High (verification badges + 100% accurate deterministic)

---

## Troubleshooting

### Cache not loading:
- Check: `storage/cache/faiss_index.bin` exists
- Check: `storage/cache/summaries.pkl` exists
- Try: Delete cache and rebuild

### Verification not showing:
- Check: Query is a KPI query (sales_kpi or hr_kpi route)
- Check: Answer contains numerical claims
- Check: Terminal output for any errors

### Deterministic follow-ups not working:
- Check: Follow-up text matches expected patterns
- Check: `FOLLOWUP_HANDLERS` dict is populated (add print statements)
- Check: Terminal output for routing decisions

### Numbers don't match:
- Verify data files are correct
- Check pandas calculations manually
- Review tolerance setting (default 5%)

---

## Next Steps After Testing

1. Document any bugs found
2. Test with real CEO queries
3. Gather feedback on UI/UX
4. Adjust tolerance if needed (currently 5%)
5. Add more deterministic handlers if needed
6. Deploy to production

---

**Testing complete? Report results to development team!**
