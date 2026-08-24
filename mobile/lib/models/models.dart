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
  });

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
