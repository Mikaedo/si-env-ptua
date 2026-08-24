import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:flutter/services.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../core/constants.dart';
import '../widgets/ptua_logo.dart';
import 'nouveau_signalement_screen.dart';

class MapScreen extends StatefulWidget {
  const MapScreen({super.key});

  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  List<Polygon> _zones = [];
  List<Marker> _markers = [];
  List<_ChantierData> _chantiers = [];
  bool _loading = true;
  int _selectedChantier = -1;
  bool _satelliteMode = false;
  String _zoneFilter = 'Toutes';
  final MapController _mapController = MapController();

  static const _projetColors = <String, Color>{
    '4EME_PONT': Color(0xFFE8770E),
    'Y4': Color(0xFF1B2A4E),
    'LATRILLE': Color(0xFF7B1FA2),
    'SORTIE_EST': Color(0xFF00838F),
    'SORTIE_OUEST': Color(0xFFC62828),
    'ECHANGEURS_CG': Color(0xFF2E7D32),
  };

  // Doit correspondre mot pour mot aux entrees de kChantiers (constants.dart) :
  // le libelle tape sur la carte est transmis tel quel a l'ecran de
  // signalement, qui le retrouve par egalite de chaine dans cette liste.
  static const _projetLabels = <String, String>{
    '4EME_PONT': "4e Pont d'Abidjan",
    'Y4': 'Rocade Y4',
    'LATRILLE': 'Bd Latrille',
    'SORTIE_EST': 'Sortie Est',
    'SORTIE_OUEST': 'Sortie Ouest',
    'ECHANGEURS_CG': 'Echangeurs CG',
  };

  @override
  void initState() {
    super.initState();
    _loadZones();
  }

