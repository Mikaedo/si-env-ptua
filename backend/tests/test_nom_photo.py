"""Le nom de fichier envoye par le client ne doit pas designer un chemin.

Le nom arrivait jusqu'a os.path.join sans filtrage : le prefixe temporel
ne protegeait pas, puisque « ../ » remonte depuis lui. Un appelant
authentifie pouvait donc faire ecrire le serveur hors du dossier des
photographies.
"""

import os

import pytest

from app.services import photo_storage


class TestAssainissementDuNom:
    def test_une_remontee_de_dossier_ne_survit_pas(self):
        nom = photo_storage.nom_unique(1, "../../../etc/passwd")
        assert ".." not in nom
        assert "/" not in nom
        assert "\\" not in nom

    def test_un_chemin_absolu_est_reduit_a_son_dernier_segment(self):
        nom = photo_storage.nom_unique(1, "/var/www/html/porte.jpg")
        assert nom.endswith("porte.jpg")
        assert "/" not in nom

    def test_un_chemin_windows_est_traite_aussi(self):
        nom = photo_storage.nom_unique(1, r"C:\Windows\System32\note.png")
        assert nom.endswith("note.png")
        assert "\\" not in nom

    def test_une_extension_executable_devient_une_photo(self):
        # Le serveur ecrit des photographies : il n'a pas a poser sur son
        # disque un nom d'extension choisi par l'appelant.
        nom = photo_storage.nom_unique(1, "charge.php")
        assert nom.endswith(".jpg")
        assert ".php" not in nom

    def test_la_double_extension_ne_passe_pas(self):
        nom = photo_storage.nom_unique(1, "photo.jpg.php")
        assert nom.endswith(".jpg")
        assert ".php" not in nom

    def test_un_nom_ordinaire_reste_lisible(self):
        # L'assainissement ne doit pas rendre les noms illisibles pour
        # qui consulte le dossier des photographies.
        nom = photo_storage.nom_unique(42, "chantier-nord_02.jpg")
        assert nom.startswith("sig_42_")
        assert nom.endswith("chantier-nord_02.jpg")

    def test_un_nom_vide_reste_nommable(self):
        nom = photo_storage.nom_unique(1, "")
        assert nom.endswith("photo.jpg")

    @pytest.mark.parametrize("extension", [".jpg", ".jpeg", ".png", ".webp"])
    def test_les_extensions_de_photo_sont_conservees(self, extension):
        nom = photo_storage.nom_unique(1, f"vue{extension}")
        assert nom.endswith(extension)


class TestVerrouAEcriture:
    def test_l_ecriture_hors_du_dossier_est_refusee(self, tmp_path):
        """Second verrou, independant de nom_unique.

        Il protege meme si un autre appelant construisait le nom
        lui-meme sans passer par l'assainissement.
        """
        stockage = photo_storage._StockageLocal(str(tmp_path / "photos"))
        with pytest.raises(ValueError):
            stockage.enregistrer(os.path.join("..", "evade.txt"), b"x")

    def test_un_nom_normal_s_ecrit_bien(self, tmp_path):
        dossier = tmp_path / "photos"
        stockage = photo_storage._StockageLocal(str(dossier))
        rendu = stockage.enregistrer("sig_1_photo.jpg", b"contenu")
        assert rendu == "sig_1_photo.jpg"
        assert (dossier / "sig_1_photo.jpg").read_bytes() == b"contenu"
