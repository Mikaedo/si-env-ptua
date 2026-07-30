import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../core/constants.dart';

class FiltersScreen extends StatefulWidget {
  final Map<String, dynamic>? initial;
  const FiltersScreen({super.key, this.initial});

  @override
  State<FiltersScreen> createState() => _FiltersScreenState();
}

class _FiltersScreenState extends State<FiltersScreen> {
  String? _statut;
  String? _criticite;
  String? _typeNuisance;
  int? _chantierId;
  int? _periodeJours;

  @override
  void initState() {
    super.initState();
    final init = widget.initial ?? {};
    _statut = init['statut'];
    _criticite = init['criticite'];
    _typeNuisance = init['typeNuisance'];
    _chantierId = init['chantierId'];
    _periodeJours = init['periodeJours'];
  }

  void _reset() => setState(() {
        _statut = null;
        _criticite = null;
        _typeNuisance = null;
        _chantierId = null;
        _periodeJours = null;
      });

  int _activeCount() =>
      [_statut, _criticite, _typeNuisance, _chantierId, _periodeJours].where((e) => e != null).length;

  @override
  Widget build(BuildContext context) {
    final count = _activeCount();
    return Scaffold(
      backgroundColor: kGray50,
      appBar: AppBar(
        backgroundColor: kGray50,
        leading: IconButton(icon: const Icon(LucideIcons.x), onPressed: () => Navigator.pop(context)),
        title: const Text('Filtres'),
        actions: [
          if (count > 0)
            TextButton(onPressed: _reset, child: const Text('Réinitialiser', style: TextStyle(color: kOrange, fontWeight: FontWeight.w600))),
        ],
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
          children: [
            // Statut
            _Section(
              icon: LucideIcons.flag,
              title: 'Statut',
              child: _ChipGroup(
                options: const {'NOUVEAU': 'Nouveau', 'EN_TRAITEMENT': 'En cours', 'CLOTURE': 'Traité', 'REJETE': 'Rejeté'},
                selected: _statut,
                colorOf: (k) => kStatutColors[k],
                onSelected: (v) => setState(() => _statut = v),
              ),
            ),
            // Criticité
            _Section(
              icon: LucideIcons.shield,
              title: 'Criticité',
              child: _ChipGroup(
                options: const {'FAIBLE': 'Faible', 'MODERE': 'Modéré', 'ELEVE': 'Élevé'},
                selected: _criticite,
                colorOf: (k) => kCriticiteColors[k],
                onSelected: (v) => setState(() => _criticite = v),
              ),
            ),
            // Type de nuisance
            _Section(
              icon: LucideIcons.tags,
              title: 'Type de nuisance',
              child: _ChipGroup(
                options: {for (final t in kNuisanceTypes) t: t},
                selected: _typeNuisance,
                onSelected: (v) => setState(() => _typeNuisance = v),
              ),
            ),
            // Chantier
            _Section(
              icon: LucideIcons.hardHat,
              title: 'Chantier',
              child: _ChipGroup(
                options: {for (int i = 0; i < kChantiers.length; i++) '${i + 1}': kChantiers[i]},
                selected: _chantierId?.toString(),
                onSelected: (v) => setState(() => _chantierId = v == null ? null : int.parse(v)),
              ),
            ),
            // Période
            _Section(
              icon: Icons.schedule_rounded,
              title: 'Période',
              child: _ChipGroup(
                options: const {'7': '7 jours', '30': '30 jours', '90': '3 mois'},
                selected: _periodeJours?.toString(),
                onSelected: (v) => setState(() => _periodeJours = v == null ? null : int.parse(v)),
              ),
            ),
          ],
        ),
      ),
      bottomNavigationBar: Container(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 20),
        decoration: BoxDecoration(color: kWhite, boxShadow: [BoxShadow(color: kBlack.withValues(alpha: 0.06), blurRadius: 12, offset: const Offset(0, -2))]),
        child: SizedBox(
          height: 52,
          child: ElevatedButton(
            onPressed: () => Navigator.pop(context, {
              'statut': _statut,
              'criticite': _criticite,
              'typeNuisance': _typeNuisance,
              'chantierId': _chantierId,
              'periodeJours': _periodeJours,
            }),
            child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
              const Icon(Icons.check_rounded, size: 20),
              const SizedBox(width: 8),
              Text(count > 0 ? 'Appliquer ($count)' : 'Appliquer les filtres', style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
            ]),
          ),
        ),
      ),
    );
  }
}

class _Section extends StatelessWidget {
  final IconData icon;
  final String title;
  final Widget child;
  const _Section({required this.icon, required this.title, required this.child});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: kWhite, borderRadius: BorderRadius.circular(16), border: Border.all(color: kGray200, width: 1)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Container(width: 30, height: 30, decoration: BoxDecoration(color: kBlue.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(8)),
            child: Icon(icon, size: 16, color: kBlue)),
          const SizedBox(width: 10),
          Text(title, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: kGray800)),
        ]),
        const SizedBox(height: 12),
        child,
      ]),
    );
  }
}

/// Toggleable chip group. Tapping the selected chip deselects it (returns null).
class _ChipGroup extends StatelessWidget {
  final Map<String, String> options; // value -> label
  final String? selected;
  final ValueChanged<String?> onSelected;
  final Color? Function(String key)? colorOf;
  const _ChipGroup({required this.options, required this.selected, required this.onSelected, this.colorOf});

  @override
  Widget build(BuildContext context) {
    return Wrap(spacing: 8, runSpacing: 8, children: options.entries.map((e) {
      final isSel = e.key == selected;
      final c = colorOf?.call(e.key) ?? kBlue;
      return GestureDetector(
        onTap: () => onSelected(isSel ? null : e.key),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 140),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
          decoration: BoxDecoration(
            color: isSel ? c : kGray100,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: isSel ? c : kGray200, width: 1),
          ),
          child: Text(e.value, style: TextStyle(fontSize: 12.5, fontWeight: FontWeight.w600, color: isSel ? kWhite : kGray600)),
        ),
      );
    }).toList());
  }
}
