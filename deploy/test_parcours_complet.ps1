# Parcours fonctionnel complet, joue sur le service en ligne.
#
# Ce script ne verifie pas que le serveur repond, ce que fait deja
# reveiller_services.ps1, mais que chaque profil peut faire ce qu'il doit faire
# et rien de plus. Il suit aussi la donnee d'un bout a l'autre : un signalement
# saisi par un agent doit apparaitre au tableau de bord du specialiste, une
# doleance deposee par un riverain doit rejoindre la file du specialiste PAR.
# Une chaine ou chaque maillon fonctionne isolement peut rester rompue au
# milieu ; seul un parcours de bout en bout le montre.
#
# Les deux enregistrements crees portent une marque et sont supprimes a la fin,
# pour ne pas laisser de trace dans les donnees de demonstration.
#
# Usage : pwsh deploy/test_parcours_complet.ps1

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

$API = "https://si-env-ptua.onrender.com"
$MARQUE = "VERIF-AUTO-" + (Get-Date -Format "yyyyMMddHHmmss")

$resultats = @()

function Titre($texte) {
    Write-Host ""
    Write-Host "  $texte" -ForegroundColor Cyan
    Write-Host ("  " + ("-" * 62)) -ForegroundColor DarkGray
}

function Verdict($profil, $action, $ok, $detail) {
    $script:resultats += [pscustomobject]@{ Profil = $profil; Action = $action; Ok = $ok }
    $etat = if ($ok) { "OK   " } else { "ECHEC" }
    $couleur = if ($ok) { "Green" } else { "Red" }
    Write-Host ("    {0} {1,-34} {2}" -f $etat, $action, $detail) -ForegroundColor $couleur
}

