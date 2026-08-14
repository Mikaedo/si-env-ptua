import 'dart:io';
import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:image_picker/image_picker.dart';
import 'package:uuid/uuid.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../blocs/signalement/signalement_bloc.dart';
import '../blocs/sync/sync_bloc.dart';
import '../core/constants.dart';
import '../models/models.dart';
import '../services/local_database.dart';
import '../services/gps_service.dart';
import '../services/api_service.dart';
import '../services/ia_service.dart';
import 'camera_live_screen.dart';
import 'confirmation_screen.dart';

class NouveauSignalementScreen extends StatefulWidget {
  final String typeNuisance;
  const NouveauSignalementScreen({super.key, required this.typeNuisance});

  @override
  State<NouveauSignalementScreen> createState() => _NouveauSignalementScreenState();
}

class _NouveauSignalementScreenState extends State<NouveauSignalementScreen> {
  late String _selectedType;
  String _selectedChantier = kChantiers.first;
  String _criticite = 'FAIBLE';
  String _gpsSource = 'AUTO';
  double? _latitude;
  double? _longitude;
  bool _gpsAuto = true;
  bool _iaLoading = false;
  IaResult? _iaResult;
  // Detections issues du viseur live (circuit dechets). Quand non nul, le type
  // de nuisance et la criticite sont figes automatiquement : l'agent n'a plus
  // aucun choix a faire pour les dechets, conformement au principe pose.
  int? _nbObjetsDetectes;
  final _descriptionController = TextEditingController();
  final _gpsController = TextEditingController();
  XFile? _photo;

  @override
  void initState() {
    super.initState();
    _selectedType = widget.typeNuisance;
    _getGps();
    IaService().loadModels();
  }

  Future<void> _getGps() async {
    final pos = await GpsService.getCurrentPosition();
    if (!mounted) return;
    if (pos != null) {
      setState(() {
        _latitude = pos.latitude;
        _longitude = pos.longitude;
        _gpsController.text = '${pos.latitude.toStringAsFixed(5)} N, ${pos.longitude.toStringAsFixed(5)} W';
      });
    } else {
      setState(() {
        _gpsAuto = false;
        _gpsSource = 'MANUEL';
      });
    }
  }

  Future<void> _pickPhoto() async {
    final granted = await GpsService.requestCameraPermission();
    if (!granted || !mounted) return;

    // Circuit dechets : viseur live avec detection YOLO en superposition, la
    // criticite est deduite automatiquement du nombre d'objets detectes.
    // L'agent n'evalue plus, ne choisit plus : il pointe et il capture.
    if (_hasIa) {
      final navigator = Navigator.of(context);
      final resultat = await navigator.push<CameraLiveResultat>(
        MaterialPageRoute(builder: (_) => const CameraLiveScreen()),
      );
      if (!mounted || resultat == null) return;
      final n = resultat.cadres.length;
      setState(() {
        _photo = resultat.photo;
        _nbObjetsDetectes = n;
        _criticite = _deriverCriticite(n);
        _iaResult = IaResult(
          detected: n > 0,
          criticite: _criticite,
          confiance: n == 0
              ? null
              : (resultat.cadres.map((c) => c.confidence).reduce((a, b) => a > b ? a : b) * 100),
          objets: resultat.cadres.map((c) => c.label).toSet().toList(),
        );
        _iaLoading = false;
      });
      return;
    }

    // Autres nuisances : chemin historique via l'appareil photo natif.
    final picker = ImagePicker();
    final photo = await picker.pickImage(source: ImageSource.camera, imageQuality: 85);
    if (photo != null) {
      setState(() {
        _photo = photo;
        _iaLoading = false;
      });
    }
  }

  /// Regle deterministe du §5.8 du memoire : peu d'objets = faible, moyen =
  /// modere, beaucoup = eleve. Reste centralisee ici pour que la meme regle
  /// soit appliquee quel que soit l'appelant.
  String _deriverCriticite(int nbObjets) {
    if (nbObjets >= 6) return 'ELEVE';
    if (nbObjets >= 3) return 'MODERE';
    return 'FAIBLE';
  }

  bool get _hasIa => _selectedType == 'Déchets de chantier';

  /// Vrai des qu'on est passe par le viseur live : dans ce cas, l'agent ne peut
  /// plus changer ni le type de nuisance ni la criticite.
  bool get _diagnosticIaFige => _hasIa && _nbObjetsDetectes != null;

