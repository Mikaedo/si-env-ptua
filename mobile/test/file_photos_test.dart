import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

/// La file d'attente des photographies, et la migration qui la porte.
///
/// La photographie ne pouvait pas suivre un signalement saisi hors
/// ligne : elle etait envoyee des la creation, alors que l'envoi exige
/// l'identifiant attribue par le serveur. Sans reseau, cet identifiant
/// n'existait pas, et la photographie disparaissait sans que personne le
/// sache.
///
/// Ces tests portent sur ce qui pouvait mal tourner : la migration d'un
/// telephone deja en service, qui ne doit rien perdre, et la selection
/// des photographies restant a envoyer.
///
/// `LocalDatabase` etant un singleton qui s'ouvre sur le chemin du
/// telephone, les tests rejouent ici son schema et ses requetes sur une
/// base en memoire. Le schema est donc duplique : les tests de migration
/// ci-dessous echoueront si l'un des deux change sans l'autre, ce qui
/// est le comportement voulu.
void main() {
  sqfliteFfiInit();
  final fabrique = databaseFactoryFfi;

  // Le schema d'avant la migration : ni photo_path, ni serveur_id.
  const schemaV1 = '''
    CREATE TABLE signalements_local (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      uuid_mobile TEXT UNIQUE,
      type_nuisance TEXT NOT NULL,
      description TEXT,
      criticite TEXT NOT NULL,
      criticite_ia TEXT,
      confiance_ia REAL,
      gps_source TEXT DEFAULT 'AUTO',
      statut TEXT DEFAULT 'NOUVEAU',
      latitude REAL,
      longitude REAL,
      chantier_id INTEGER,
      sync_status TEXT DEFAULT 'PENDING_SYNC',
      created_at TEXT
    )
  ''';

  /// Les deux colonnes ajoutees par la version 2, telles que
  /// `LocalDatabase.onUpgrade` les ajoute.
  Future<void> migrerVers2(Database db) async {
    await db.execute(
      'ALTER TABLE signalements_local ADD COLUMN photo_path TEXT',
    );
    await db.execute(
      'ALTER TABLE signalements_local ADD COLUMN serveur_id INTEGER',
    );
  }

  Future<Database> baseV1() async {
    return fabrique.openDatabase(
      inMemoryDatabasePath,
      options: OpenDatabaseOptions(
        version: 1,
        onCreate: (db, v) => db.execute(schemaV1),
      ),
    );
  }

  group('Migration d\'un telephone deja en service', () {
    test('les signalements en attente survivent a la migration', () async {
      // Le cas qui compte : un agent a des constats non transmis sur son
      // telephone quand la mise a jour arrive. Les perdre serait pire
      // que le defaut qu'on corrige.
      final db = await baseV1();
      await db.insert('signalements_local', {
        'uuid_mobile': 'constat-du-terrain',
        'type_nuisance': 'Déchets de chantier',
        'criticite': 'ELEVE',
        'latitude': 5.3547,
        'longitude': -3.8853,
        'sync_status': 'PENDING_SYNC',
        'created_at': '2026-09-01T08:00:00',
      });

      await migrerVers2(db);

      final lignes = await db.query('signalements_local');
      expect(lignes, hasLength(1));
      expect(lignes.first['uuid_mobile'], 'constat-du-terrain');
      expect(lignes.first['criticite'], 'ELEVE');
      expect(lignes.first['latitude'], closeTo(5.3547, 0.00001));
      // Les nouvelles colonnes existent, et sont vides : un signalement
      // d'avant la migration n'avait pas de photographie enregistree.
      expect(lignes.first['photo_path'], isNull);
      expect(lignes.first['serveur_id'], isNull);

      await db.close();
    });

    test('les colonnes ajoutees acceptent des valeurs', () async {
      final db = await baseV1();
      await migrerVers2(db);

      await db.insert('signalements_local', {
        'uuid_mobile': 'avec-photo',
        'type_nuisance': 'Eaux stagnantes',
        'criticite': 'MODERE',
        'sync_status': 'PENDING_SYNC',
        'photo_path': '/cache/photo_1.jpg',
        'created_at': '2026-09-05T09:00:00',
      });

      final ligne = (await db.query('signalements_local')).first;
      expect(ligne['photo_path'], '/cache/photo_1.jpg');

      await db.close();
    });
  });

  group('Les photographies restant a envoyer', () {
    /// La requete de `LocalDatabase.photosEnAttente`.
    Future<List<Map<String, Object?>>> photosEnAttente(Database db) {
      return db.query(
        'signalements_local',
        columns: ['uuid_mobile', 'photo_path', 'serveur_id'],
        where: "sync_status = 'SYNCED' AND photo_path IS NOT NULL "
            "AND serveur_id IS NOT NULL",
      );
    }

    Future<Database> baseV2() async {
      final db = await baseV1();
      await migrerVers2(db);
      return db;
    }

    Future<void> ajouter(
      Database db, {
      required String uuid,
      required String syncStatus,
      String? photoPath,
      int? serveurId,
    }) async {
      await db.insert('signalements_local', {
        'uuid_mobile': uuid,
        'type_nuisance': 'Déchets de chantier',
        'criticite': 'FAIBLE',
        'sync_status': syncStatus,
        'photo_path': photoPath,
        'serveur_id': serveurId,
        'created_at': '2026-09-05T10:00:00',
      });
    }

    test('un signalement transmis dont la photographie reste', () async {
      // Le cas que la reprise doit rattraper : la saisie est passee, le
      // fichier a echoue. Sans cette file, il ne serait jamais repris,
      // le signalement ne figurant plus parmi ceux en attente.
      final db = await baseV2();
      await ajouter(db,
          uuid: 'photo-a-reprendre',
          syncStatus: 'SYNCED',
          photoPath: '/cache/photo_1.jpg',
          serveurId: 42);

      final restantes = await photosEnAttente(db);
      expect(restantes, hasLength(1));
      expect(restantes.first['uuid_mobile'], 'photo-a-reprendre');
      expect(restantes.first['serveur_id'], 42);

      await db.close();
    });

    test('un signalement encore en attente est ignore', () async {
      // Sa photographie partira avec lui : la prendre ici l'enverrait
      // avant que le signalement existe cote serveur.
      final db = await baseV2();
      await ajouter(db,
          uuid: 'pas-encore-parti',
          syncStatus: 'PENDING_SYNC',
          photoPath: '/cache/photo_2.jpg');

      expect(await photosEnAttente(db), isEmpty);
      await db.close();
    });

    test('un signalement transmis sans photographie est ignore', () async {
      final db = await baseV2();
      await ajouter(db,
          uuid: 'sans-photo', syncStatus: 'SYNCED', serveurId: 7);

      expect(await photosEnAttente(db), isEmpty);
      await db.close();
    });

    test('une photographie sans identifiant serveur est ignoree', () async {
      // Sans identifiant, on ne saurait pas a quel signalement rattacher
      // le fichier : la reprise serait vouee a echouer.
      final db = await baseV2();
      await ajouter(db,
          uuid: 'sans-identifiant',
          syncStatus: 'SYNCED',
          photoPath: '/cache/photo_3.jpg');

      expect(await photosEnAttente(db), isEmpty);
      await db.close();
    });

    test('oublier la photographie la retire de la file', () async {
      // Ce qu'appelle la synchronisation apres un envoi reussi, ou quand
      // le fichier a disparu du cache. Le signalement, lui, reste.
      final db = await baseV2();
      await ajouter(db,
          uuid: 'transmise',
          syncStatus: 'SYNCED',
          photoPath: '/cache/photo_4.jpg',
          serveurId: 11);

      await db.update(
        'signalements_local',
        {'photo_path': null},
        where: 'uuid_mobile = ?',
        whereArgs: ['transmise'],
      );

      expect(await photosEnAttente(db), isEmpty);
      // Le signalement n'a pas ete supprime, seule sa photographie est
      // oubliee.
      expect(await db.query('signalements_local'), hasLength(1));

      await db.close();
    });

    test('le comptage decide du reveil de la veille', () async {
      // La veille sonde le reseau seulement s'il y a quelque chose a
      // envoyer. Ce comptage doit donc voir une photographie restee
      // seule, sans quoi la veille sortirait et ne la reprendrait
      // jamais. Il doit compter les memes lignes que la file.
      Future<int> compter(Database db) async {
        final r = await db.rawQuery(
          "SELECT COUNT(*) AS c FROM signalements_local "
          "WHERE sync_status = 'SYNCED' AND photo_path IS NOT NULL "
          "AND serveur_id IS NOT NULL",
        );
        return r.first['c'] as int;
      }

      final db = await baseV2();
      expect(await compter(db), 0);

      await ajouter(db,
          uuid: 'seule',
          syncStatus: 'SYNCED',
          photoPath: '/cache/seule.jpg',
          serveurId: 5);
      expect(await compter(db), 1);
      // Le comptage et la file voient la meme chose.
      expect(await compter(db), (await photosEnAttente(db)).length);

      await db.close();
    });

    test('plusieurs photographies se reprennent ensemble', () async {
      final db = await baseV2();
      await ajouter(db,
          uuid: 'a',
          syncStatus: 'SYNCED',
          photoPath: '/cache/a.jpg',
          serveurId: 1);
      await ajouter(db,
          uuid: 'b',
          syncStatus: 'SYNCED',
          photoPath: '/cache/b.jpg',
          serveurId: 2);
      await ajouter(db, uuid: 'c', syncStatus: 'SYNCED', serveurId: 3);

      final restantes = await photosEnAttente(db);
      expect(restantes, hasLength(2));
      expect(
        restantes.map((r) => r['uuid_mobile']).toList(),
        containsAll(['a', 'b']),
      );

      await db.close();
    });
  });
}
