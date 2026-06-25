@echo off
REM Build GymManagerSetup.exe on Windows (requires Inno Setup 6+)
REM 1. pyinstaller build.spec
REM 2. Run this script from the installer folder

set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"

if not exist %ISCC% (
  echo Inno Setup not found. Install from https://jrsoftware.org/isinfo.php
  exit /b 1
)

%ISCC% GymManager.iss
echo.
echo Installer written to installer\Output\GymManagerSetup.exe
