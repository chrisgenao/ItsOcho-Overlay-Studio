@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul 2>nul
title ItsOcho - The Road to GTA VI - Panel v5.14 Desktop
color 0B
cd /d "%~dp0"
echo.
echo =============================================================
echo    ITSOCHO - THE ROAD TO GTA VI - CONTROL v5.14 - DESKTOP
 echo =============================================================
echo.
if not exist "server.py" goto :archivos
if not exist "panel.html" goto :archivos
if not exist "overlay.html" goto :archivos

echo [1/3] Buscando tu Python instalado (aunque no este en PATH)...
set "PYTHON_EXE="

rem Un nombre de archivo personalizable, para ordenadores con instalacion especial.
if exist "%~dp0RUTA_PYTHON.txt" (
  for /f "usebackq delims=" %%P in ("%~dp0RUTA_PYTHON.txt") do call :probar "%%P"
)
if defined ITSOCHO_PYTHON call :probar "%ITSOCHO_PYTHON%"

rem Instalaciones habituales en Windows. Esto incluye Python 3.12 en AppData.
for %%V in (315 314 313 312 311 310) do (
  call :probar "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
  call :probar "%ProgramFiles%\Python%%V\python.exe"
)

rem Otra distribucion portable o instalaciones personalizadas en las carpetas conocidas.
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*" "%USERPROFILE%\AppData\Local\Programs\Python\Python3*" "%ProgramFiles%\Python3*") do (
  call :probar "%%~fD\python.exe"
)
call :probar "%USERPROFILE%\scoop\apps\python\current\python.exe"

rem Lanzador de Python, si esta instalado (py.exe o el nuevo Python manager).
if not defined PYTHON_EXE (
  for /f "delims=" %%P in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do call :probar "%%P"
)

rem PATH: solo al final, para evitar los falsos alias de Microsoft Store.
if not defined PYTHON_EXE (
  for /f "delims=" %%P in ('where python.exe 2^>nul') do call :probar "%%P"
)
if not defined PYTHON_EXE (
  for /f "delims=" %%P in ('where python3.exe 2^>nul') do call :probar "%%P"
)
if not defined PYTHON_EXE goto :sin_python

echo [OK] Python encontrado: "%PYTHON_EXE%"
"%PYTHON_EXE%" --version
echo [2/3] Iniciando servidor local...
echo [3/3] Abriendo panel en tu navegador...
echo.
echo     PANEL: http://127.0.0.1:8767/panel
echo     OBS:   http://127.0.0.1:8767/overlay
echo.
echo     DEJA ESTA VENTANA ABIERTA DURANTE EL STREAM.
echo.
"%PYTHON_EXE%" -u "server.py"
set "SALIDA=%ERRORLEVEL%"
goto :termino

:probar
if defined PYTHON_EXE exit /b 0
if not exist "%~1" exit /b 0
"%~1" -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
if not errorlevel 1 set "PYTHON_EXE=%~1"
exit /b 0

:archivos
echo [ERROR] Faltan archivos. Extrae TODO el ZIP en una carpeta.
set "SALIDA=10"
goto :termino

:sin_python
echo [ERROR] No pude localizar Python automaticamente.
echo NO necesitas reinstalarlo si ya lo tienes.
echo Abre el archivo DIAGNOSTICO.bat y enviame el resultado.
echo Tambien puedes crear RUTA_PYTHON.txt en esta carpeta y poner
 echo ahi la ruta completa a tu python.exe (una sola linea).
set "SALIDA=11"
goto :termino

:termino
echo.
echo =============================================================
if "%SALIDA%"=="0" (
  echo [INFO] El panel se ha cerrado.
) else (
  echo [ERROR] El panel se detuvo. Codigo: %SALIDA%
)
echo Esta ventana queda abierta hasta que presiones una tecla.
pause >nul
exit /b %SALIDA%
