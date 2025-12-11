@echo off
chcp 65001 >nul
cd /d %~dp0

:: venv check
if not exist venv (
    echo ⚠️  Virtual environment not found. Please run 'python -m venv venv' first.
    exit /b 1
)

:: Activate venv
call venv\Scripts\activate
set MAU_ENV=development

echo 🚀 Starting AI-Mau in DEVELOPMENT mode (Windows)...
echo ----------------------------------------

:: Run the bot (New path)
python -m src.app.main
pause
