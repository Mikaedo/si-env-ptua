import 'dart:typed_data';
import 'dart:io';
import 'package:flutter/services.dart';
import 'package:onnxruntime/onnxruntime.dart';
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';

/// Boite de detection retournee par le detecteur YOLO. Coordonnees exprimees
/// dans le repere normalise [0, 1] de l'image d'entree, afin que l'overlay
/// puisse les projeter sur n'importe quelle taille d'apercu.
class DetectionBox {
  final double x;
  final double y;
  final double width;
  final double height;
  final String label;
  final double confidence;

  const DetectionBox({
    required this.x,
    required this.y,
    required this.width,
    required this.height,
    required this.label,
    required this.confidence,
  });
}

class IaService {
  static final IaService _instance = IaService._internal();
  factory IaService() => _instance;
  IaService._internal();

  // ignore: unused_field
  OrtSession? _detectionSession;
  OrtSession? _classificationSession;
  bool _loaded = false;

  Future<void> loadModels() async {
    if (_loaded) return;
    try {
      await _loadDetection();
      await _loadClassification();
      _loaded = true;
    } catch (e) {
      // Mode degradation : si les modeles ne sont pas presents, on continue sans IA
    }
  }

  /// Chemin local d'un modele telecharge depuis le backend, s'il existe. Ce
  /// fichier prend le pas sur celui embarque dans l'APK : c'est le mecanisme
  /// qui permet a l'administrateur de redeployer un modele sans passer par
  /// le Play Store (paragraphe 2.5 du chapitre V).
  Future<File> _fichierLocal(String typeModele) async {
    final dossier = await getApplicationDocumentsDirectory();
    return File('${dossier.path}/modele_$typeModele.onnx');
  }

  Future<void> _loadDetection() async {
    try {
      final local = await _fichierLocal('detection');
      final octets = await local.exists()
          ? await local.readAsBytes()
          : (await rootBundle.load('assets/models/detection_yolov8n.onnx')).buffer.asUint8List();
      final options = OrtSessionOptions();
      _detectionSession = OrtSession.fromBuffer(octets, options);
    } catch (_) {}
  }

  Future<void> _loadClassification() async {
    try {
      final local = await _fichierLocal('classification');
      final octets = await local.exists()
          ? await local.readAsBytes()
          : (await rootBundle.load('assets/models/classification_mobilenetv2.onnx')).buffer.asUint8List();
      final options = OrtSessionOptions();
      _classificationSession = OrtSession.fromBuffer(octets, options);
    } catch (_) {}
  }

  /// Compare la version deployee cote serveur a la derniere version
  /// installee localement (SharedPreferences). Ne telecharge rien : sert
  /// uniquement a decider si la banniere de mise a jour doit s'afficher.
  Future<List<String>> verifierMisesAJourDisponibles() async {
    try {
      final versions = await ApiService().getModelVersions();
      final prefs = await SharedPreferences.getInstance();
      final disponibles = <String>[];
      for (final type in ['detection', 'classification']) {
        final info = versions[type] as Map<String, dynamic>?;
        if (info == null || info['disponible'] != true) continue;
        final versionServeur = info['version'] as int? ?? 0;
        final versionLocale = prefs.getInt('modele_version_$type') ?? 0;
        if (versionServeur > versionLocale) disponibles.add(type);
      }
      return disponibles;
    } catch (_) {
      return const [];
    }
  }

  /// Telecharge le modele demande, l'installe localement et recharge la
  /// session ONNX correspondante. Retourne false si le telechargement echoue
  /// (reseau absent, entre autres), sans jamais casser la session existante.
  Future<bool> telechargerEtInstaller(String typeModele) async {
    try {
      final octets = await ApiService().downloadModel(typeModele);
      final versions = await ApiService().getModelVersions();
      final info = versions[typeModele] as Map<String, dynamic>?;
      final version = info?['version'] as int? ?? 0;

      final fichier = await _fichierLocal(typeModele);
      await fichier.writeAsBytes(octets);

      final prefs = await SharedPreferences.getInstance();
      await prefs.setInt('modele_version_$typeModele', version);

      final options = OrtSessionOptions();
      final session = OrtSession.fromBuffer(octets, options);
      if (typeModele == 'detection') {
        _detectionSession = session;
      } else {
        _classificationSession = session;
      }
      return true;
    } catch (_) {
      return false;
    }
  }

  bool get isLoaded => _loaded;

  Future<IaResult> analyzeImage(String imagePath) async {
    if (!_loaded || _classificationSession == null) {
      return IaResult(detected: false, criticite: null, confiance: null, objets: []);
    }

    try {
      final file = File(imagePath);
      final bytes = await file.readAsBytes();

      // Preprocessing : redimensionner a 224x224 et normaliser (MobileNetV2)
      final inputTensor = _preprocessImage(bytes);

      // Inference classification
      final inputName = _classificationSession!.inputNames.isNotEmpty
          ? _classificationSession!.inputNames[0]
          : 'input';
      final inputs = {
        inputName: OrtValueTensor.createTensorWithDataList(inputTensor, [1, 3, 224, 224]),
      };
      final outputs = _classificationSession!.run(OrtRunOptions(), inputs);
      
      if (outputs.isEmpty || outputs[0] == null) {
        return IaResult(detected: false, criticite: null, confiance: null, objets: []);
      }
      
      final outputData = outputs[0]!.value as List;

      // Decoder les probabilites.
      // L'ordre est celui qu'impose torchvision : ImageFolder classe les
      // dossiers par ordre alphabetique, soit faible(0), important(1),
      // modere(2). Ranger « MODERE » en deuxieme position intervertissait donc
      // les deux criticites les plus hautes a chaque diagnostic.
      final classes = ['FAIBLE', 'ELEVE', 'MODERE'];
      int maxIdx = 0;
      double maxVal = 0;
      for (int i = 0; i < outputData[0].length; i++) {
        if (outputData[0][i] > maxVal) {
          maxVal = outputData[0][i];
          maxIdx = i;
        }
      }

      return IaResult(
        detected: true,
        criticite: classes[maxIdx],
        confiance: (maxVal * 100).roundToDouble(),
        objets: ['dechets'],
      );
    } catch (e) {
      return IaResult(detected: false, criticite: null, confiance: null, objets: []);
    }
  }

