# -*- coding: utf-8 -*-
"""
Ajoute au §6.8 un paragraphe sur les ameliorations "niveau app moderne"
(cache OTP en base, refresh tokens, 2FA email, monitoring d'erreurs
embarque, rate limiting, pagination). Compense en supprimant le tableau
6.6 qui n'apporte plus rien (info dans le paragraphe precedent).
"""
import copy
import docx
from docx.text.paragraph import Paragraph

CHEMIN = r"C:\Users\DELL\Downloads\MEMOIRE\MEMOIRE_FINAL.docx"
d = docx.Document(CHEMIN)


def par(debut):
    for p in d.paragraphs:
        if p.text.strip().startswith(debut):
            return p
    raise SystemExit("PARAGRAPHE INTROUVABLE : " + debut[:70])


# 1) Trouver le paragraphe qui parle du dispositif watchdog (avant "Ce
# dispositif ne se substitue pas..." qui est le dernier)
p_watchdog = par("L'hébergement gratuit a une limite structurelle")

# 2) Inserer un nouveau paragraphe apres celui-la, sur les ameliorations pro
neuf = copy.deepcopy(p_watchdog._p)
p_watchdog._p.addnext(neuf)
nouveau = Paragraph(neuf, p_watchdog._parent)
texte = (
    "Au-dela de la disponibilite, le backend a ete rapproche du niveau attendu "
    "d'une application transactionnelle moderne. Les codes a usage unique de "
    "reinitialisation de mot de passe et d'authentification a deux facteurs "
    "sont persistes dans une table dediee, ce qui garantit leur survie aux "
    "redemarrages du service ; les jetons d'acces sont associes a des jetons "
    "de rafraichissement revocables, permettant la deconnexion cote serveur ; "
    "la deuxieme authentification par courriel est activable par utilisateur ; "
    "chaque exception non geree est capturee par un intergiciel et consignee "
    "dans une table d'audit consultable par l'administrateur, tenant lieu de "
    "monitoring embarque ; un limiteur de debit protege les points d'entree "
    "des acces massifs ; les listes administratives sont paginees. Ces "
    "ajouts, tous developpes en Python pur ou en SQL sans dependance a un "
    "service tiers, evitent la creation de comptes supplementaires tout en "
    "rapprochant le systeme des standards Sentry, Redis ou Auth0."
)
nouveau.runs[0].text = texte
for r in nouveau.runs[1:]:
    r.text = ""

d.save(CHEMIN)
print("§6.8 : paragraphe 'ameliorations pro' ajoute.")
