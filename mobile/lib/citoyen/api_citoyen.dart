import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../core/constants.dart';

/// Verdict rendu sur la position du riverain avant toute inscription.
///
/// La distance et le rayon accompagnent le verdict pour une raison précise :
/// un refus sec laisserait la personne sans moyen de comprendre pourquoi
/// l'application lui est fermée. Savoir qu'elle se trouve à trois kilomètres
/// du chantier le plus proche lui donne au moins une explication.
class ZoneVerifiee {
  final bool autorise;
  final int chantierId;
  final String chantierNom;
  final String? commune;
  final int distanceM;
  final int rayonM;

  ZoneVerifiee({
    required this.autorise,
    required this.chantierId,
    required this.chantierNom,
    required this.commune,
    required this.distanceM,
    required this.rayonM,
  });

  factory ZoneVerifiee.fromJson(Map<String, dynamic> json) => ZoneVerifiee(
        autorise: json['autorise'] ?? false,
        chantierId: json['chantier_id'] ?? 0,
        chantierNom: json['chantier_nom'] ?? '',
        commune: json['commune'],
        distanceM: json['distance_m'] ?? 0,
        rayonM: json['rayon_m'] ?? 0,
      );

  /// Distance exprimée dans l'unité la plus parlante pour un habitant.
  String get distanceLisible => distanceM >= 1000
      ? '${(distanceM / 1000).toStringAsFixed(1)} km'
      : '$distanceM m';
}

/// Doléance déposée par un riverain.
class Doleance {
  final int id;
  final String description;
  final String? categorie;
  final String statut;
  final DateTime? creeLe;

  Doleance({
    required this.id,
    required this.description,
    required this.categorie,
    required this.statut,
    required this.creeLe,
  });

  factory Doleance.fromJson(Map<String, dynamic> json) => Doleance(
        id: json['id'],
        description: json['description'] ?? '',
        categorie: json['categorie'],
        statut: json['statut'] ?? 'OUVERTE',
        creeLe: json['cree_le'] != null ? DateTime.tryParse(json['cree_le']) : null,
      );

  /// Statut traduit en langage courant.
  ///
  /// Le vocabulaire interne du système ne dit rien à un habitant : personne
  /// ne sait ce qu'est une doléance « OUVERTE ». On lui répond dans les
  /// termes qu'il attend, ceux d'un suivi de dossier.
  String get statutLisible => switch (statut) {
        'OUVERTE' => 'Reçue',
        'EN_COURS' => 'En cours d\'examen',
        'RESOLU' => 'Traitée',
        'REJETE' => 'Classée sans suite',
        _ => 'Reçue',
      };
}

/// Catégories proposées au dépôt.
///
/// Le vocabulaire est celui d'un habitant, non celui d'un technicien :
/// personne ne se plaint spontanément d'un dépassement de seuil de particules,
/// on se plaint de poussière.
const Map<String, String> kCategoriesDoleance = {
  'bruit': 'Bruit',
  'poussiere': 'Poussière',
  'circulation': 'Circulation',
  'eau': 'Eau stagnante',
  'dechets': 'Déchets',
  'autre': 'Autre',
};

/// Accès à l'API pour l'application citoyenne.
///
/// Volontairement distinct du service des agents : les deux applications
/// n'appellent pas les mêmes routes, et mêler les deux surfaces exposerait à
/// chacune des opérations qui ne la concernent pas.
class ApiCitoyen {
  static final ApiCitoyen _instance = ApiCitoyen._interne();
  factory ApiCitoyen() => _instance;
  ApiCitoyen._interne();

  static const _cleJeton = 'citoyen_token';
  static const _cleNom = 'citoyen_nom';
  static const _cleEmail = 'citoyen_email';
  static const _cleChantier = 'citoyen_chantier';

  String? _jeton;
  String? nom;
  String? email;
  String? chantierRattachement;

  String? get jeton => _jeton;
  bool get connecte => _jeton != null;

  Map<String, String> get _entetes => {
        'Content-Type': 'application/json',
        if (_jeton != null) 'Authorization': 'Bearer $_jeton',
      };

  Future<void> charger() async {
    final prefs = await SharedPreferences.getInstance();
    _jeton = prefs.getString(_cleJeton);
    nom = prefs.getString(_cleNom);
    email = prefs.getString(_cleEmail);
    chantierRattachement = prefs.getString(_cleChantier);
  }

