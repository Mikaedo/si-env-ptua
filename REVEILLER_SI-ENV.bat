@echo off
REM Double-cliquez sur ce fichier avant une demonstration.
REM
REM Il reveille le serveur en ligne, qui se met en veille apres quinze minutes
REM sans requete, puis verifie que la connexion et la base repondent. Comptez
REM une minute la premiere fois, quelques secondes ensuite.
REM
REM Le travail reel est fait par deploy\reveiller_services.ps1 ; ce fichier ne
REM sert qu'a le lancer sans avoir a ouvrir un terminal.

cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "deploy\reveiller_services.ps1"
