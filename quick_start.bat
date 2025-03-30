@echo off
echo Starting Flask application directly...
cd /d "%~dp0"
python -m flask --app app run --debug
pause