  Future<void> _loadZones() async {
    try {
      final jsonString = await rootBundle.loadString('assets/shapefile/zones_ptua.geojson');
      final geojson = jsonDecode(jsonString) as Map<String, dynamic>;
      final features = geojson['features'] as List;
      final polygons = <Polygon>[];
      final markers = <Marker>[];
      final chantiers = <_ChantierData>[];

      for (int i = 0; i < features.length; i++) {
        final feature = features[i];
        final props = feature['properties'] as Map<String, dynamic>;
        final nom = props['nom'] as String? ?? 'Zone chantier';
        final coords = feature['geometry']['coordinates'][0] as List;
        final points = coords.map((c) => LatLng((c[1] as num).toDouble(), (c[0] as num).toDouble())).toList();

        final projet = props['projet'] as String? ?? '';
        final zoneColor = _projetColors[projet] ?? kBlue;
        final label = _projetLabels[projet] ?? nom;

        double sumLat = 0, sumLng = 0;
        for (final p in points) {
          sumLat += p.latitude;
          sumLng += p.longitude;
        }
        final center = LatLng(sumLat / points.length, sumLng / points.length);

        polygons.add(Polygon(
          points: points,
          color: zoneColor.withValues(alpha: 0.15),
          borderColor: zoneColor,
          borderStrokeWidth: 2,
          label: nom,
        ));

        markers.add(Marker(
          point: center,
          width: 50,
          height: 60,
          child: GestureDetector(
            onTap: () => setState(() => _selectedChantier = i),
            child: _ChantierPin(
              label: label,
              color: zoneColor,
              isSelected: _selectedChantier == i,
            ),
          ),
        ));

        chantiers.add(_ChantierData(
          index: i,
          nom: nom,
          label: label,
          projet: projet,
          color: zoneColor,
          center: center,
        ));
      }

      setState(() {
        _zones = polygons;
        _markers = markers;
        _chantiers = chantiers;
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  List<Polygon> get _filteredZones {
    if (_zoneFilter == 'Toutes') return _zones;
    final filtered = <Polygon>[];
    for (final c in _chantiers) {
      if (c.label == _zoneFilter) {
        filtered.add(_zones[c.index]);
      }
    }
    return filtered;
  }

  List<Marker> get _filteredMarkers {
    if (_zoneFilter == 'Toutes') return _markers;
    final filtered = <Marker>[];
    for (final c in _chantiers) {
      if (c.label == _zoneFilter) {
        filtered.add(_markers[c.index]);
      }
    }
    return filtered;
  }

  void _flyToChantier(_ChantierData c) {
    _mapController.move(c.center, 14.0);
    setState(() => _selectedChantier = c.index);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          if (_loading)
            const Center(child: CircularProgressIndicator(color: kBlue))
          else
            FlutterMap(
              mapController: _mapController,
              options: MapOptions(
                initialCenter: const LatLng(5.36, -4.02),
                initialZoom: 11.5,
                onTap: (_, __) => setState(() => _selectedChantier = -1),
              ),
              children: [
                TileLayer(
                  // La cle change avec le mode : force flutter_map a
                  // re-instancier le layer et vider son cache de tiles,
                  // sans quoi le switch Plan/Satellite ne rechargeait rien.
                  key: ValueKey(_satelliteMode),
                  urlTemplate: _satelliteMode
                      ? 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
                      : 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
                  subdomains: _satelliteMode ? const ['a'] : const ['a', 'b', 'c', 'd'],
                  userAgentPackageName: 'ci.ageroute.sienv',
                ),
                PolygonLayer(polygons: _filteredZones),
                MarkerLayer(markers: _filteredMarkers),
              ],
            ),
          // Top bar
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            child: Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [kBlueDark.withValues(alpha: 0.9), Colors.transparent],
                  stops: const [0.0, 1.0],
                ),
              ),
              padding: const EdgeInsets.only(top: 12, left: 16, right: 8, bottom: 24),
              child: SafeArea(
                bottom: false,
                child: Row(
                  children: [
                    Container(
                      margin: const EdgeInsets.only(right: 10),
                      child: const PtuaLogo(size: 36),
                    ),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text('Carte des chantiers', style: TextStyle(
                            fontSize: 15, fontWeight: FontWeight.w700, color: kWhite,
                          ), maxLines: 1, overflow: TextOverflow.ellipsis),
                          Text('PTUA • Abidjan', style: TextStyle(
                            fontSize: 10, color: kWhite.withValues(alpha: 0.7),
                          ), maxLines: 1, overflow: TextOverflow.ellipsis),
                        ],
                      ),
                    ),
                    Stack(children: [
                      IconButton(
                        onPressed: () => Navigator.pushNamed(context, '/alertes'),
                        icon: Icon(Icons.notifications_outlined, color: kWhite.withValues(alpha: 0.9), size: 22),
                      ),
                      Positioned(top: 6, right: 6, child: Container(
                        width: 8, height: 8,
                        decoration: BoxDecoration(color: kOrange, shape: BoxShape.circle, border: Border.all(color: kBlueDark, width: 2)),
                      )),
                    ]),
                  ],
                ),
              ),
            ),
          ),
          // Zone filter button - right side
          Positioned(
            top: 120,
            right: 16,
            child: GestureDetector(
              onTap: () => _showZoneFilter(context),
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: kWhite,
                  borderRadius: BorderRadius.circular(14),
                  boxShadow: [BoxShadow(color: kBlack.withValues(alpha: 0.15), blurRadius: 12, offset: const Offset(0, 4))],
                ),
                child: Column(
                  children: [
                    Icon(Icons.filter_alt_rounded, color: kOrange, size: 22),
                    const SizedBox(height: 2),
                    Text('Zones', style: TextStyle(fontSize: 9, fontWeight: FontWeight.w600, color: kGray800)),
                  ],
                ),
              ),
            ),
          ),
          // Satellite toggle - right side below Zones
          Positioned(
            top: 190,
            right: 16,
            child: GestureDetector(
              onTap: () => setState(() => _satelliteMode = !_satelliteMode),
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: kWhite,
                  borderRadius: BorderRadius.circular(14),
                  boxShadow: [BoxShadow(color: kBlack.withValues(alpha: 0.15), blurRadius: 12, offset: const Offset(0, 4))],
                ),
                child: Column(
                  children: [
                    Icon(_satelliteMode ? Icons.satellite_alt_rounded : Icons.map_outlined,
                        color: _satelliteMode ? kOrange : kBlue, size: 22),
                    const SizedBox(height: 2),
                    Text(_satelliteMode ? 'Satellite' : 'Plan',
                        style: TextStyle(fontSize: 9, fontWeight: FontWeight.w600, color: kGray800)),
                  ],
                ),
              ),
            ),
          ),
          // Active zone filter chip
          if (_zoneFilter != 'Toutes')
            Positioned(
              top: 120,
              left: 16,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: kOrange,
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: [BoxShadow(color: kOrange.withValues(alpha: 0.3), blurRadius: 8)],
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(_zoneFilter, style: const TextStyle(color: kWhite, fontSize: 12, fontWeight: FontWeight.w600)),
                    const SizedBox(width: 6),
                    GestureDetector(
                      onTap: () => setState(() => _zoneFilter = 'Toutes'),
                      child: const Icon(LucideIcons.x, color: kWhite, size: 16),
                    ),
                  ],
                ),
              ),
            ),
          // Bottom sheet
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: AnimatedSwitcher(
              duration: const Duration(milliseconds: 300),
              child: _selectedChantier >= 0 && _selectedChantier < _chantiers.length
                  ? _ChantierInfoSheet(
                      key: ValueKey(_selectedChantier),
                      chantier: _chantiers[_selectedChantier],
                      onClose: () => setState(() => _selectedChantier = -1),
                      onNavigate: () => Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => NouveauSignalementScreen(
                            typeNuisance: 'Déchets de chantier',
                            chantierInitial: _chantiers[_selectedChantier].label,
                          ),
                        ),
                      ),
                    )
                  : _LegendSheet(
                      key: const ValueKey('legend'),
                      onChantierTap: (c) => _flyToChantier(c),
                      chantiers: _chantiers,
                    ),
            ),
          ),
        ],
      ),
    );
  }

  void _showZoneFilter(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: kWhite,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (ctx) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(Icons.filter_alt_rounded, color: kOrange, size: 22),
                  const SizedBox(width: 8),
                  Text('Filtrer par zone', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: kGray800)),
                ],
              ),
              const SizedBox(height: 16),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  _ZoneChip(
                    label: 'Toutes',
                    color: kBlue,
                    isSelected: _zoneFilter == 'Toutes',
                    onTap: () { setState(() => _zoneFilter = 'Toutes'); Navigator.pop(ctx); },
                  ),
                  ..._chantiers.map((c) => _ZoneChip(
                    label: c.label,
                    color: c.color,
                    isSelected: _zoneFilter == c.label,
                    onTap: () { setState(() => _zoneFilter = c.label); _flyToChantier(c); Navigator.pop(ctx); },
                  )),
                ],
              ),
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }
}

