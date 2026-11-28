@echo off
REM === BIR MARTA ISHLATILADI: hamma narsani o'rnatadi ===
cd /d "%~dp0"
echo [1/4] Virtual muhit yaratilmoqda...
python -m venv venv
if errorlevel 1 (
  echo XATO: Python topilmadi. Python 3.10+ o'rnating, o'rnatishda "Add Python to PATH" belgilang.
  pause
  exit /b 1
)
echo [2/4] Kutubxonalar o'rnatilmoqda...
if exist wheels (
  echo wheels papkasidan o'rnatilmoqda, internet shart emas.
  venv\Scripts\python -m pip install --no-index --find-links=wheels -r requirements.txt
) else (
  venv\Scripts\python -m pip install -r requirements.txt
)
if errorlevel 1 (
  echo.
  echo XATO: kutubxonalar o'rnatilmadi. Internet yo'q bo'lsa, wheels papkasi kerak.
  pause
  exit /b 1
)
echo [3/4] Baza tayyorlanmoqda...
venv\Scripts\python manage.py migrate
echo [4/4] Rahbar ^(admin^) hisobini yarating:
venv\Scripts\python manage.py createsuperuser
echo.
echo TAYYOR. Endi run.bat ni ikki marta bosing.
pause
