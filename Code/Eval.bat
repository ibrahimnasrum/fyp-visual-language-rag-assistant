@echo off
cd /d "%~dp0"

echo ==========================================
echo   RUN AUTO EVALUATION (MY RETAILCHAIN)
echo ==========================================

set "CONDA_BASE=C:\Users\User\software"

echo.
echo Checking conda...
if exist "%CONDA_BASE%\condabin\conda.bat" (
  echo Found: %CONDA_BASE%\condabin\conda.bat
  call "%CONDA_BASE%\condabin\conda.bat" activate burger
) else (
  echo NOT FOUND: %CONDA_BASE%\condabin\conda.bat
  echo Trying activate.bat...
  if exist "%CONDA_BASE%\Scripts\activate.bat" (
    echo Found: %CONDA_BASE%\Scripts\activate.bat
    call "%CONDA_BASE%\Scripts\activate.bat"
    call conda activate burger
  ) else (
    echo ERROR: Cannot find conda.bat or activate.bat in:
    echo   %CONDA_BASE%
    echo Please run this in Anaconda Prompt:
    echo   conda info --base
    echo Then update CONDA_BASE in this .bat
    pause
    exit /b 1
  )
)

echo.
echo Python being used:
python -c "import sys; print(sys.executable)"

echo.
echo Running auto eval...
python "C:\Users\User\eval\run_auto_eval.py" ^
  --assistant "C:\Users\User\oneclick_my_retailchain_v2_models_logging.py" ^
  --questions "C:\Users\User\eval\questions.csv" ^
  --outdir "C:\Users\User\eval\out" ^
  --models llama3:latest mistral:latest qwen2.5:7b ^
  --repeat 1

echo.
echo DONE. Check output files:
echo   C:\Users\User\eval\out\results_raw.csv
echo   C:\Users\User\eval\out\results_summary.csv
pause
