@echo off
chcp 65001 >nul
taskkill /f /im weekly_agent.exe >nul 2>&1
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\WeeklyReport eslatma.lnk" >nul 2>&1
rmdir /s /q "%LOCALAPPDATA%\WeeklyReport" >nul 2>&1
echo WeeklyReport eslatma dasturi o'chirildi.
pause
