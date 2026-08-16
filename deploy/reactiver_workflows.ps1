# Verifie et reactive les taches planifiees du depot.
#
# A quoi sert ce script alors que keepalive.yml previent deja le probleme ?
# A la seule situation que keepalive.yml ne peut pas traiter : celle ou les
# workflows sont deja desactives. Un workflow planifie eteint ne se rallume pas
# tout seul, puisqu'il ne s'execute plus. La reparation doit donc venir de
# l'exterieur, depuis un poste authentifie.
#
# A lancer si le service Render repond lentement sans raison, si aucune
# execution recente n'apparait dans l'onglet Actions, ou par precaution dans
# les jours qui precedent la soutenance.
#
# Prerequis : le client gh installe et connecte (gh auth login).
#
# Usage :
#   pwsh deploy/reactiver_workflows.ps1
#   pwsh deploy/reactiver_workflows.ps1 -Pousser

param(
    # Pousse en plus un commit d'horodatage, ce qui remet a zero le compteur
    # des 60 jours sans attendre la prochaine execution hebdomadaire.
    [switch]$Pousser
)

$ErrorActionPreference = "Stop"

function Ecrire($texte, $couleur = "Gray") {
    Write-Host $texte -ForegroundColor $couleur
}

# --- Verifications prealables ------------------------------------------------

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Ecrire "Le client gh est introuvable. Installez-le depuis https://cli.github.com" "Red"
    exit 1
}

try { gh auth status 2>&1 | Out-Null } catch {
    Ecrire "Vous n'etes pas connecte. Lancez d'abord : gh auth login" "Red"
    exit 1
}

$depot = gh repo view --json nameWithOwner --jq .nameWithOwner
Ecrire "Depot : $depot" "Cyan"
Ecrire ""

# --- Etat des workflows ------------------------------------------------------

$workflows = gh workflow list --all --repo $depot --json id,name,state | ConvertFrom-Json

$actifs = @($workflows | Where-Object { $_.state -eq "active" })
$eteints = @($workflows | Where-Object { $_.state -ne "active" })

Ecrire "Workflows actifs : $($actifs.Count)" "Green"
foreach ($w in $actifs) { Ecrire "   $($w.name)" }

if ($eteints.Count -eq 0) {
    Ecrire ""
    Ecrire "Aucun workflow desactive. Rien a reparer." "Green"
} else {
    Ecrire ""
    Ecrire "Workflows desactives : $($eteints.Count)" "Yellow"
    foreach ($w in $eteints) {
        Ecrire "   $($w.name)  [$($w.state)]" "Yellow"
    }
    Ecrire ""
    foreach ($w in $eteints) {
        try {
            gh workflow enable $w.id --repo $depot
            Ecrire "   reactive : $($w.name)" "Green"
        } catch {
            Ecrire "   echec sur $($w.name) : $_" "Red"
        }
    }
}

# --- Anciennete de la derniere activite --------------------------------------

Ecrire ""
$dernier = gh api "repos/$depot/commits?per_page=1" --jq '.[0].commit.committer.date'
$ecart = (Get-Date).ToUniversalTime() - [datetime]::Parse($dernier).ToUniversalTime()
$jours = [math]::Floor($ecart.TotalDays)
$restants = 60 - $jours

Ecrire "Dernier commit : il y a $jours jour(s)."
if ($restants -le 14) {
    Ecrire "Desactivation automatique dans $restants jour(s). Poussez quelque chose." "Red"
} elseif ($restants -le 30) {
    Ecrire "Desactivation automatique dans $restants jour(s)." "Yellow"
} else {
    Ecrire "Desactivation automatique dans $restants jour(s). Marge confortable." "Green"
}

# --- Remise a zero du compteur, sur demande ----------------------------------

if ($Pousser) {
    Ecrire ""
    $horodatage = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd HH:mm:ss")
    $chemin = ".github/derniere_activite.txt"
    $contenu = @"
Ce fichier n'a qu'un role : produire une activite reguliere sur le depot, afin
que GitHub ne desactive pas les workflows planifies.

Derniere mise a jour : $horodatage UTC
Origine : deploy/reactiver_workflows.ps1
"@
    New-Item -ItemType Directory -Force -Path ".github" | Out-Null
    Set-Content -Path $chemin -Value $contenu -Encoding utf8

    git add $chemin
    git commit -m "Maintien de l'activite du depot pour les taches planifiees"
    git push
    Ecrire "Compteur des 60 jours remis a zero." "Green"
}
