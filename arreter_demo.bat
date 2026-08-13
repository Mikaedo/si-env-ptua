@echo off
:: SI-ENV - Arret propre de la demonstration.
:: Double-cliquez pour arreter Docker et retirer la redirection USB.

title SI-ENV - Arret de la demonstration
color 0E
setlocal
cd /d "%~dp0"

echo.
echo ============================================================
echo   SI-ENV / PTUA - Arret de la demonstration
echo ============================================================
echo.

echo [1/2] Retrait de la redirection USB...
adb reverse --remove-all >nul 2>&1
echo   OK.

echo.
echo [2/2] Arret des conteneurs Docker...
cd backend
docker compose down
cd ..

echo.
echo ============================================================
echo   Demonstration arretee.
echo.
echo   Les donnees restent dans le volume Docker sienv_data,
echo   elles seront retrouvees au prochain demarrage.
echo ============================================================
echo.
timeout /t 5 >nul
endlocal
