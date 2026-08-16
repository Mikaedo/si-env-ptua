# -*- coding: utf-8 -*-
"""
Inventorie puis supprime les comptes rattaches a une adresse donnee.

L'envoi de courriels passe par Resend en mode bac a sable : seule l'adresse
proprietaire du compte recoit reellement les messages. La demonstration de
creation d'un utilisateur devant un jury doit donc viser cette adresse, ce qui
suppose qu'aucun compte ne l'occupe deja au moment de la soutenance.

Le script n'efface rien sans avoir montre ce qu'il s'apprete a effacer. Un
premier appel se contente d'inventorier ; la suppression demande le drapeau
--supprimer. Cette separation evite qu'une faute de frappe dans l'adresse
n'emporte des comptes sans rapport.

Les dependances sont retirees avant le compte lui-meme, faute de quoi les
cles etrangeres feraient echouer la suppression a mi-parcours et laisseraient
la base dans un etat batard.

Usage :
    python deploy/purger_compte_demo.py mon.adresse@gmail.com
    python deploy/purger_compte_demo.py mon.adresse@gmail.com --supprimer
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from sqlalchemy import text                                    # noqa: E402
from app.database import SessionLocal                          # noqa: E402

# Tables portant une reference a un utilisateur, dans l'ordre ou elles doivent
# etre purgees : les feuilles avant les branches.
DEPENDANCES = [
    ("photos", "signalement_id IN (SELECT id FROM signalements WHERE utilisateur_id = :uid)"),
    ("actions_correctives", "utilisateur_id = :uid"),
    ("alertes", "signalement_id IN (SELECT id FROM signalements WHERE utilisateur_id = :uid)"),
    ("non_conformites", "signalement_id IN (SELECT id FROM signalements WHERE utilisateur_id = :uid)"),
    ("signalements", "utilisateur_id = :uid"),
    ("plaintes", "plaignant_id = :uid"),
    ("rapports", "utilisateur_id = :uid"),
    ("journaux", "utilisateur_id = :uid"),
]


def compter(db, table, condition, uid):
    """Nombre de lignes concernees, ou None si la table n'existe pas."""
    try:
        return db.execute(text(f"SELECT count(*) FROM {table} WHERE {condition}"),
                          {"uid": uid}).scalar()
    except Exception:
        db.rollback()
        return None


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    adresse = sys.argv[1].strip().lower()
    supprimer = "--supprimer" in sys.argv

    db = SessionLocal()
    try:
        comptes = db.execute(
            text("SELECT id, email, nom, role FROM utilisateurs "
                 "WHERE lower(email) = :e"),
            {"e": adresse},
        ).fetchall()

        if not comptes:
            print(f"Aucun compte pour {adresse}. L'adresse est libre.")
            return

        print(f"{len(comptes)} compte(s) pour {adresse} :\n")
        total = 0
        for uid, email, nom, role in comptes:
            print(f"  #{uid}  {nom}  [{role}]")
            for table, condition in DEPENDANCES:
                n = compter(db, table, condition, uid)
                if n:
                    print(f"        {n:>4} ligne(s) dans {table}")
                    total += n
            print()

        if not supprimer:
            print(f"{total} ligne(s) dependante(s) au total.")
            print("\nRien n'a ete supprime. Pour proceder, relancez avec :")
            print(f"    python deploy/purger_compte_demo.py {adresse} --supprimer")
            return

        for uid, email, nom, role in comptes:
            for table, condition in DEPENDANCES:
                try:
                    db.execute(text(f"DELETE FROM {table} WHERE {condition}"),
                               {"uid": uid})
                except Exception as erreur:
                    db.rollback()
                    print(f"    {table} ignoree : {str(erreur)[:70]}")
            db.execute(text("DELETE FROM utilisateurs WHERE id = :uid"),
                       {"uid": uid})
            print(f"  supprime : #{uid} {email} [{role}]")

        db.commit()

        reste = db.execute(
            text("SELECT count(*) FROM utilisateurs WHERE lower(email) = :e"),
            {"e": adresse},
        ).scalar()
        print(f"\nComptes restants pour cette adresse : {reste}")
        print("L'adresse est libre pour une creation en direct.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
