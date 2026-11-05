@echo off
title B3 Swing Trade Pro
echo ========================================================
echo   Iniciando o Analisador Automatico B3 Swing Trade Pro
echo   Foco em ITUB4, BBDC4 e Acoes da B3
echo ========================================================
echo.
cd /d "%~dp0"
"C:\Users\User\AppData\Local\Programs\Python\Python311\python.exe" -m streamlit run app.py
pause
