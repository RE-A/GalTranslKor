@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto install
py -3.11 -m venv .venv
if errorlevel 1 goto failed
:install
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip check
if errorlevel 1 goto failed
echo Setup complete. Set backendSpecific.Ollama.model in examples\ollama_ko\config.yaml.
exit /b 0
:failed
echo Setup failed. Python 3.11 with the Windows Python Launcher and Internet access are required.
exit /b 1
