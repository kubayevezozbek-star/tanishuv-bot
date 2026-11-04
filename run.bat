@echo off
title Tanishuv Boti
echo ==============================================
echo        Tanishuv Boti ishga tushirilmoqda...
echo ==============================================
cd /d "%~dp0"
call venv\Scripts\activate.bat
python main.py
pause
