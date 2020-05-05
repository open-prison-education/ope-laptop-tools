@echo off
SETLOCAL ENABLEEXTENSIONS
SETLOCAL ENABLEDELAYEDEXPANSION

SET ESC=[
SET ESC_CLEAR=%ESC%2j
SET ESC_RESET=%ESC%0m
SET ESC_GREEN=%ESC%32m
SET ESC_RED=%ESC%31m
SET ESC_YELLOW=%ESC%33m

if [%1] EQU [] (
    rem No param, use master branch
    SET GIT_BRANCH=master

) else (
    rem Param provided, use it as the current branch
    SET GIT_BRANCH=%1    
    echo using git branch %GIT_BRANCH%
)

rem echo Starting Credential Process...
rem pause

set tfile=%temp%\runasuac.vbs
rem check if we have UAC permissions
rem >nul 2>&1 "%SYSTEMROOT%\system32\icacls.exe" "%SYSTEMROOT%\system32\config\system"
NET FILE 1>NUL 2>NUL

rem error flag set = no admin priv
if '%errorlevel%' NEQ '0' (
    rem echo Not admin...
    rem pause
    goto switchToUAC
) else ( goto isAlreadyUAC )

echo %ESC_RED%Why are you here - this is a bug - please report it%ESC_RESET%
pause

:switchToUAC
    echo Not UAC - Switching to UAC...
    echo Set UAC = CreateObject^("Shell.Application"^) > "%tfile%"
    echo args = "/C %~s0 %*" >> "%tfile%"
    echo For Each strArg in WScript.Arguments >> "%tfile%"
    echo   args = args ^& strArg ^& " " >> "%tfile%"
    echo Next >> "%tfile%"
    echo UAC.ShellExecute "cmd", args, "", "runas", 1 >> "%tfile%"
    
    rem wscript "%tfile%" %*
    wscript "%tfile%"
    rem echo Params  %*
    rem pause
    exit /B
    
:isAlreadyUAC
    rem echo Alread Running with UAC...
    rem pause
    if exist "%tfile%" ( del "%tfile%" )
    pushd "%CD%"
    cd /D "%~dp0"
    rem pause


echo %ESC_GREEN%[ ---- Configuring Laptop for Inmate Use ---- ]%ESC_RESET%
echo.

rem - Remove at some point - service is stopped/restarted in install_service now
rem echo %ESC_YELLOW%-- Turning off OPEService...%ESC_RESET%
net stop OPEService 2>NUL 1>NUL

REM IF YOUR NETWORK DEVICE IS DISABLED - YOU WILL NEED TO TURN IN BACK ON!!!
REM echo waiting for service to stop...
REM timeout /t 10 /nobreak

rem run update from Git server
echo %ESC_GREEN%-- Getting latest updates from local git server...%ESC_RESET%
rem call %~dp0bin\OfflineUpdate.cmd auto
call %~dp0bin\PullUpdates.cmd %GIT_BRANCH%
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo %ESC_RED%****** Credential process did not complete properly - this Laptop is NOT ready to hand out to students. *******%ESC_RESET%
    echo.
    pause
    exit /b 2
)

rem call the main credential script
echo %ESC_GREEN%-- Starting credential process...%ESC_RESET%
call %~dp0bin\run_credential_process.cmd
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo %ESC_RED%****** Credential process did not complete properly - this Laptop is NOT ready to hand out to students. *******%ESC_RESET%
    echo.
    pause
    exit /b 2
)
