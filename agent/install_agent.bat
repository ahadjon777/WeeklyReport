@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
set "APP=%LOCALAPPDATA%\WeeklyReport"
if not exist "%APP%" mkdir "%APP%"

echo ==== WeeklyReport eslatma dasturini o'rnatish ====
echo.
set "SERVER="
if exist server.txt set /p SERVER=<server.txt
if not defined SERVER set /p SERVER=Server manzili, masalan http://192.168.1.10:8000 : 
set /p WRUSER=Shu kompyuter egasining logini: 

(
echo [agent]
echo server=%SERVER%
echo username=%WRUSER%
)> "%APP%\agent_config.ini"

if exist weekly_agent.exe goto EXE
goto PY

:EXE
taskkill /f /im weekly_agent.exe >nul 2>&1
timeout /t 1 >nul
copy /y weekly_agent.exe "%APP%\weekly_agent.exe" >nul
set "TARGET=%APP%\weekly_agent.exe"
set "ARGS="
goto SHORTCUT

:PY
where pythonw >nul 2>&1
if errorlevel 1 goto NOPY
copy /y weekly_agent.py "%APP%\weekly_agent.py" >nul
for /f "delims=" %%i in ('where pythonw') do set "TARGET=%%i" & goto PYOK
:PYOK
set "ARGS="%APP%\weekly_agent.py""
goto SHORTCUT

:NOPY
echo.
echo XATO: weekly_agent.exe topilmadi va bu kompyuterda Python ham yo'q.
echo weekly_agent.exe ni shu papkaga qo'ying (build_agent.bat bilan yaratiladi).
pause
exit /b 1

:SHORTCUT
powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Startup')+'\WeeklyReport eslatma.lnk'); $s.TargetPath='%TARGET%'; $s.Arguments='%ARGS%'; $s.WorkingDirectory='%APP%'; $s.Save()"

if defined ARGS (start "" "%TARGET%" %ARGS%) else (start "" "%TARGET%")
timeout /t 2 >nul
echo.
echo O'rnatildi. Kompyuter yoqilganda dastur o'zi ishga tushadi.
echo Hozir sinov eslatma oynasi chiqadi...
if defined ARGS (start "" "%TARGET%" %ARGS% --test) else (start "" "%TARGET%" --test)
echo.
pause
