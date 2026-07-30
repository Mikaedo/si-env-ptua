import 'package:flutter_test/flutter_test.dart';
import 'package:si_env/models/models.dart';

void main() {
  group('Utilisateur', () {
    test('fromJson should parse correctly', () {
      final json = {
        'id': 1,
        'nom': 'Test User',
        'email': 'test@test.com',
        'role': 'ADMIN',
        'premiere_connexion': false,
        'telephone': '+22507000000',
        'cree_le': '2026-07-22T10:00:00',
      };
      final u = Utilisateur.fromJson(json);
      expect(u.id, 1);
      expect(u.nom, 'Test User');
      expect(u.email, 'test@test.com');
      expect(u.role, 'ADMIN');
      expect(u.premiereConnexion, false);
      expect(u.telephone, '+22507000000');
    });
  });

  group('Signalement', () {
    test('fromJson should parse correctly', () {
      final json = {
        'id': 10,
        'uuid_mobile': 'uuid-123',
        'type_nuisance': 'Dechets de chantier',
        'description': 'Accumulation de dechets',
        'criticite': 'ELEVE',
        'criticite_ia': 'MODERE',
        'confiance_ia': 87.5,
        'gps_source': 'AUTO',
        'statut': 'NOUVEAU',
        'cree_le': '2026-07-22T10:00:00',
        'auteur_id': 1,
        'chantier_id': 2,
      };
      final s = Signalement.fromJson(json);
      expect(s.id, 10);
      expect(s.uuidMobile, 'uuid-123');
      expect(s.typeNuisance, 'Dechets de chantier');
      expect(s.criticite, 'ELEVE');
      expect(s.criticiteIa, 'MODERE');
      expect(s.confianceIa, 87.5);
      expect(s.gpsSource, 'AUTO');
      expect(s.statut, 'NOUVEAU');
    });

    test('toJson should serialize correctly', () {
      final s = Signalement(
        uuidMobile: 'uuid-456',
        typeNuisance: 'Bruit',
        criticite: 'FAIBLE',
        gpsSource: 'MANUEL',
        latitude: 5.36,
        longitude: -4.01,
        chantierId: 3,
      );
      final json = s.toJson();
      expect(json['uuid_mobile'], 'uuid-456');
      expect(json['type_nuisance'], 'Bruit');
      expect(json['criticite'], 'FAIBLE');
      expect(json['gps_source'], 'MANUEL');
      expect(json['latitude'], 5.36);
      expect(json['longitude'], -4.01);
      expect(json['chantier_id'], 3);
    });

    test('toLocalDb should include sync_status', () {
      final s = Signalement(
        uuidMobile: 'uuid-789',
        typeNuisance: 'Poussieres',
        criticite: 'MODERE',
      );
      final db = s.toLocalDb();
      expect(db['uuid_mobile'], 'uuid-789');
      expect(db['type_nuisance'], 'Poussieres');
      expect(db['sync_status'], 'PENDING_SYNC');
    });
  });

  group('Alerte', () {
    test('fromJson should parse correctly', () {
      final json = {
        'id': 1,
        'message': 'Seuil depasse',
        'niveau': 'CRITIQUE',
        'valeur': 72.5,
        'cree_le': '2026-07-22T10:00:00',
        'chantier_id': 2,
        'recue': false,
      };
      final a = Alerte.fromJson(json);
      expect(a.id, 1);
      expect(a.message, 'Seuil depasse');
      expect(a.niveau, 'CRITIQUE');
      expect(a.valeur, 72.5);
      expect(a.recue, false);
    });
  });

  group('Statistiques', () {
    test('fromJson should parse correctly', () {
      final json = {
        'total': 50,
        'traites': 30,
        'en_attente': 15,
        'urgents': 5,
        'taux_traitement': 60.0,
        'repartition': {'Dechets': 20, 'Bruit': 10},
        'evolution': {'2026-05': 15, '2026-06': 20, '2026-07': 15},
      };
      final s = Statistiques.fromJson(json);
      expect(s.total, 50);
      expect(s.traites, 30);
      expect(s.enAttente, 15);
      expect(s.urgents, 5);
      expect(s.tauxTraitement, 60.0);
      expect(s.repartition['Dechets'], 20);
      expect(s.evolution['2026-07'], 15);
    });
  });

  group('Chantier', () {
    test('fromJson should parse correctly', () {
      final json = {'id': 1, 'nom': '4eme Pont', 'commune': 'Yopougon'};
      final c = Chantier.fromJson(json);
      expect(c.id, 1);
      expect(c.nom, '4eme Pont');
      expect(c.commune, 'Yopougon');
    });
  });
}
