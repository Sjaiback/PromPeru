@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo El entorno virtual no existe. Sigue primero los pasos de README.md.
  pause
  exit /b 1
)
echo Sistema PROMPERU disponible en esta PC: http://127.0.0.1:8000
echo En otras PCs usa: http://IP-DE-ESTA-PC:8000
echo Para detenerlo, presiona Ctrl+C.
".venv\Scripts\python.exe" manage.py runserver 0.0.0.0:8000
endlocal
