class Utilisateur {
  final int id;
  final String nom;
  final String email;
  final String role;
  final bool premiereConnexion;
  final String? telephone;
  final DateTime creeLe;

  Utilisateur({
    required this.id,
    required this.nom,
    required this.email,
    required this.role,
    required this.premiereConnexion,
    this.telephone,
    required this.creeLe,
  });

  factory Utilisateur.fromJson(Map<String, dynamic> json) {
    return Utilisateur(
      id: json['id'],
      nom: json['nom'],
      email: json['email'],
      role: json['role'],
      premiereConnexion: json['premiere_connexion'] ?? false,
      telephone: json['telephone'],
      creeLe: DateTime.parse(json['cree_le']),
    );
  }
}

class Chantier {
  final int id;
  final String nom;
  final String? commune;

  Chantier({required this.id, required this.nom, this.commune});

  factory Chantier.fromJson(Map<String, dynamic> json) {
    return Chantier(
      id: json['id'],
      nom: json['nom'],
      commune: json['commune'],
    );
  }
}

class Signalement {
  final int? id;
  final String uuidMobile;
  final String typeNuisance;
  final String? description;
  final String criticite;
  final String? criticiteIa;
  final double? confianceIa;
  final String gpsSource;
  final String statut;
  final DateTime? creeLe;
  final int? auteurId;
  final int? chantierId;
  // Nom envoye directement par le serveur (route GET /signalements, objet
  // "chantier" imbriqué). Prioritaire sur toute resolution locale par
  // kChantiers, qui ne doit plus servir que de repli si absent.
  final String? chantierNom;
  final double? latitude;
  final double? longitude;

  /// Le constat a-t-il deja rejoint le serveur ?
  ///
  /// L'agent voyait ses constats sans savoir lesquels etaient partis :
  /// la liste les melangeait, et rien ne distinguait un constat transmis
  /// d'un constat encore en attente dans le telephone. Il ne pouvait
  /// donc pas savoir ce qui lui restait a remonter en quittant la zone.
  ///
  /// Vaut vrai pour tout ce qui vient du serveur, par construction.
  final bool transmis;

  /// L'heure a laquelle l'agent a saisi le constat sur le terrain.
  ///
  /// A distinguer de [creeLe], qui porte l'heure de reception par le
  /// serveur. Hors ligne, les deux sont separees de plusieurs heures.
  final DateTime? saisiLe;

  Signalement({
    this.id,
    required this.uuidMobile,
    required this.typeNuisance,
    this.description,
    required this.criticite,
    this.criticiteIa,
    this.confianceIa,
    this.gpsSource = 'AUTO',
    this.statut = 'NOUVEAU',
    this.creeLe,
    this.auteurId,
    this.chantierId,
    this.chantierNom,
    this.latitude,
    this.longitude,
    this.transmis = true,
    this.saisiLe,
  });

  /// Reconstruit un constat depuis la base locale du telephone.
  ///
  /// C'est la seule source qui contient aussi ce qui n'est pas encore
  /// parti : le cache du serveur, par definition, ne peut pas le
  /// connaitre.
  factory Signalement.depuisBaseLocale(Map<String, dynamic> ligne) {
    DateTime? lire(String champ) {
      final v = ligne[champ];
      return v is String ? DateTime.tryParse(v) : null;
    }

    final saisi = lire('created_at');
    return Signalement(
      id: ligne['serveur_id'] as int?,
      uuidMobile: ligne['uuid_mobile'] as String,
      typeNuisance: ligne['type_nuisance'] as String,
      description: ligne['description'] as String?,
      criticite: (ligne['criticite'] as String?) ?? 'FAIBLE',
      criticiteIa: ligne['criticite_ia'] as String?,
      confianceIa: (ligne['confiance_ia'] as num?)?.toDouble(),
      gpsSource: (ligne['gps_source'] as String?) ?? 'AUTO',
      statut: (ligne['statut'] as String?) ?? 'NOUVEAU',
      creeLe: saisi,
      saisiLe: saisi,
      chantierId: ligne['chantier_id'] as int?,
      latitude: (ligne['latitude'] as num?)?.toDouble(),
      longitude: (ligne['longitude'] as num?)?.toDouble(),
      transmis: ligne['sync_status'] == 'SYNCED',
    );
  }

