@echo off
REM Build Attendance Reminder as a single EXE using PyInstaller

echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 exit /b %errorlevel%

echo Installing PyInstaller...
pip install pyinstaller
if %errorlevel% neq 0 exit /b %errorlevel%

echo Building executable...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "AttendanceReminder" ^
    --hidden-import PIL._tkinter_finder ^
    --clean ^
    --noconfirm ^
    main.py

if %errorlevel% equ 0 (
    echo.
    echo Build complete! Executable created at: dist\AttendanceReminder.exe
) else (
    echo.
    echo Build failed!
    exit /b %errorlevel%
)
