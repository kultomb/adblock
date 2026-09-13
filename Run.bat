@echo off
chcp 65001 > NUL
title HBGAdBlocker - Cong Cu AdBlock ^& Debloat

echo ========================================================
echo   DANG KHOI CHAY HBGADBLOCKER (ADBLOCK ^& DEBLOAT)...
echo ========================================================

python HBGAdBlocker.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [LOI] Khong the chay HBGAdBlocker.py!
    echo Vui long kiem tra lai Python va cac thu vien can thiet.
    pause
)
