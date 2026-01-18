# Two-Tier Evaluation Implementation - Quick Start Guide

**Date**: January 17, 2026  
**Status**: ✅ COMPLETE - Ready for use

---

## What's Been Implemented

### 1. ✅ FYP Documentation
**File**: [FYP_EVALUATION_METHODOLOGY_REDESIGN.md](FYP_EVALUATION_METHODOLOGY_REDESIGN.md)

Complete 10-section academic documentation covering:
- Limitation discovery (routing mismatch ≠ bad answer)
- Root cause analysis (binary evaluation conflates routing vs quality)
- Evaluation philosophy (quality-first, routing-secondary)
- Ground truth ambiguity handling (multi-route acceptance)
- Manual validation methodology (checklist-based rubric)
- Two-tier evaluation framework architecture
- Implementation roadmap
- Expected outcomes and academic contribution

**Use for**: FYP thesis chapter, presentations, documentation

### 2. ✅ Ground Truth Test Suite Enhancement
**File**: [comprehensive_test_suite.py](comprehensive_test_suite.py) (updated)

**What Changed**:
- Added `preferred_route` field (optimal route)
- Added `acceptable_routes` list (valid alternatives)
- Added `answer_criteria` dict with:
  - `must_contain`: Required keywords
  - `acceptable_if_includes`: Bonus keywords
  - `min_semantic_similarity`: Threshold (0.0-1.0)
  - `clarification_expected`: For ambiguous queries
  - `out_of_scope`: For invalid requests

**Example**: H08 now accepts both `hr_kpi` (preferred) and `rag_docs` (acceptable)

### 3. ✅ Answer Quality Evaluator
**File**: [answer_quality_evaluator.py](answer_quality_evaluator.py) (new)

**Features**:
- **Semantic similarity** using sentence-transformers (cosine similarity)
- **Completeness checking** against answer_criteria keywords
- **Factual accuracy** verification (numerical claims, dates, entities)
- **Presentation quality** assessment (formatting, hallucinations, clarity)
- Weighted scoring: 25% + 30% + 30% + 15% = 100%
- Fallback to keyword-based if semantic model unavailable

**Functions**:
- `evaluate_answer_quality()` → quality_score (0-1), breakdown, justification
- `evaluate_route_accuracy()` → route_score (1.0/0.7/0.0), route_status
- `compute_overall_evaluation()` → overall_score (0.3×route + 0.7×quality), final_status

### 4. ✅ Manual Evaluation Rubric
**File**: [../ground_truth/MANUAL_EVALUATION_RUBRIC.md](../ground_truth/MANUAL_EVALUATION_RUBRIC.md) (new)

