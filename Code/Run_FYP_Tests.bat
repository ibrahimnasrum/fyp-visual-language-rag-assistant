@echo off
REM FYP Quick Test - Run evaluation to generate thesis results
echo ============================================================
echo FYP EVALUATION SUITE - QUICK START
echo ============================================================
echo.
echo This will run 30 test scenarios and generate results for thesis.
echo.
pause

cd tests
python run_fyp_tests.py

echo.
echo ============================================================
echo Done! Check fyp_evaluation_results.json for results.
echo ============================================================
echo.
pause
