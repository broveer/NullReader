@echo off
title Infinity Comic Reader Server
echo =========================================
echo      Updating Library Data...
echo =========================================

:: Run the PowerShell script to parse new CBZ files
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0UpdateLibrary.ps1"

echo.
echo =========================================
echo      Starting Comic Reader via Python
echo =========================================
echo Opening browser...
echo If the browser does not open, please navigate to http://localhost:8080/index.html
echo 

python server.py

:: Keep window open if server fails
pause