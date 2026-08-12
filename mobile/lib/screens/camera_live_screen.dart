import 'dart:typed_data';
import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../services/ia_service.dart';

/// Ecran de capture avec detection EN DIRECT : les cadres verts et le type de
/// dechet s'affichent sur l'apercu video avant meme la prise de vue, a la
/// maniere d'une camera de surveillance.
class CameraLiveScreen extends StatefulWidget {
  const CameraLiveScreen({super.key});

  @override
  State<CameraLiveScreen> createState() => _CameraLiveScreenState();
}

class _CameraLiveScreenState extends State<CameraLiveScreen> {
  CameraController? _controller;
  bool _pret = false;
  String? _erreur;

  /// Une seule inference a la fois : on ignore les frames qui arrivent pendant
  /// qu'on analyse, sinon la file d'attente explose.
  bool _analyseEnCours = false;
  List<DetectionBox> _cadres = const [];
  bool _auMoinsUneAnalyse = false;

  @override
  void initState() {
    super.initState();
    _initCamera();
  }

  Future<void> _initCamera() async {
    try {
      final cameras = await availableCameras();
      if (cameras.isEmpty) {
        setState(() => _erreur = 'Aucune camera disponible');
        return;
      }
      final arriere = cameras.firstWhere(
        (c) => c.lensDirection == CameraLensDirection.back,
        orElse: () => cameras.first,
      );
      final ctrl = CameraController(
        arriere,
        ResolutionPreset.medium,
        enableAudio: false,
        imageFormatGroup: ImageFormatGroup.yuv420,
      );
      await ctrl.initialize();
      if (!mounted) {
        await ctrl.dispose();
        return;
      }
      await ctrl.startImageStream(_traiterFrame);
      setState(() {
        _controller = ctrl;
        _pret = true;
      });
    } catch (e) {
      if (mounted) setState(() => _erreur = 'Camera indisponible : $e');
    }
  }

  Future<void> _traiterFrame(CameraImage image) async {
    if (_analyseEnCours || !mounted) return;
    _analyseEnCours = true;
    try {
      final prep = _yuv420VersTenseur(image);
      if (prep != null) {
        final cadres = await IaService().detecterDepuisTenseur(
          prep.tenseur,
          ratio: prep.ratio,
          decalageX: prep.decalageX,
          decalageY: prep.decalageY,
          largeurSource: image.width,
          hauteurSource: image.height,
        );
        if (mounted) {
          setState(() {
            _cadres = cadres;
            _auMoinsUneAnalyse = true;
          });
        }
      }
    } finally {
      _analyseEnCours = false;
    }
  }

