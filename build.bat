@echo off
setlocal
chcp 65001 >nul

echo Building executable...
python build_executable.py

if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
) else (
    echo Build succeeded. Output is in: release\
    pause
)