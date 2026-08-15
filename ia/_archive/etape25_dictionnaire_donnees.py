# -*- coding: utf-8 -*-
"""
Etape 25 : reconstruire le dictionnaire de donnees (annexe F, tableau F.2)
a partir du vrai schema de la base (backend/app/models.py).

L'ancien tableau F.2, intitule « restreint (principales entites) », ne
couvrait que 5 entites sur les 10 reelles, et certaines etaient reduites a
leur seule cle primaire (Chantier : un seul champ ; Alerte : un seul champ).
Cette etape le remplace par un dictionnaire complet des 10 tables reelles
(utilisateurs, chantiers, signalements, photos, alertes, actions_correctives,
non_conformites, plaintes, alertes_seuils, journaux), reste en annexe F comme
demande.

Sortie : mise a jour de MEMOIRE_FINAL.docx
"""
import os
import sys

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.table import Table

sys.stdout.reconfigure(encoding='utf-8')

CIBLE = os.path.join('C:', os.sep, 'Users', 'DELL', 'Downloads', 'MEMOIRE',
                     'MEMOIRE_FINAL.docx')
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
WQ = '{%s}' % W

LARGEURS = [2200, 2200, 1600, 3000]  # twips : Entité, Attribut, Type, Description


def qw(tag):
    return qn('w:' + tag)


