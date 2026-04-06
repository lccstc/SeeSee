@echo off
setlocal

set "PROJECT_ROOT=C:\SeeSee\wxbot\bookkeeping-platform"
set "PYTHON_EXE=C:\Users\lccst\AppData\Local\Programs\Python\Python311\python.exe"

if not exist "%PROJECT_ROOT%" (
  echo [ERROR] Project root not found: %PROJECT_ROOT%
  pause
  exit /b 1
)

if not exist "%PYTHON_EXE%" (
  echo [ERROR] Python not found: %PYTHON_EXE%
  pause
  exit /b 1
)

cd /d "%PROJECT_ROOT%"
echo Starting WeChat adapter...
"%PYTHON_EXE%" -m wechat_adapter.main

echo.
echo WeChat adapter exited.
pause