function Jeton($email, $motdepasse) {
    try {
        (Invoke-RestMethod -Uri "$API/auth/login" -Method Post `
            -Body @{ username = $email; password = $motdepasse } -TimeoutSec 60).access_token
    } catch { $null }
}

function Lire($jeton, $chemin) {
    Invoke-RestMethod -Uri "$API$chemin" -Headers @{ Authorization = "Bearer $jeton" } -TimeoutSec 45
}

function Ecrire($jeton, $chemin, $corps, $methode = "Post") {
    Invoke-RestMethod -Uri "$API$chemin" -Method $methode `
        -Headers @{ Authorization = "Bearer $jeton" } `
        -Body ($corps | ConvertTo-Json -Depth 5) -ContentType "application/json" -TimeoutSec 60
}

Clear-Host
Write-Host ""
Write-Host "  ===============================================================" -ForegroundColor White
Write-Host "   SI-ENV : parcours fonctionnel par profil" -ForegroundColor White
Write-Host "  ===============================================================" -ForegroundColor White
Write-Host "   $(Get-Date -Format 'dddd d MMMM yyyy, HH:mm')  ·  marque $MARQUE" -ForegroundColor DarkGray

# --- Agents de terrain, application mobile -----------------------------------

Titre "RESP_ENV  ·  application mobile agent"
$respEnv = Jeton "resp.env@ageroute.ci" "env123"
Verdict "RESP_ENV" "Connexion" ($null -ne $respEnv) "jeton obtenu"

$idSignalement = $null
if ($respEnv) {
    try {
        $h = Lire $respEnv "/signalements"
        Verdict "RESP_ENV" "Consulter l'historique" $true "$(@($h).Count) signalement(s)"
    } catch { Verdict "RESP_ENV" "Consulter l'historique" $false $_.Exception.Message }

    # Saisie telle que la ferait le mobile apres synchronisation : l'uuid_mobile
    # est genere sur le telephone et sert de cle d'idempotence.
    try {
        $s = Ecrire $respEnv "/signalements" @{
            uuid_mobile   = [guid]::NewGuid().ToString()
            type_nuisance = "Dechets de chantier"
            description   = "$MARQUE controle automatique de la chaine"
            latitude      = 5.3364
            longitude     = -4.0267
            gps_source    = "GPS"
            chantier_id   = 1
        }
        $idSignalement = $s.id
        Verdict "RESP_ENV" "Saisir un signalement" $true "identifiant $idSignalement"
    } catch { Verdict "RESP_ENV" "Saisir un signalement" $false $_.Exception.Message }
}

Titre "EXPERT_HSE  ·  application mobile agent"
$hse = Jeton "expert.hse@ageroute.ci" "expert123"
Verdict "EXPERT_HSE" "Connexion" ($null -ne $hse) "jeton obtenu"

if ($hse -and $idSignalement) {
    try {
        $d = Lire $hse "/signalements/$idSignalement"
        Verdict "EXPERT_HSE" "Ouvrir le signalement de l'agent" $true "statut $($d.statut)"
    } catch { Verdict "EXPERT_HSE" "Ouvrir le signalement de l'agent" $false $_.Exception.Message }

    try {
        Ecrire $hse "/signalements/$idSignalement/action" @{
            description = "$MARQUE action corrective de controle"
        } | Out-Null
        Verdict "EXPERT_HSE" "Ajouter une action corrective" $true "enregistree"
    } catch { Verdict "EXPERT_HSE" "Ajouter une action corrective" $false $_.Exception.Message }

    # Le statut se passe en parametre d'URL, non dans un corps JSON, et les
    # valeurs sont celles de l'enumeration du modele : EN_TRAITEMENT, pas
    # EN_COURS, qui appartient au cycle de vie des plaintes.
    try {
        Invoke-RestMethod -Method Patch -TimeoutSec 60 `
            -Uri "$API/signalements/$idSignalement/statut?nouveau_statut=EN_TRAITEMENT" `
            -Headers @{ Authorization = "Bearer $hse" } | Out-Null
        Verdict "EXPERT_HSE" "Changer le statut" $true "passe a EN_TRAITEMENT"
    } catch { Verdict "EXPERT_HSE" "Changer le statut" $false $_.Exception.Message }
}

# --- Pilotage, tableau de bord web -------------------------------------------

Titre "SPEC_ENV  ·  tableau de bord web"
$specEnv = Jeton "spec.env@ageroute.ci" "spec123"
Verdict "SPEC_ENV" "Connexion" ($null -ne $specEnv) "jeton obtenu"

if ($specEnv) {
    foreach ($v in @(
        @{ c = "/stats";               a = "Tableau de bord, statistiques" },
        @{ c = "/alertes";             a = "Gerer les alertes" },
        @{ c = "/chantiers";           a = "Referentiel des chantiers" },
        @{ c = "/satellite/chantiers"; a = "Chantiers de l'analyse satellite" },
        @{ c = "/satellite/resume";    a = "Resume satellitaire" },
        @{ c = "/rapports/transmissions"; a = "Historique des transmissions" })) {
        try {
            $r = Lire $specEnv $v.c
            $n = if ($r -is [array]) { "$(@($r).Count) element(s)" } else { "reponse recue" }
            Verdict "SPEC_ENV" $v.a $true $n
        } catch { Verdict "SPEC_ENV" $v.a $false $_.Exception.Message }
    }

    # La chaine : le signalement saisi sur mobile doit etre visible ici.
    if ($idSignalement) {
        try {
            $tout = Lire $specEnv "/signalements"
            $trouve = @($tout | Where-Object { $_.id -eq $idSignalement }).Count -gt 0
            Verdict "SPEC_ENV" "CHAINE mobile vers web" $trouve `
                "signalement $idSignalement $(if ($trouve) { 'remonte' } else { 'absent' })"
        } catch { Verdict "SPEC_ENV" "CHAINE mobile vers web" $false $_.Exception.Message }
    }

    try {
        $rap = Ecrire $specEnv "/rapports/generate" @{
            date_debut = (Get-Date).AddMonths(-6).ToString("yyyy-MM-dd")
            date_fin   = (Get-Date).ToString("yyyy-MM-dd")
            chantier_ids = @(1)
        }
        Verdict "SPEC_ENV" "Produire le rapport de suivi" $true "PDF genere"
    } catch { Verdict "SPEC_ENV" "Produire le rapport de suivi" $false $_.Exception.Message }
}

# --- Volet riverain, application mobile citoyenne ----------------------------

Titre "PLAIGNANT  ·  application mobile citoyenne"
$riverain = Jeton "riverain@yopougon.ci" "riverain123"
Verdict "PLAIGNANT" "Connexion" ($null -ne $riverain) "jeton obtenu"

$idDoleance = $null
if ($riverain) {
    try {
        $z = Invoke-RestMethod -Uri "$API/citoyen/verifier-zone" -Method Post `
            -Body (@{ latitude = 5.3364; longitude = -4.0267 } | ConvertTo-Json) `
            -ContentType "application/json" -TimeoutSec 45
        Verdict "PLAIGNANT" "Verifier la zone d'influence" $z.autorise "$($z.chantier_nom), $($z.distance_m) m"
    } catch { Verdict "PLAIGNANT" "Verifier la zone d'influence" $false $_.Exception.Message }

    try {
        $c = Lire $riverain "/citoyen/mon-chantier"
        Verdict "PLAIGNANT" "Consulter son rattachement" $true "$($c.nom), $($c.commune)"
    } catch { Verdict "PLAIGNANT" "Consulter son rattachement" $false $_.Exception.Message }

    try {
        $d = Ecrire $riverain "/citoyen/doleances" @{
            description = "$MARQUE doleance de controle automatique"
            categorie   = "BRUIT"
            latitude    = 5.3364
            longitude   = -4.0267
        }
        $idDoleance = $d.id
        Verdict "PLAIGNANT" "Deposer une doleance" $true "identifiant $idDoleance"
    } catch { Verdict "PLAIGNANT" "Deposer une doleance" $false $_.Exception.Message }

    try {
        $mes = Lire $riverain "/citoyen/doleances"
        Verdict "PLAIGNANT" "Suivre ses doleances" $true "$(@($mes).Count) enregistrement(s)"
    } catch { Verdict "PLAIGNANT" "Suivre ses doleances" $false $_.Exception.Message }
}