class _ChantierData {
  final int index;
  final String nom;
  final String label;
  final String projet;
  final Color color;
  final LatLng center;

  const _ChantierData({
    required this.index,
    required this.nom,
    required this.label,
    required this.projet,
    required this.color,
    required this.center,
  });
}

class _ChantierPin extends StatelessWidget {
  final String label;
  final Color color;
  final bool isSelected;
  const _ChantierPin({required this.label, required this.color, required this.isSelected});

  @override
  Widget build(BuildContext context) {
    return Stack(
      alignment: Alignment.bottomCenter,
      children: [
        // Pin body - circle with icon
        AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          width: isSelected ? 44 : 36,
          height: isSelected ? 44 : 36,
          decoration: BoxDecoration(
            color: color,
            shape: BoxShape.circle,
            border: Border.all(color: kWhite, width: 2.5),
            boxShadow: [
              BoxShadow(color: color.withValues(alpha: 0.5), blurRadius: isSelected ? 16 : 8, offset: const Offset(0, 4)),
            ],
          ),
          child: Icon(LucideIcons.hardHat, color: kWhite, size: isSelected ? 22 : 18),
        ),
        // Pin pointer - rotated square
        Transform.translate(
          offset: const Offset(0, 4),
          child: Transform.rotate(
            angle: 0.785,
            child: Container(
              width: 10, height: 10,
              decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(2)),
            ),
          ),
        ),
        // Label on selected
        if (isSelected)
          Positioned(
            top: -28,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: kBlueDark,
                borderRadius: BorderRadius.circular(8),
                boxShadow: [BoxShadow(color: kBlack.withValues(alpha: 0.2), blurRadius: 6)],
              ),
              child: Text(label, style: const TextStyle(color: kWhite, fontSize: 10, fontWeight: FontWeight.w600)),
            ),
          ),
      ],
    );
  }
}

class _ZoneChip extends StatelessWidget {
  final String label;
  final Color color;
  final bool isSelected;
  final VoidCallback onTap;
  const _ZoneChip({required this.label, required this.color, required this.isSelected, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? color : color.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: color, width: 1.5),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(width: 8, height: 8, decoration: BoxDecoration(color: isSelected ? kWhite : color, shape: BoxShape.circle)),
            const SizedBox(width: 6),
            Text(label, style: TextStyle(
              color: isSelected ? kWhite : color,
              fontSize: 12,
              fontWeight: FontWeight.w600,
            )),
          ],
        ),
      ),
    );
  }
}

