@echo off
echo Installing ffmpeg for audio processing...
echo.

REM Check if winget is available
winget --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: winget is not available on this system.
    echo Please install ffmpeg manually from: https://ffmpeg.org/download.html
    echo.
    echo Alternative methods:
    echo 1. Download the Windows build from https://ffmpeg.org/download.html
    echo 2. Extract to a folder and add it to your PATH
    echo 3. Or use Chocolatey: choco install ffmpeg
    pause
    exit /b 1
)

echo Installing ffmpeg using winget...
winget install ffmpeg

if %errorlevel% equ 0 (
    echo.
    echo ffmpeg installed successfully!
    echo You may need to restart your terminal/command prompt.
    echo.
    echo Now you can run: python server.py
) else (
    echo.
    echo Failed to install ffmpeg using winget.
    echo Please install manually from: https://ffmpeg.org/download.html
)

pause