  factory Signalement.fromJson(Map<String, dynamic> json) {
    final chantier = json['chantier'] as Map<String, dynamic>?;
    return Signalement(
      id: json['id'],
      uuidMobile: json['uuid_mobile'],
      typeNuisance: json['type_nuisance'],
      description: json['description'],
      criticite: json['criticite'] ?? 'FAIBLE',
      criticiteIa: json['criticite_ia'],
      confianceIa: json['confiance_ia']?.toDouble(),
      gpsSource: json['gps_source'] ?? 'AUTO',
      statut: json['statut'] ?? 'NOUVEAU',
      creeLe: json['cree_le'] != null ? DateTime.parse(json['cree_le']) : null,
      // Le serveur conserve l'heure de saisie terrain a cote de l'heure
      // de reception. Les constats anterieurs a cette distinction n'en
      // portent pas : on retombe alors sur l'heure de reception.
      saisiLe: json['saisi_le'] != null
          ? DateTime.tryParse(json['saisi_le'])
          : (json['cree_le'] != null
              ? DateTime.tryParse(json['cree_le'])
              : null),
      auteurId: json['auteur_id'],
      chantierId: json['chantier_id'] ?? chantier?['id'],
      chantierNom: chantier?['nom'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'uuid_mobile': uuidMobile,
      'type_nuisance': typeNuisance,
      'description': description,
      'criticite': criticite,
      'criticite_ia': criticiteIa,
      'confiance_ia': confianceIa,
      'gps_source': gpsSource,
      'latitude': latitude,
      'longitude': longitude,
      'chantier_id': chantierId,
      // L'heure de la saisie sur le terrain.
      //
      // Sans elle, le serveur horodatait a la reception : un constat
      // saisi a 7h hors couverture et transmis a 18h s'affichait a 18h,
      // donc apres un constat saisi a 8h avec reseau. L'ordre des faits
      // etait inverse sur le tableau de bord.
      'saisi_le': (saisiLe ?? creeLe)?.toUtc().toIso8601String(),
    };
  }

  Map<String, dynamic> toLocalDb() {
    return {
      'uuid_mobile': uuidMobile,
      'type_nuisance': typeNuisance,
      'description': description,
      'criticite': criticite,
      'criticite_ia': criticiteIa,
      'confiance_ia': confianceIa,
      'gps_source': gpsSource,
      'statut': statut,
      'latitude': latitude,
      'longitude': longitude,
      'chantier_id': chantierId,
      'sync_status': 'PENDING_SYNC',
    };
  }
}

class Alerte {
  final int id;
  final String message;
  final String niveau;
  final double? valeur;
  final DateTime creeLe;
  final int? chantierId;
  final bool recue;

  Alerte({
    required this.id,
    required this.message,
    required this.niveau,
    this.valeur,
    required this.creeLe,
    this.chantierId,
    this.recue = false,
  });

  factory Alerte.fromJson(Map<String, dynamic> json) {
    return Alerte(
      id: json['id'],
      message: json['message'],
      niveau: json['niveau'],
      valeur: json['valeur']?.toDouble(),
      creeLe: DateTime.parse(json['cree_le']),
      chantierId: json['chantier_id'],
      recue: json['recue'] ?? false,
    );
  }
}

class Statistiques {
  final int total;
  final int traites;
  final int enAttente;
  final int urgents;
  final double tauxTraitement;
  final Map<String, int> repartition;
  final Map<String, int> evolution;

  Statistiques({
    required this.total,
    required this.traites,
    required this.enAttente,
    required this.urgents,
    required this.tauxTraitement,
    required this.repartition,
    required this.evolution,
  });

  factory Statistiques.fromJson(Map<String, dynamic> json) {
    return Statistiques(
      total: json['total'],
      traites: json['traites'],
      enAttente: json['en_attente'],
      urgents: json['urgents'],
      tauxTraitement: json['taux_traitement']?.toDouble() ?? 0,
      repartition: Map<String, int>.from(json['repartition']),
      evolution: Map<String, int>.from(json['evolution']),
    );
  }
}
