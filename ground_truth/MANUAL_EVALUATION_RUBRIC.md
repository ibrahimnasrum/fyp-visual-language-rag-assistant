# Manual Answer Quality Evaluation Rubric

**Version**: 1.0  
**Date**: January 17, 2026  
**Purpose**: Structured checklist-based evaluation for 94 test questions within 8-12 hour budget

---

## Overview

This rubric provides a **structured, checklist-based approach** for evaluating answer quality without requiring full gold-standard answers. Designed for efficiency while maintaining evaluation rigor.

**Time Budget**: 8-12 hours for 94 questions (~5-8 minutes per question)  
**Evaluation Method**: Dual evaluation for pilot set (inter-rater reliability), single evaluator for remainder

---

## Evaluation Dimensions

| Dimension | Weight | Pass Threshold | Time Allocation |
|-----------|--------|----------------|-----------------|
| **Semantic Relevance** | 25% | ≥3/5 points | ~1 minute |
| **Information Completeness** | 30% | ≥4/5 points | ~2 minutes |
| **Factual Accuracy** | 30% | ≥4/5 points | ~2 minutes |
| **Presentation Quality** | 15% | ≥3/5 points | ~1 minute |
| **TOTAL** | 100% | ≥14/20 points (0.70) | ~6 minutes |

---

## Dimension 1: Semantic Relevance (5 points, 25%)

**Question**: Does the answer address what the user asked?

### Checklist

- [ ] **1 point**: Answer is related to the general topic (e.g., query about sales → answer mentions sales)
- [ ] **1 point**: Answer addresses the specific entity/subject (e.g., query mentions "Cheese Burger" → answer discusses that product)
- [ ] **1 point**: Answer addresses the specific time period if mentioned (e.g., "June 2024" → answer covers that month)
- [ ] **1 point**: Answer provides relevant context or details (not just yes/no)
- [ ] **1 point**: Answer directly answers the question without excessive tangents

### Scoring Guide

- **5/5**: Perfect alignment - answer is exactly what user needs
- **3-4/5**: Mostly relevant - answer addresses query with minor tangents
- **1-2/5**: Loosely relevant - answer related but misses key aspects
- **0/5**: Irrelevant - answer doesn't address the query

### Special Cases