DONNEES = [
    ("Entité", "Attribut", "Type", "Description"),

    ("Utilisateur", "id", "Entier (PK)", "Identifiant unique de l'utilisateur"),
    ("Utilisateur", "nom", "Texte", "Nom complet de l'utilisateur"),
    ("Utilisateur", "email", "Texte", "Identifiant de connexion, unique"),
    ("Utilisateur", "mot_de_passe_hash", "Texte", "Empreinte bcrypt du mot de passe"),
    ("Utilisateur", "role", "Énuméré", "Habilitation : RESP_ENV, EXPERT_HSE, SPEC_ENV, SPEC_PAR, ADMIN"),
    ("Utilisateur", "premiere_connexion", "Booléen", "Force le changement de mot de passe à la première connexion"),
    ("Utilisateur", "telephone", "Texte", "Contact téléphonique, optionnel"),
    ("Utilisateur", "cree_le", "Horodatage", "Date de création du compte"),
    ("Utilisateur", "token_invitation", "Texte", "Jeton à usage unique pour l'activation du compte"),
    ("Utilisateur", "token_invitation_expire", "Horodatage", "Date d'expiration du jeton d'invitation"),

    ("Chantier", "id", "Entier (PK)", "Identifiant du chantier"),
    ("Chantier", "nom", "Texte", "Nom ou tronçon du chantier PTUA"),
    ("Chantier", "commune", "Texte", "Commune d'Abidjan concernée"),
    ("Chantier", "geom", "Geometry (Point)", "Coordonnées GPS du chantier, WGS84"),

    ("Signalement", "id", "Entier (PK)", "Identifiant séquentiel du signalement"),
    ("Signalement", "uuid_mobile", "Texte", "Identifiant généré côté mobile pour la synchronisation hors ligne"),
    ("Signalement", "type_nuisance", "Texte", "Catégorie(s) de nuisance signalée(s)"),
    ("Signalement", "description", "Texte long", "Commentaire libre de l'agent"),
    ("Signalement", "criticite", "Énuméré", "Criticité déclarée : FAIBLE, MODERE, ELEVE"),
    ("Signalement", "criticite_ia", "Énuméré", "Criticité estimée par le modèle IA"),
    ("Signalement", "confiance_ia", "Décimal", "Score de confiance du diagnostic IA"),
    ("Signalement", "gps_source", "Texte", "Origine des coordonnées : AUTO ou MANUEL"),
    ("Signalement", "statut", "Énuméré", "État : NOUVEAU, EN_TRAITEMENT, CLOTURE, REJETE"),
    ("Signalement", "geom", "Geometry (Point)", "Localisation du signalement, WGS84"),
    ("Signalement", "cree_le", "Horodatage", "Date de création"),
    ("Signalement", "auteur_id", "Entier (FK)", "Référence à l'utilisateur auteur"),
    ("Signalement", "chantier_id", "Entier (FK)", "Référence au chantier concerné"),

    ("Photo", "id", "Entier (PK)", "Identifiant de la photo"),
    ("Photo", "chemin", "Texte", "Chemin de stockage du fichier image"),
    ("Photo", "signalement_id", "Entier (FK)", "Référence au signalement illustré"),

    ("Alerte", "id", "Entier (PK)", "Identifiant de l'alerte"),
    ("Alerte", "message", "Texte", "Contenu de l'alerte"),
    ("Alerte", "niveau", "Texte", "Niveau de sévérité : INFO, WARNING…"),
    ("Alerte", "valeur", "Décimal", "Valeur mesurée ayant déclenché l'alerte"),
    ("Alerte", "cree_le", "Horodatage", "Date de déclenchement"),
    ("Alerte", "chantier_id", "Entier (FK)", "Chantier concerné"),
    ("Alerte", "utilisateur_id", "Entier (FK)", "Destinataire de l'alerte"),
    ("Alerte", "recue", "Booléen", "Accusé de réception"),

    ("ActionCorrective", "id", "Entier (PK)", "Identifiant de l'action corrective"),
    ("ActionCorrective", "description", "Texte long", "Description de l'action à mener"),
    ("ActionCorrective", "echeance", "Horodatage", "Date limite de réalisation"),
    ("ActionCorrective", "cree_le", "Horodatage", "Date de création"),
    ("ActionCorrective", "signalement_id", "Entier (FK)", "Signalement à l'origine de l'action"),

    ("NonConformite", "id", "Entier (PK)", "Identifiant de la non-conformité"),
    ("NonConformite", "description", "Texte long", "Description de l'écart constaté"),
    ("NonConformite", "severite", "Texte", "Gravité : FAIBLE, MOYENNE, ELEVEE"),
    ("NonConformite", "resolue", "Booléen", "Statut de résolution"),
    ("NonConformite", "cree_le", "Horodatage", "Date de constat"),
    ("NonConformite", "signalement_id", "Entier (FK)", "Signalement associé"),

    ("Plainte", "id", "Entier (PK)", "Identifiant de la plainte (MGP)"),
    ("Plainte", "nom_plaignant", "Texte", "Identité du plaignant"),
    ("Plainte", "contact", "Texte", "Moyen de contact du plaignant"),
    ("Plainte", "description", "Texte long", "Objet de la plainte"),
    ("Plainte", "statut", "Texte", "État de traitement : OUVERTE…"),
    ("Plainte", "cree_le", "Horodatage", "Date de dépôt"),
    ("Plainte", "chantier_id", "Entier (FK)", "Chantier concerné"),

    ("AlerteSeuil", "id", "Entier (PK)", "Identifiant du seuil configuré"),
    ("AlerteSeuil", "nom", "Texte", "Nom du seuil"),
    ("AlerteSeuil", "indicateur", "Texte", "Indicateur surveillé : NO2, RISQUE_PLUIE…"),
    ("AlerteSeuil", "seuil", "Décimal", "Valeur de déclenchement"),
    ("AlerteSeuil", "niveau", "Texte", "Niveau associé au dépassement"),
    ("AlerteSeuil", "actif", "Booléen", "Seuil actuellement actif"),
    ("AlerteSeuil", "cree_le", "Horodatage", "Date de création du seuil"),

    ("Journal", "id", "Entier (PK)", "Identifiant de l'entrée de journal"),
    ("Journal", "niveau", "Texte", "Niveau de log : INFO, WARNING, ERROR"),
    ("Journal", "message", "Texte long", "Message journalisé"),
    ("Journal", "utilisateur", "Texte", "Utilisateur concerné, si applicable"),
    ("Journal", "ip_source", "Texte", "Adresse IP source"),
    ("Journal", "cree_le", "Horodatage", "Horodatage de l'événement"),
]


def cellule(tc_el, texte, entete=False):
    tcpr = OxmlElement('w:tcPr')
    tc_el.append(tcpr)
    tcw = OxmlElement('w:tcW')
    tcw.set(qw('type'), 'dxa')
    tcpr.append(tcw)
    if entete:
        shd = OxmlElement('w:shd')
        shd.set(qw('val'), 'clear')
        shd.set(qw('color'), 'auto')
        shd.set(qw('fill'), 'E8E8E8')
        tcpr.append(shd)

    p_el = OxmlElement('w:p')
    tc_el.append(p_el)
    ppr = OxmlElement('w:pPr')
    p_el.append(ppr)
    spacing = OxmlElement('w:spacing')
    spacing.set(qw('after'), '20')
    spacing.set(qw('line'), '240')
    spacing.set(qw('lineRule'), 'auto')
    ppr.append(spacing)

    r = OxmlElement('w:r')
    p_el.append(r)
    rpr = OxmlElement('w:rPr')
    r.append(rpr)
    sz = OxmlElement('w:sz')
    sz.set(qw('val'), '18')
    rpr.append(sz)
    lang = OxmlElement('w:lang')
    lang.set(qw('val'), 'fr-FR')
    rpr.append(lang)
    t = OxmlElement('w:t')
    t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    t.text = texte
    r.append(t)
    return tcw


