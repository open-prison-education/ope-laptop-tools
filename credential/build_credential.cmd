@echo off
SETLOCAL ENABLEEXTENSIONS

rem Build script for credential.exe
rem Similar to build_svc.py but for credential

echo Building credential.exe...

rem Script folder (spec, config, bin\) — always this path regardless of caller CWD
set "CURRENT_DIR=%~dp0"
rem Project root: dist\ and build\ live here (same as running PyInstaller from root)
for %%I in ("%CURRENT_DIR%..") do set "ROOT=%%~fI"
set "DIST_OUT=%ROOT%\dist"
set "BUILD_WORK=%ROOT%\build\credential"

rem Run PyInstaller from credential\ so spec-relative datas (e.g. bin\) resolve
cd /d "%CURRENT_DIR%"

rem Check if PyInstaller is available
python -c "import PyInstaller" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: PyInstaller not found. Please install it first.
    echo Run: pip install pyinstaller
    exit /b 1
)

rem Clean previous builds (root-level dist/build)
if exist "%DIST_OUT%\credential" rmdir /s /q "%DIST_OUT%\credential"
if exist "%BUILD_WORK%" rmdir /s /q "%BUILD_WORK%"

rem Build: force output to repo root dist\ and build\credential\
echo Building credential.exe using PyInstaller...
python -m PyInstaller --clean --distpath "%DIST_OUT%" --workpath "%BUILD_WORK%" "%CURRENT_DIR%credential.spec"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Build failed!
    exit /b 1
)

echo.
echo Build completed successfully!
echo Executable created at: %DIST_OUT%\credential\credential.exe
echo.

rem Copy config file to dist directory
if exist "%CURRENT_DIR%credential_config.json" (
    copy "%CURRENT_DIR%credential_config.json" "%DIST_OUT%\credential\"
    echo Configuration file copied to dist directory.
)

rem copy readme file to dist directory
if exist "%CURRENT_DIR%README.md" (
    copy "%CURRENT_DIR%README.md" "%DIST_OUT%\credential\"
    echo Readme file copied to dist directory.
)

echo Ready for deployment!
echo You can now distribute the contents of: %DIST_OUT%\credential
echo.
