import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../widgets/ptua_logo.dart';
import '../core/constants.dart';
import '../services/api_service.dart';
import '../models/models.dart';

class StatsScreen extends StatefulWidget {
  const StatsScreen({super.key});

  @override
  State<StatsScreen> createState() => _StatsScreenState();
}

class _StatsScreenState extends State<StatsScreen> with TickerProviderStateMixin {
  Statistiques? _stats;
  bool _loading = true;
  bool _hasError = false;
  late AnimationController _animCtrl;

  @override
  void initState() {
    super.initState();
    _animCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 700));
    _loadStats();
  }

  @override
  void dispose() {
    _animCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadStats() async {
    setState(() { _loading = true; _hasError = false; });
    try {
      final s = await ApiService().getStatistiques();
      if (!mounted) return;
      setState(() { _stats = s; _loading = false; });
      _animCtrl.forward(from: 0);
    } catch (e) {
      debugPrint('Stats error: $e');
      if (mounted) setState(() { _loading = false; _hasError = true; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kGray50,
      appBar: AppBar(
        backgroundColor: kBlue,
        titleSpacing: 0,
        title: Row(children: [
          Container(margin: const EdgeInsets.only(left: 16, right: 10), child: const PtuaLogo(size: 30)),
          const Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
              Text('Tableau de bord', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: kWhite)),
              Text('Statistiques environnementales', style: TextStyle(fontSize: 11, color: Color(0xAAFFFFFF))),
            ]),
          ),
        ]),
        actions: [
          IconButton(
            onPressed: _loadStats,
            icon: const Icon(LucideIcons.refreshCw, color: kWhite, size: 20),
          ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_loading) {
      return const Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
        CircularProgressIndicator(color: kBlue, strokeWidth: 3),
        SizedBox(height: 16),
        Text('Chargement...', style: TextStyle(fontSize: 13, color: kGray500)),
      ]));
    }

    if (_hasError || _stats == null) {
      return Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
        Container(width: 72, height: 72,
          decoration: BoxDecoration(color: kRedLight, borderRadius: BorderRadius.circular(22)),
          child: const Icon(LucideIcons.cloudOff, color: kRed, size: 32)),
        const SizedBox(height: 16),
        const Text('Données indisponibles', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: kGray800)),
        const SizedBox(height: 8),
        const Text('Vérifiez votre connexion\net reconnectez-vous si nécessaire.',
          textAlign: TextAlign.center, style: TextStyle(fontSize: 13, color: kGray500)),
        const SizedBox(height: 24),
        SizedBox(width: 180, child: ElevatedButton.icon(
          onPressed: _loadStats,
          icon: const Icon(LucideIcons.refreshCw, size: 16),
          label: const Text('Réessayer'),
        )),
      ]));
    }

    final s = _stats!;
    return RefreshIndicator(
      color: kBlue,
      onRefresh: _loadStats,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
        children: [
          _heroCard(s),
          const SizedBox(height: 14),
          _kpiRow(s),
          const SizedBox(height: 14),
          _tauxCard(s),
          const SizedBox(height: 14),
          _repartitionCard(s),
          const SizedBox(height: 14),
          _evolutionCard(s),
        ],
      ),
    );
  }

  Widget _heroCard(Statistiques s) {
    return Container(
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft, end: Alignment.bottomRight,
          colors: [kBlue, kBlueDark],
        ),
        borderRadius: BorderRadius.circular(22),
        boxShadow: [BoxShadow(color: kBlue.withValues(alpha: 0.3), blurRadius: 20, offset: const Offset(0, 8))],
      ),
      child: Row(children: [
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(color: kWhite.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(20)),
            child: Text('Total signalements', style: TextStyle(fontSize: 11, color: kWhite.withValues(alpha: 0.9), fontWeight: FontWeight.w600)),
          ),
          const SizedBox(height: 12),
          Text('${s.total}', style: const TextStyle(fontSize: 52, fontWeight: FontWeight.w900, color: kWhite, height: 1)),
          const SizedBox(height: 8),
          Row(children: [
            const Icon(LucideIcons.trendingUp, size: 14, color: Color(0xFF81C784)),
            const SizedBox(width: 6),
            Text('${s.tauxTraitement.round()}% de taux de traitement',
              style: const TextStyle(fontSize: 12, color: Color(0xFF81C784), fontWeight: FontWeight.w700)),
          ]),
        ])),
        const SizedBox(width: 16),
        _ringGauge(percent: s.tauxTraitement / 100),
      ]),
    );
  }

  Widget _ringGauge({required double percent}) {
    return SizedBox(width: 90, height: 90,
      child: Stack(alignment: Alignment.center, children: [
        SizedBox(width: 90, height: 90,
          child: CircularProgressIndicator(
            value: percent.clamp(0, 1), strokeWidth: 9,
            backgroundColor: kWhite.withValues(alpha: 0.15),
            valueColor: const AlwaysStoppedAnimation(kOrange),
          )),
        Column(mainAxisSize: MainAxisSize.min, children: [
          Text('${(percent * 100).round()}%', style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w900, color: kWhite)),
          const Text('traité', style: TextStyle(fontSize: 9, color: Color(0xAAFFFFFF))),
        ]),
      ]),
    );
  }

  Widget _kpiRow(Statistiques s) {
    return Row(children: [
      _kpi('Traités', s.traites, LucideIcons.checkCircle, const Color(0xFF2E7D32), const Color(0xFFE8F5E9)),
      const SizedBox(width: 10),
      _kpi('En attente', s.enAttente, LucideIcons.clock, kOrange, kOrangeLight),
      const SizedBox(width: 10),
      _kpi('Urgents', s.urgents, LucideIcons.alertTriangle, kRed, kRedLight),
    ]);
  }

  Widget _kpi(String label, int value, IconData icon, Color color, Color bg) {
    return Expanded(child: Container(
      padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 10),
      decoration: BoxDecoration(color: kWhite, borderRadius: BorderRadius.circular(18), border: Border.all(color: kGray200)),
      child: Column(children: [
        Container(width: 42, height: 42, decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(13)),
          child: Icon(icon, color: color, size: 22)),
        const SizedBox(height: 10),
        Text('$value', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900, color: color)),
        const SizedBox(height: 2),
        Text(label, style: const TextStyle(fontSize: 10, color: kGray500, fontWeight: FontWeight.w600)),
      ]),
    ));
  }

  Widget _tauxCard(Statistiques s) {
    final pct = (s.tauxTraitement / 100).clamp(0.0, 1.0);
    return _CardShell(icon: LucideIcons.activity, title: 'Taux de traitement',
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          Text('${s.traites} / ${s.total} traités', style: const TextStyle(fontSize: 12, color: kGray500)),
          Container(padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
            decoration: BoxDecoration(color: kBlueLight, borderRadius: BorderRadius.circular(20)),
            child: Text('${s.tauxTraitement.round()}%', style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w800, color: kBlue))),
        ]),
        const SizedBox(height: 12),
        ClipRRect(borderRadius: BorderRadius.circular(6),
          child: LinearProgressIndicator(value: pct, minHeight: 12, backgroundColor: kGray100, color: kBlue)),
      ]));
  }

  Widget _repartitionCard(Statistiques s) {
    const palette = [kBlue, kOrange, Color(0xFF1565C0), Color(0xFF6A1B9A), Color(0xFF00897B)];
    final entries = s.repartition.entries.toList();
    final maxV = entries.isEmpty ? 1 : entries.map((e) => e.value).reduce((a, b) => a > b ? a : b);
    return _CardShell(icon: LucideIcons.pieChart, title: 'Répartition par nuisance',
      child: entries.isEmpty
          ? const Padding(padding: EdgeInsets.symmetric(vertical: 12),
              child: Text('Aucune donnée', style: TextStyle(fontSize: 12, color: kGray400)))
          : Column(children: [
              for (int i = 0; i < entries.length; i++)
                _repRow(entries[i].key, entries[i].value, maxV, palette[i % palette.length], s.total),
            ]));
  }

  Widget _repRow(String label, int count, int maxV, Color color, int total) {
    final pct = maxV > 0 ? count / maxV : 0.0;
    final share = total > 0 ? (count / total * 100).round() : 0;
    return Padding(padding: const EdgeInsets.only(bottom: 10),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          Row(children: [
            Container(width: 10, height: 10, decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(3))),
            const SizedBox(width: 8),
            Text(label, style: const TextStyle(fontSize: 12, color: kGray800, fontWeight: FontWeight.w600)),
          ]),
          Text('$count • $share%', style: const TextStyle(fontSize: 11, color: kGray500)),
        ]),
        const SizedBox(height: 6),
        ClipRRect(borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(value: pct, minHeight: 8, backgroundColor: kGray100, color: color)),
      ]));
  }

  Widget _evolutionCard(Statistiques s) {
    final entries = s.evolution.entries.toList();
    final maxV = entries.isEmpty ? 1 : entries.map((e) => e.value).reduce((a, b) => a > b ? a : b);
    return _CardShell(icon: LucideIcons.barChart2, title: 'Évolution mensuelle',
      child: entries.isEmpty
          ? const Padding(padding: EdgeInsets.symmetric(vertical: 12),
              child: Text('Aucune donnée', style: TextStyle(fontSize: 12, color: kGray400)))
          : SizedBox(height: 140,
              child: Row(crossAxisAlignment: CrossAxisAlignment.end, mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: entries.map((e) {
                  final month = e.key.contains('-') ? e.key.split('-')[1] : e.key;
                  return _barCol(month, e.value, maxV);
                }).toList())));
  }

  Widget _barCol(String label, int value, int maxV) {
    final h = maxV > 0 ? (value / maxV * 90) : 0.0;
    return Column(mainAxisAlignment: MainAxisAlignment.end, children: [
      Text('$value', style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: kGray600)),
      const SizedBox(height: 4),
      AnimatedBuilder(animation: _animCtrl, builder: (_, __) => Container(
        width: 24, height: (h * _animCtrl.value).clamp(4, 90),
        decoration: BoxDecoration(
          gradient: const LinearGradient(begin: Alignment.topCenter, end: Alignment.bottomCenter, colors: [kOrange, kBlue]),
          borderRadius: const BorderRadius.vertical(top: Radius.circular(6))),
      )),
      const SizedBox(height: 6),
      Text(label, style: const TextStyle(fontSize: 10, color: kGray500, fontWeight: FontWeight.w500)),
    ]);
  }
}

class _CardShell extends StatelessWidget {
  final IconData icon;
  final String title;
  final Widget child;
  const _CardShell({required this.icon, required this.title, required this.child});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: kWhite, borderRadius: BorderRadius.circular(20),
        border: Border.all(color: kGray200),
        boxShadow: const [BoxShadow(color: kShadowColor, blurRadius: 8, offset: Offset(0, 2))],
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Container(width: 36, height: 36,
            decoration: BoxDecoration(color: kBlueLight, borderRadius: BorderRadius.circular(11)),
            child: Icon(icon, size: 18, color: kBlue)),
          const SizedBox(width: 10),
          Text(title, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: kGray800)),
        ]),
        const SizedBox(height: 16),
        child,
      ]),
    );
  }
}
