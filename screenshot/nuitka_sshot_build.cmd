@echo off
cd /d "%~dp0.."

set VERSION=1.0.109

python -m nuitka ^
    --standalone ^
    --mingw64 ^
    --windows-icon-from-ico=.\common\logo_icon.ico ^
    --windows-company-name=OPE_PROJECT ^
    --windows-product-name=OPEService ^
    --windows-file-version=%VERSION% ^
    --windows-product-version=%VERSION% ^
    --windows-file-description="OPEService - OPE Service Utility" ^
    --disable-plugin=numpy --disable-plugin=tk-inter --disable-plugin=pyqt5 --disable-plugin=pyside2 ^
    --output-dir=.\build ^
    .\screenshot\sshot.py

echo Move sshot.dist to dist dir
move /Y ".\build\sshot.dist" ".\dist\sshot"

echo Copy font to sshot dist
xcopy /y .\screenshot\STENCIL.TTF .\dist\sshot\
