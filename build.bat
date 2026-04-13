@echo off
REM Build script for creating standalone executable
REM Uses onedir mode for faster builds (single directory instead of single file)

echo Building Balatro Certamen executable...
echo This may take 2-3 minutes...

cd /d "%~dp0"

python -m PyInstaller ^
  --distpath ".\release" ^
  --buildpath ".\build" ^
  --specpath "." ^
  --onedir ^
  --windowed ^
  --add-data "assets:assets" ^
  --name "BalatroCartemen" ^
  main.py

if %errorlevel% equ 0 (
  echo.
  echo Build completed successfully!
  echo Executable location: %cd%\release\BalatroCartemen\BalatroCartemen.exe
) else (
  echo Build failed with error code %errorlevel%
)

pause
