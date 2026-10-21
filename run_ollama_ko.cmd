@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto run
call "%~dp0setup_ollama_ko.cmd"
if errorlevel 1 exit /b 1
:run
set PYTHONUTF8=1
".venv\Scripts\python.exe" "%~dp0run_ollama_ko.py" %*
set "GALTRANSL_EXIT_CODE=%ERRORLEVEL%"
if not "%GALTRANSL_EXIT_CODE%"=="0" pause
exit /b %GALTRANSL_EXIT_CODE%
