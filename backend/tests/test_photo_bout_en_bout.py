# -*- coding: utf-8 -*-
"""Le circuit de la photo, du telephone de l'agent a l'ecran du specialiste.

Une photo prise sur le terrain doit se retrouver dans le dossier consulte
depuis le tableau de bord : c'est la preuve visuelle sur laquelle repose
l'appreciation de la criticite.
"""
import uuid

# Un PNG minimal, mais valide : le stockage doit accepter un vrai fichier.
PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d494844520000000100000001080600000"
    "01f15c4890000000d49444154789c6360000002000100ffff03000006"
    "0005574bd6b40000000049454e44ae426082")


def _signalement_avec_photo(client, headers, chantier, image=PNG):
    reponse = client.post("/signalements", json={
        "uuid_mobile": str(uuid.uuid4()),
        "type_nuisance": "Eaux stagnantes",
        "description": "Stagnation apres pluie",
        "criticite": "MODERE",
        "chantier_id": chantier.id,
        "latitude": 5.341, "longitude": -4.103,
    }, headers=headers)
    assert reponse.status_code in (200, 201), reponse.text
    identifiant = reponse.json()["id"]
    depot = client.post(f"/signalements/{identifiant}/photos",
                        files={"file": ("terrain.png", image, "image/png")},
                        headers=headers)
    return identifiant, depot


class TestCircuitPhoto:

    def test_photo_deposee_est_enregistree(self, client, agent_headers, chantier):
        _, depot = _signalement_avec_photo(client, agent_headers, chantier)
        assert depot.status_code == 200, depot.text
        assert depot.json()["chemin"], "aucun chemin retourne pour la photo"

    def test_photo_visible_dans_le_dossier(self, client, agent_headers, chantier):
        """Le detail consulte depuis le tableau de bord porte la photo."""
        identifiant, _ = _signalement_avec_photo(client, agent_headers, chantier)
        detail = client.get(f"/signalements/{identifiant}", headers=agent_headers)
        assert detail.status_code == 200
        photos = detail.json().get("photos", [])
        assert len(photos) == 1, f"photos attendues : 1, obtenues : {len(photos)}"
        assert photos[0]["chemin"]

    def test_photo_listee_par_son_endpoint(self, client, agent_headers, chantier):
        identifiant, _ = _signalement_avec_photo(client, agent_headers, chantier)
        liste = client.get(f"/signalements/{identifiant}/photos", headers=agent_headers)
        assert liste.status_code == 200
        assert len(liste.json()) == 1

    def test_plusieurs_photos_sur_un_meme_signalement(self, client, agent_headers, chantier):
        identifiant, _ = _signalement_avec_photo(client, agent_headers, chantier)
        for _ in range(2):
            client.post(f"/signalements/{identifiant}/photos",
                        files={"file": ("autre.png", PNG, "image/png")},
                        headers=agent_headers)
        detail = client.get(f"/signalements/{identifiant}", headers=agent_headers)
        assert len(detail.json()["photos"]) == 3