  /// Convertit une frame YUV420 en tenseur [1,3,320,320] normalise 0..1, en
  /// appliquant un LETTERBOX : les proportions de la frame sont conservees et
  /// les marges sont remplies de gris 114, comme a l'entrainement du modele.
  ///
  /// Deux precautions de performance : on echantillonne directement a la taille
  /// du modele (convertir la frame entiere puis la redimensionner serait bien
  /// trop lent en Dart), et la conversion couleur se fait en arithmetique
  /// entiere.
  _FramePreparee? _yuv420VersTenseur(CameraImage image) {
    if (image.planes.length < 3) return null;
    const t = 320;
    const aire = t * t;
    // Valeur de remplissage des marges : 114/255, identique a Ultralytics.
    const gris = 114 / 255.0;

    final planY = image.planes[0];
    final planU = image.planes[1];
    final planV = image.planes[2];
    final octetsY = planY.bytes;
    final octetsU = planU.bytes;
    final octetsV = planV.bytes;

    final largeur = image.width;
    final hauteur = image.height;
    final pasLigneY = planY.bytesPerRow;
    final pasLigneUV = planU.bytesPerRow;
    final pasPixelUV = planU.bytesPerPixel ?? 1;

    // Parametres du letterbox
    final ratio = (t / largeur) < (t / hauteur) ? t / largeur : t / hauteur;
    final largeurUtile = (largeur * ratio).round();
    final hauteurUtile = (hauteur * ratio).round();
    final decalageX = ((t - largeurUtile) / 2).round();
    final decalageY = ((t - hauteurUtile) / 2).round();

    // Fond gris sur les 3 canaux, puis on ne remplit que la zone utile.
    final sortie = Float32List(3 * aire)..fillRange(0, 3 * aire, gris);

    for (int dy = 0; dy < hauteurUtile; dy++) {
      final sy = (dy * hauteur) ~/ hauteurUtile;
      final baseY = sy * pasLigneY;
      final baseUV = (sy >> 1) * pasLigneUV;
      final decalageLigne = (dy + decalageY) * t + decalageX;

      for (int dx = 0; dx < largeurUtile; dx++) {
        final sx = (dx * largeur) ~/ largeurUtile;

        final iY = baseY + sx;
        final iUV = baseUV + (sx >> 1) * pasPixelUV;
        if (iY >= octetsY.length || iUV >= octetsU.length || iUV >= octetsV.length) {
          continue;
        }

        final yv = octetsY[iY];
        final uv = octetsU[iUV] - 128;
        final vv = octetsV[iUV] - 128;

        // Conversion BT.601 en entiers (evite les flottants dans la boucle)
        int r = yv + ((1436 * vv) >> 10);
        int g = yv - ((352 * uv + 731 * vv) >> 10);
        int b = yv + ((1815 * uv) >> 10);
        if (r < 0) {
          r = 0;
        } else if (r > 255) {
          r = 255;
        }
        if (g < 0) {
          g = 0;
        } else if (g > 255) {
          g = 255;
        }
        if (b < 0) {
          b = 0;
        } else if (b > 255) {
          b = 255;
        }

        final idx = decalageLigne + dx;
        sortie[idx] = r / 255.0;               // canal R
        sortie[aire + idx] = g / 255.0;        // canal G
        sortie[2 * aire + idx] = b / 255.0;    // canal B
      }
    }
    return _FramePreparee(
      tenseur: sortie,
      ratio: ratio,
      decalageX: decalageX.toDouble(),
      decalageY: decalageY.toDouble(),
    );
  }

