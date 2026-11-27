@echo off
REM Bir marta ishlatiladi (faqat Python o'rnatilgan kompyuterda): weekly_agent.exe yaratadi.
cd /d "%~dp0"
python -m pip install pyinstaller
python -m PyInstaller --onefile --noconsole --name weekly_agent weekly_agent.py
copy /y dist\weekly_agent.exe weekly_agent.exe
echo.
echo Tayyor: weekly_agent.exe. Endi shu papkani (weekly_agent.exe, install_agent.bat, server.txt) xodimlar kompyuteriga nusxalang.
pause
