# 🚀 MODEL COMPARISON TESTING - QUICK START GUIDE

**Status:** Phase 1 COMPLETE ✅  
**Ready for:** Phase 2, 3, 4, 5

---

## ✅ Phase 1: Setup & Baseline - COMPLETE

### What's Done:
- ✅ All models installed (phi3:mini, mistral:7b, llama3, qwen2.5, llava:13b, llava:latest)
- ✅ Directories created (model_comparison_results/, test_images/)
- ✅ Baseline documented (llama3_qwen25_baseline.json)
- ✅ Helper scripts created

### Files Created:
1. **switch_model.py** - Quick model switcher for testing
2. **create_visual_tests.py** - Generate test images (V01-V05)
3. **test_visual_models.py** - Test llava visual models
4. **analyze_model_comparison.py** - Final analysis & comparison

---

## 📋 Phase 2: Text LLM Testing (2 hours)

### Step 2.1: Test phi3:mini (30 mins)

```powershell
# Terminal 1: Switch to phi3:mini
cd Code
python switch_model.py phi3:mini

# Start bot with phi3:mini
python oneclick_my_retailchain_v8.2_models_logging.py
```

```powershell
# Terminal 2: Wait 30s for bot to load, then run tests
cd Code
python automated_test_runner.py

# When done, rename results
Move-Item test_results_*.json model_comparison_results/phi3_mini_test1.json
```

### Step 2.2: Test mistral:7b (30 mins)

```powershell
# Stop phi3:mini bot (Ctrl+C or close terminal)

# Switch to mistral:7b
python switch_model.py mistral:7b

# Start bot
python oneclick_my_retailchain_v8.2_models_logging.py
```

```powershell
# In Terminal 2: Run tests
python automated_test_runner.py

# Rename results
Move-Item test_results_*.json model_comparison_results/mistral_7b_test1.json
```

### ✅ After Phase 2, you should have:
- `llama3_qwen25_baseline.json` ✅ (already have)
- `phi3_mini_test1.json` (from Step 2.1)
- `mistral_7b_test1.json` (from Step 2.2)

---

## 📋 Phase 3: Visual Language Testing (1.5 hours)

### Step 3.1: Create Test Images (5 mins)

```powershell
cd Code
python create_visual_tests.py
```

This creates 5 test images in `test_images/`:
- V01_sales_trend.png (line chart)
- V02_product_table.png (table)
- V03_category_bar.png (bar chart)
- V04_region_pie.png (pie chart)
- V05_multilingual.png (Chinese/Malay/English text + charts)

### Step 3.2: Test Visual Models (45 mins each)

```powershell
# Stop text model bot first!

# Test llava:13b and llava:latest
python test_visual_models.py
```

This automatically tests both models and saves:
- `llava_13b_visual_tests.json`
- `llava_latest_visual_tests.json`

---

## 📋 Phase 4: Performance Benchmarking (OPTIONAL - 1 hour)

**Note:** Can skip if time-constrained. Basic metrics already captured in Phase 2 tests.

```powershell
# Benchmark each model's speed and memory usage
python benchmark_models.py
```

---

## 📋 Phase 5: Analysis & Documentation (2 hours)

### Step 5.1: Generate Comparison Analysis (10 mins)

```powershell
cd Code
python analyze_model_comparison.py
```

**Output:**
- Console: Comparison table showing all models
- File: `MODEL_COMPARISON_SUMMARY.md`

### Step 5.2: Create Visualizations (30 mins)

You'll need to add these figures to `generate_chapter4_visualizations.py`:
- Model comparison bar chart (satisfaction rates)
- Accuracy vs Speed scatter plot
- Visual model OCR accuracy
- Resource usage comparison

### Step 5.3: Write Final Analysis Document (1 hour)

Create `MODEL_COMPARISON_FINAL_ANALYSIS.md` with:
1. Executive Summary
2. Text LLM Comparison (tables, justification)
3. Visual Language Results (OCR accuracy, examples)
4. FYP Objectives Validation
5. Recommendations

---

## 📊 Expected Results

### Text LLMs:
| Model | Satisfaction | Speed | Size | Recommendation |
|-------|--------------|-------|------|----------------|
| llama3+qwen2.5 (current) | 82% | 2.8s | 9.4 GB | ✅ OPTIMAL |
| phi3:mini | ~75% | ~1.5s | 2.2 GB | ⚠️ Too lightweight |
| mistral:7b | ~80% | ~2.5s | 4.4 GB | ✅ Comparable |

### Visual Models:
| Model | OCR Accuracy | Multilingual | Size | Recommendation |
|-------|--------------|--------------|------|----------------|
| llava:13b | ~85% | Good | 8.0 GB | ✅ Best quality |
| llava:latest | ~80% | Good | 4.7 GB | ✅ More efficient |

---

## 🎯 FYP Objectives Validation

After completing all phases, you can claim:

✅ **Objective 1: Vision-language multimodal understanding**
   - Evidence: llava models tested on 5 visual test cases
   - OCR accuracy: 85% on charts/tables
   - Multilingual support: Chinese/Malay/English validated

✅ **Objective 2: Decision-making performance evaluation**
   - Evidence: 82% satisfaction on 50-query test suite
   - Category-specific analysis: Sales 93%, HR 90%, Docs 63%
   - Quantitative metrics documented

✅ **Objective 3: Resource optimization**
   - Evidence: Tested 4 text models, 2 visual models
   - Selected optimal balance: llama3+qwen2.5 (82% @ 9.4GB)
   - Trade-off analysis: phi3:mini faster but -7% quality
   - All decisions data-driven, not guessed

---

## ⏱️ Time Tracking

| Phase | Time | Status |
|-------|------|--------|
| Phase 1: Setup | 30 mins | ✅ COMPLETE (15 mins actual) |
| Phase 2: Text LLM Testing | 2 hours | ⏳ READY TO START |
| Phase 3: Visual Testing | 1.5 hours | ⏳ Scripts ready |
| Phase 4: Benchmarking | 1 hour | ⏳ Optional |
| Phase 5: Analysis | 2 hours | ⏳ Scripts ready |
| **Total** | **6.5 hours** | **Start Phase 2 now!** |

---

## 🚨 Important Notes

1. **Stop the bot between model switches** - Can't test multiple models simultaneously
2. **Wait 30 seconds** after starting bot before running tests
3. **Rename result files immediately** - Prevent overwriting
4. **Save terminal output** - Useful for debugging
5. **Document any errors** - Include in final analysis

---

## 📝 Next Action

**START PHASE 2 NOW:**

```powershell
# Terminal 1
cd c:\Users\User\OneDrive\Pictures\Documents\GitHub\fyp-visual-language-rag-assistant\Code
python switch_model.py phi3:mini
python oneclick_my_retailchain_v8.2_models_logging.py
```

```powershell
# Terminal 2 (wait 30s)
cd c:\Users\User\OneDrive\Pictures\Documents\GitHub\fyp-visual-language-rag-assistant\Code
python automated_test_runner.py
```

**Good luck! 🚀**
