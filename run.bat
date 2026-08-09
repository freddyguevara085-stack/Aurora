@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" app.py
) else (
  echo No se encontro el entorno virtual en .venv.
  echo Crea uno con: py -m venv .venv
  pause
)
