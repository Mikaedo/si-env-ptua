import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../blocs/signalement/signalement_bloc.dart';
import '../core/constants.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../widgets/ptua_logo.dart';
import 'signalement_detail_screen.dart';
import 'filters_screen.dart';
import 'nouveau_signalement_screen.dart';

class SignalementsListScreen extends StatefulWidget {
  const SignalementsListScreen({super.key});

  @override
  State<SignalementsListScreen> createState() => _SignalementsListScreenState();
}

class _SignalementsListScreenState extends State<SignalementsListScreen>
    with SingleTickerProviderStateMixin {
  final _searchController = TextEditingController();
  Map<String, dynamic> _activeFilters = {};
  int _total = 0;
  int _nouveaux = 0;
  int _enCours = 0;
  int _traites = 0;
  bool _statsLoading = true;
  String _userRole = '';
  bool _isExpert = false;
  Timer? _refreshTimer;
  late AnimationController _animCtrl;
  late Animation<double> _fadeAnim;

  @override
  void initState() {
    super.initState();
    _userRole = ApiService().role ?? '';
    _isExpert = _userRole == 'EXPERT_HSE';
    _loadWithFilters();
    _loadStats();
    _animCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 600));
    _fadeAnim = CurvedAnimation(parent: _animCtrl, curve: Curves.easeOut);
    _animCtrl.forward();
    _refreshTimer = Timer.periodic(const Duration(seconds: 10), (_) {
      _loadWithFilters();
      _loadStats();
    });
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    _searchController.dispose();
    _animCtrl.dispose();
    super.dispose();
  }

  void _loadWithFilters() {
    context.read<SignalementBloc>().add(LoadSignalements(
      statut: _activeFilters['statut'],
      criticite: _activeFilters['criticite'],
      typeNuisance: _activeFilters['typeNuisance'],
      chantierId: _activeFilters['chantierId'],
      periodeJours: _activeFilters['periodeJours'],
    ));
  }

  Future<void> _loadStats() async {
    try {
      final stats = await ApiService().getStatistiques();
      if (!mounted) return;
      setState(() {
        _total = stats.total;
        _traites = stats.traites;
        _enCours = stats.enAttente;
        _nouveaux = stats.total - stats.traites - stats.enAttente;
        if (_nouveaux < 0) _nouveaux = 0;
        _statsLoading = false;
      });
    } catch (_) {
      if (mounted) setState(() => _statsLoading = false);
    }
  }

  String _filterLabel(String key, dynamic value) {
    switch (key) {
      case 'statut': return kStatutLabels[value] ?? '$value';
      case 'criticite': return kCriticiteLabels[value] ?? '$value';
      case 'chantierId':
        final idx = (value as int) - 1;
        return idx >= 0 && idx < kChantiers.length ? kChantiers[idx] : 'Chantier $value';
      case 'periodeJours': return '$value j';
      default: return '$value';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kGray50,
      appBar: AppBar(
        backgroundColor: kBlue,
        elevation: 0,
        titleSpacing: 0,
        title: Row(
          children: [
            Container(margin: const EdgeInsets.only(left: 16, right: 10), child: const PtuaLogo(size: 30)),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    _userRole == 'RESP_ENV' ? 'Mes signalements' : 'File à traiter',
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: kWhite),
                  ),
                  Text(
                    'Plateforme AGEROUTE',
                    style: TextStyle(fontSize: 11, color: kWhite.withValues(alpha: 0.7)),
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          _filterButton(),
          const SizedBox(width: 8),
        ],
      ),
      body: Column(
        children: [
          _buildSearchBar(),
          if (_activeFilters.isNotEmpty) _buildFilterChips(),
          if (_isExpert) _buildPendingBanner(),
          Expanded(child: _buildList()),
        ],
      ),
    );
  }

  Widget _filterButton() {
    return GestureDetector(
      onTap: _openFilters,
      child: Container(
        margin: const EdgeInsets.only(right: 8),
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: _activeFilters.isEmpty ? kWhite.withValues(alpha: 0.15) : kOrange,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Stack(
          clipBehavior: Clip.none,
          children: [
            const Icon(LucideIcons.sliders, color: kWhite, size: 20),
            if (_activeFilters.isNotEmpty)
              Positioned(
                top: -4, right: -4,
                child: Container(
                  width: 8, height: 8,
                  decoration: const BoxDecoration(color: kWhite, shape: BoxShape.circle),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Future<void> _openFilters() async {
    final result = await Navigator.push(context,
        MaterialPageRoute(builder: (_) => FiltersScreen(initial: _activeFilters)));
    if (result != null && result is Map<String, dynamic>) {
      setState(() => _activeFilters = result);
      _loadWithFilters();
    }
  }

  Widget _buildSearchBar() {
    return Container(
      color: kBlue,
      child: Container(
        decoration: const BoxDecoration(
          color: kGray50,
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
        padding: const EdgeInsets.fromLTRB(16, 14, 16, 4),
        child: TextField(
          controller: _searchController,
          onChanged: (_) => setState(() {}),
          style: const TextStyle(fontSize: 14, color: kGray800),
          decoration: InputDecoration(
            hintText: 'Rechercher un signalement...',
            hintStyle: const TextStyle(fontSize: 13, color: kGray400),
            prefixIcon: const Icon(LucideIcons.search, color: kGray400, size: 18),
            suffixIcon: _searchController.text.isNotEmpty
                ? IconButton(
                    icon: const Icon(LucideIcons.x, size: 16, color: kGray400),
                    onPressed: () { _searchController.clear(); setState(() {}); },
                  )
                : null,
            filled: true,
            fillColor: kWhite,
            contentPadding: const EdgeInsets.symmetric(vertical: 0, horizontal: 16),
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: kGray200)),
            enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: kGray200)),
            focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: kBlue, width: 1.5)),
          ),
        ),
      ),
    );
  }

  Widget _buildFilterChips() {
    return Container(
      color: kGray50,
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 6),
      child: Wrap(spacing: 6, runSpacing: 4, children: [
        ..._activeFilters.entries.where((e) => e.value != null).map((e) => Chip(
          label: Text(_filterLabel(e.key, e.value), style: const TextStyle(fontSize: 11, color: kBlue, fontWeight: FontWeight.w600)),
          onDeleted: () { setState(() => _activeFilters.remove(e.key)); _loadWithFilters(); },
          backgroundColor: kBlueLight,
          deleteIconColor: kBlue,
          side: BorderSide.none,
          materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
          visualDensity: VisualDensity.compact,
          padding: const EdgeInsets.symmetric(horizontal: 4),
        )),
      ]),
    );
  }

  Widget _buildPendingBanner() {
    final pending = _total - _traites;
    if (pending <= 0) return const SizedBox.shrink();
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 8, 16, 8),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: kOrangeLight,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: kOrange.withValues(alpha: 0.3)),
      ),
      child: Row(
        children: [
          const Icon(LucideIcons.alertCircle, color: kOrange, size: 20),
          const SizedBox(width: 12),
          Expanded(child: Text(
            '$pending signalement(s) en attente de traitement',
            style: const TextStyle(color: kOrange, fontSize: 13, fontWeight: FontWeight.w600),
          )),
        ],
      ),
    );
  }

  Widget _buildList() {
    return BlocBuilder<SignalementBloc, SignalementState>(
      builder: (context, state) {
        if (state is SignalementLoading) {
          return const Center(child: CircularProgressIndicator(color: kBlue));
        }
        if (state is SignalementError) {
          return _buildErrorState(state.message);
        }
        if (state is SignalementsLoaded) {
          final query = _searchController.text.toLowerCase();
          var list = state.signalements;
          if (query.isNotEmpty) {
            list = list.where((s) =>
                s.typeNuisance.toLowerCase().contains(query) ||
                (s.description?.toLowerCase().contains(query) ?? false)).toList();
          }
          if (list.isEmpty) {
            return _buildEmptyState();
          }
          return RefreshIndicator(
            color: kBlue,
            onRefresh: () async { _loadWithFilters(); await _loadStats(); },
            child: ListView.separated(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 80),
              itemCount: list.length,
              separatorBuilder: (_, __) => const SizedBox(height: 12),
              itemBuilder: (context, index) {
                final sig = list[index];
                return TweenAnimationBuilder<double>(
                  duration: Duration(milliseconds: 300 + (index * 50).clamp(0, 500)),
                  tween: Tween(begin: 0, end: 1),
                  curve: Curves.easeOutQuart,
                  builder: (ctx, value, child) => Transform.translate(
                    offset: Offset(0, 30 * (1 - value)),
                    child: Opacity(opacity: value, child: child),
                  ),
                  child: _SignalementCard(
                    signalement: sig,
                    onTap: () => Navigator.push(context,
                      MaterialPageRoute(builder: (_) => SignalementDetailScreen(signalement: sig)),
                    ).then((_) => _loadWithFilters()),
                  ),
                );
              },
            ),
          );
        }
        return const SizedBox.shrink();
      },
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(color: kBlueLight, shape: BoxShape.circle),
            child: const Icon(LucideIcons.inbox, color: kBlue, size: 48),
          ),
          const SizedBox(height: 24),
          const Text('Aucun signalement', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: kGray800)),
          const SizedBox(height: 8),
          const Text('Il n\'y a pas de signalements\ncorrespondant à vos critères.',
            textAlign: TextAlign.center, style: TextStyle(color: kGray500, fontSize: 13, height: 1.4)),
          const SizedBox(height: 24),
          TextButton.icon(
            onPressed: () {
              setState(() { _activeFilters.clear(); _searchController.clear(); });
              _loadWithFilters();
            },
            icon: const Icon(LucideIcons.x, size: 18),
            label: const Text('Effacer les filtres'),
            style: TextButton.styleFrom(foregroundColor: kBlue),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorState(String message) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(color: kRedLight, shape: BoxShape.circle),
              child: const Icon(LucideIcons.alertOctagon, color: kRed, size: 48),
            ),
            const SizedBox(height: 24),
            const Text('Erreur de chargement', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: kGray800)),
            const SizedBox(height: 8),
            Text(message, textAlign: TextAlign.center, style: const TextStyle(color: kGray500, fontSize: 13, height: 1.4)),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: _loadWithFilters,
              icon: const Icon(LucideIcons.refreshCw, size: 16),
              label: const Text('Réessayer'),
              style: ElevatedButton.styleFrom(backgroundColor: kBlue, foregroundColor: kWhite),
            ),
          ],
        ),
      ),
    );
  }
}

