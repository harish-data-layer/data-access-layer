# Easy-Start Script for the SAP Data API Server
# Run this from the root folder (tai-data-api)

$env:PYTHONIOENCODING = "utf-8"
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " Starting SAP Data API (FastAPI) on Port 8000... " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

.\venv\Scripts\python.exe -m uvicorn hybrid_orm.main:app --host 0.0.0.0 --port 8000 --reload
