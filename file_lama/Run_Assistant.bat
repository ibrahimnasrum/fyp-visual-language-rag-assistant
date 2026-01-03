@echo off
echo ==================================================
echo   STARTING BURGER SALES AI ASSISTANT (GPU MODE)
echo ==================================================

REM --- PASTE THE PATH YOU COPIED BELOW ---
set ANACONDA_HOME=C:\Users\User\software

REM --- Verify path exists ---
if not exist "%ANACONDA_HOME%\Scripts\activate.bat" (
    echo.
    echo ❌ ERROR: The path "%ANACONDA_HOME%" is incorrect.
    echo Please run 'conda info --base' in your prompt to find the right one.
    pause
    exit
)

REM --- Activate Anaconda and Burger Environment ---
call "%ANACONDA_HOME%\Scripts\activate.bat"
call conda activate burger

echo.
echo Running Python Script...
python "C:\Users\User\oneclick.py"

pause