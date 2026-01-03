@echo off
echo ==================================================
echo   STARTING MY RETAILCHAIN AI ASSISTANT
echo ==================================================

set ANACONDA_HOME=C:\Users\User\software

if not exist "%ANACONDA_HOME%\Scripts\activate.bat" (
    echo.
    echo ERROR: The path "%ANACONDA_HOME%" is incorrect.
    echo Run: conda info --base
    pause
    exit
)

call "%ANACONDA_HOME%\Scripts\activate.bat"
call conda activate burger

echo.
echo Python being used:
python -c "import sys; print(sys.executable)"

echo.
echo Running Python Script...
python "C:\Users\User\oneclick_my_retailchain_v1.py"

pause
