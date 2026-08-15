"""
test_redaction_pges.py
----------------------
Verifie que le commentaire du rapport suit reellement les donnees.

Le rapport comportait auparavant une introduction et une conclusion figees,
identiques d'un trimestre a l'autre quels que soient les chiffres. Un tel texte
n'apporte rien a son lecteur : il ne lui dit ni ou porter son attention, ni si
la situation s'ameliore. Les tests ci-dessous s'attachent donc a une seule
propriete, mais la plus importante : deux situations differentes doivent
produire deux rapports differents, et le texte doit dire quelque chose de vrai
sur les donnees qu'il accompagne.

Un second souci les traverse : la sobriete. Le systeme constate des volumes et
des delais, il ne se prononce pas sur la qualite environnementale reelle d'un
chantier, qui releve d'une expertise de terrain. Le commentaire ne doit donc
jamais affirmer plus que ce que les enregistrements etablissent.
"""
import pytest

from app.services import redaction_pges as redaction


def chantier(**surcharges) -> dict:
    """Chantier de reference, dont chaque test ne modifie que ce qui l'occupe."""
    base = {
        "id": 1, "nom": "Rocade Y4", "commune": "Yopougon",
        "nb_signalements": 10, "nb_alertes": 2, "nb_plaintes": 3,
        "nb_non_conformites": 2, "nb_traites": 8, "nb_en_cours": 1,
        "nb_nouveaux": 1, "nb_eleves": 1, "nb_plaintes_ouvertes": 1,
        "nb_plaintes_mobile": 2, "nb_nc_ouvertes": 0,
        "types_frequents": [{"type": "Poussière", "n": 6}],
    }
    base.update(surcharges)
    return base


class TestPeriode:
    """Mise en forme des dates, qui ouvre chaque rapport."""

    def test_les_deux_bornes(self):
        assert redaction.periode_redigee("2026-01-01", "2026-06-30") == \
            "du 1er janvier 2026 au 30 juin 2026"

    def test_le_premier_du_mois_prend_son_ordinal(self):
        """« du 1 janvier » se lit mal dans un document officiel."""
        assert "1er janvier" in redaction.periode_redigee("2026-01-01", None)

    def test_sans_borne(self):
        assert redaction.periode_redigee(None, None) == \
            "sur l'ensemble de la période disponible"


class TestSynthese:
    """Le commentaire des volumes globaux."""

    def test_l_absence_de_donnee_est_signalee_avec_prudence(self):
        """Zero signalement ne prouve pas qu'un chantier est irreprochable.

        Cela peut aussi traduire un defaut de remontee, et le rapport doit
        poser la question plutot que de conclure a la place du lecteur.
        """
        texte = redaction.synthese([chantier(
            nb_signalements=0, nb_plaintes=0, nb_alertes=0,
            nb_non_conformites=0, nb_traites=0, nb_en_cours=0,
            nb_nouveaux=0, nb_eleves=0, nb_plaintes_ouvertes=0,
            nb_nc_ouvertes=0, types_frequents=[],
        )], "2026-01-01", "2026-06-30")
        assert "défaut de remontée" in texte
        assert "prudente" in texte

    def test_un_taux_eleve_et_un_taux_faible_ne_se_lisent_pas_pareil(self):
        bon = redaction.synthese(
            [chantier(nb_signalements=10, nb_traites=9, nb_en_cours=1, nb_nouveaux=0)],
            None, None,
        )
        mauvais = redaction.synthese(
            [chantier(nb_signalements=10, nb_traites=2, nb_en_cours=4, nb_nouveaux=4)],
            None, None,
        )
        assert bon != mauvais
        assert "90 %" in bon
        assert "20 %" in mauvais
        assert "attention particulière" in mauvais

    def test_les_nuisances_sont_nommees(self):
        """Compter des signalements sans dire de quoi il s'agit n'apprend rien."""
        texte = redaction.synthese([chantier(
            types_frequents=[{"type": "Eaux stagnantes", "n": 7}],
        )], None, None)
        assert "eaux stagnantes" in texte.lower()

    def test_le_canal_citoyen_est_distingue(self):
        """L'apport de l'application mobile doit etre mesurable dans le rapport."""
        texte = redaction.synthese([chantier(nb_plaintes=5, nb_plaintes_mobile=4)], None, None)
        assert "application mobile" in texte
        assert "4" in texte

    def test_les_non_conformites_ouvertes_sont_mises_en_avant(self):
        texte = redaction.synthese([chantier(nb_non_conformites=3, nb_nc_ouvertes=2)], None, None)
        assert "conformité du projet" in texte

    def test_l_absence_de_non_conformite_ouverte_est_dite_aussi(self):
        texte = redaction.synthese([chantier(nb_non_conformites=3, nb_nc_ouvertes=0)], None, None)
        assert "régularisées" in texte


