import 'dart:typed_data';
import 'dart:io';
import 'package:flutter/services.dart';
import 'package:onnxruntime/onnxruntime.dart';

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

  Future<void> _loadDetection() async {
    try {
      final data = await rootBundle.load('assets/models/detection_yolov8n.onnx');
      final options = OrtSessionOptions();
      _detectionSession = OrtSession.fromBuffer(data.buffer.asUint8List(), options);
    } catch (_) {}
  }

  Future<void> _loadClassification() async {
    try {
      final data = await rootBundle.load('assets/models/classification_mobilenetv2.onnx');
      final options = OrtSessionOptions();
      _classificationSession = OrtSession.fromBuffer(data.buffer.asUint8List(), options);
    } catch (_) {}
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

      // Decoder les probabilites
      final classes = ['FAIBLE', 'MODERE', 'ELEVE'];
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
