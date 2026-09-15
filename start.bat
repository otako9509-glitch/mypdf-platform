@echo off
title MyPDF - Starting Services

echo ========================================
echo         MyPDF Starting...
echo ========================================
echo.

cd /d C:\Users\ADIL\Documents\pj

if not exist storage\jobs mkdir storage\jobs
if not exist storage\uploads mkdir storage\uploads
if not exist storage\outputs mkdir storage\outputs

echo Starting FastAPI...
start "MyPDF API" cmd /k "cd /d C:\Users\ADIL\Documents\pj\api-fastapi && python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload"

timeout /t 3 /nobreak >nul

echo Starting Worker...
start "MyPDF Worker" cmd /k "cd /d C:\Users\ADIL\Documents\pj\worker-python && python main_worker.py"

timeout /t 2 /nobreak >nul

echo Starting Frontend...
start "MyPDF Frontend" cmd /k "cd /d C:\Users\ADIL\Documents\pj\frontend && python -m http.server 5500"

timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo MyPDF is running!
echo ========================================
echo.
echo Frontend: http://localhost:5500
echo API:      http://localhost:8080
echo.
echo ========================================

start http://localhost:5500

pause