  Future<void> _enregistrer(String jeton, {String? nom, String? email}) async {
    _jeton = jeton;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_cleJeton, jeton);
    if (nom != null) {
      this.nom = nom;
      await prefs.setString(_cleNom, nom);
    }
    if (email != null) {
      this.email = email;
      await prefs.setString(_cleEmail, email);
    }
  }

  Future<void> enregistrerChantier(String libelle) async {
    chantierRattachement = libelle;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_cleChantier, libelle);
  }

  Future<void> deconnecter() async {
    _jeton = null;
    nom = null;
    email = null;
    chantierRattachement = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_cleJeton);
    await prefs.remove(_cleNom);
    await prefs.remove(_cleEmail);
    await prefs.remove(_cleChantier);
  }

  /// Extrait le motif renvoyé par le serveur.
  ///
  /// Ces messages sont rédigés pour être lus par la personne concernée
  /// (« Vous vous trouvez à 3,2 km du chantier le plus proche »). Les écraser
  /// par un libellé générique priverait l'utilisateur de la seule explication
  /// dont il dispose.
  String _motif(http.Response res, String defaut) {
    try {
      final corps = jsonDecode(utf8.decode(res.bodyBytes));
      final detail = corps is Map ? corps['detail'] : null;
      if (detail is String && detail.isNotEmpty) return detail;
    } catch (_) {}
    return defaut;
  }

  Future<ZoneVerifiee> verifierZone(double latitude, double longitude) async {
    final res = await http
        .post(
          Uri.parse('$kApiBaseUrl/citoyen/verifier-zone'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'latitude': latitude, 'longitude': longitude}),
        )
        .timeout(const Duration(seconds: 20));
    if (res.statusCode == 200) {
      return ZoneVerifiee.fromJson(jsonDecode(utf8.decode(res.bodyBytes)));
    }
    throw Exception(_motif(res, 'La vérification de votre position a échoué.'));
  }

  Future<void> inscrire({
    required String nom,
    required String email,
    required String motDePasse,
    String? telephone,
    required double latitude,
    required double longitude,
  }) async {
    final res = await http
        .post(
          Uri.parse('$kApiBaseUrl/citoyen/inscription'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'nom': nom,
            'email': email,
            'mot_de_passe': motDePasse,
            'telephone': telephone,
            'latitude': latitude,
            'longitude': longitude,
          }),
        )
        .timeout(const Duration(seconds: 30));
    if (res.statusCode == 200) {
      final data = jsonDecode(utf8.decode(res.bodyBytes));
      await _enregistrer(data['access_token'], nom: nom, email: email);
      return;
    }
    throw Exception(_motif(res, 'La création du compte a échoué.'));
  }

  Future<void> connecter(String email, String motDePasse) async {
    final res = await http
        .post(
          Uri.parse('$kApiBaseUrl/auth/login'),
          body: {'username': email, 'password': motDePasse},
        )
        .timeout(const Duration(seconds: 20));
    if (res.statusCode != 200) {
      throw Exception(_motif(res, 'Adresse ou mot de passe incorrect.'));
    }
    final data = jsonDecode(utf8.decode(res.bodyBytes));
    // Cloisonnement des deux applications : un agent qui saisirait ses
    // identifiants ici serait refusé, et réciproquement.
    if (data['role'] != 'PLAIGNANT') {
      throw Exception(
        'Ce compte n\'est pas un compte riverain. '
        'Les agents AGEROUTE disposent d\'une application distincte.',
      );
    }
    await _enregistrer(data['access_token'], email: email);
  }

  Future<String> monChantier() async {
    final res = await http
        .get(Uri.parse('$kApiBaseUrl/citoyen/mon-chantier'), headers: _entetes)
        .timeout(const Duration(seconds: 20));
    if (res.statusCode == 200) {
      final c = jsonDecode(utf8.decode(res.bodyBytes));
      final libelle = c['commune'] != null && (c['commune'] as String).isNotEmpty
          ? '${c['nom']}, ${c['commune']}'
          : '${c['nom']}';
      await enregistrerChantier(libelle);
      return libelle;
    }
    throw Exception(_motif(res, 'Chantier de rattachement introuvable.'));
  }

  Future<Doleance> deposer({
    required String description,
    String? categorie,
    double? latitude,
    double? longitude,
  }) async {
    final res = await http
        .post(
          Uri.parse('$kApiBaseUrl/citoyen/doleances'),
          headers: _entetes,
          body: jsonEncode({
            'description': description,
            'categorie': categorie,
            'latitude': latitude,
            'longitude': longitude,
          }),
        )
        .timeout(const Duration(seconds: 30));
    if (res.statusCode == 200) {
      return Doleance.fromJson(jsonDecode(utf8.decode(res.bodyBytes)));
    }
    throw Exception(_motif(res, 'Votre doléance n\'a pas pu être enregistrée.'));
  }

  /// Doléances mises en cache, pour un affichage immédiat à l'ouverture.
  Future<List<Doleance>?> mesDoleancesEnCache() async {
    final prefs = await SharedPreferences.getInstance();
    final brut = prefs.getString('citoyen_cache_doleances');
    if (brut == null) return null;
    try {
      return (jsonDecode(brut) as List).map((e) => Doleance.fromJson(e)).toList();
    } catch (_) {
      return null;
    }
  }

  Future<List<Doleance>> mesDoleances() async {
    final res = await http
        .get(Uri.parse('$kApiBaseUrl/citoyen/doleances'), headers: _entetes)
        .timeout(const Duration(seconds: 20));
    if (res.statusCode == 200) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('citoyen_cache_doleances', utf8.decode(res.bodyBytes));
      return (jsonDecode(utf8.decode(res.bodyBytes)) as List)
          .map((e) => Doleance.fromJson(e))
          .toList();
    }
    throw Exception(_motif(res, 'Vos doléances n\'ont pas pu être chargées.'));
  }

  Future<void> changerMotDePasse(String ancien, String nouveau) async {
    final res = await http
        .post(
          Uri.parse('$kApiBaseUrl/auth/change-password'),
          headers: _entetes,
          body: jsonEncode({
            'ancien_mot_de_passe': ancien,
            'nouveau_mot_de_passe': nouveau,
          }),
        )
        .timeout(const Duration(seconds: 20));
    if (res.statusCode != 200) {
      throw Exception(_motif(res, 'Le mot de passe n\'a pas pu être modifié.'));
    }
  }
}
