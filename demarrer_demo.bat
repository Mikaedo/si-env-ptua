@echo off
:: SI-ENV - Demarrage complet de la demonstration en un clic.
:: Double-cliquez sur ce fichier pour lancer :
::   - Docker (backend FastAPI, PostgreSQL/PostGIS, nginx)
::   - Redirection USB vers le telephone (adb reverse)
::   - L'application mobile sur le telephone connecte
::   - Le tableau de bord dans votre navigateur
::
:: Prerequis : Docker Desktop ouvert, telephone branche en USB avec
:: debogage active. Voir arreter_demo.bat pour tout arreter.

title SI-ENV - Demarrage de la demonstration
color 0B
setlocal
cd /d "%~dp0"

echo.
echo ============================================================
echo   SI-ENV / PTUA - Demarrage de la demonstration en local
echo ============================================================
echo.

echo [1/5] Verification de Docker...
docker info >nul 2>&1
if errorlevel 1 (
    color 0C
    echo.
    echo ERREUR : Docker Desktop ne repond pas.
    echo Ouvrez Docker Desktop, attendez qu'il soit pret, puis relancez ce fichier.
    echo.
    pause
    exit /b 1
)
echo   Docker OK.

echo.
echo [2/5] Demarrage des conteneurs (backend + base + nginx)...
cd backend
docker compose up -d
if errorlevel 1 (
    color 0C
    echo.
    echo ERREUR : le demarrage Docker a echoue. Consultez la sortie ci-dessus.
    pause
    exit /b 1
)
cd ..

echo.
echo [3/5] Attente du backend (15 secondes)...
timeout /t 15 /nobreak >nul

echo.
echo [4/5] Redirection USB pour le mobile...

:: Recherche automatique de adb.exe, meme si le PATH n'est pas configure.
:: On tente d'abord la commande simple (PATH), sinon on cherche l'emplacement
:: standard d'installation Android SDK, sinon on abandonne proprement.
set "ADB=adb"
where adb >nul 2>&1
if errorlevel 1 (
    if exist "%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe" (
        set "ADB=%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"
    ) else if exist "%USERPROFILE%\AppData\Local\Android\Sdk\platform-tools\adb.exe" (
        set "ADB=%USERPROFILE%\AppData\Local\Android\Sdk\platform-tools\adb.exe"
    ) else if exist "%PROGRAMFILES%\Android\Android Studio\plugins\android\lib\platform-tools\adb.exe" (
        set "ADB=%PROGRAMFILES%\Android\Android Studio\plugins\android\lib\platform-tools\adb.exe"
    ) else (
        echo   adb.exe introuvable. Le mobile ne sera pas relie.
        echo   Installez Android SDK Platform-Tools ou verifiez que Android Studio est present.
        goto :apres_adb
    )
)

"%ADB%" devices >nul 2>&1
if errorlevel 1 (
    echo   Aucun telephone detecte. Verifiez le cable USB et le debogage USB.
    goto :apres_adb
)

"%ADB%" reverse tcp:8000 tcp:8000 >nul 2>&1
"%ADB%" reverse tcp:80 tcp:80 >nul 2>&1
echo   tcp:8000 et tcp:80 rediriges vers votre PC.

echo.
echo   Lancement de l'application sur le telephone...
"%ADB%" shell am start -n ci.ageroute.si_env/.MainActivity >nul 2>&1

:apres_adb

echo.
echo [5/5] Ouverture du tableau de bord dans votre navigateur...
start "" http://localhost/

echo.
echo ============================================================
echo   Systeme demarre.
echo.
echo   Dashboard web : http://localhost/
echo   API + Swagger : http://localhost:8000/docs
echo   Mobile        : lance sur votre telephone
echo.
echo   Comptes de demonstration :
echo     spec.env@ageroute.ci  / spec123    (Spec. Suivi Env)
echo     admin@sienv.ci        / admin123   (Administrateur)
echo     expert.hse@ageroute.ci / expert123 (Expert HSE)
echo     spec.par@ageroute.ci  / spec123    (Spec. Suivi P.A.R)
echo.
echo   Pour tout arreter proprement, double-cliquez sur : arreter_demo.bat
echo ============================================================
echo.
echo Vous pouvez fermer cette fenetre : les services continueront a tourner.
pause
endlocal
