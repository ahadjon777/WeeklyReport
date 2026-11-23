@echo off
REM === Xodimlarni xodimlar.csv dan ommaviy qo'shadi, parollar.csv yaratadi ===
cd /d "%~dp0"
venv\Scripts\python manage.py import_employees xodimlar.csv --out parollar.csv
pause
