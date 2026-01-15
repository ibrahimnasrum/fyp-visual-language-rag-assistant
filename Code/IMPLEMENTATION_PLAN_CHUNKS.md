# IMPROVEMENT IMPLEMENTATION PLAN - CHUNK 1
**Date**: January 15, 2026  
**Baseline**: test_results_20260115_112123.csv (57/94 = 60.6%)

---

## 🎯 ANALYSIS COMPLETE - READY FOR IMPLEMENTATION

### Key Findings

1. **Answer Failures (12 cases)**:
   - Likely ALREADY FIXED (format_num corrected at 01:28 AM)
   - Test run at 11:21 AM used fixed code
   - Need fresh test to confirm

2. **Route Failures (25 cases)**:
   - **40% (10)**: HR queries misrouted to RAG
   - **32% (8)**: Sales trend queries misrouted to RAG
   - **28% (7)**: Organizational queries misrouted to Sales

---

## 📋 IMPLEMENTATION ROADMAP

### CHUNK 1: Fix HR Query Routing (11 failures → 0)
**Target Accuracy**: 60.6% → 72.3% (+11.7%)

#### Strategy A: Enhanced Few-Shot Examples
Add 30 training examples for HR granular queries to router

#### Strategy B: Keyword Rules
Add rule-based overrides for HR-specific terms

**Files to modify**:
- oneclick_my_retailchain_v8.2_models_logging.py (routing function)

**Expected time**: 2-3 hours

---

### CHUNK 2: Fix Sales Trend Routing (8 failures → 0)
**Target Accuracy**: 72.3% → 80.8% (+8.5%)

#### Strategy: Temporal Pattern Detection
Add time-series query detection logic

**Files to modify**:
- oneclick_my_retailchain_v8.2_models_logging.py (query classification)

**Expected time**: 2-3 hours

---

### CHUNK 3: Fix Organizational Query Routing (7 failures → 0)
**Target Accuracy**: 80.8% → 88.2% (+7.4%)

####Strategy: Intent Classification Layer
Add "how-to" vs "fact" query detection

**Files to modify**:
- oneclick_my_retailchain_v8.2_models_logging.py (intent detection)

**Expected time**: 2-3 hours

---

### CHUNK 4: Comprehensive Testing & Documentation
**Target Accuracy**: 88.2% → Verify actual improvement

- Run full test suite
- Compare before/after metrics
- Document each change with evidence

**Expected time**: 1-2 hours

---

## 🔄 NEXT ACTIONS

1. Start with CHUNK 1 (HR routing)
2. Document changes as we go
3. Test incrementally after each chunk
4. Create before/after comparison for FYP report

---

**Status**: Ready to implement Chunk 1  
**Current Task**: Improve HR query routing accuracy
