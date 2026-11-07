@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

set "VENV="
if exist ".venv\Scripts\activate.bat" set "VENV=.venv"
if not defined VENV if exist "venv\Scripts\activate.bat" set "VENV=venv"
if not defined VENV (
  echo Creating Python virtual environment...
  python -m venv venv
  set "VENV=venv"
)

call "!VENV!\Scripts\activate.bat"
python -m pip install -q -r requirements.txt
start "" http://localhost:8000
python -m recall.server
