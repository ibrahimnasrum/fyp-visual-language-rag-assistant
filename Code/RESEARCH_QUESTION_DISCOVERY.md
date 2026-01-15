# Research: Question Discovery & Accuracy Validation
## Hypothesis Tree

### Primary Objective
Identify ALL questions in the system and validate answer accuracy

### Hypotheses About Question Sources

**H1: Follow-up questions are auto-generated**
- Confidence: HIGH (95%)
- Evidence needed: Find generate_followups() or similar function
- Location: Likely in oneclick_my_retailchain_v8.2_models_logging.py

**H2: Test questions exist in multiple files**
- Confidence: HIGH (90%)
- Evidence needed: Search test*.py files, *QUESTION*.md, *TEST*.md
- Known locations: QUESTION_INVENTORY.md, test_*.py files

**H3: Example queries hardcoded in UI**
- Confidence: MEDIUM (60%)
- Evidence needed: Search for gr.Examples or example_queries
- Location: Gradio interface definition

**H4: Questions embedded in documentation**
- Confidence: MEDIUM (50%)
- Evidence needed: Search README files for example queries
- Location: README*.md, QUICKSTART*.md

### Research Plan

**Phase 1: Question Discovery** (Current)
1. Search for follow-up generation logic → Find templates/patterns
2. Parse QUESTION_INVENTORY.md → Extract all 65 questions
3. Search test files → Extract test queries
4. Search for gr.Examples → Find UI examples
5. Search docs for "Query:" or "Question:" → Find documentation examples

**Phase 2: Question Extraction**
- Create unified question database with metadata
- Categorize by source and intent
- Tag with priority/complexity

**Phase 3: Automated Testing**
- Run each question through live system
- Capture: answer text, route, response time, follow-ups generated
- Store results for analysis

**Phase 4: Accuracy Analysis**
- Compare answers against expected behavior
- Flag: incorrect routes, incomplete answers, wrong calculations
- Generate improvement recommendations

### Progress Notes
- Started: 2026-01-15
- ✅ Phase 1 Complete: Found all question sources
  - UI Examples: 8 questions in gr.Examples
  - QUESTION_INVENTORY.md: 65 catalogued questions
  - Dynamic follow-ups: ~50+ patterns in generate_ceo_followup_questions()
- ✅ Phase 2 Complete: Created master database (MASTER_QUESTION_DATABASE.md)
  - Total: 108+ unique question patterns identified
- ✅ Phase 3 Complete: Built automated_question_analyzer.py
  - Tests all questions via Gradio Client API
  - Captures: question + full answer + follow-ups + route + timing
  - Exports comprehensive JSON for analysis
- 🔄 Phase 4 In Progress: Running tests to validate accuracy
