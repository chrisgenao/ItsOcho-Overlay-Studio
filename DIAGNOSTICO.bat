@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul 2>nul
cd /d "%~dp0"
title ItsOcho - Diagnostico Python
color 0E
echo =====================================================
echo      ITSOCHO - DIAGNOSTICO DE PYTHON
 echo =====================================================
echo.
echo Carpeta: %CD%
echo.
echo [1] Python 3.12 instalado en AppData:
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
  echo [OK] Existe Python312.
  "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" --version
) else (
  echo No se encuentra en esa ruta.
)
echo.
echo [2] Python Launcher:
where py 2>nul
py -3 --version 2>&1
echo.
echo [3] Comando python:
where python 2>nul
python --version 2>&1
echo.
echo [4] Instalaciones visibles:
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
  if exist "%%~fD\python.exe" echo    %%~fD\python.exe
)
echo.
echo [5] Archivos necesarios:
for %%F in (INICIAR_PANEL.bat server.py panel.html overlay.html) do (
  if exist "%%F" (echo [OK] %%F) else (echo [FALTA] %%F)
)
echo.
echo Enviame una captura o copia el texto de la ventana.
pause
