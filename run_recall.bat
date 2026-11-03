@echo off
setlocal
cd /d "%~dp0"

if not exist venv (
  echo Creating Python virtual environment...
  python -m venv venv
)

call venv\Scripts\activate
python -m pip install -q -r requirements.txt
start "" http://localhost:8000
python -m recall.server
