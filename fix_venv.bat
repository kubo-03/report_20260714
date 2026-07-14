@echo off
setlocal enabledelayedexpansion

set "PROJECT_DIR=%~dp0"
set "VENV_DIR=%PROJECT_DIR%venv"
set "CFG=%VENV_DIR%\pyvenv.cfg"

if not exist "%CFG%" (
    echo [ERROR] venv not found: %CFG%
    echo   Create it with:
    echo   py -3.11 -m venv "%VENV_DIR%"
    echo   "%VENV_DIR%\Scripts\python.exe" -m pip install -r "%PROJECT_DIR%requirements.txt"
    exit /b 1
)

rem Find the real Python 3.11 install on this machine (prefer the py launcher, fall back to PATH)
set "PYEXE="
for /f "delims=" %%P in ('py -3.11 -c "import sys; print(sys.executable)" 2^>nul') do set "PYEXE=%%P"

if "%PYEXE%"=="" (
    for /f "delims=" %%P in ('where python 2^>nul') do (
        if "!PYEXE!"=="" set "PYEXE=%%P"
    )
)

if "%PYEXE%"=="" (
    echo [ERROR] Python not found. Install Python 3.11 and add it to PATH.
    exit /b 1
)

"%PYEXE%" -c "import platform; print(platform.python_version())" > "%TEMP%\_pyver.txt"
set /p PYVER=<"%TEMP%\_pyver.txt"
del "%TEMP%\_pyver.txt" >nul 2>&1

for %%F in ("%PYEXE%") do set "PYHOME=%%~dpF"
if "%PYHOME:~-1%"=="\" set "PYHOME=%PYHOME:~0,-1%"

echo Local Python found: %PYEXE% (%PYVER%)
echo Updating pyvenv.cfg ...

> "%CFG%.tmp" (
    echo home = %PYHOME%
    echo include-system-site-packages = false
    echo version = %PYVER%
    echo executable = %PYEXE%
    echo command = %PYEXE% -m venv "%VENV_DIR%"
)
move /y "%CFG%.tmp" "%CFG%" >nul

"%VENV_DIR%\Scripts\python.exe" -c "import sys; print('venv OK:', sys.executable)"
if errorlevel 1 (
    echo [ERROR] Failed to repair venv. Rebuild it from requirements.txt:
    echo   rmdir /s /q "%VENV_DIR%"
    echo   "%PYEXE%" -m venv "%VENV_DIR%"
    echo   "%VENV_DIR%\Scripts\python.exe" -m pip install -r "%PROJECT_DIR%requirements.txt"
    exit /b 1
)

echo.
echo Ready. Activate with:
echo   venv\Scripts\activate.bat
