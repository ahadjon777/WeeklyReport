@echo off
REM === HAR KUNI: serverni ishga tushiradi ===
cd /d "%~dp0"
venv\Scripts\python manage.py migrate --noinput
venv\Scripts\python manage.py collectstatic --noinput >nul
venv\Scripts\python serve.py
pause