- **Out-of-scope query** (e.g., "What's the weather?"): Give 4/5 if system appropriately says "cannot answer" or "out of scope"
- **Ambiguous query** (e.g., "sales"): Give 4/5 if system asks for clarification (e.g., "Do you mean sales revenue or sales process?")
- **Clarification request**: Appropriate clarification = high score (don't penalize for asking)

---

## Dimension 2: Information Completeness (5 points, 30%)

**Question**: Does the answer cover the key concepts and provide sufficient information?

### Checklist

- [ ] **1 point**: Answer includes primary information requested (e.g., headcount query → provides number or discusses headcount)
- [ ] **1 point**: Answer includes relevant secondary context (e.g., comparisons, trends, implications)
- [ ] **1 point**: Answer covers multiple aspects if query is multi-faceted (e.g., "sales by state" → mentions multiple states)
- [ ] **1 point**: Answer provides actionable or useful information (not just generic statements)
- [ ] **1 point**: Answer includes specific examples, numbers, or evidence (not vague generalities)

### Scoring Guide

- **5/5**: Comprehensive - covers all aspects with rich detail
- **4/5**: Complete - addresses main points with adequate detail
- **3/5**: Adequate - covers essentials but lacks depth
- **2/5**: Incomplete - misses key information
- **1/5**: Minimal - provides very little useful information
- **0/5**: No useful information

### Reference: Answer Criteria

Use the `answer_criteria` from test case definition:
- **must_contain**: Check if all required keywords/concepts present
- **acceptable_if_includes**: Bonus points for additional relevant concepts
- **numerical_range**: If specified, check if answer provides numbers in expected range

### Length Heuristic

- **< 50 characters**: Likely incomplete (max 3/5 unless perfectly concise)
- **50-200 characters**: Reasonable length (normal scoring)
- **> 200 characters**: Detailed (bonus consideration if relevant)

---

## Dimension 3: Factual Accuracy (5 points, 30%)

**Question**: Are numerical and factual claims correct?

### Checklist

- [ ] **2 points**: Numerical values are correct (within ±5% tolerance) OR no numbers required and facts seem plausible
- [ ] **1 point**: Dates/time periods are correct and consistent
- [ ] **1 point**: Entity names (products, states, departments) are correct and not fabricated
- [ ] **1 point**: Facts can be verified from source documents or ground truth data
- [ ] **0 points deduction**: If answer admits uncertainty ("I don't have exact data") → don't penalize

### Scoring Guide

- **5/5**: Perfectly accurate - all claims verified
- **4/5**: Mostly accurate - minor discrepancies or some unverifiable claims
- **3/5**: Partially accurate - some correct, some questionable
- **2/5**: Mostly inaccurate - majority of claims wrong
- **0-1/5**: Completely inaccurate or fabricated

### Verification Resources

1. **CALCULATED_GROUND_TRUTH.json**: Reference for KPI numerical values
2. **Source Documents**: For policy, company info, operational facts
3. **Reasonable Judgment**: If you can't verify, assess plausibility

### Common Issues to Watch For

- ❌ **Hallucinated numbers**: Random figures not from data
- ❌ **Wrong time periods**: Claims about June using May data
- ❌ **Invented entities**: Mentions products/locations not in dataset
- ✅ **Honest uncertainty**: "I don't have data for July" (GOOD - don't penalize)
- ✅ **Approximate values**: "Around RM 100,000" when exact is RM 99,852 (ACCEPTABLE)

---

## Dimension 4: Presentation Quality (5 points, 15%)

**Question**: Is the answer well-formatted, clear, and free from hallucinations?

### Checklist

- [ ] **1 point**: Clear and readable formatting (line breaks, bullets, or logical structure)
- [ ] **1 point**: No grammatical errors or awkward phrasing
- [ ] **1 point**: Professional tone appropriate for business context
- [ ] **1 point**: No obvious hallucinations or fabricated details (check for "made up", "invented", disclaimers)
- [ ] **1 point**: Appropriate level of detail (not too verbose, not too terse)

### Scoring Guide

- **5/5**: Excellent presentation - polished and professional
- **4/5**: Good presentation - clear with minor issues
- **3/5**: Adequate presentation - understandable but rough
- **2/5**: Poor presentation - difficult to read or unprofessional
- **0-1/5**: Unacceptable presentation - incomprehensible or clearly fabricated

### Formatting Examples

**Good Formatting** (5/5):
```
Sales for June 2024: RM 99,852.83

Breakdown by state:
• Selangor: RM 45,230
• KL: RM 32,100
• Penang: RM 22,522

This represents a 12% increase from May 2024.
```

**Acceptable Formatting** (3-4/5):
```
Sales for June 2024 is RM 99,852.83. Selangor has highest at RM 45,230, followed by KL and Penang. Up 12% from last month.
```

**Poor Formatting** (1-2/5):
```
sales june RM99852 selangor 45230 kl 32100 penang 22522 up 12% may
```

---

## Overall Scoring

### Calculation

```
Total Points = Semantic (0-5) + Completeness (0-5) + Accuracy (0-5) + Presentation (0-5)
Quality Score = Total Points / 20
```

### Pass/Fail Thresholds

| Quality Score | Category | Status |
|--------------|----------|--------|
| ≥ 0.85 (17+ points) | **Excellent** | ✅ PASS |
| 0.70-0.84 (14-16 points) | **Acceptable** | ✅ PASS |
| 0.50-0.69 (10-13 points) | **Marginal** | ⚠️  BORDERLINE |
| < 0.50 (0-9 points) | **Poor** | ❌ FAIL |

### Final Status Determination

**Combined with Routing**:
```
Overall Score = (0.3 × Route Score) + (0.7 × Quality Score)

Status:
- PERFECT: quality ≥ 0.80 AND route = preferred (1.0)
- ACCEPTABLE: quality ≥ 0.70 (regardless of routing)
- FAILED: quality < 0.70 OR (quality < 0.80 AND route = wrong)
```

---

## Evaluation Workflow

### Step-by-Step Process (6-8 minutes per question)

1. **Read Query** (30 seconds)
   - Understand what user is asking
   - Note any ambiguity or special requirements

2. **Read System Answer** (1 minute)
   - First impression: Does it seem relevant?
   - Note key claims and structure

3. **Evaluate Dimension 1: Semantic Relevance** (1 minute)
   - Check 5-point checklist
   - Record score (0-5)

4. **Evaluate Dimension 2: Completeness** (2 minutes)
   - Refer to answer_criteria from test case
   - Check for must_contain keywords
   - Check 5-point checklist
   - Record score (0-5)

5. **Evaluate Dimension 3: Accuracy** (2 minutes)
   - Verify numbers against CALCULATED_GROUND_TRUTH.json
   - Check dates, entities, facts
   - Check 5-point checklist
   - Record score (0-5)

6. **Evaluate Dimension 4: Presentation** (1 minute)
   - Assess formatting and clarity
   - Check for hallucinations
   - Check 5-point checklist
   - Record score (0-5)

7. **Calculate Total** (30 seconds)
   - Sum all dimension scores (0-20)
   - Convert to 0-1 scale (divide by 20)
   - Record quality_score

8. **Add Notes** (30 seconds)
   - Any special observations
   - Examples of particularly good/bad aspects

---

## Inter-Rater Reliability Protocol

### Objective

Ensure evaluation consistency between evaluators through calibration.

### Phase 1: Pilot Evaluation (10-15 questions)

**Selection Criteria**:
- Stratified sample across categories (SALES_KPI, HR_KPI, RAG_DOCS, ROBUSTNESS)
- Mix of priorities (CRITICAL, HIGH, MEDIUM, LOW)
- Include edge cases (ambiguous queries, typos, out-of-scope)

**Recommended Pilot Set** (10 questions, ~80 minutes total):

| ID | Query | Category | Priority | Why Selected |
|----|-------|----------|----------|--------------|
| S01 | sales bulan 2024-06 berapa? | SALES_KPI | HIGH | Simple KPI query |
| S07 | top 3 product bulan 2024-06 | SALES_KPI | CRITICAL | Ranking query |
| H01 | headcount berapa? | HR_KPI | HIGH | Simple HR query |
| H08 | staff with more than 5 years | HR_KPI | LOW | Multi-route ambiguous (user's example) |
| D01 | What is the annual leave entitlement per year? | RAG_DOCS | CRITICAL | Policy query |
| D13 | Why did sales drop in Selangor? | RAG_DOCS | HIGH | Analytical query |
| R01 | top products | ROBUSTNESS | CRITICAL | Ambiguous - needs clarification |
| R03 | staff | ROBUSTNESS | MEDIUM | Vague - multi-route (user's example) |
| R04 | salse bulan 2024-06 | ROBUSTNESS | MEDIUM | Typo handling |
| R06 | What's the weather today? | ROBUSTNESS | LOW | Out of scope |

### Phase 2: Dual Evaluation

**Process**:
1. Both evaluators independently score all 10 pilot questions using rubric
2. Record scores in evaluation sheet (see template below)
3. Do NOT discuss during evaluation

**Time Estimate**: 10 questions × 8 minutes × 2 evaluators = ~2.5 hours

### Phase 3: Calculate Inter-Rater Agreement

**Cohen's Kappa Calculation**:
```python
from sklearn.metrics import cohen_kappa_score

evaluator1_scores = [0.85, 0.70, 0.90, ...]  # Quality scores (0-1)
evaluator2_scores = [0.80, 0.75, 0.90, ...]

# Convert to categorical for kappa
# PASS (≥0.70) vs FAIL (<0.70)
eval1_categories = [1 if s >= 0.70 else 0 for s in evaluator1_scores]
eval2_categories = [1 if s >= 0.70 else 0 for s in evaluator2_scores]

kappa = cohen_kappa_score(eval1_categories, eval2_categories)
print(f"Cohen's Kappa: {kappa:.3f}")
```

**Interpretation**:
- **κ ≥ 0.80**: Excellent agreement → Proceed to full evaluation
- **κ 0.60-0.79**: Good agreement → Discuss discrepancies, refine rubric, optionally re-pilot
- **κ < 0.60**: Poor agreement → Revise rubric, conduct training session, re-pilot

### Phase 4: Calibration Session

**Agenda** (1 hour):
1. Compare dimension-level scores for each pilot question (15 min)
2. Identify discrepancies > 0.2 (20 min)
   - Discuss interpretation differences
   - Clarify rubric ambiguities
3. Refine rubric based on findings (15 min)
4. Re-score 2-3 contentious questions together (10 min)

**Outcome**: Aligned understanding of rubric criteria

### Phase 5: Full Evaluation

**Process**:
- After calibration, ONE evaluator scores remaining 84 questions
- Spot-check: Second evaluator scores random 5% sample (~4 questions) to verify consistency

**Time Estimate**: 84 questions × 6 minutes = ~8.5 hours

---

## Evaluation Recording Template

### CSV Format

```csv
question_id,query,actual_route,preferred_route,semantic_score,completeness_score,accuracy_score,presentation_score,quality_score,quality_status,route_score,route_status,overall_score,final_status,notes,evaluator
H08,staff with more than 5 years,rag_docs,hr_kpi,4,5,4,4,0.85,EXCELLENT,0.7,ACCEPTABLE,0.81,ACCEPTABLE,"Answer comprehensive despite wrong route. Includes tenure discussion and HR policy references.",Evaluator1
S01,sales bulan 2024-06 berapa?,sales_kpi,sales_kpi,5,4,5,4,0.90,EXCELLENT,1.0,PERFECT,0.93,PERFECT,"Perfect routing. Correct numerical value (RM 99,852.83) with good formatting.",Evaluator1
```

### Required Fields

- **question_id**: Test case ID (e.g., "H08", "S01")
- **query**: User's question text
- **actual_route**: Route system took
- **preferred_route**: Optimal route from test case
- **semantic_score**: 0-5 points (Dimension 1)
- **completeness_score**: 0-5 points (Dimension 2)
- **accuracy_score**: 0-5 points (Dimension 3)
- **presentation_score**: 0-5 points (Dimension 4)
- **quality_score**: 0.00-1.00 (sum of dimensions / 20)
- **quality_status**: EXCELLENT / ACCEPTABLE / MARGINAL / POOR
- **route_score**: 0.0 / 0.7 / 1.0
- **route_status**: PERFECT / ACCEPTABLE / WRONG
- **overall_score**: 0.00-1.00 (weighted: 0.3×route + 0.7×quality)
- **final_status**: PERFECT / ACCEPTABLE / FAILED
- **notes**: Free-text observations (optional but recommended)
- **evaluator**: Evaluator ID (Evaluator1, Evaluator2)

---

## Common Evaluation Scenarios

### Scenario 1: Good Answer, Wrong Route

**Example**: Query "staff with more than 5 years" → routes to rag_docs (expected hr_kpi) but provides comprehensive tenure analysis

**Scoring**:
- Semantic: 4-5 (addresses query)
- Completeness: 4-5 (covers key concepts)
- Accuracy: 3-4 (may lack precise numbers)
- Presentation: 4-5 (well-formatted)
- **Quality Score**: ~0.80-0.90 → **EXCELLENT/ACCEPTABLE**
- Route Score: 0.7 (acceptable alternative)
- **Overall Score**: 0.79 → **ACCEPTABLE**

**Status**: ✅ PASS - User satisfied despite routing inefficiency

### Scenario 2: Perfect Route, Poor Answer

**Example**: Query "sales June 2024" → routes to sales_kpi (correct) but answer says "I don't have data for June"

**Scoring**:
- Semantic: 2-3 (acknowledges query but doesn't answer)
- Completeness: 1-2 (no useful information)
- Accuracy: 3 (honest uncertainty, not fabricated)
- Presentation: 3 (clear but unhelpful)
- **Quality Score**: ~0.45-0.55 → **MARGINAL/POOR**
- Route Score: 1.0 (perfect)
- **Overall Score**: 0.62 → **FAILED**

**Status**: ❌ FAIL - Routing correct but user not satisfied

### Scenario 3: Ambiguous Query with Clarification

**Example**: Query "sales" → system asks "Do you mean sales revenue, sales process, or sales team?"

**Scoring**:
- Semantic: 4-5 (appropriate clarification request)
- Completeness: 3-4 (provides options but not final answer)
- Accuracy: 5 (no factual claims to verify)
- Presentation: 4-5 (clear formatting)
- **Quality Score**: ~0.80-0.85 → **EXCELLENT**
- Route Score: 1.0 or 0.7 (depends on test case acceptable_routes)
- **Overall Score**: 0.80-0.90 → **ACCEPTABLE/PERFECT**

**Status**: ✅ PASS - Appropriate behavior for ambiguous query

### Scenario 4: Out-of-Scope Query

**Example**: Query "What's the weather today?" → system responds "I cannot provide weather information"

**Scoring**:
- Semantic: 4 (appropriate rejection)
- Completeness: 3 (explains limitation)
- Accuracy: 5 (honest about capabilities)
- Presentation: 4 (clear)
- **Quality Score**: ~0.80 → **ACCEPTABLE**
- Route Score: varies (likely 0.7-1.0 depending on expected handling)
- **Overall Score**: 0.75-0.85 → **ACCEPTABLE**

**Status**: ✅ PASS - Correct behavior for out-of-scope request

---

## Quality Assurance

### Self-Checks During Evaluation

- [ ] Did I read the answer_criteria from test case before scoring?
- [ ] Did I verify numerical claims against ground truth if available?
- [ ] Did I consider multi-route acceptance for ambiguous queries?
- [ ] Did I avoid penalizing honest uncertainty ("I don't have data")?
- [ ] Did I reward appropriate clarification requests?
- [ ] Are my scores consistent with previous similar queries?

### Spot-Check Protocol

After every 20 evaluations, randomly re-evaluate 2 previous questions:
- Compare scores
- If discrepancy > 0.15, review both and adjust if needed
- Document any rubric interpretation changes

---

## Appendix A: Quick Reference Checklist

**Print this page for quick reference during evaluation**

### Scoring Shorthand

| Score | Quality | Symbol |
|-------|---------|--------|
| 0.85-1.00 | Excellent | ⭐⭐⭐ |
| 0.70-0.84 | Acceptable | ⭐⭐ |
| 0.50-0.69 | Marginal | ⭐ |
| 0.00-0.49 | Poor | ❌ |

### Dimension Quick Checks

**Semantic (5 pts)**: Topic? Entity? Time? Context? Direct answer?  
**Completeness (5 pts)**: Primary info? Context? Multi-aspect? Actionable? Specific?  
**Accuracy (5 pts)**: Numbers correct? Dates right? Entities real? Verifiable? (Honest uncertainty OK)  
**Presentation (5 pts)**: Formatting? Grammar? Professional? No hallucination? Appropriate detail?

### Common Pitfalls to Avoid

- ❌ Don't penalize appropriate clarification requests
- ❌ Don't penalize honest uncertainty ("I don't have data")
- ❌ Don't expect perfect routing if answer quality high
- ❌ Don't give perfect accuracy score to unverifiable claims
- ✅ Do refer to answer_criteria before scoring
- ✅ Do verify numbers against ground truth
- ✅ Do consider multi-route acceptance

---

## Appendix B: Example Evaluation

**Test Case**: H08

```json
{
  "id": "H08",
  "query": "staff with more than 5 years",
  "preferred_route": "hr_kpi",
  "acceptable_routes": ["hr_kpi", "rag_docs"],
  "answer_criteria": {
    "must_contain": ["years", "staff"],
    "acceptable_if_includes": ["5 years", "tenure", "experienced", "retention"],
    "min_semantic_similarity": 0.70
  }
}
```

**System Response**:
```
Based on the HR data, we have several staff members with more than 5 years of tenure. 
The average tenure of experienced staff is around 6.5 years. These long-serving employees 
contribute significantly to our retention metrics and organizational knowledge. Our HR 
policies encourage retention through competitive compensation and career development 
opportunities.
```

**Actual Route**: rag_docs

### Evaluation

**Dimension 1: Semantic Relevance (5 pts)**
- [x] Related to topic (tenure/experience) → 1 pt
- [x] Addresses specific entity (staff) → 1 pt
- [x] Addresses specific criteria (5+ years) → 1 pt
- [x] Provides relevant context (retention, policies) → 1 pt
- [x] Directly answers question → 1 pt
**Score: 5/5**

**Dimension 2: Information Completeness (5 pts)**
- [x] Includes primary info (staff with 5+ years) → 1 pt
- [x] Includes context (retention metrics, policies) → 1 pt
- [x] Multi-faceted (tenure, policies, implications) → 1 pt
- [x] Actionable (mentions retention strategies) → 1 pt
- [x] Specific (6.5 years average) → 1 pt
**Score: 5/5**

**Dimension 3: Factual Accuracy (5 pts)**
- [x] Numbers seem plausible (6.5 years average) → 2 pts (cannot verify precisely)
- [x] No incorrect dates → 1 pt
- [x] Entity names correct (staff, HR) → 1 pt
- [x] Claims seem verifiable → 1 pt
**Score: 5/5** (Note: Give benefit of doubt when cannot verify but plausible)

**Dimension 4: Presentation Quality (5 pts)**
- [x] Clear formatting (paragraph structure) → 1 pt
- [x] No grammatical errors → 1 pt
- [x] Professional tone → 1 pt
- [x] No hallucinations detected → 1 pt
- [ ] Good detail level but could use bullets → 0.5 pt
**Score: 4.5/5** → Round to **4/5**

### Final Scoring

```
Total Points: 5 + 5 + 5 + 4 = 19/20
Quality Score: 19/20 = 0.95 → EXCELLENT

Route Score: 0.7 (rag_docs is acceptable alternative)
Route Status: ACCEPTABLE

Overall Score: (0.3 × 0.7) + (0.7 × 0.95) = 0.88
Final Status: ACCEPTABLE (quality ≥ 0.70, route acceptable)
```

**Notes**: "Answer comprehensive despite non-preferred routing. Provides numerical insight (6.5 years), discusses retention factors, and references HR policies. Demonstrates that rag_docs can effectively answer this query even though hr_kpi is preferred."

---

**Document Status**: ✅ COMPLETE  
**Ready for Use**: Yes - begin with pilot evaluation  
**Estimated Total Time**: 10-13 hours (pilot 2.5h + calibration 1h + full eval 8.5h + buffer 1h)
