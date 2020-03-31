@echo off

rem echo Starting Credential Process...
rem pause

set tfile=%temp%\runasuac.vbs
rem check if we have UAC permissions
rem >nul 2>&1 "%SYSTEMROOT%\system32\icacls.exe" "%SYSTEMROOT%\system32\config\system"
NET FILE 1>NUL 2>NUL

rem error flag set = no admin priv
rem if '%errorlevel%' NEQ '0' (
if '%errorlevel%' NEQ '0' (
    rem echo Not admin...
    rem pause
    goto switchToUAC
) else ( goto isAlreadyUAC )

echo Why are you here - this is a bug - please report it
pause

:switchToUAC
    echo Not UAC - Switching to UAC...
    echo Set UAC = CreateObject^("Shell.Application"^) > "%tfile%"
    echo args = "/C %~s0" >> "%tfile%"
    echo For Each strArg in WScript.Arguments >> "%tfile%"
    echo   args = args ^& strArg ^& " " >> "%tfile%"
    echo Next >> "%tfile%"
    echo UAC.ShellExecute "cmd", args, "", "runas", 1 >> "%tfile%"
    
    wscript "%tfile%" %*
    rem pause
    exit /B
    
:isAlreadyUAC
    rem echo Alread Running with UAC...
    rem pause
    if exist "%tfile%" ( del "%tfile%" )
    pushd "%CD%"
    cd /D "%~dp0"
    rem pause

echo [ ---- Configuring Laptop for Inmate Use ---- ]
echo(

echo -- Turning off OPEService...
net stop OPEService 2>NUL 1>NUL
REM IF YOUR NETWORK DEVICE IS DISABLED - YOU WILL NEED TO TURN IN BACK ON!!!
REM echo waiting for service to stop...
REM timeout /t 10 /nobreak

rem run update from Git server
echo -- Getting latest updates from local git server...
call %~dp0bin\OfflineUpdate.cmd auto

rem call the main credential script
echo -- Starting credential process...
call %~dp0bin\run_credential_process.cmd
    

