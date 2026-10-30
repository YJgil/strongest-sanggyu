@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
 py -3 main.pyw
) else (
 python main.pyw
)
if errorlevel 1 (
 echo.
 echo Python 3 with tkinter is required. See README.txt.
 pause
)
