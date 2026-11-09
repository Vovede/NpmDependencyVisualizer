 @echo off
setlocal

cd /d "%~dp0"

set "PYTHONPATH=%CD%\src"

python -m visualizer.main %*

if errorlevel 1 (
    echo.
    echo Ошибка при запуске программы.
    exit /b 1
)

endlocal