@echo off
chcp 65001 >nul
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel%==0 (
    python server.py
    goto :end
)
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 server.py
    goto :end
)
where python3 >nul 2>nul
if %errorlevel%==0 (
    python3 server.py
    goto :end
)

echo.
echo   没找到 Python。装一个再来：https://www.python.org/downloads/
echo   或者直接双击 index.html —— 那种方式数据只能存在浏览器里。
echo.
pause

:end
