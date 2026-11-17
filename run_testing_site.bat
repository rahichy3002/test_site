@echo off
title Progsity Mock Exam & Local Judge Platform
cd /d "%~dp0"

echo =================================================================
echo   Starting Progsity Secured Exam Mock Platform & Local Judge
echo =================================================================
echo.
echo   Local Address: http://localhost:5500
echo.
echo   - Press F1 on the exam screen to test TypeWriter AI Capture & Solve.
echo   - Use the "Proctor Audit" button on top right to verify stealth metrics.
echo.
echo   Opening browser in 2 seconds...
echo.

start "" http://localhost:5500

python server.py
pause