**Contents**:
- 4-dimension checklist (Semantic, Completeness, Accuracy, Presentation)
- 5-point scale per dimension → 20 points total → 0-1 quality score
- Pass threshold: ≥0.70 (14/20 points)
- Inter-rater reliability protocol (pilot 10 questions, Cohen's kappa, calibration)
- Time budget: 6-8 min/question, total 10-13 hours for 94 questions
- CSV recording template
- Common scenario examples

**Use for**: Human evaluation of test results

### 5. ✅ Updated Automated Test Runner
**File**: [automated_test_runner.py](automated_test_runner.py) (updated)

**What Changed**:
- Import answer_quality_evaluator module
- Initialize `AnswerQualityEvaluator` on startup
- Pass full `test_case` to `run_single_test()`
- Evaluate both routing (Tier 1) and quality (Tier 2)
- Compute weighted overall_score
- New status values: `PERFECT`, `ACCEPTABLE`, `FAILED` (replaces `PASS`/`FAIL`)
- Enhanced reporting with quality metrics breakdown
- Save CSV with quality dimensions

**Backward Compatible**: Falls back to routing-only if quality evaluation fails

---

## How to Use

### Step 1: Install Dependencies

```powershell
# Required for semantic similarity
pip install sentence-transformers scikit-learn

# Already installed (should be present)
pip install gradio_client
```

### Step 2: Run Two-Tier Automated Tests

```powershell
cd Code

# Full test suite with two-tier evaluation
python automated_test_runner.py

# Test limited subset (e.g., 3 tests per category)
python automated_test_runner.py 3
```

**Expected Output**:
```
✅ Answer quality evaluator initialized (two-tier evaluation enabled)
🔌 Connecting to http://127.0.0.1:7866...
✅ Connected successfully!

🧪 TEST [H08] (LOW)
   Query: staff with more than 5 years
   Preferred Route: hr_kpi
   Acceptable Routes: hr_kpi, rag_docs

📊 TIER 1: Routing Accuracy
   Route: rag_docs (Preferred: hr_kpi)
   Score: 0.70 (ACCEPTABLE)

📊 TIER 2: Answer Quality
   Score: 0.850
   • Semantic: 0.820
   • Completeness: 0.900
   • Accuracy: 0.880
   • Presentation: 0.800

📊 COMBINED EVALUATION
   Overall Score: 0.805
   Status: ACCEPTABLE
   ✅ ACCEPTABLE: User satisfaction threshold met
      (Note: Non-optimal routing but answer quality compensates)
```

### Step 3: Analyze Results

**JSON Output** (complete data):
```json
{
  "evaluation_mode": "two-tier",
  "total_tests": 94,
  "perfect": 45,
  "acceptable": 38,
  "failed": 9,
  "user_satisfaction_rate": 0.883,
  "results": [...]
}
```

**CSV Output** (for Excel analysis):
| id | query | route_score | quality_score | overall_score | status |
|----|-------|-------------|---------------|---------------|--------|
| H08 | staff with more than 5 years | 0.7 | 0.85 | 0.81 | ACCEPTABLE |
| S01 | sales June 2024 | 1.0 | 0.90 | 0.93 | PERFECT |

### Step 4: Manual Validation (Optional)

For research validation or inter-rater reliability:

1. **Select pilot set**: Use 10 questions from [MANUAL_EVALUATION_RUBRIC.md](../ground_truth/MANUAL_EVALUATION_RUBRIC.md) Appendix B
2. **Dual evaluation**: Two evaluators independently score using rubric
3. **Calculate kappa**: Check inter-rater agreement
4. **Calibration**: Discuss discrepancies, refine rubric
5. **Full evaluation**: One evaluator scores remaining 84 questions

---

## Understanding the Results

### Status Values

| Status | Meaning | Criteria |
|--------|---------|----------|
| **PERFECT** | ⭐⭐⭐ Ideal | route_score = 1.0 (preferred) AND quality_score ≥ 0.80 |
| **ACCEPTABLE** | ⭐⭐ Good enough | quality_score ≥ 0.70 (regardless of routing) |
| **FAILED** | ❌ Poor | quality_score < 0.70 OR (quality < 0.80 AND route = wrong) |

### Key Metrics

**User Satisfaction Rate**: (PERFECT + ACCEPTABLE) / Total  
**Routing Accuracy**: Average route_score (0.0-1.0)  
**Answer Quality**: Average quality_score (0.0-1.0)  
**Overall Score**: 0.3 × route_score + 0.7 × quality_score

### Interpreting Quality Breakdown

```
Quality Score: 0.850
• Semantic: 0.820   → Answer relevance to query
• Completeness: 0.900 → Coverage of key concepts
• Accuracy: 0.880   → Factual correctness
• Presentation: 0.800 → Formatting and clarity
```

Each dimension scored 0.0-1.0:
- **≥0.85**: Excellent
- **0.70-0.84**: Acceptable
- **0.50-0.69**: Marginal
- **<0.50**: Poor

---

## Comparing Old vs New Evaluation

### Old Method (Routing-Only)

```
Query: "staff with more than 5 years"
Expected: hr_kpi
Actual: rag_docs
Status: ❌ FAIL

Problem: Answer is comprehensive and useful, but marked as failure!
```

### New Method (Two-Tier)

```
Query: "staff with more than 5 years"
Preferred: hr_kpi
Actual: rag_docs (acceptable alternative)

Tier 1 - Routing: 0.70 (ACCEPTABLE - valid alternative route)
Tier 2 - Quality: 0.85 (EXCELLENT - comprehensive answer)
Combined: 0.81 (ACCEPTABLE)

Status: ✅ ACCEPTABLE

Insight: User satisfied despite non-optimal routing!
```

---

## Troubleshooting

### Issue: "sentence-transformers not available"

**Solution**:
```powershell
pip install sentence-transformers scikit-learn
```

**Fallback**: System automatically uses keyword-based relevance if semantic model unavailable

### Issue: Quality evaluation fails

**Symptoms**: Test output shows "⚠️ Quality evaluation failed"

**Solution**: Check test_case has `answer_criteria` field. If missing, add:
```python
"answer_criteria": {
    "must_contain": ["keyword1", "keyword2"],
    "min_semantic_similarity": 0.70
}
```

### Issue: All tests showing FAILED

**Possible Causes**:
1. Gradio app not running or wrong URL
2. Answer quality genuinely poor (check quality_breakdown)
3. Answer_criteria too strict (lower min_semantic_similarity)

**Debug**: Run single test with print statements in answer_quality_evaluator.py

---

## Configuration Options

### Disable Two-Tier Evaluation (Legacy Mode)

Edit `automated_test_runner.py`:
```python
# Change line ~18:
runner = TestRunner(use_quality_evaluation=False)
```

### Adjust Weighting

Edit `answer_quality_evaluator.py`, line ~290:
```python
# Current: 30% routing, 70% quality
overall_score = (0.3 * route_score) + (0.7 * quality_score)

# Alternative: 50% routing, 50% quality (balanced)
overall_score = (0.5 * route_score) + (0.5 * quality_score)
```

### Change Quality Threshold

Edit `answer_quality_evaluator.py`, line ~305:
```python
# Current threshold: 0.70
elif quality_score >= 0.7:

# Stricter threshold: 0.80
elif quality_score >= 0.8:
```

---

## Next Steps

### Phase 1: Validation (This Week)

1. ✅ Run automated tests with two-tier evaluation
2. ✅ Review ACCEPTABLE cases - verify answers truly acceptable
3. ✅ Review FAILED cases - verify answers truly poor
4. ✅ Adjust answer_criteria if needed

### Phase 2: Manual Validation (Next Week)

1. Select 10-question pilot set
2. Dual evaluation with second evaluator
3. Calculate Cohen's kappa (target ≥0.70)
4. Calibration session if needed
5. Full evaluation of remaining 84 questions

### Phase 3: Analysis (Week After)

1. Statistical analysis: correlation between routing and quality
2. Pattern identification: which query types benefit from multi-route
3. System recommendations: focus on routing vs quality improvements
4. FYP chapter writing

### Phase 4: Final Documentation

1. Compile results into FYP chapter
2. Create presentation slides
3. Prepare demo for evaluation
4. Write comparative analysis report

---

## Files Created/Modified Summary

### New Files (4)
1. `Code/FYP_EVALUATION_METHODOLOGY_REDESIGN.md` - Academic documentation
2. `Code/answer_quality_evaluator.py` - Quality evaluation engine
3. `ground_truth/MANUAL_EVALUATION_RUBRIC.md` - Human evaluation guide
4. `Code/TWO_TIER_IMPLEMENTATION_GUIDE.md` - This file (quick start)

### Modified Files (2)
1. `Code/comprehensive_test_suite.py` - Added multi-route acceptance and answer_criteria
2. `Code/automated_test_runner.py` - Integrated two-tier evaluation logic

### Backward Compatibility
- ✅ Old test results still work (JSON/CSV format compatible)
- ✅ Can toggle back to routing-only mode if needed
- ✅ Legacy fields (`expected_route`, `route_match`) preserved

---

## FAQ

**Q: Do I need to update all 94 test questions with answer_criteria?**  
A: No. Start with critical/high priority questions (H08, R02, R03 already updated). System falls back gracefully for missing criteria.

**Q: How accurate is semantic similarity without fine-tuning?**  
A: `all-MiniLM-L6-v2` model gives 70-80% correlation with human judgment out-of-box. Good enough for research validation.

**Q: Can I use this for live system (not just testing)?**  
A: Yes! Integrate `answer_quality_evaluator.py` into main app for real-time quality monitoring.

**Q: What if two evaluators disagree significantly (kappa < 0.60)?**  
A: Refine rubric definitions, conduct training session with examples, re-pilot 5 questions, recalculate kappa.

**Q: How do I cite this methodology in my FYP?**  
A: Refer to [FYP_EVALUATION_METHODOLOGY_REDESIGN.md](FYP_EVALUATION_METHODOLOGY_REDESIGN.md) Section 10.3 for academic framing.

---

## Contact & Support

For implementation issues or questions:
1. Check [FYP_EVALUATION_METHODOLOGY_REDESIGN.md](FYP_EVALUATION_METHODOLOGY_REDESIGN.md) Section 9 (Limitations)
2. Review [MANUAL_EVALUATION_RUBRIC.md](../ground_truth/MANUAL_EVALUATION_RUBRIC.md) Appendix A (Common Pitfalls)
3. Debug with test example in `answer_quality_evaluator.py` (run directly: `python answer_quality_evaluator.py`)

---

**Document Status**: ✅ COMPLETE  
**Last Updated**: January 17, 2026  
**Version**: 1.0  
**Ready for Production**: YES