  Future<void> _capturer() async {
    final ctrl = _controller;
    if (ctrl == null || !ctrl.value.isInitialized) return;
    try {
      // On coupe le flux d'analyse avant la prise de vue pour liberer le
      // capteur et eviter une photo floue.
      if (ctrl.value.isStreamingImages) {
        await ctrl.stopImageStream();
      }
      final fichier = await ctrl.takePicture();
      if (!mounted) return;
      Navigator.pop(context, fichier);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Echec de la capture : $e')),
      );
    }
  }

  @override
  void dispose() {
    final ctrl = _controller;
    _controller = null;
    if (ctrl != null) {
      // stopImageStream avant dispose sinon des frames peuvent arriver sur un
      // controleur detruit.
      if (ctrl.value.isStreamingImages) {
        ctrl.stopImageStream().catchError((_) {}).whenComplete(ctrl.dispose);
      } else {
        ctrl.dispose();
      }
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: SafeArea(
        child: Stack(
          children: [
            if (_erreur != null)
              Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Text(_erreur!,
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: Colors.white)),
                ),
              )
            else if (!_pret || _controller == null)
              const Center(child: CircularProgressIndicator(color: Colors.white))
            else ...[
              Center(
                child: AspectRatio(
                  aspectRatio: 1 / _controller!.value.aspectRatio,
                  child: Stack(
                    fit: StackFit.expand,
                    children: [
                      CameraPreview(_controller!),
                      _OverlayDetections(cadres: _cadres),
                    ],
                  ),
                ),
              ),
              // Bandeau d'etat en haut : type detecte ou "aucun dechet"
              Positioned(top: 12, left: 12, right: 12, child: _bandeauEtat()),
              // Bouton de capture
              Positioned(
                bottom: 28,
                left: 0,
                right: 0,
                child: Center(
                  child: GestureDetector(
                    onTap: _capturer,
                    child: Container(
                      width: 74,
                      height: 74,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: Colors.white.withValues(alpha: 0.25),
                        border: Border.all(color: Colors.white, width: 4),
                      ),
                      child: const Icon(LucideIcons.camera,
                          color: Colors.white, size: 30),
                    ),
                  ),
                ),
              ),
            ],
            Positioned(
              top: 10,
              left: 6,
              child: IconButton(
                icon: const Icon(LucideIcons.x, color: Colors.white),
                onPressed: () => Navigator.pop(context),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _bandeauEtat() {
    // Regroupe les types detectes avec leur meilleure confiance
    final meilleurParType = <String, double>{};
    for (final c in _cadres) {
      final actuel = meilleurParType[c.label];
      if (actuel == null || c.confidence > actuel) {
        meilleurParType[c.label] = c.confidence;
      }
    }

    final String texte;
    final Color couleur;
    if (!_auMoinsUneAnalyse) {
      texte = 'Analyse en cours...';
      couleur = Colors.white70;
    } else if (meilleurParType.isEmpty) {
      texte = 'Aucun dechet reconnu';
      couleur = Colors.white;
    } else {
      final parts = meilleurParType.entries
          .map((e) => '${e.key} ${(e.value * 100).round()}%')
          .toList()
        ..sort();
      texte = parts.join('   ');
      couleur = const Color(0xFF00E676);
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.black.withValues(alpha: 0.55),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: couleur.withValues(alpha: 0.5)),
      ),
      child: Row(children: [
        Icon(
          meilleurParType.isEmpty
              ? Icons.search_rounded
              : LucideIcons.checkCircle,
          color: couleur,
          size: 18,
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            texte,
            style: TextStyle(
                color: couleur, fontSize: 13, fontWeight: FontWeight.w700),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ]),
    );
  }
}

/// Frame video convertie en tenseur, accompagnee des parametres du letterbox
/// necessaires pour replacer les detections sur l'image affichee.
class _FramePreparee {
  final Float32List tenseur;
  final double ratio;
  final double decalageX;
  final double decalageY;

  _FramePreparee({
    required this.tenseur,
    required this.ratio,
    required this.decalageX,
    required this.decalageY,
  });
}

/// Dessine les cadres verts + etiquettes par-dessus l'apercu video.
class _OverlayDetections extends StatelessWidget {
  final List<DetectionBox> cadres;
  const _OverlayDetections({required this.cadres});

  @override
  Widget build(BuildContext context) {
    if (cadres.isEmpty) return const SizedBox.shrink();
    return LayoutBuilder(builder: (context, contraintes) {
      final l = contraintes.maxWidth;
      final h = contraintes.maxHeight;
      return Stack(
        children: cadres.map((c) {
          final gauche = (c.x * l).clamp(0.0, l);
          final haut = (c.y * h).clamp(0.0, h);
          final largeur = (c.width * l).clamp(0.0, l - gauche);
          final hauteur = (c.height * h).clamp(0.0, h - haut);
          return Positioned(
            left: gauche,
            top: haut,
            width: largeur,
            height: hauteur,
            child: Stack(clipBehavior: Clip.none, children: [
              Container(
                decoration: BoxDecoration(
                  border: Border.all(color: const Color(0xFF00E676), width: 2.5),
                  borderRadius: BorderRadius.circular(4),
                ),
              ),
              // Etiquette : type + pourcentage, posee au-dessus du cadre
              Positioned(
                left: 0,
                top: -20,
                child: Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: const Color(0xFF00E676),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    '${c.label} ${(c.confidence * 100).round()}%',
                    style: const TextStyle(
                      color: Colors.black,
                      fontSize: 10,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
              ),
            ]),
          );
        }).toList(),
      );
    });
  }
}