def construire_tableau(ancre_el, doc, lignes, largeurs):
    tbl = OxmlElement('w:tbl')
    ancre_el.addprevious(tbl)

    tblpr = OxmlElement('w:tblPr')
    tbl.append(tblpr)
    style = OxmlElement('w:tblStyle')
    style.set(qw('val'), 'Grilledutableau')
    tblpr.append(style)
    tblw = OxmlElement('w:tblW')
    tblw.set(qw('w'), '0')
    tblw.set(qw('type'), 'auto')
    tblpr.append(tblw)
    jc = OxmlElement('w:jc')
    jc.set(qw('val'), 'center')
    tblpr.append(jc)
    look = OxmlElement('w:tblLook')
    look.set(qw('val'), '04A0')
    look.set(qw('firstRow'), '1')
    look.set(qw('lastRow'), '0')
    look.set(qw('firstColumn'), '1')
    look.set(qw('lastColumn'), '0')
    look.set(qw('noHBand'), '0')
    look.set(qw('noVBand'), '1')
    tblpr.append(look)

    grid = OxmlElement('w:tblGrid')
    tbl.append(grid)
    for w in largeurs:
        gc = OxmlElement('w:gridCol')
        gc.set(qw('w'), str(w))
        grid.append(gc)

    for i, ligne in enumerate(lignes):
        tr = OxmlElement('w:tr')
        tbl.append(tr)
        trpr = OxmlElement('w:trPr')
        tr.append(trpr)
        trpr.append(OxmlElement('w:cantSplit'))
        if i == 0:
            trpr.append(OxmlElement('w:tblHeader'))
        for j, valeur in enumerate(ligne):
            tc = OxmlElement('w:tc')
            tr.append(tc)
            tcw_el = cellule(tc, valeur, entete=(i == 0))
            tcw_el.set(qw('w'), str(largeurs[j]))

    return Table(tbl, doc)


def main():
    doc = Document(CIBLE)
    body = doc.element.body
    els = list(body)

    # ── Repérage de l'ancienne légende + tableau F.2 dans le corps ──────────
    i_leg = None
    for i, el in enumerate(els):
        if not el.tag.endswith('}p'):
            continue
        txt = ''.join(t.text or '' for t in el.iter(WQ + 't')).strip()
        if txt.startswith('Tableau F.2'):
            # confirmer que suivi d'un vrai tableau (pas l'entrée de liste)
            for j in range(i + 1, min(i + 3, len(els))):
                if els[j].tag.endswith('}tbl'):
                    i_leg = i
                    break
            if i_leg is not None:
                break
    assert i_leg is not None, "légende F.2 introuvable"

    i_tbl = None
    for j in range(i_leg + 1, min(i_leg + 3, len(els))):
        if els[j].tag.endswith('}tbl'):
            i_tbl = j
            break
    assert i_tbl is not None, "tableau F.2 introuvable"

    print("  ancienne légende : el%d | tableau : el%d" % (i_leg, i_tbl))

    # Nouvelle légende (sans le mot "restreint")
    from docx.text.paragraph import Paragraph
    leg_par = Paragraph(els[i_leg], doc.paragraphs[0]._parent)
    noeuds = list(els[i_leg].iter(WQ + 't'))
    noeuds[0].text = ("Tableau F.2 : Dictionnaire de données du SI-ENV "
                      "(10 entités).")
    for n in noeuds[1:]:
        n.text = ''

    # Suppression de l'ancien tableau, insertion du nouveau à sa place
    ancre = els[i_tbl]
    nouveau = construire_tableau(ancre, doc, DONNEES, LARGEURS)
    ancre.getparent().remove(ancre)

    print("  nouveau tableau F.2 : %d lignes (%d entités)"
          % (len(DONNEES), len(set(r[0] for r in DONNEES[1:]))))

    doc.save(CIBLE)
    print("\nEnregistré : %s" % CIBLE)


if __name__ == "__main__":
    main()
