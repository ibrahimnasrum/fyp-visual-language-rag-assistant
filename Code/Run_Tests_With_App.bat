@echo off
REM Automated Testing with Gradio App - One-Click Solution
echo ============================================================
echo FYP AUTOMATED TEST RUNNER - v8.2
echo ============================================================
echo.
echo This will:
echo 1. Start your Gradio app (v8.2) in background
echo 2. Wait 30 seconds for app to load
echo 3. Run automated tests with advanced metrics
echo 4. Generate confusion matrix and latency visualizations
echo.
pause

cd /d "%~dp0"

echo.
echo [1/3] Starting Gradio app in background...
start /B python oneclick_my_retailchain_v8.2_models_logging.py

echo.
echo [2/3] Waiting 30 seconds for app to initialize...
timeout /t 30 /nobreak

echo.
echo [3/3] Running automated tests...
python automated_test_runner.py

echo.
echo ============================================================
echo DONE! Check these files:
echo   - test_results_TIMESTAMP.json
echo   - test_results_TIMESTAMP.csv
echo   - confusion_matrix_TIMESTAMP.png
echo   - latency_distribution_TIMESTAMP.png
echo ============================================================
echo.
echo Note: Gradio app is still running in background on port 7860.
echo Open browser: http://127.0.0.1:7860
echo Press Ctrl+C to stop it, or close this window.
echo.
pause
