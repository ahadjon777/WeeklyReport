@echo off
chcp 65001 >nul
REM === INTERNET BOR kompyuterda ishlatiladi: internetsiz tarmoq uchun kutubxonalarni yig'adi ===
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (
  echo XATO: avval shu kompyuterda setup.bat ni ishga tushiring.
  pause
  exit /b 1
)
echo Kutubxonalar wheels papkasiga yuklanmoqda ^(taxminan 15 MB^)...
venv\Scripts\python -m pip download -r requirements.txt -d wheels
if errorlevel 1 (
  echo XATO: yuklab bo'lmadi. Internetni tekshiring.
  pause
  exit /b 1
)
echo.
echo Python versiyasi ^(boshqa kompyuterga AYNAN SHU versiyani o'rnating^):
venv\Scripts\python --version
echo.
echo TAYYOR. Endi README dagi "Internetsiz tarmoqqa ko'chirish" bo'limiga qarang.
pause
