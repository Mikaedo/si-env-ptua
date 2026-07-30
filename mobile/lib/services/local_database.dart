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

  Future<Database> _initDb() async {
    final path = join(await getDatabasesPath(), 'sienv.db');
    return await openDatabase(
      path,
      version: 1,
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
            created_at TEXT
          )
        ''');
      },
    );
  }

  Future<int> insertSignalement(Signalement s) async {
    final db = await database;
    return await db.insert('signalements_local', {
      ...s.toLocalDb(),
      'created_at': DateTime.now().toIso8601String(),
    });
  }

  Future<List<Map<String, dynamic>>> getPendingSignalements() async {
    final db = await database;
    return await db.query('signalements_local', where: "sync_status = 'PENDING_SYNC'");
  }

  Future<void> markSynced(String uuidMobile) async {
    final db = await database;
    await db.update(
      'signalements_local',
      {'sync_status': 'SYNCED'},
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
}