class _SignalementCard extends StatelessWidget {
  final Signalement signalement;
  final VoidCallback onTap;

  const _SignalementCard({required this.signalement, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final statusColor = kStatutColors[signalement.statut] ?? kGray500;
    final criticiteColor = kCriticiteColors[signalement.criticite] ?? kGray500;
    final chantierId = signalement.chantierId ?? 0;
    final chantierName = chantierId >= 1 && chantierId <= kChantiers.length
        ? kChantiers[chantierId - 1] : 'Chantier $chantierId';
    final date = signalement.creeLe != null ? _formatDate(signalement.creeLe!) : '—';

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        decoration: BoxDecoration(
          color: kWhite,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: kGray200),
          boxShadow: const [BoxShadow(color: kShadowColor, blurRadius: 8, offset: Offset(0, 2))],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              height: 4,
              decoration: BoxDecoration(
                color: statusColor,
                borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: statusColor.withValues(alpha: 0.1),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Icon(_getStatusIcon(signalement.statut), color: statusColor, size: 22),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              signalement.typeNuisance,
                              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: kGray800),
                              maxLines: 1, overflow: TextOverflow.ellipsis,
                            ),
                            const SizedBox(height: 4),
                            Row(
                              children: [
                                const Icon(LucideIcons.calendar, size: 12, color: kGray500),
                                const SizedBox(width: 4),
                                Text(date, style: const TextStyle(fontSize: 11, color: kGray500, fontWeight: FontWeight.w500)),
                              ],
                            ),
                          ],
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: criticiteColor.withValues(alpha: 0.1),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: criticiteColor.withValues(alpha: 0.3)),
                        ),
                        child: Text(
                          kCriticiteLabels[signalement.criticite] ?? signalement.criticite,
                          style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: criticiteColor),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),
                  if (signalement.description != null && signalement.description!.isNotEmpty) ...[
                    Text(
                      signalement.description!,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 13, color: kGray600, height: 1.4),
                    ),
                    const SizedBox(height: 14),
                  ],
                  Row(
                    children: [
                      Expanded(
                        child: Row(
                          children: [
                            const Icon(LucideIcons.mapPin, size: 14, color: kGray400),
                            const SizedBox(width: 4),
                            Expanded(
                              child: Text(chantierName, style: const TextStyle(fontSize: 11, color: kGray600, fontWeight: FontWeight.w500), maxLines: 1, overflow: TextOverflow.ellipsis),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: kGray100,
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(
                          kStatutLabels[signalement.statut] ?? signalement.statut,
                          style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: statusColor),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _formatDate(DateTime dt) {
    return '${dt.day.toString().padLeft(2, '0')}/${dt.month.toString().padLeft(2, '0')}/${dt.year} ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
  }

  IconData _getStatusIcon(String statut) {
    switch (statut) {
      case 'EN_ATTENTE': return LucideIcons.clock;
      case 'EN_COURS': return LucideIcons.loader;
      case 'TRAITE': return LucideIcons.checkCircle;
      case 'REJETE': return LucideIcons.xCircle;
      default: return LucideIcons.fileText;
    }
  }
}
