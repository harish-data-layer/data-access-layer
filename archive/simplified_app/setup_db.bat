@echo off
echo Setting up TAI Database...

:: Activate Virtual Environment
call venv\Scripts\activate.bat

:: Install Requirements (Optional, if not already)
:: pip install -r requirements.txt

:: Run Migrations
echo Running Migrations...
alembic upgrade head

:: Run Checker/Seed Script
echo Running Seed Script...
python -m db.seed

echo Setup Complete.
pause
