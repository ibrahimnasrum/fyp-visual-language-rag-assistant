# Knowledge Source Hierarchy - Correction

## ❌ Previous (INCORRECT) Understanding

The previous implementation incorrectly listed `reference/` folder as PRIMARY SOURCE in the knowledge hierarchy. This was a misunderstanding - the `reference/` folder contains:
- Copy of Chapter 6 - Prompt Engineering.ipynb - Colab.pdf
- Copy of Chapter 7 - Advanced Text Generation Techniques.ipynb - Colab.pdf
- Hands-On Large Language Models_251204_001050.pdf

These materials were **for the developer's reference** when designing the prompt engineering system, NOT for the CEO Bot to use as a data source at runtime.

## ✅ Corrected Understanding

### Actual CEO Bot Data Sources (Runtime):

1. **docs/ folder** → Policy/procedure documents loaded as `[DOC:filename]`
   - Company_Profile_MY.txt
   - FAQ_MY.txt
   - HR_Policy_MY.txt
   - Sales_SOP_MY.txt
   - State_Operations_*.txt
   - Performance_Drivers_Analysis.txt
   - Ops_Incident_Report_MY.txt

2. **data/ folder** → Structured datasets processed as KPI facts
   - MY_Retail_Sales_2024H1.csv (29,635 transactions)
   - MY_Retail_HR_Employees.csv

3. **OCR text** → Visual document analysis (when images provided)

### Corrected Knowledge Hierarchy (in System Prompt):

```
## KNOWLEDGE SOURCE HIERARCHY (CRITICAL)
Use sources in this exact priority order:
1. [DOC:filename] documents (Company policies, SOPs, FAQs from docs/ folder) — PRIMARY SOURCE for policy/procedure questions
2. Computed KPI facts (Sales/HR metrics from data/ folder CSVs) — PRIMARY SOURCE for quantitative analysis
3. Retrieved context (RAG-retrieved paragraphs from [DOC:...]) — SUPPORTING EVIDENCE
4. OCR text (visual document analysis) — ADDITIONAL SOURCE when images provided

**Source Selection Rules:**
- Policy/SOP questions → Use ONLY [DOC:filename] citations
- Sales/HR metrics → Use computed_kpi_facts (deterministic calculations)
- General business questions → Combine [DOC:...] context + KPI facts
- If no [DOC:...] evidence exists for policy question → Say "Policy document not available"
- NEVER infer policy from CSV data (Sales/HR records are NOT policy documents)
```

## 📝 Changes Made

### 1. System Prompt (`get_ceo_system_prompt()`)
- ✅ Removed incorrect reference to `reference/` folder
- ✅ Updated hierarchy to reflect actual runtime data sources
- ✅ Clarified dual PRIMARY sources: [DOC:...] for policy, KPI facts for metrics
- ✅ Added explicit source selection rules

### 2. Prompt Builder (`build_ceo_prompt()`)
- ✅ Removed `reference_materials` parameter (not needed)
- ✅ Updated function signature to 7 parameters (was 8)
- ✅ Updated docstring to clarify data sources
- ✅ Removed "REFERENCE MATERIALS" section from prompt template
- ✅ Updated comment numbering (3, 4, 5, 6, 7, 8 → correct sequence)

### 3. Documentation Updates
- ✅ Updated PROMPT_ENGINEERING_IMPLEMENTATION.md
- ✅ Updated test_prompt_engineering.py
- ✅ Created this correction document

## 🎯 Key Takeaway

**reference/ folder** = Learning materials for prompt engineering design (one-time use)  
**docs/ folder** = Actual business documents for CEO Bot (runtime data)  
**data/ folder** = Actual business metrics for CEO Bot (runtime data)

The CEO Bot operates on `docs/` and `data/` folders only. The `reference/` folder was only for the developer to learn how to build proper prompts.

---

**Date:** 2025-01-14  
**Status:** ✅ Corrected and verified (no syntax errors)
