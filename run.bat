@echo off
REM === HAR KUNI: serverni ishga tushiradi ===
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (
  echo XATO: venv topilmadi. Avval setup.bat ni ishga tushiring.
  pause
  exit /b 1
)
echo Kutubxonalar tekshirilmoqda...
venv\Scripts\python -m pip install -q -r requirements.txt
if errorlevel 1 echo OGOHLANTIRISH: kutubxonalarni yangilab bo'lmadi (internet yo'q bo'lishi mumkin). Davom etamiz...
venv\Scripts\python manage.py migrate --noinput
if errorlevel 1 goto ERR
venv\Scripts\python manage.py collectstatic --noinput >nul
venv\Scripts\python serve.py
:ERR
echo.
echo Dastur xato bilan to'xtadi. Yuqoridagi qizil matnni dasturchiga yuboring.
pause
