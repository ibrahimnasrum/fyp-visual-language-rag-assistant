@echo off
setlocal

REM Optional: enable UTF-8 in the console (for emojis / BM text)
chcp 65001 >nul

echo ==================================================
echo   STARTING COMPANY AI ASSISTANT (SALES CEO KPI)
echo ==================================================

REM ==================================================
REM  1) Set your Anaconda/Miniconda base path
REM     (Run this in CMD: conda info --base)
REM ==================================================
set "ANACONDA_HOME=C:\Users\User\software"

REM --- Verify path exists ---
if not exist "%ANACONDA_HOME%\Scripts\activate.bat" (
    echo.
    echo ❌ ERROR: The path "%ANACONDA_HOME%" is incorrect.
    echo Fix it by running: conda info --base
    echo Then set ANACONDA_HOME to that path.
    pause
    exit /b 1
)

REM ==================================================
REM  2) Activate conda env (burger)
REM ==================================================
call "%ANACONDA_HOME%\Scripts\activate.bat"
call conda activate burger

REM ==================================================
REM  3) Run the assistant script from THIS folder
REM     (Put this .bat, .py, and both CSV files together)
REM ==================================================
set "SCRIPT_DIR=%~dp0"
set "SCRIPT=%SCRIPT_DIR%oneclick_sales_kpi_v2.py"

REM If the KPI script is not found, fallback to the old oneclick.py
if not exist "%SCRIPT%" (
    echo.
    echo ⚠️  WARNING: oneclick_sales_kpi_v2.py not found in:
    echo     %SCRIPT_DIR%
    echo     Falling back to oneclick.py
    set "SCRIPT=%SCRIPT_DIR%oneclick.py"
)

if not exist "%SCRIPT%" (
    echo.
    echo ❌ ERROR: Cannot find assistant script.
    echo Put one of these files in the same folder as this .bat:
    echo   - oneclick_sales_kpi_v2.py  (recommended)
    echo   - oneclick.py
    pause
    exit /b 1
)

REM --- Check required data files ---
if not exist "%SCRIPT_DIR%retail_burger_sales.csv" (
    echo.
    echo ❌ ERROR: retail_burger_sales.csv not found in:
    echo     %SCRIPT_DIR%
    pause
    exit /b 1
)

if not exist "%SCRIPT_DIR%HR.csv" (
    echo.
    echo ❌ ERROR: HR.csv not found in:
    echo     %SCRIPT_DIR%
    pause
    exit /b 1
)

REM --- Optional: warn if Ollama is missing (needed for RAG fallback) ---
where ollama >nul 2>nul
if errorlevel 1 (
    echo.
    echo ⚠️  WARNING: Ollama not found in PATH.
    echo If you use the Llama3 RAG fallback, install Ollama and run:
    echo   ollama pull llama3
    echo.
)

echo.
echo Running Python Script:
echo   %SCRIPT%
python "%SCRIPT%"

pause
endlocal
