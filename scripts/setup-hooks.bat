@echo off
REM Setup pre-commit hook for version bump validation (Windows)

setlocal enabledelayedexpansion

set "HOOK_SOURCE=.githooks\pre-commit"
set "HOOK_TARGET=.git\hooks\pre-commit"

if not exist "%HOOK_SOURCE%" (
    echo X Hook source not found: %HOOK_SOURCE%
    exit /b 1
)

echo Installing pre-commit hook...

REM Create hooks directory if needed
if not exist ".git\hooks" mkdir ".git\hooks"

REM Copy hook
copy "%HOOK_SOURCE%" "%HOOK_TARGET%" >nul

echo. 
echo ✓ Pre-commit hook installed at %HOOK_TARGET%
echo.
echo Next: Run this in PowerShell or bash:
echo   git config core.hooksPath .githooks
echo.
echo Then read: VERSIONING.md for the workflow
