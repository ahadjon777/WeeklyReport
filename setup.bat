@echo off
REM === BIR MARTA ISHLATILADI: hamma narsani o'rnatadi ===
cd /d "%~dp0"
echo [1/4] Virtual muhit yaratilmoqda...
python -m venv venv
if errorlevel 1 (
  echo XATO: Python topilmadi. python.org dan Python 3.10+ o'rnating ("Add to PATH" belgilang).
  pause
  exit /b 1
)
echo [2/4] Kutubxonalar o'rnatilmoqda...
venv\Scripts\python -m pip install -r requirements.txt
echo [3/4] Baza tayyorlanmoqda...
venv\Scripts\python manage.py migrate
echo [4/4] Rahbar (admin) hisobini yarating:
venv\Scripts\python manage.py createsuperuser
echo.
echo TAYYOR. Endi run.bat ni ikki marta bosing.
pause
