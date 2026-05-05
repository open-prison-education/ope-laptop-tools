@echo off
setlocal ENABLEEXTENSIONS

rem Full clean build: wipe repo dist\ and build\, then mgmt, screenshot, credential, opeService.
cd /d "%~dp0"
set "ROOT=%CD%"

set "VENV=%ROOT%\.venv"
set "VENV_ACT=%VENV%\Scripts\activate.bat"

if exist "%VENV_ACT%" (
    call "%VENV_ACT%"
) else (
    echo Creating Python virtual environment at "%VENV%" ...
    python -m venv "%VENV%"
    if errorlevel 1 goto :fail
    call "%VENV_ACT%"
    if exist "%ROOT%\modules.txt" (
        python -m pip install --upgrade pip
        python -m pip install -r "%ROOT%\modules.txt"
    ) else (
        echo ERROR: No modules.txt found. Cannot populate new venv.
        goto :fail
    )
    if errorlevel 1 goto :fail
)

set "DIST_OUT=%ROOT%\dist"
set "BUILD_WORK=%ROOT%\build"

echo Building all components...
echo ROOT=%ROOT%
echo.

if exist "%DIST_OUT%" rmdir /s /q "%DIST_OUT%"
if exist "%BUILD_WORK%" rmdir /s /q "%BUILD_WORK%"

call "%ROOT%\mgmt\nuitka_mgmt_build.cmd"
if errorlevel 1 goto :fail
cd /d "%ROOT%"

call "%ROOT%\screenshot\nuitka_sshot_build.cmd"
if errorlevel 1 goto :fail
cd /d "%ROOT%"

call "%ROOT%\credential\build_credential.cmd"
if errorlevel 1 goto :fail
cd /d "%ROOT%"

call python "%ROOT%\opeService\build_svc.py"
if errorlevel 1 goto :fail

echo.
echo All builds completed successfully.
echo Output under: %DIST_OUT%
exit /b 0

:fail
echo.
echo Build failed. See errors above.
exit /b 1
