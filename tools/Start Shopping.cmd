@echo off
rem Double-click to open Shopping in the Agent OS Executive window. Add -Demo for invented test data.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-Shopping.ps1" %*
if errorlevel 1 pause
