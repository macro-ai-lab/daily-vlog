@echo off
rem ExecutionPolicy applies only to this process; machine policy is not changed.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0run.ps1" %*
exit /b %ERRORLEVEL%
