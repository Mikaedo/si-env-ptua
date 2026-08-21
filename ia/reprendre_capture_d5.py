# -*- coding: utf-8 -*-
"""
Reprend la capture de la figure D.5, devenue fausse.

La capture montrait le menu du tableau de bord annoncant « Rapports PGES ».
Ce libelle a change avec le renommage du rapport, et le memoire ne l'emploie
plus nulle part : la copie d'ecran contredisait donc le texte qu'elle est
censee illustrer.

Le service en ligne est reveille avant toute chose. Il se met en veille apres
quinze minutes et la premiere page mettrait sinon une minute a s'afficher, ce
qui ferait echouer la capture sur un ecran de chargement.

La capture est prise apres attente du rendu effectif du tableau, et non apres
un simple delai fixe : une temporisation en dur est le meilleur moyen de
photographier une page a moitie dessinee.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "https://si-env-ptua.pages.dev"
API = "https://si-env-ptua.onrender.com"
COMPTE = ("spec.env@ageroute.ci", "spec123")
SORTIE = Path(r"C:\Users\DELL\AppData\Local\Temp\claude"
              r"\d--etude-soutenance-SI-ENV\3233866b-194c-446a-b8f6-65c65b911c25"
              r"\scratchpad\figures\D5_nouvelle.png")


def main():
    with sync_playwright() as pw:
        nav = pw.chromium.launch(headless=True)
        page = nav.new_page(viewport={"width": 1600, "height": 950},
                            device_scale_factor=2)

        # Reveil du serveur avant d'ouvrir l'interface.
        try:
            page.request.get(f"{API}/", timeout=90000)
        except Exception as e:
            print(f"  reveil : {e}")

        page.goto(URL, wait_until="networkidle", timeout=90000)

        # Les champs portent des identifiants explicites : les viser evite de
        # dependre du type, que le bouton de revelation du mot de passe change.
        page.fill("#login-email", COMPTE[0])
        page.fill("#login-password", COMPTE[1])
        page.click("#btn-login")
        page.wait_for_url(lambda u: "login" not in u, timeout=90000)
        print("  connecte")

        # Le libelle du menu est ce que la capture doit montrer : on l'attend
        # explicitement plutot que de supposer qu'il est deja peint.
        menu = page.get_by_text("Rapports de suivi", exact=False).first
        menu.wait_for(state="visible", timeout=60000)
        libelle = menu.inner_text().strip()
        print(f"  libelle du menu : « {libelle} »")

        menu.click()
        page.wait_for_load_state("networkidle", timeout=90000)
        page.wait_for_timeout(2500)

        SORTIE.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(SORTIE))
        print(f"  capture : {SORTIE.name}")

        texte = page.inner_text("body")
        for interdit in ("Rapports PGES", "rapport PGES"):
            if interdit in texte:
                print(f"  ATTENTION : « {interdit} » encore present a l'ecran")
        nav.close()


if __name__ == "__main__":
    main()