  /// Detecte les dechets sur un tenseur pre-traite en 320x320 (format YOLOv8n).
  ///
  /// Le tenseur est deja normalise 0..1, en canaux CHW, et fourni avec les
  /// parametres du letterbox (ratio et decalages) qui ont servi a le
  /// construire : ils permettent de reprojeter les detections dans le repere
  /// [0, 1] de l'image d'origine, celui qu'attend l'overlay.
  ///
  /// Comportement de degradation : si le detecteur ONNX n'est pas charge (fichier
  /// modele absent), on retourne une liste vide. L'ecran continue de tourner et
  /// affiche « Aucun dechet reconnu », sans faire planter la camera live.
  Future<List<DetectionBox>> detecterDepuisTenseur(
    Float32List tenseur, {
    required double ratio,
    required double decalageX,
    required double decalageY,
    required int largeurSource,
    required int hauteurSource,
    double seuilConfiance = 0.35,
  }) async {
    if (!_loaded || _detectionSession == null) return const [];

    try {
      final nomEntree = _detectionSession!.inputNames.isNotEmpty
          ? _detectionSession!.inputNames[0]
          : 'images';
      final entrees = {
        nomEntree: OrtValueTensor.createTensorWithDataList(tenseur, [1, 3, 320, 320]),
      };
      final sorties = _detectionSession!.run(OrtRunOptions(), entrees);
      if (sorties.isEmpty || sorties[0] == null) return const [];

      // Sortie YOLOv8 : [1, 4 + nc, N] ou nc = nombre de classes.
      // On decode les boites au-dessus du seuil et on les reprojette dans le
      // repere normalise de l'image d'origine (compensation du letterbox).
      final brut = sorties[0]!.value as List;
      final canaux = (brut[0] as List);
      if (canaux.length < 5) return const [];
      final n = (canaux[0] as List).length;
      final nbClasses = canaux.length - 4;

      final resultats = <DetectionBox>[];
      // L'ordre suit celui des classes du modele, lisible dans ses metadonnees
      // ONNX : {0: cardboard, 1: glass, 2: metal, 3: organic, 4: paper,
      // 5: plastic}. Toute modification du modele impose de relire ce champ :
      // l'index seul est retourne par le reseau, la correspondance est ici.
      const etiquettes = [
        'carton', 'verre', 'métal', 'organique', 'papier', 'plastique',
      ];

      for (int i = 0; i < n; i++) {
        // Meilleure classe pour cette ancre
        int idxClasse = 0;
        double meilleure = 0;
        for (int c = 0; c < nbClasses; c++) {
          final s = (canaux[4 + c][i] as num).toDouble();
          if (s > meilleure) {
            meilleure = s;
            idxClasse = c;
          }
        }
        if (meilleure < seuilConfiance) continue;

        // Coordonnees en pixels dans l'espace du modele (320x320)
        final cx = (canaux[0][i] as num).toDouble();
        final cy = (canaux[1][i] as num).toDouble();
        final w = (canaux[2][i] as num).toDouble();
        final h = (canaux[3][i] as num).toDouble();

        // Compensation du letterbox : on retire le decalage, on divise par le
        // ratio, on ramene en [0, 1] par rapport a l'image d'origine.
        final gx = ((cx - w / 2) - decalageX) / (ratio * largeurSource);
        final gy = ((cy - h / 2) - decalageY) / (ratio * hauteurSource);
        final gw = w / (ratio * largeurSource);
        final gh = h / (ratio * hauteurSource);

        if (gx < 0 || gy < 0 || gx + gw > 1 || gy + gh > 1) continue;

        resultats.add(DetectionBox(
          x: gx, y: gy, width: gw, height: gh,
          label: idxClasse < etiquettes.length ? etiquettes[idxClasse] : 'objet',
          confidence: meilleure,
        ));
      }
      return resultats;
    } catch (_) {
      return const [];
    }
  }

  Float32List _preprocessImage(Uint8List bytes) {
    // Conversion simplifiee : en production, utiliser image package pour resize
    // Ici on cree un tensor placeholder 1x3x224x224 normalise
    final tensor = Float32List(1 * 3 * 224 * 224);
    for (int i = 0; i < tensor.length; i++) {
      tensor[i] = (bytes[i % bytes.length] / 127.5) - 1.0;
    }
    return tensor;
  }
}

class IaResult {
  final bool detected;
  final String? criticite;
  final double? confiance;
  final List<String> objets;

  IaResult({required this.detected, this.criticite, this.confiance, required this.objets});
}
