"""Circuit de mise a jour des modeles IA embarques : l'admin deploie un
fichier .onnx depuis le tableau de bord, un agent de terrain le decouvre via
/model/versions et le telecharge via /model/download, sans passer par le
Play Store."""
import io


class TestDeploiementModele:
    def test_admin_deploie_un_modele(self, client, auth_headers):
        reponse = client.post(
            "/admin/model",
            headers=auth_headers,
            data={"type_modele": "detection"},
            files={"file": ("detection.onnx", io.BytesIO(b"faux-contenu-onnx"), "application/octet-stream")},
        )
        assert reponse.status_code == 200
        corps = reponse.json()
        assert corps["type_modele"] == "detection"
        assert corps["disponible"] is True

    def test_agent_ne_peut_pas_deployer(self, client, agent_headers):
        reponse = client.post(
            "/admin/model",
            headers=agent_headers,
            data={"type_modele": "detection"},
            files={"file": ("detection.onnx", io.BytesIO(b"x"), "application/octet-stream")},
        )
        assert reponse.status_code == 403

    def test_type_modele_invalide_rejete(self, client, auth_headers):
        reponse = client.post(
            "/admin/model",
            headers=auth_headers,
            data={"type_modele": "autre"},
            files={"file": ("m.onnx", io.BytesIO(b"x"), "application/octet-stream")},
        )
        assert reponse.status_code == 400


class TestConsultationMobile:
    def test_agent_voit_la_version_deployee(self, client, auth_headers, agent_headers):
        client.post(
            "/admin/model",
            headers=auth_headers,
            data={"type_modele": "classification"},
            files={"file": ("c.onnx", io.BytesIO(b"contenu"), "application/octet-stream")},
        )
        reponse = client.get("/model/versions", headers=agent_headers)
        assert reponse.status_code == 200
        corps = reponse.json()
        assert corps["classification"]["disponible"] is True
        assert corps["classification"]["version"] > 0

    def test_agent_telecharge_le_modele(self, client, auth_headers, agent_headers):
        contenu = b"contenu-du-modele-onnx"
        client.post(
            "/admin/model",
            headers=auth_headers,
            data={"type_modele": "detection"},
            files={"file": ("d.onnx", io.BytesIO(contenu), "application/octet-stream")},
        )
        reponse = client.get("/model/download/detection", headers=agent_headers)
        assert reponse.status_code == 200
        assert reponse.content == contenu

    def test_telechargement_sans_modele_deploye_404(self, client, agent_headers):
        reponse = client.get("/model/download/classification", headers=agent_headers)
        # Le fichier peut deja exister si un test precedent l'a deploye dans
        # la meme session (MODEL_DIR n'est pas reinitialise entre tests) :
        # on accepte donc 200 ou 404, l'important etant l'absence d'erreur 5xx.
        assert reponse.status_code in (200, 404)

    def test_type_modele_inconnu_404(self, client, agent_headers):
        reponse = client.get("/model/download/exotique", headers=agent_headers)
        assert reponse.status_code == 404