class TestCommentaireChantier:
    """L'analyse propre a chaque site."""

    def test_un_chantier_sans_constat_appelle_une_verification(self):
        texte = redaction.commentaire_chantier(chantier(
            nb_signalements=0, nb_plaintes=0, nb_alertes=0,
            nb_traites=0, nb_eleves=0, nb_nc_ouvertes=0, types_frequents=[],
        ))
        assert "application de terrain" in texte

    def test_un_chantier_entierement_traite_est_reconnu(self):
        texte = redaction.commentaire_chantier(chantier(
            nb_signalements=6, nb_traites=6, nb_eleves=0,
            nb_plaintes=0, nb_alertes=0, nb_nc_ouvertes=0,
        ))
        assert "intégralité" in texte

    def test_un_chantier_sans_aucune_cloture_declenche_une_alerte_de_gestion(self):
        texte = redaction.commentaire_chantier(chantier(
            nb_signalements=6, nb_traites=0,
        ))
        assert "entreprise attributaire" in texte


class TestConclusion:
    """Les recommandations, qui doivent decouler des constats."""

    def test_une_situation_saine_ne_recommande_rien(self):
        texte = redaction.conclusion([chantier(
            nb_traites=10, nb_en_cours=0, nb_nouveaux=0, nb_eleves=0,
            nb_plaintes_ouvertes=0, nb_nc_ouvertes=0,
        )], None, None)
        assert "Aucune situation appelant une action corrective" in texte

    def test_chaque_recommandation_porte_son_motif(self):
        """Une recommandation sans justification se lit comme une exigence
        arbitraire, et le destinataire ne peut pas en apprecier l'urgence."""
        texte = redaction.conclusion([chantier(nb_nc_ouvertes=2)], None, None)
        assert "Régulariser" in texte
        assert "opposable au projet" in texte

    def test_les_recommandations_sont_numerotees(self):
        texte = redaction.conclusion([chantier(
            nb_nc_ouvertes=2, nb_eleves=3, nb_plaintes_ouvertes=2,
        )], None, None)
        assert "<b>1.</b>" in texte
        assert "<b>3.</b>" in texte

    def test_le_rapport_rappelle_ses_propres_limites(self):
        """Le systeme constate des enregistrements, il ne juge pas de la
        realite environnementale d'un chantier."""
        texte = redaction.conclusion([chantier()], None, None)
        assert "visites de terrain" in texte


class TestVariabilite:
    """La propriete centrale : le texte suit les donnees."""

    def test_deux_situations_produisent_deux_rapports_differents(self):
        degrade = chantier(
            nb_signalements=20, nb_traites=3, nb_en_cours=9, nb_nouveaux=8,
            nb_eleves=5, nb_plaintes_ouvertes=4, nb_nc_ouvertes=3,
        )
        assaini = chantier(
            nb_signalements=20, nb_traites=20, nb_en_cours=0, nb_nouveaux=0,
            nb_eleves=0, nb_plaintes_ouvertes=0, nb_nc_ouvertes=0,
        )
        assert redaction.synthese([degrade], None, None) != \
               redaction.synthese([assaini], None, None)
        assert redaction.conclusion([degrade], None, None) != \
               redaction.conclusion([assaini], None, None)

    def test_le_perimetre_est_decrit_selon_son_etendue(self):
        seul = redaction.introduction([chantier()], None, None, "ANDE")
        plusieurs = redaction.introduction(
            [chantier(), chantier(id=2, nom="Bd Latrille", commune="Cocody")],
            None, None, "ANDE",
        )
        assert "le chantier de Rocade Y4" in seul
        assert "2 chantiers" in plusieurs
        assert "Cocody" in plusieurs

    def test_le_destinataire_est_nomme_en_toutes_lettres(self):
        ande = redaction.introduction([chantier()], None, None, "ANDE")
        bad = redaction.introduction([chantier()], None, None, "BAD")
        assert "Agence Nationale de l'Environnement" in ande
        assert "Banque Africaine de Développement" in bad
