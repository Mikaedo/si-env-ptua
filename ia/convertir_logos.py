# -*- coding: utf-8 -*-
"""
Convertit les logos SVG des technologies en PNG a fond transparent, pour
insertion dans le tableau des technologies du memoire (Word ne sait pas
afficher un SVG dans un tableau via python-docx).

Le rendu passe par un navigateur sans interface : c'est le moteur qui
interprete le mieux les SVG complexes, la ou une bibliotheque de conversion
echouerait sur certains degrades ou masques.

Les logos issus de simple-icons sont monochromes noirs : on leur applique la
couleur officielle de la marque, sinon ils apparaitraient comme des taches
noires a cote des logos coloriens.
"""
import base64
import io
import os

from playwright.sync_api import sync_playwright

DOSSIER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logos_tech")
TAILLE = 96  # pixels ; suffisant pour une cellule de tableau imprimee

#: Couleur de marque a appliquer aux logos monochromes.
COULEURS = {
    'leaflet': '#199900',
    'jwt': '#D63AFF',
}


def main():
    fichiers = sorted(f for f in os.listdir(DOSSIER) if f.endswith('.svg'))
    if not fichiers:
        raise SystemExit("Aucun SVG dans %s" % DOSSIER)

    with sync_playwright() as p:
        nav = p.chromium.launch()
        page = nav.new_page(viewport={"width": TAILLE, "height": TAILLE})

        for fichier in fichiers:
            nom = os.path.splitext(fichier)[0]
            chemin = os.path.join(DOSSIER, fichier)
            svg = io.open(chemin, encoding='utf-8').read()

            couleur = COULEURS.get(nom)
            teinte = ("svg,svg path{fill:%s !important;}" % couleur) if couleur else ""

            html = (
                "<!doctype html><html><head><meta charset='utf-8'><style>"
                "html,body{margin:0;padding:0;background:transparent;}"
                "#c{width:%dpx;height:%dpx;display:flex;align-items:center;"
                "justify-content:center;}"
                "#c svg{width:100%%;height:100%%;}"
                "%s"
                "</style></head><body><div id='c'>%s</div></body></html>"
                % (TAILLE, TAILLE, teinte, svg)
            )
            page.set_content(html)
            page.wait_for_timeout(350)
            sortie = os.path.join(DOSSIER, nom + ".png")
            page.locator("#c").screenshot(path=sortie, omit_background=True)
            print("  %-12s -> %s (%d octets)"
                  % (nom, os.path.basename(sortie), os.path.getsize(sortie)))

        nav.close()
    print("\nPNG disponibles dans :", DOSSIER)


if __name__ == "__main__":
    main()
