@echo off

:: 1. Check if a message was provided as a command-line argument
set msg=%~1

:: 2. If no argument, ask for input (interactive mode)
if "%msg%"=="" (
    echo Updating Database Schema...
    set /p msg="Enter description of your changes (e.g., 'added phone number'): "
)

:: 3. Activate Virtual Environment
call venv\Scripts\activate.bat

:: 4. Generate Migration
echo.
echo [1/2] Generating migration for: "%msg%"...
alembic revision --autogenerate -m "%msg%"

:: 5. Apply Changes
echo.
echo [2/2] Applying changes to database...
alembic upgrade head

echo.
echo ===========================================
echo   SUCCESS! Database schema updated.
echo ===========================================
