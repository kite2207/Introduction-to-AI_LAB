@echo off
setlocal

set "ROOT=%~dp0"
set "TEX_DIR=%ROOT%Report"
set "TEX_FILE=LAB01.tex"
set "XELATEX=%LOCALAPPDATA%\Programs\MiKTeX\miktex\bin\x64\xelatex.exe"

if not exist "%XELATEX%" (
    where xelatex >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] Khong tim thay XeLaTeX.
        echo Hay mo MiKTeX Console va hoan tat phan Updates/Packages.
        pause
        exit /b 1
    )
    set "XELATEX=xelatex"
)

if not exist "%TEX_DIR%\%TEX_FILE%" (
    echo [ERROR] Khong tim thay "%TEX_DIR%\%TEX_FILE%".
    pause
    exit /b 1
)

pushd "%TEX_DIR%"
echo Dang bien dich %TEX_FILE% bang XeLaTeX...
"%XELATEX%" -interaction=nonstopmode -halt-on-error "%TEX_FILE%"
if errorlevel 1 goto :failed
"%XELATEX%" -interaction=nonstopmode -halt-on-error "%TEX_FILE%"
if errorlevel 1 goto :failed

echo.
echo [OK] Da tao: "%TEX_DIR%\LAB01.pdf"
popd
pause
exit /b 0

:failed
echo.
echo [ERROR] Bien dich that bai. Xem loi tai "%TEX_DIR%\LAB01.log".
popd
pause
exit /b 1
