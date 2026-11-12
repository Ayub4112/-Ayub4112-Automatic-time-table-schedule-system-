@echo off
cd /d "%~dp0standalone-demo"
python -m http.server 8080
pause