class _LegendSheet extends StatelessWidget {
  final void Function(_ChantierData) onChantierTap;
  final List<_ChantierData> chantiers;
  const _LegendSheet({super.key, required this.onChantierTap, required this.chantiers});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 0, 16, 16),
      decoration: BoxDecoration(
        color: kWhite,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [BoxShadow(color: kBlack.withValues(alpha: 0.15), blurRadius: 20, offset: const Offset(0, 8))],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Row(
              children: [
                Icon(Icons.layers_rounded, color: kBlue, size: 18),
                const SizedBox(width: 8),
                Text('Zones PTUA', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: kGray800)),
                const Spacer(),
                Text('${chantiers.length} chantiers', style: const TextStyle(fontSize: 11, color: kGray600)),
              ],
            ),
          ),
          const Divider(height: 1),
          SizedBox(
            height: 56,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              itemCount: chantiers.length,
              itemBuilder: (_, i) {
                final c = chantiers[i];
                return GestureDetector(
                  onTap: () => onChantierTap(c),
                  child: Container(
                    margin: const EdgeInsets.only(right: 8),
                    padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 5),
                    decoration: BoxDecoration(
                      color: c.color.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: c.color.withValues(alpha: 0.3), width: 1),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Container(width: 10, height: 10, decoration: BoxDecoration(color: c.color, borderRadius: BorderRadius.circular(3))),
                        const SizedBox(width: 6),
                        Text(c.label, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: c.color)),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _ChantierInfoSheet extends StatelessWidget {
  final _ChantierData chantier;
  final VoidCallback onClose;
  final VoidCallback onNavigate;
  const _ChantierInfoSheet({super.key, required this.chantier, required this.onClose, required this.onNavigate});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 0, 16, 16),
      decoration: BoxDecoration(
        color: kWhite,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [BoxShadow(color: kBlack.withValues(alpha: 0.15), blurRadius: 20, offset: const Offset(0, 8))],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            height: 6,
            decoration: BoxDecoration(
              color: chantier.color,
              borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      width: 44, height: 44,
                      decoration: BoxDecoration(color: chantier.color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(14)),
                      child: Icon(LucideIcons.hardHat, color: chantier.color, size: 22),
                    ),
                    const SizedBox(width: 12),
                    Expanded(child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(chantier.label, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: kGray800)),
                        Text(chantier.nom, style: const TextStyle(fontSize: 11, color: kGray600)),
                      ],
                    )),
                    IconButton(
                      onPressed: onClose,
                      icon: const Icon(LucideIcons.x, color: kGray400, size: 20),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    _MiniStat(icon: LucideIcons.flag, label: 'Actif', color: chantier.color),
                    const SizedBox(width: 16),
                    _MiniStat(icon: LucideIcons.mapPin, label: 'Abidjan', color: chantier.color),
                    const SizedBox(width: 16),
                    _MiniStat(icon: Icons.eco_outlined, label: 'Suivi env.', color: chantier.color),
                  ],
                ),
                const SizedBox(height: 14),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton(
                        onPressed: onClose,
                        style: OutlinedButton.styleFrom(
                          foregroundColor: chantier.color,
                          side: BorderSide(color: chantier.color.withValues(alpha: 0.3)),
                        ),
                        child: const Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                          Icon(Icons.visibility_outlined, size: 16),
                          SizedBox(width: 6),
                          Text('Fermer'),
                        ]),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: ElevatedButton(
                        onPressed: onNavigate,
                        style: ElevatedButton.styleFrom(backgroundColor: chantier.color),
                        child: const Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                          Icon(Icons.add_rounded, size: 16, color: kWhite),
                          SizedBox(width: 6),
                          Text('Signaler'),
                        ]),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _MiniStat extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  const _MiniStat({required this.icon, required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Row(mainAxisSize: MainAxisSize.min, children: [
      Icon(icon, size: 14, color: color),
      const SizedBox(width: 4),
      Text(label, style: const TextStyle(fontSize: 11, color: kGray600, fontWeight: FontWeight.w500)),
    ]);
  }
}
