"""
MANUAL TEST GUIDE - CEO Bot v8.2
Quick reference for testing all question types manually via UI
"""

print("""
################################################################################
# MANUAL TEST GUIDE - CEO Bot v8.2
# Test Timer Updates + Stop Button + Routing Accuracy
################################################################################

INSTRUCTIONS:
1. Open http://127.0.0.1:7866 in your browser
2. For each test below:
   - Copy the question
   - Paste into the chatbox
   - Click Submit
   - ✅ WATCH: Timer should update continuously (0.0s → 0.3s → 1.5s → etc.)
   - ✅ VERIFY: Route badge shows correct category
   - ✅ TEST: Click Stop button mid-query (should cancel within 1s)
3. Mark results: ✅ Pass / ❌ Fail

################################################################################
# CATEGORY 1: SALES KPI (15 tests)
# Expected: Route = sales_kpi, Timer updates every 0.3-0.5s
################################################################################

[S01] CRITICAL - Simple total
Query: sales bulan 2024-06 berapa?
Expected Route: sales_kpi
Expected Answer: Total sales amount for June 2024
Timer Test: Should show 0.0s → 0.5s → 1.2s → Done (fast query ~1-3s)
Stop Test: Click stop immediately after submit
Result: ___________

[S02] HIGH - English variation  
Query: Total sales June 2024
Expected Route: sales_kpi
Expected Answer: Same as S01
Timer Test: Continuous updates
Stop Test: Click stop mid-generation
Result: ___________

[S03] MEDIUM - Different month
Query: revenue bulan 2024-05
Expected Route: sales_kpi
Expected Answer: May 2024 sales total
Timer Test: Continuous updates
Result: ___________

[S04] HIGH - Month comparison
Query: banding sales bulan 2024-06 vs 2024-05
Expected Route: sales_kpi
Expected Answer: June vs May comparison with difference/percentage
Timer Test: Should update during calculation (~2-4s)
Result: ___________

[S05] HIGH - Comparison English
Query: Compare June vs May sales
Expected Route: sales_kpi
Expected Answer: Same as S04
Result: ___________

[S07] CRITICAL - Top N ranking
Query: top 3 product bulan 2024-06
Expected Route: sales_kpi
Expected Answer: Top 3 products with sales amounts (ranked table)
Timer Test: Should show updates (~2-5s for aggregation)
Stop Test: Click stop during aggregation
Result: ___________

[S10] HIGH - State filter
Query: sales state Selangor bulan 2024-06 berapa?
Expected Route: sales_kpi
Expected Answer: Selangor-specific sales for June
Timer Test: Continuous updates
Result: ___________

[S15] MEDIUM - Future month (edge case)
Query: sales bulan July 2024
Expected Route: sales_kpi
Expected Answer: Should gracefully say "No data for July 2024" or similar
Timer Test: Quick response (~1-2s)
Result: ___________

################################################################################
# CATEGORY 2: HR KPI (10 tests)
# Expected: Route = hr_kpi, Timer updates during query
################################################################################

[H01] HIGH - Total headcount
Query: headcount berapa?
Expected Route: hr_kpi
Expected Answer: Total employee count
Timer Test: Fast response (~1-2s), timer should still update
Result: ___________

[H02] HIGH - English variation
Query: total employees
Expected Route: hr_kpi
Expected Answer: Same as H01
Result: ___________

[H03] HIGH - Breakdown by state
Query: headcount ikut state
Expected Route: hr_kpi
Expected Answer: Employee count per state (table)
Timer Test: Updates during aggregation (~2-3s)
Result: ___________

[H04] MEDIUM - Filtered query
Query: How many employees in Selangor?
Expected Route: hr_kpi
Expected Answer: Selangor employee count only
Result: ___________

[H06] MEDIUM - Department filter
Query: berapa staff kitchen?
Expected Route: hr_kpi
Expected Answer: Kitchen department employee count
Result: ___________

################################################################################
# CATEGORY 3: RAG/DOCUMENTS (16 tests)
# Expected: Route = rag_docs, Timer should update during 40s FAISS retrieval!
################################################################################

[D01] CRITICAL - Policy query (TIMER STRESS TEST)
Query: What is the annual leave entitlement per year?
Expected Route: rag_docs
Expected Answer: Policy details from HR_Policy_MY.txt
⚠️ CRITICAL TIMER TEST: This takes ~40s during retrieval!
   - Timer MUST show: 0.0s → 0.3s → 0.6s → ... → 5.2s → ... → 38.9s
   - Should see "Searching..." status with heartbeat
   - Then "Generating..." when LLM starts
Stop Test: Click stop at ~10s mark - should cancel within 1s
Result: ___________

[D02] HIGH - Mixed language
Query: refund policy apa?
Expected Route: rag_docs
Expected Answer: Refund policy from company docs
Timer Test: Continuous updates during ~30-40s retrieval
Stop Test: Click stop during "Searching..." phase
Result: ___________

[D03] HIGH - Process query
Query: how to request emergency leave
Expected Route: rag_docs
Expected Answer: Emergency leave process/steps
Timer Test: Updates during retrieval + generation
Result: ___________

[D08] HIGH - SOP query
Query: what is the SOP for handling customer complaints?
Expected Route: rag_docs
Expected Answer: SOP from Sales_SOP_MY.txt
Timer Test: Continuous updates (~30-40s)
Stop Test: Click stop during LLM generation phase
Result: ___________

[D13] HIGH - Mixed query (sales data + insights)
Query: Why did sales drop in Selangor?
Expected Route: rag_docs (should look for insights)
Expected Answer: Analysis/insights from docs or "no specific data"
Timer Test: May take longer due to context search
Result: ___________

################################################################################
# CATEGORY 4: ROBUSTNESS (9 tests)
# Expected: Graceful handling, clarification requests, or best-effort routing
################################################################################

[R01] CRITICAL - Ambiguous (no timeframe)
Query: top products
Expected Route: sales_kpi (with clarification request)
Expected Answer: Should ask "Which month?" or use latest available
Timer Test: Quick response
Result: ___________

[R02] HIGH - Too vague
Query: sales
Expected Route: sales_kpi
Expected Answer: Should ask for clarification (month, product, state?)
Result: ___________

[R04] MEDIUM - Typo tolerance
Query: salse bulan 2024-06
Expected Route: sales_kpi
Expected Answer: Should handle "salse" → "sales" typo
Result: ___________

[R06] LOW - Out of scope
Query: What's the weather today?
Expected Route: rag_docs (will try to search, find nothing)
Expected Answer: "I don't have weather information" or similar
Result: ___________

[R08] MEDIUM - Mixed language
Query: berapa sales for Cheese Burger in Mei 2024?
Expected Route: sales_kpi
Expected Answer: Cheese Burger sales for May 2024
Timer Test: Continuous updates
Result: ___________

################################################################################
# SUMMARY CHECKLIST
################################################################################

TIMER BEHAVIOR (CRITICAL):
[ ] Timer shows 0.0s initially
[ ] Timer updates every 0.3-0.5s during retrieval (heartbeat)
[ ] Timer updates during LLM startup (before first token)
[ ] Timer updates during LLM generation (with each token)
[ ] Timer NEVER freezes at 0.0s for >1 second
[ ] Timer shows correct elapsed time at completion

STOP BUTTON (CRITICAL):
[ ] Stop button visible during processing
[ ] Stop button hidden when idle
[ ] Clicking Stop cancels query within 1 second
[ ] Console shows "🛑 STOP REQUESTED" message
[ ] After stop, Submit button reappears
[ ] Can submit new query after stop

ROUTING ACCURACY:
[ ] Sales KPI questions → sales_kpi badge (S01-S15)
[ ] HR KPI questions → hr_kpi badge (H01-H10)
[ ] Document/Policy questions → rag_docs badge (D01-D16)
[ ] Ambiguous questions handled gracefully (R01-R09)

PERFORMANCE:
[ ] Simple queries (S01, H01): < 5 seconds
[ ] Complex queries (S07, H03): 5-10 seconds
[ ] RAG queries (D01, D02): 30-50 seconds (acceptable)
[ ] All queries: Timer updates continuously

################################################################################
# QUICK TEST (5 minutes)
################################################################################

Minimum tests to verify fixes:
1. [S01] sales bulan 2024-06 berapa? → Verify route + timer
2. [S07] top 3 product bulan 2024-06 → Test stop button mid-query
3. [D01] What is the annual leave entitlement per year? → TIMER STRESS TEST (40s)
4. [H01] headcount berapa? → Verify route + fast response
5. [R01] top products → Test ambiguous handling

If all 5 pass → System is reliable ✅
If any fail → Note failure details below

################################################################################
# FAILURE LOG
################################################################################

Test ID: _______
Issue: _________________________________________________________________
Expected: ______________________________________________________________
Actual: ________________________________________________________________

Test ID: _______
Issue: _________________________________________________________________
Expected: ______________________________________________________________
Actual: ________________________________________________________________

################################################################################
""")
