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
    rem echo using git branch %GIT_BRANCH%
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


echo %ESC_GREEN%[ ---- Configuring Laptop for Student Use ---- ]%ESC_RESET%
echo.

rem run vc_installer
echo Do you want to install the VC Runtimes?
choice /C yn /T 5 /D n /M "Press Y to set install VC Runtimes [y/n]"
if errorlevel 2 goto skipinstallvcruntimes
echo -- %ESC_GREEN%Installing required packages - please wait... %ESC_RESET% --
call "%~dp0Services\mgmt\rc\install_vc_runtimes.cmd"
echo.
:skipinstallvcruntimes


call "%~dp0Services\mgmt\mgmt.exe" config_once

rem Add win defender exclusion for our ope folder
PowerShell -NoProfile -ExecutionPolicy Bypass -Command "& {Add-MpPreference -ExclusionPath '%PROGRAMDATA%\ope'}"

echo -- %ESC_GREEN%Unlocking Machine - please wait... %ESC_RESET% --
echo.
call "%~dp0Services\mgmt\mgmt.exe" unlock_machine
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo %ESC_RED%*** ERROR - Failed to unlock machine - Quitting. ***%ESC_RESET%
    echo.
    echo.
    pause
    pause
    exit /b 2
)


rem run update from Git server
echo %ESC_GREEN%-- Getting latest updates from local git server...%ESC_RESET%
rem NOTE - Need to git_pull outside of mgmt.exe so we can update those files
call "%~dp0bin\PullUpdates.cmd" %GIT_BRANCH%
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo %ESC_YELLOW%*** WARNING - Unable to pull updates from online or local server - You may not be running the latest version of the laptop software! ***%ESC_RESET%
    echo.
    echo.
    rem /T 3
    choice /C yn /T 15 /D y /M "Do you want to continue anyway? (y/n - default y in 15 seconds): "
    if [!errorlevel!] EQU [1] goto runinstall
    exit /b 2
)

:runinstall
rem install services
echo %ESC_GREEN%-- Installing OPE Services...%ESC_RESET%
call "%~dp0bin\install_service.cmd"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo %ESC_RED%****** ERROR - Failed to install OPE services. Credential process did not complete properly - this Laptop is NOT ready to hand out to students. *******%ESC_RESET%
    echo.
    pause
    pause
    exit /b 2
)


:startcredential
rem call the main credential script
echo %ESC_GREEN%-- Starting credential process...%ESC_RESET%
rem call "%~dp0Services\mgmt\mgmt.exe" credential_laptop
call "%programdata%\ope\Services\mgmt\mgmt.exe" credential_laptop
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo %ESC_RED%****** Credential process did not complete properly - this Laptop is NOT ready to hand out to students. *******%ESC_RESET%
    echo.
    pause
    pause
    exit /b 2
)

:lock_machine
rem Lock machine down which will enable user account
echo %ESC_GREEN%-- Locking Machine...%ESC_RESET%
rem call "%~dp0Services\mgmt\mgmt.exe" lock_machine
call "%programdata%\ope\Services\mgmt\mgmt.exe" lock_machine
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo %ESC_RED%****** ERROR - Unable to lock machine. Credential process did not complete properly - this Laptop is NOT ready to hand out to students. Try mgmt lock_machine again to see if you can lock it manually. *******%ESC_RESET%
    echo.
    pause
    pause
    exit /b 2
)

rem good run - return 0

echo.
echo %ESC_GREEN% *** Credential Done *** %ESC_RESET%
echo.

rem pause
rem use ping for slight pause
set seconds=10
PING -n !seconds! 127.0.0.1 >NUL 2>&1 || PING -n !seconds! ::1 >NUL 2>&1
pause
exit /b 0
