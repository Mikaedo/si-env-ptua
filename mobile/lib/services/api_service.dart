import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../core/constants.dart';
import '../models/models.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  String? _token;
  String? _role;
  bool? _premiereConnexion;

  String? get token => _token;
  String? get role => _role;
  bool? get premiereConnexion => _premiereConnexion;

  Future<void> loadToken() async {
    final prefs = await SharedPreferences.getInstance();
    _token = prefs.getString('token');
    _role = prefs.getString('role');
    _premiereConnexion = prefs.getBool('premiere_connexion');
  }

  Future<void> _saveToken(String token, String role, bool premiere) async {
    _token = token;
    _role = role;
    _premiereConnexion = premiere;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('token', token);
    await prefs.setString('role', role);
    await prefs.setBool('premiere_connexion', premiere);
  }

  Future<void> clearToken() async {
    _token = null;
    _role = null;
    _premiereConnexion = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('token');
    await prefs.remove('role');
    await prefs.remove('premiere_connexion');
  }

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (_token != null) 'Authorization': 'Bearer $_token',
      };

  Future<Map<String, dynamic>> login(String email, String password) async {
    final res = await http.post(
      Uri.parse('$kApiBaseUrl/auth/login'),
      body: {'username': email, 'password': password},
    );
    if (res.statusCode == 200) {
      final data = jsonDecode(res.body);
      await _saveToken(data['access_token'], data['role'] ?? '', data['premiere_connexion'] ?? false);
      return data;
    }
    final err = jsonDecode(res.body);
    throw Exception(err['detail'] ?? 'Erreur de connexion');
  }

  Future<Utilisateur> me() async {
    final res = await http.get(Uri.parse('$kApiBaseUrl/auth/me'), headers: _headers);
    if (res.statusCode == 200) {
      return Utilisateur.fromJson(jsonDecode(res.body));
    }
    throw Exception('Erreur recuperation profil');
  }

  Future<Map<String, dynamic>> firstLogin(String nom, String telephone, String password) async {
    final res = await http.post(
      Uri.parse('$kApiBaseUrl/auth/first-login'),
      headers: _headers,
      body: jsonEncode({'nom': nom, 'telephone': telephone, 'mot_de_passe': password}),
    );
    if (res.statusCode == 200) {
      final data = jsonDecode(res.body);
      await _saveToken(data['access_token'], data['role'] ?? '', false);
      return data;
    }
    throw Exception('Erreur premiere connexion');
  }

  Future<void> changePassword(String oldPassword, String newPassword) async {
    final res = await http.post(
      Uri.parse('$kApiBaseUrl/auth/change-password'),
      headers: _headers,
      body: jsonEncode({'ancien_mot_de_passe': oldPassword, 'nouveau_mot_de_passe': newPassword}),
    );
    if (res.statusCode != 200) {
      throw Exception('Erreur changement mot de passe');
    }
  }

  Future<Map<String, dynamic>> forgotPassword(String email) async {
    final res = await http.post(
      Uri.parse('$kApiBaseUrl/auth/forgot'),
      headers: _headers,
      body: jsonEncode({'email': email}),
    );
    if (res.statusCode == 200) {
      return jsonDecode(res.body);
    }
    throw Exception('Email introuvable');
  }

  Future<void> verifyCode(String email, String code) async {
    final res = await http.post(
      Uri.parse('$kApiBaseUrl/auth/verify-code'),
      headers: _headers,
      body: jsonEncode({'email': email, 'code': code}),
    );
    if (res.statusCode != 200) {
      throw Exception('Code incorrect');
    }
  }

  Future<void> resetPassword(String email, String code, String newPassword) async {
    final res = await http.post(
      Uri.parse('$kApiBaseUrl/auth/reset-password'),
      headers: _headers,
      body: jsonEncode({'email': email, 'code': code, 'nouveau_mot_de_passe': newPassword}),
    );
    if (res.statusCode != 200) {
      throw Exception('Erreur reinitialisation');
    }
  }

  /// Sonde legere de joignabilite du serveur, utilisee par la synchronisation
  /// automatique en arriere-plan (section 4.6 du memoire) : elle interroge le
  /// point de sante racine avec un delai court, sans jeton ni corps de reponse
  /// a analyser, pour ne pas consommer de donnees inutilement sur le terrain.
  Future<bool> reseauDisponible() async {
    try {
      final res = await http
          .get(Uri.parse(kApiBaseUrl.replaceFirst(RegExp(r'/api/?$'), '/')))
          .timeout(const Duration(seconds: 4));
      return res.statusCode < 500;
    } catch (_) {
      return false;
    }
  }

  Future<List<Chantier>> getChantiers() async {
    final res = await http.get(Uri.parse('$kApiBaseUrl/chantiers'), headers: _headers);
    if (res.statusCode == 200) {
      final list = jsonDecode(res.body) as List;
      return list.map((e) => Chantier.fromJson(e)).toList();
    }
    throw Exception('Erreur recuperation chantiers');
  }

  Future<Signalement> createSignalement(Signalement s) async {
    final res = await http.post(
      Uri.parse('$kApiBaseUrl/signalements'),
      headers: _headers,
      body: jsonEncode(s.toJson()),
    );
    if (res.statusCode == 200) {
      return Signalement.fromJson(jsonDecode(res.body));
    }
    throw Exception('Erreur creation signalement');
  }

  Future<List<Signalement>> getSignalements({
    String? statut,
    String? criticite,
    String? typeNuisance,
    int? chantierId,
    int? periodeJours,
  }) async {
    final params = <String, String>{};
    if (statut != null) params['statut'] = statut;
    if (criticite != null) params['criticite'] = criticite;
    if (typeNuisance != null) params['type_nuisance'] = typeNuisance;
    if (chantierId != null) params['chantier_id'] = chantierId.toString();
    if (periodeJours != null) params['periode_jours'] = periodeJours.toString();

    final uri = Uri.parse('$kApiBaseUrl/signalements').replace(queryParameters: params);
    final res = await http.get(uri, headers: _headers);
    if (res.statusCode == 200) {
      final list = jsonDecode(res.body) as List;
      return list.map((e) => Signalement.fromJson(e)).toList();
    }
    throw Exception('Erreur recuperation signalements');
  }

  Future<Signalement> getSignalementDetail(int id) async {
    final res = await http.get(Uri.parse('$kApiBaseUrl/signalements/$id'), headers: _headers);
    if (res.statusCode == 200) {
      return Signalement.fromJson(jsonDecode(res.body));
    }
    throw Exception('Signalement introuvable');
  }

  Future<Signalement> updateStatut(int id, String statut) async {
    final res = await http.patch(
      Uri.parse('$kApiBaseUrl/signalements/$id/statut?nouveau_statut=$statut'),
      headers: _headers,
    );
    if (res.statusCode == 200) {
      return Signalement.fromJson(jsonDecode(res.body));
    }
    throw Exception('Erreur mise a jour statut');
  }

  Future<void> addActionCorrective(int id, String description, DateTime? echeance) async {
    final res = await http.post(
      Uri.parse('$kApiBaseUrl/signalements/$id/action'),
      headers: _headers,
      body: jsonEncode({
        'description': description,
        'echeance': echeance?.toIso8601String(),
      }),
    );
    if (res.statusCode != 200) {
      throw Exception('Erreur ajout action corrective');
    }
  }

  Future<void> retournerAgent(int id, String motif) async {
    final res = await http.post(
      Uri.parse('$kApiBaseUrl/signalements/$id/retour'),
      headers: _headers,
      body: jsonEncode({'motif': motif}),
    );
    if (res.statusCode != 200) {
      throw Exception('Erreur retour agent');
    }
  }

  Future<List<Alerte>> getAlertes() async {
    final res = await http.get(Uri.parse('$kApiBaseUrl/alertes'), headers: _headers);
    if (res.statusCode == 200) {
      final list = jsonDecode(res.body) as List;
      return list.map((e) => Alerte.fromJson(e)).toList();
    }
    throw Exception('Erreur recuperation alertes');
  }

  Future<void> accuserReception(int alerteId) async {
    final res = await http.post(
      Uri.parse('$kApiBaseUrl/alertes/$alerteId/accuser'),
      headers: _headers,
    );
    if (res.statusCode != 200) {
      throw Exception('Erreur accusation reception');
    }
  }

  Future<Statistiques> getStatistiques() async {
    final res = await http.get(Uri.parse('$kApiBaseUrl/stats'), headers: _headers);
    if (res.statusCode == 200) {
      return Statistiques.fromJson(jsonDecode(res.body));
    }
    throw Exception('Erreur recuperation statistiques');
  }

  Future<Map<String, dynamic>> uploadPhoto(int signalementId, String filePath) async {
    final uri = Uri.parse('$kApiBaseUrl/signalements/$signalementId/photos');
    final request = http.MultipartRequest('POST', uri);
    request.headers['Authorization'] = 'Bearer $_token';
    request.files.add(await http.MultipartFile.fromPath('file', filePath, contentType: MediaType('image', 'jpeg')));
    final res = await request.send();
    if (res.statusCode == 200) {
      final body = await res.stream.bytesToString();
      return jsonDecode(body);
    }
    throw Exception('Erreur upload photo');
  }

  Future<List<Map<String, dynamic>>> getPhotos(int signalementId) async {
    final res = await http.get(Uri.parse('$kApiBaseUrl/signalements/$signalementId/photos'), headers: _headers);
    if (res.statusCode == 200) {
      final list = jsonDecode(res.body) as List;
      return list.cast<Map<String, dynamic>>();
    }
    throw Exception('Erreur recuperation photos');
  }
}
