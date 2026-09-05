import 'package:path/path.dart';
import 'package:sqflite/sqflite.dart';
import '../models/models.dart';

class LocalDatabase {
  static final LocalDatabase _instance = LocalDatabase._internal();
  factory LocalDatabase() => _instance;
  LocalDatabase._internal();

  Database? _db;

  Future<Database> get database async {
    if (_db != null) return _db!;
    _db = await _initDb();
    return _db!;
  }

  /// Version 2 : ajout de `photo_path`.
  ///
  /// La photographie ne pouvait pas suivre un signalement saisi hors
  /// ligne. Elle etait envoyee des la creation, mais l'envoi exige
  /// l'identifiant que le serveur attribue : sans reseau, il n'existe
  /// pas, et la photographie etait perdue sans que personne le sache.
  ///
  /// Le chemin du fichier est donc conserve ici, et la synchronisation
  /// envoie la photographie apres avoir recu l'identifiant.
  static const int _version = 2;

  Future<Database> _initDb() async {
    final path = join(await getDatabasesPath(), 'sienv.db');
    return await openDatabase(
      path,
      version: _version,
      onCreate: (db, v) async {
        await db.execute('''
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
            photo_path TEXT,
            serveur_id INTEGER,
            created_at TEXT
          )
        ''');
      },
      onUpgrade: (db, ancienne, nouvelle) async {
        // Les telephones qui portent deja des signalements en attente
        // doivent les garder : on ajoute les colonnes, on ne recree pas
        // la table. Elles restent nulles pour les signalements
        // existants, ce que la synchronisation interprete comme « pas de
        // photo a envoyer ».
        if (ancienne < 2) {
          await db.execute(
            'ALTER TABLE signalements_local ADD COLUMN photo_path TEXT',
          );
          await db.execute(
            'ALTER TABLE signalements_local ADD COLUMN serveur_id INTEGER',
          );
        }
      },
    );
  }

  /// Enregistre un signalement dans la file d'attente locale.
  ///
  /// [cheminPhoto] est le fichier pris par l'agent, s'il y en a un. Il
  /// reste local : il n'appartient pas au modele qui monte au serveur,
  /// mais la synchronisation en a besoin pour envoyer la photographie
  /// une fois l'identifiant obtenu.
  Future<int> insertSignalement(Signalement s, {String? cheminPhoto}) async {
    final db = await database;
    return await db.insert('signalements_local', {
      ...s.toLocalDb(),
      'photo_path': cheminPhoto,
      'created_at': DateTime.now().toIso8601String(),
    });
  }

  /// Oublie la photographie d'un signalement, une fois transmise ou
  /// definitivement introuvable. Le signalement, lui, reste.
  Future<void> oublierPhoto(String uuidMobile) async {
    final db = await database;
    await db.update(
      'signalements_local',
      {'photo_path': null},
      where: 'uuid_mobile = ?',
      whereArgs: [uuidMobile],
    );
  }

  Future<List<Map<String, dynamic>>> getPendingSignalements() async {
    final db = await database;
    return await db.query('signalements_local', where: "sync_status = 'PENDING_SYNC'");
  }

  /// Les signalements transmis dont la photographie reste a envoyer.
  ///
  /// Une photographie peut echouer alors que son signalement est bien
  /// parti : reseau instable au moment de l'envoi du fichier, qui est
  /// plus lourd. Sans cette seconde file, elle ne serait jamais reprise,
  /// puisque le signalement ne figure plus parmi ceux en attente.
  ///
  /// `serveur_id` est conserve a la transmission, faute de quoi la
  /// reprise ne saurait pas a quel signalement rattacher le fichier.
  Future<List<Map<String, dynamic>>> photosEnAttente() async {
    final db = await database;
    return await db.query(
      'signalements_local',
      columns: ['uuid_mobile', 'photo_path', 'serveur_id'],
      where: "sync_status = 'SYNCED' AND photo_path IS NOT NULL "
          "AND serveur_id IS NOT NULL",
    );
  }

  /// Marque un signalement transmis, en retenant l'identifiant que le
  /// serveur lui a attribue.
  ///
  /// Cet identifiant sert a rattacher la photographie si son envoi doit
  /// etre repris plus tard : sans lui, la reprise ne saurait pas a quel
  /// signalement l'attacher.
  Future<void> markSynced(String uuidMobile, {int? serveurId}) async {
    final db = await database;
    final valeurs = <String, Object?>{'sync_status': 'SYNCED'};
    if (serveurId != null) valeurs['serveur_id'] = serveurId;
    await db.update(
      'signalements_local',
      valeurs,
      where: 'uuid_mobile = ?',
      whereArgs: [uuidMobile],
    );
  }

  Future<List<Map<String, dynamic>>> getAllLocal() async {
    final db = await database;
    return await db.query('signalements_local', orderBy: 'created_at DESC');
  }

  Future<int> pendingCount() async {
    final db = await database;
    final result = await db.rawQuery("SELECT COUNT(*) as c FROM signalements_local WHERE sync_status = 'PENDING_SYNC'");
    return result.first['c'] as int;
  }

  /// Combien de photographies restent a envoyer.
  ///
  /// La veille s'en sert pour decider s'il y a lieu de sonder le
  /// reseau. Compter plutot que rapatrier les lignes : cette question
  /// est posee toutes les minutes, sur la batterie de l'agent.
  Future<int> nombrePhotosEnAttente() async {
    final db = await database;
    final resultat = await db.rawQuery(
      "SELECT COUNT(*) AS c FROM signalements_local "
      "WHERE sync_status = 'SYNCED' AND photo_path IS NOT NULL "
      "AND serveur_id IS NOT NULL",
    );
    return resultat.first['c'] as int;
  }
}
