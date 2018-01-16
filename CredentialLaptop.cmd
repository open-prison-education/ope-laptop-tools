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

echo Why are you here
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

echo ---- Configuring Laptop for Inmate Use ----
echo(

echo -- Disabling OPEService...
net stop OPEService 2>NUL 1>NUL
REM IF YOUR NETWORK DEVICE IS DISABLED - YOU WILL NEED TO TURN IN BACK ON!!!
REM echo waiting for service to stop...
REM timeout /t 10 /nobreak

rem run update from Git server
echo -- Getting latest updates from local git server...
call %~dp0\OfflineUpdate.cmd auto

echo -- Running Credential App to setup student account and link with Canvas...
set credential_app="%~dp0\Credential\credential.exe"
set credential_app="python %~dp0\laptop_credential\app.py"
echo %credential_app%
%credential_app%

echo -- Installing latest OPEService...
REM TODO
rem call %~dp0\install_service.cmd 2>NUL 1<NUL

echo -- Applying windows group policy...
rem call %~dp0\restore_gpo.cmd

echo(
echo(
echo -- Set an Admin password for this laptop!!!!
echo(
echo Hit CTRL + ALT + Delete and choose "Change Password"
echo - This will let you set an admin password for this laptop
echo - DO NOT USE YOUR NORMAL ADMIN PASSWORD FOR YOUR NETWORK!!
pause
echo(
echo(
echo -- Are you sure you set the admin password?
pause


echo Done. 
echo(
echo Make sure to set a unique admin password in the BIOS and disable alternative boot devices.
echo Student will need to plug in to the secure docking station, login and run the LMS app to download Canvas files.
pause
echo -- WARNING - Don't forget to set an admin BIOS password!!!
pause