  IconData _iconForType(String type) {
    switch (type) {
      case 'Déchets de chantier': return LucideIcons.trash2;
      case 'Eaux stagnantes': return LucideIcons.droplets;
      case 'Poussières': return LucideIcons.wind;
      case 'Bruit': return LucideIcons.volume2;
      case 'Dégradation végétation': return LucideIcons.trees;
      default: return LucideIcons.alertTriangle;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kGray50,
      appBar: AppBar(
        backgroundColor: kGray50,
        leading: IconButton(icon: const Icon(LucideIcons.arrowLeft), onPressed: () => Navigator.pop(context)),
        title: const Text('Nouveau signalement'),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
          children: [
            _buildPhotoHero(),
            const SizedBox(height: 20),

            // Circuit dechets fige : l'agent voit le diagnostic mais ne
            // change plus rien. Les selecteurs type/criticite sont remplaces
            // par des cartes en lecture seule qui reprennent la decision du
            // modele. Le chantier reste modifiable (proximite GPS peut se
            // tromper), la description aussi.
            if (!_diagnosticIaFige) ...[
              _sectionLabel('Type de nuisance', LucideIcons.tags),
              const SizedBox(height: 10),
              _buildTypeSelector(),
              const SizedBox(height: 20),
            ] else ...[
              _sectionLabel('Diagnostic automatique', LucideIcons.brain),
              const SizedBox(height: 10),
              _buildIaCard(),
              const SizedBox(height: 20),
            ],

            _sectionLabel('Chantier concerné', LucideIcons.hardHat),
            const SizedBox(height: 10),
            _buildChantierField(),
            const SizedBox(height: 20),
            _sectionLabel('Localisation', LucideIcons.mapPin),
            const SizedBox(height: 10),
            _buildGpsCard(),

            if (!_diagnosticIaFige) ...[
              const SizedBox(height: 20),
              _sectionLabel('Niveau de criticité', LucideIcons.shield),
              const SizedBox(height: 10),
              _buildCriticiteSelector(),
            ],
            const SizedBox(height: 20),
            _sectionLabel('Description', LucideIcons.alignLeft),
            const SizedBox(height: 10),
            _buildDescriptionField(),
          ],
        ),
      ),
      bottomNavigationBar: _buildBottomBar(),
    );
  }

  // ---------- PHOTO HERO ----------
  Widget _buildPhotoHero() {
    return GestureDetector(
      onTap: _pickPhoto,
      child: Container(
        height: 200,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(20),
          color: kGray100,
          border: Border.all(color: _photo != null ? kBlue : kGray200, width: _photo != null ? 2 : 1.5),
        ),
        clipBehavior: Clip.antiAlias,
        child: _photo != null
            ? Stack(fit: StackFit.expand, children: [
                Image.file(File(_photo!.path), fit: BoxFit.cover),
                // Gradient overlay
                Container(decoration: BoxDecoration(
                  gradient: LinearGradient(begin: Alignment.topCenter, end: Alignment.bottomCenter,
                    colors: [Colors.transparent, kBlack.withValues(alpha: 0.55)]),
                )),
                Positioned(right: 12, top: 12, child: _circleBtn(LucideIcons.x, () => setState(() { _photo = null; _iaResult = null; }))),
                Positioned(left: 14, bottom: 12, child: Row(children: [
                  const Icon(LucideIcons.checkCircle, color: kWhite, size: 18),
                  const SizedBox(width: 6),
                  const Text('Photo capturée', style: TextStyle(color: kWhite, fontSize: 13, fontWeight: FontWeight.w600)),
                ])),
                Positioned(right: 12, bottom: 12, child: _circleBtn(LucideIcons.refreshCw, _pickPhoto)),
              ])
            : Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                Container(width: 60, height: 60, decoration: BoxDecoration(color: kBlue.withValues(alpha: 0.1), shape: BoxShape.circle),
                  child: const Icon(LucideIcons.camera, size: 28, color: kBlue)),
                const SizedBox(height: 12),
                const Text('Prendre une photo', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: kGray800)),
                const SizedBox(height: 4),
                Text(_hasIa ? 'L\'IA analysera automatiquement les déchets' : 'Documentez la nuisance observée',
                  style: const TextStyle(fontSize: 11, color: kGray600)),
              ]),
      ),
    );
  }

  Widget _circleBtn(IconData icon, VoidCallback onTap) {
    return GestureDetector(onTap: onTap, child: Container(
      width: 34, height: 34,
      decoration: BoxDecoration(color: kBlack.withValues(alpha: 0.4), shape: BoxShape.circle),
      child: Icon(icon, color: kWhite, size: 18),
    ));
  }

  // ---------- TYPE SELECTOR ----------
  Widget _buildTypeSelector() {
    return SizedBox(
      height: 96,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: kNuisanceTypes.length,
        separatorBuilder: (_, i) => const SizedBox(width: 10),
        itemBuilder: (_, i) {
          final type = kNuisanceTypes[i];
          final selected = type == _selectedType;
          return GestureDetector(
            onTap: () => setState(() { _selectedType = type; _iaResult = null; }),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 180),
              width: 92,
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: selected ? kBlue : kWhite,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: selected ? kBlue : kGray200, width: 1.5),
              ),
              child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                Icon(_iconForType(type), size: 26, color: selected ? kWhite : kBlue),
                const SizedBox(height: 8),
                Text(type, textAlign: TextAlign.center, maxLines: 2, overflow: TextOverflow.ellipsis,
                  style: TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: selected ? kWhite : kGray600, height: 1.15)),
              ]),
            ),
          );
        },
      ),
    );
  }

  // ---------- CHANTIER ----------
  Widget _buildChantierField() {
    return Container(
      decoration: BoxDecoration(color: kWhite, borderRadius: BorderRadius.circular(14), border: Border.all(color: kGray200, width: 1.5)),
      padding: const EdgeInsets.symmetric(horizontal: 14),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          isExpanded: true,
          value: _selectedChantier,
          icon: const Icon(LucideIcons.chevronDown, color: kGray600),
          borderRadius: BorderRadius.circular(14),
          items: kChantiers.map((c) => DropdownMenuItem(value: c, child: Text(c, style: const TextStyle(fontSize: 14, color: kGray800)))).toList(),
          onChanged: (v) => setState(() => _selectedChantier = v!),
        ),
      ),
    );
  }

  // ---------- GPS CARD ----------
  Widget _buildGpsCard() {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: kWhite, borderRadius: BorderRadius.circular(16), border: Border.all(color: kGray200, width: 1.5)),
      child: Column(children: [
        Row(children: [
          Container(width: 42, height: 42,
            decoration: BoxDecoration(color: kBlue.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(12)),
            child: Icon(_gpsAuto ? Icons.gps_fixed_rounded : Icons.edit_location_alt_rounded, color: kBlue, size: 20)),
          const SizedBox(width: 12),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(_gpsAuto ? 'GPS automatique' : 'Saisie manuelle', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: kGray800)),
            const SizedBox(height: 2),
            Text(_gpsController.text.isEmpty ? 'Acquisition en cours...' : _gpsController.text,
              style: const TextStyle(fontSize: 11, color: kGray600), maxLines: 1, overflow: TextOverflow.ellipsis),
          ])),
          Switch(value: _gpsAuto, activeThumbColor: kBlue, onChanged: (v) => setState(() { _gpsAuto = v; _gpsSource = v ? 'AUTO' : 'MANUEL'; })),
        ]),
        if (!_gpsAuto) ...[
          const SizedBox(height: 10),
          TextField(controller: _gpsController, decoration: const InputDecoration(hintText: 'Ex : 5.36000 N, -4.01000 W', isDense: true)),
        ],
      ]),
    );
  }

  // ---------- IA CARD ----------
  Widget _buildIaCard() {
    if (_iaLoading) {
      return Container(
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(color: kOrangeLight, borderRadius: BorderRadius.circular(16)),
        child: const Row(children: [
          SizedBox(width: 18, height: 18, child: CircularProgressIndicator(color: kOrange, strokeWidth: 2.5)),
          SizedBox(width: 14),
          Text('Analyse IA en cours...', style: TextStyle(fontSize: 13, color: kOrange, fontWeight: FontWeight.w600)),
        ]),
      );
    }
    if (_iaResult != null && _iaResult!.detected) {
      final c = kCriticiteColors[_iaResult!.criticite] ?? kOrange;
      return Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          gradient: LinearGradient(begin: Alignment.topLeft, end: Alignment.bottomRight,
            colors: [kOrange.withValues(alpha: 0.08), kOrange.withValues(alpha: 0.02)]),
          border: Border.all(color: kOrange.withValues(alpha: 0.2), width: 1),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Container(width: 34, height: 34, decoration: BoxDecoration(color: kOrange.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(10)),
              child: const Icon(LucideIcons.brain, color: kOrange, size: 18)),
            const SizedBox(width: 10),
            const Expanded(child: Text('Déchets détectés', style: TextStyle(fontWeight: FontWeight.w700, color: kGray800, fontSize: 14))),
            Container(padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(color: c.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(20)),
              child: Text(kCriticiteLabels[_iaResult!.criticite] ?? '', style: TextStyle(color: c, fontSize: 11, fontWeight: FontWeight.w700))),
          ]),
          const SizedBox(height: 12),
          _iaRow(Icons.visibility_rounded, 'Objets', _iaResult!.objets.isEmpty ? '-' : _iaResult!.objets.join(', ')),
          const SizedBox(height: 6),
          _iaRow(LucideIcons.trendingUp, 'Confiance', '${_iaResult!.confiance ?? 0}%'),
          const SizedBox(height: 6),
          _iaRow(Icons.memory_rounded, 'Modèle', 'YOLOv8n + MobileNetV2'),
        ]),
      );
    }
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: kGray100, borderRadius: BorderRadius.circular(16)),
      child: Row(children: [
        const Icon(Icons.info_outline_rounded, color: kGray400, size: 20),
        const SizedBox(width: 12),
        Expanded(child: Text('Prenez une photo pour lancer l\'analyse automatique des déchets',
          style: const TextStyle(fontSize: 12, color: kGray600))),
      ]),
    );
  }

  Widget _iaRow(IconData icon, String label, String value) {
    return Row(children: [
      Icon(icon, size: 14, color: kOrange),
      const SizedBox(width: 8),
      Text(label, style: const TextStyle(fontSize: 11, color: kGray600)),
      const Spacer(),
      Flexible(child: Text(value, textAlign: TextAlign.end, maxLines: 1, overflow: TextOverflow.ellipsis,
        style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: kGray800))),
    ]);
  }

  // ---------- CRITICITE ----------
  Widget _buildCriticiteSelector() {
    return Row(children: kCriticites.map((c) {
      final selected = c == _criticite;
      final color = kCriticiteColors[c] ?? kGray400;
      return Expanded(child: Padding(
        padding: EdgeInsets.only(right: c == kCriticites.last ? 0 : 8),
        child: GestureDetector(
          onTap: () => setState(() => _criticite = c),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 160),
            padding: const EdgeInsets.symmetric(vertical: 14),
            decoration: BoxDecoration(
              color: selected ? color.withValues(alpha: 0.12) : kWhite,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: selected ? color : kGray200, width: selected ? 2 : 1.5),
            ),
            child: Column(children: [
              Icon(selected ? LucideIcons.checkCircle : Icons.circle_outlined, color: selected ? color : kGray400, size: 20),
              const SizedBox(height: 6),
              Text(kCriticiteLabels[c] ?? c, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: selected ? color : kGray600)),
            ]),
          ),
        ),
      ));
    }).toList());
  }

  // ---------- DESCRIPTION ----------
  Widget _buildDescriptionField() {
    return TextField(
      controller: _descriptionController,
      maxLines: 3,
      decoration: const InputDecoration(hintText: 'Ajoutez des précisions (optionnel)...'),
    );
  }

  // ---------- SECTION LABEL ----------
  Widget _sectionLabel(String text, IconData icon) {
    return Row(children: [
      Icon(icon, size: 16, color: kBlue),
      const SizedBox(width: 8),
      Text(text, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: kGray800)),
    ]);
  }

  // ---------- BOTTOM BAR ----------
  Widget _buildBottomBar() {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 20),
      decoration: BoxDecoration(color: kWhite, boxShadow: [BoxShadow(color: kBlack.withValues(alpha: 0.06), blurRadius: 12, offset: const Offset(0, -2))]),
      child: BlocConsumer<SignalementBloc, SignalementState>(
        listener: (context, state) {
          if (state is SignalementCreated) {
            if (_photo != null && state.signalement.id != null) {
              ApiService().uploadPhoto(state.signalement.id!, _photo!.path).catchError((_) => <String, dynamic>{});
            }
            Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => ConfirmationScreen(signalement: state.signalement)));
          }
        },
        builder: (context, state) {
          if (state is SignalementLoading) {
            return const SizedBox(height: 52, child: Center(child: CircularProgressIndicator(color: kBlue)));
          }
          return SizedBox(
            height: 52,
            child: ElevatedButton(
              onPressed: () async {
                final uuid = const Uuid().v4();
                final chantierId = kChantiers.indexOf(_selectedChantier) + 1;
                final s = Signalement(
                  uuidMobile: uuid,
                  typeNuisance: _selectedType,
                  chantierId: chantierId,
                  description: _descriptionController.text,
                  criticite: _criticite,
                  criticiteIa: _hasIa && _iaResult != null ? _iaResult!.criticite : null,
                  confianceIa: _hasIa && _iaResult != null ? _iaResult!.confiance : null,
                  gpsSource: _gpsSource,
                  latitude: _latitude ?? 5.36,
                  longitude: _longitude ?? -4.01,
                );
                await LocalDatabase().insertSignalement(s);
                if (!context.mounted) return;
                context.read<SignalementBloc>().add(CreateSignalement(s));
                context.read<SyncBloc>().add(CheckPendingCount());
              },
              child: const Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                Icon(Icons.send_rounded, size: 20), SizedBox(width: 10), Text('Enregistrer le signalement'),
              ]),
            ),
          );
        },
      ),
    );
  }
}
