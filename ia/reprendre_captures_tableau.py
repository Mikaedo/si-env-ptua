# -*- coding: utf-8 -*-
"""
Reprend les captures du tableau de bord devenues fausses.

Sept d'entre elles montrent encore « Rapports PGES » dans le menu lateral,
libelle abandonne au renommage du rapport. Une huitieme, cote administrateur,
affiche un onglet « Configuration » depuis deplace vers l'analyse
satellitaire. Ces captures contredisent donc le texte qu'elles illustrent, et
le defaut se repete assez pour finir par se voir.

La navigation se fait en cliquant les entrees du menu plutot qu'en visant des
adresses : l'interface est une application a page unique dont les routes
peuvent changer, alors que les libelles du menu sont ce que le memoire decrit.

Chaque capture attend le rendu effectif d'un element de la page visee. Une
temporisation fixe photographierait tot ou tard un ecran de chargement.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "https://si-env-ptua.pages.dev"
API = "https://si-env-ptua.onrender.com"
SORTIE = Path(r"C:\Users\DELL\AppData\Local\Temp\claude"
              r"\d--etude-soutenance-SI-ENV\3233866b-194c-446a-b8f6-65c65b911c25"
              r"\scratchpad\figures")

SPEC = ("spec.env@ageroute.ci", "spec123")
ANDE = ("controle@ande.ci", "ande123")
ADMIN = ("admin@sienv.ci", "admin123")

# (fichier, compte, entree de menu, texte attendu a l'ecran, defilement)
PLAN = [
    ("D2_nouvelle.png", SPEC, "Tableau de bord", "Tableau de bord", 0),
    ("G2_nouvelle.png", SPEC, "Tableau de bord", "Tableau de bord", 0),
    ("D3_nouvelle.png", SPEC, "Alertes", "Alertes", 0),
    ("D4_nouvelle.png", SPEC, "Analyse satellitaire", "Analyse satellitaire", 0),
    ("C1_nouvelle.png", SPEC, "Analyse satellitaire", "Analyse satellitaire", 700),
    ("C2_nouvelle.png", SPEC, "Analyse satellitaire", "Analyse satellitaire", 1400),
    ("410_nouvelle.png", ANDE, "Signalements", "Signalements", 0),
    ("G3_nouvelle.png", ADMIN, "Journaux", "Journ", 0),
]


def connecter(page, compte):
    # Une session active renvoie directement au tableau de bord : sans purge,
    # le formulaire de connexion n'existe pas et le changement de compte echoue.
    page.goto(URL, wait_until="domcontentloaded", timeout=90000)
    page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
    page.context.clear_cookies()
    page.goto(URL, wait_until="networkidle", timeout=90000)
    page.fill("#login-email", compte[0])
    page.fill("#login-password", compte[1])
    page.click("#btn-login")
    page.wait_for_url(lambda u: "login" not in u, timeout=90000)
    page.wait_for_timeout(1500)


def main():
    with sync_playwright() as pw:
        nav = pw.chromium.launch(headless=True)
        page = nav.new_page(viewport={"width": 1600, "height": 950},
                            device_scale_factor=2)
        try:
            page.request.get(f"{API}/", timeout=90000)
        except Exception as e:
            print(f"  reveil : {e}")

        courant = None
        for fichier, compte, menu, attendu, defilement in PLAN:
            if compte != courant:
                connecter(page, compte)
                courant = compte
                print(f"\nconnecte : {compte[0]}")

            try:
                entree = page.get_by_text(menu, exact=False).first
                entree.wait_for(state="visible", timeout=45000)
                entree.click()
                page.wait_for_load_state("networkidle", timeout=90000)
                page.wait_for_timeout(2500)
                if defilement:
                    page.mouse.wheel(0, defilement)
                    page.wait_for_timeout(1500)
                page.screenshot(path=str(SORTIE / fichier))
                reste = "Rapports PGES" in page.inner_text("body")
                print(f"  {fichier:<18} {menu:<22} "
                      f"{'ANCIEN LIBELLE PRESENT' if reste else 'a jour'}")
            except Exception as e:
                print(f"  {fichier:<18} ECHEC : {str(e)[:90]}")

        nav.close()


if __name__ == "__main__":
    main()