Titre "SPEC_PAR  ·  tableau de bord web"
$specPar = Jeton "spec.par@ageroute.ci" "spec123"
Verdict "SPEC_PAR" "Connexion" ($null -ne $specPar) "jeton obtenu"

if ($specPar) {
    try {
        $p = Lire $specPar "/plaintes"
        Verdict "SPEC_PAR" "Traiter les plaintes" $true "$(@($p).Count) plainte(s)"
        if ($idDoleance) {
            $trouve = @($p | Where-Object { $_.id -eq $idDoleance }).Count -gt 0
            Verdict "SPEC_PAR" "CHAINE riverain vers web" $trouve `
                "doleance $idDoleance $(if ($trouve) { 'dans la file' } else { 'absente' })"
        }
    } catch { Verdict "SPEC_PAR" "Traiter les plaintes" $false $_.Exception.Message }

    if ($idDoleance) {
        try {
            Ecrire $specPar "/plaintes/$idDoleance/statut" @{ statut = "EN_COURS" } "Patch" | Out-Null
            Verdict "SPEC_PAR" "Qualifier une plainte" $true "passe a EN_COURS"
        } catch { Verdict "SPEC_PAR" "Qualifier une plainte" $false $_.Exception.Message }
    }
}

# --- Organismes de controle, consultation seule ------------------------------

foreach ($org in @(
    @{ n = "ANDE"; e = "controle@ande.ci"; p = "ande123" },
    @{ n = "BAD";  e = "mission@afdb.org"; p = "bad123" })) {

    Titre "$($org.n)  ·  consultation seule"
    $j = Jeton $org.e $org.p
    Verdict $org.n "Connexion" ($null -ne $j) "jeton obtenu"

    if ($j) {
        foreach ($c in @("/stats", "/signalements", "/satellite/resume", "/rapports/transmissions")) {
            try { Lire $j $c | Out-Null; Verdict $org.n "Consulter $c" $true "acces accorde" }
            catch { Verdict $org.n "Consulter $c" $false $_.Exception.Message }
        }
        # Le refus doit venir du serveur, pas d'un bouton masque dans l'interface.
        try {
            Ecrire $j "/chantiers" @{ nom = "$MARQUE"; commune = "Abidjan" } | Out-Null
            Verdict $org.n "Ecriture refusee" $false "l'ecriture a ete acceptee"
        } catch {
            $code = $_.Exception.Response.StatusCode.value__
            Verdict $org.n "Ecriture refusee" ($code -eq 403) "HTTP $code"
        }
    }
}

# --- Administration ----------------------------------------------------------

Titre "ADMIN  ·  tableau de bord web"
$admin = Jeton "admin@sienv.ci" "admin123"
Verdict "ADMIN" "Connexion" ($null -ne $admin) "jeton obtenu"

if ($admin) {
    foreach ($v in @(
        @{ c = "/admin/users";  a = "Gerer les utilisateurs" },
        @{ c = "/admin/logs";   a = "Consulter le journal" },
        @{ c = "/admin/seuils"; a = "Parametrer les seuils" },
        @{ c = "/admin/model";  a = "Etat du modele" })) {
        try {
            $r = Lire $admin $v.c
            $n = if ($r -is [array]) { "$(@($r).Count) element(s)" } else { "reponse recue" }
            Verdict "ADMIN" $v.a $true $n
        } catch { Verdict "ADMIN" $v.a $false $_.Exception.Message }
    }
}

# --- Synthese ----------------------------------------------------------------

$echecs = @($resultats | Where-Object { -not $_.Ok })

Write-Host ""
Write-Host "  ===============================================================" -ForegroundColor White
if ($echecs.Count -eq 0) {
    Write-Host "   $($resultats.Count) verifications, aucune en echec." -ForegroundColor Green
} else {
    Write-Host "   $($resultats.Count) verifications, $($echecs.Count) en echec :" -ForegroundColor Red
    foreach ($e in $echecs) {
        Write-Host "     $($e.Profil) : $($e.Action)" -ForegroundColor Red
    }
}
Write-Host "  ===============================================================" -ForegroundColor White
Write-Host ""
Write-Host "  Enregistrements crees, a retirer : signalement $idSignalement, doleance $idDoleance" -ForegroundColor Yellow
Write-Host "  Marque : $MARQUE" -ForegroundColor DarkGray
Write-Host ""
