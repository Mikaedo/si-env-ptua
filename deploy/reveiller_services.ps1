# Reveille et verifie toute la chaine SI-ENV avant une demonstration.
#
# Le service Render se met en veille apres quinze minutes sans requete. La
# premiere requete qui suit paie un demarrage a froid d'environ cinquante
# secondes. Ce delai, subi devant un jury, ressemble a une panne.
#
# Ce script paie ce demarrage a votre place, puis verifie que la chaine
# repond vraiment : pas seulement que le serveur est joignable, mais qu'une
# connexion aboutit et que la base repond. Un serveur qui renvoie une page
# d'erreur est joignable et pourtant inutilisable.
#
# Aucun secret n'est requis : le script n'utilise que des adresses publiques
# et un compte de demonstration. Il peut donc etre lance par double-clic.
#
# Usage : double-clic sur REVEILLER_SI-ENV.bat, ou
#         pwsh deploy/reveiller_services.ps1

param(
    # Ferme sans attendre de touche. Utile pour un appel automatise ou un test.
    [switch]$Auto
)

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

$API  = "https://si-env-ptua.onrender.com"
$WEB  = "https://si-env-ptua.pages.dev"
$COMPTE = @{ username = "spec.env@ageroute.ci"; password = "spec123" }

$resultats = @()

function Etape($libelle) {
    Write-Host ""
    Write-Host "  $libelle" -ForegroundColor Cyan
}

function Verdict($nom, $ok, $detail) {
    $script:resultats += [pscustomobject]@{ Nom = $nom; Ok = $ok; Detail = $detail }
    if ($ok) {
        Write-Host "    OK    $detail" -ForegroundColor Green
    } else {
        Write-Host "    ECHEC $detail" -ForegroundColor Red
    }
}

Clear-Host
Write-Host ""
Write-Host "  =====================================================" -ForegroundColor White
Write-Host "   SI-ENV : reveil des services avant demonstration" -ForegroundColor White
Write-Host "  =====================================================" -ForegroundColor White
Write-Host "   $(Get-Date -Format 'dddd d MMMM yyyy, HH:mm')" -ForegroundColor DarkGray

# --- 1. Backend, avec patience -----------------------------------------------

Etape "1/5  Reveil du serveur d'application"
Write-Host "        Un demarrage a froid peut prendre une minute." -ForegroundColor DarkGray

$chrono = [Diagnostics.Stopwatch]::StartNew()
$reveille = $false
foreach ($essai in 1..6) {
    try {
        $r = Invoke-WebRequest -Uri "$API/" -TimeoutSec 30 -UseBasicParsing
        if ($r.StatusCode -lt 500) { $reveille = $true; break }
    } catch {
        Write-Host "        tentative $essai, le serveur demarre encore..." -ForegroundColor DarkGray
    }
}
$chrono.Stop()
$secondes = [math]::Round($chrono.Elapsed.TotalSeconds, 1)

if ($reveille) {
    Verdict "Backend" $true "reveille en $secondes s"
} else {
    Verdict "Backend" $false "injoignable apres $secondes s"
    Write-Host ""
    Write-Host "    Le reste des verifications depend du backend." -ForegroundColor Yellow
    Write-Host "    Verifiez votre connexion Internet, puis relancez." -ForegroundColor Yellow
}

# --- 2. Documentation --------------------------------------------------------

if ($reveille) {
    Etape "2/5  Documentation de l'API"
    try {
        $r = Invoke-WebRequest -Uri "$API/docs" -TimeoutSec 30 -UseBasicParsing
        Verdict "Swagger" ($r.StatusCode -eq 200) "HTTP $($r.StatusCode)"
    } catch {
        Verdict "Swagger" $false $_.Exception.Message
    }

    # --- 3. Connexion reelle -------------------------------------------------

    Etape "3/5  Connexion avec un compte de demonstration"
    $jeton = $null
    try {
        $r = Invoke-RestMethod -Uri "$API/auth/login" -Method Post -Body $COMPTE -TimeoutSec 30
        $jeton = $r.access_token
        Verdict "Authentification" ($null -ne $jeton) "jeton obtenu pour $($COMPTE.username)"
    } catch {
        Verdict "Authentification" $false $_.Exception.Message
    }

    # --- 4. Base de donnees et donnees spatiales -----------------------------

    Etape "4/5  Base de donnees et referentiel des chantiers"
    if ($jeton) {
        try {
            $entetes = @{ Authorization = "Bearer $jeton" }
            $chantiers = Invoke-RestMethod -Uri "$API/chantiers" -Headers $entetes -TimeoutSec 30
            $n = @($chantiers).Count
            Verdict "Base PostGIS" ($n -ge 6) "$n chantiers lus"
        } catch {
            Verdict "Base PostGIS" $false $_.Exception.Message
        }
    } else {
        Verdict "Base PostGIS" $false "non testee, la connexion a echoue"
    }
}

# --- 5. Tableau de bord ------------------------------------------------------

Etape "5/5  Tableau de bord web"
try {
    $r = Invoke-WebRequest -Uri $WEB -TimeoutSec 30 -UseBasicParsing
    Verdict "Dashboard" ($r.StatusCode -eq 200) "HTTP $($r.StatusCode)"
} catch {
    Verdict "Dashboard" $false $_.Exception.Message
}

# --- Synthese ----------------------------------------------------------------

$echecs = @($resultats | Where-Object { -not $_.Ok })

Write-Host ""
Write-Host "  -----------------------------------------------------" -ForegroundColor White
if ($echecs.Count -eq 0) {
    Write-Host "   TOUT EST PRET. Vous pouvez presenter." -ForegroundColor Green
    Write-Host ""
    Write-Host "   Tableau de bord : $WEB" -ForegroundColor Gray
    Write-Host "   API             : $API/docs" -ForegroundColor Gray
    Write-Host "   Mobile          : aucun cable requis, les deux" -ForegroundColor Gray
    Write-Host "                     applications visent le serveur en ligne." -ForegroundColor Gray
} else {
    Write-Host "   $($echecs.Count) point(s) en echec :" -ForegroundColor Red
    foreach ($e in $echecs) {
        Write-Host "     - $($e.Nom) : $($e.Detail)" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "   Relancez une fois : un demarrage a froid suffit" -ForegroundColor Yellow
    Write-Host "   parfois a fausser la premiere tentative." -ForegroundColor Yellow
}
Write-Host "  -----------------------------------------------------" -ForegroundColor White
Write-Host ""

if (-not $Auto) {
    Write-Host "  Appuyez sur une touche pour fermer..." -ForegroundColor DarkGray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

exit $echecs.Count
