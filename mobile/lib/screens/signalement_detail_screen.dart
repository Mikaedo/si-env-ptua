import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../blocs/signalement/signalement_bloc.dart';
import '../core/constants.dart';
import '../models/models.dart';
import '../services/api_service.dart';

class SignalementDetailScreen extends StatefulWidget {
  final Signalement signalement;
  const SignalementDetailScreen({super.key, required this.signalement});

  @override
  State<SignalementDetailScreen> createState() => _SignalementDetailScreenState();
}

class _SignalementDetailScreenState extends State<SignalementDetailScreen> {
  final _actionController = TextEditingController();
  final _motifController = TextEditingController();
  DateTime? _echeance;
  bool _showRetour = false;
  bool _isExpert = false;

  @override
  void initState() {
    super.initState();
    _isExpert = ApiService().role == 'EXPERT_HSE';
  }

  @override
  Widget build(BuildContext context) {
    final s = widget.signalement;
    final critColor = kCriticiteColors[s.criticite] ?? kGray400;
    final critLabel = kCriticiteLabels[s.criticite] ?? s.criticite;
    final statutColor = kStatutColors[s.statut] ?? kGray400;
    final statutLabel = kStatutLabels[s.statut] ?? s.statut;
    final hasIa = s.criticiteIa != null;

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(icon: const Icon(LucideIcons.arrowLeft), onPressed: () => Navigator.pop(context)),
        title: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Détail du signalement', style: TextStyle(fontSize: 16)),
          Text('SIG-${s.id ?? ''}', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w400)),
        ]),
        backgroundColor: Colors.transparent,
      ),
      extendBodyBehindAppBar: true,
      body: SingleChildScrollView(
        padding: EdgeInsets.fromLTRB(16, MediaQuery.of(context).padding.top + 64, 16, 24),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          // Hero header card
          Container(
            decoration: BoxDecoration(
              color: kWhite,
              borderRadius: BorderRadius.circular(24),
              boxShadow: const [
                BoxShadow(
                  color: kShadowLgColor,
                  blurRadius: 24,
                  offset: Offset(0, 8),
                ),
              ],
            ),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(children: [
                // Photo placeholder
                Container(
                  height: 180,
                  decoration: BoxDecoration(
                    color: kGray100,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                    Icon(_iconForType(s.typeNuisance), size: 48, color: critColor.withOpacity(0.5)),
                    const SizedBox(height: 8),
                    Text('Aucune photo', style: TextStyle(fontSize: 12, color: kGray400)),
                  ])),
                ),
                const SizedBox(height: 16),
                // Type + criticité badge
                Row(children: [
                  Expanded(child: Text(s.typeNuisance, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: kGray800))),
                  Container(padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(color: critColor.withOpacity(0.1), borderRadius: BorderRadius.circular(20), border: Border.all(color: critColor.withOpacity(0.2))),
                    child: Row(mainAxisSize: MainAxisSize.min, children: [
                      Icon(_critIcon(s.criticite), size: 14, color: critColor),
                      const SizedBox(width: 4),
                      Text(critLabel.toUpperCase(), style: TextStyle(color: critColor, fontSize: 10, fontWeight: FontWeight.w800)),
                    ])),
                ]),
                const SizedBox(height: 16),
                // Status badge
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(color: statutColor.withOpacity(0.08), borderRadius: BorderRadius.circular(12)),
                  child: Row(children: [
                    Icon(_statutIcon(s.statut), size: 18, color: statutColor),
                    const SizedBox(width: 12),
                    Text(statutLabel, style: TextStyle(color: statutColor, fontSize: 14, fontWeight: FontWeight.w700)),
                    const Spacer(),
                    Text(s.creeLe != null ? _formatDate(s.creeLe!) : '-', style: const TextStyle(fontSize: 12, color: kGray600)),
                    ]),
                  ),
                ]),
              ),
            ),
            const SizedBox(height: 12),
            // Info grid
            Container(
              decoration: BoxDecoration(color: kWhite, borderRadius: BorderRadius.circular(16), border: Border.all(color: kGray200, width: 1)),
              child: Column(children: [
                _InfoTile(icon: Icons.category_rounded, label: 'Type', value: s.typeNuisance),
                const Divider(height: 1, indent: 56),
                _InfoTile(icon: Icons.location_on_rounded, label: 'GPS', value: '${s.latitude?.toStringAsFixed(5) ?? "-"}, ${s.longitude?.toStringAsFixed(5) ?? "-"}'),
                const Divider(height: 1, indent: 56),
                _InfoTile(icon: Icons.gps_fixed_rounded, label: 'Source GPS', value: s.gpsSource == 'AUTO' ? 'Automatique' : 'Manuel'),
                const Divider(height: 1, indent: 56),
                _InfoTile(icon: Icons.shield_rounded, label: 'Criticité agent', value: critLabel, valueColor: critColor),
                if (hasIa) ...[
                  const Divider(height: 1, indent: 56),
                  _InfoTile(icon: Icons.psychology_rounded, label: 'Criticité IA', value: '${kCriticiteLabels[s.criticiteIa] ?? s.criticiteIa} (${s.confianceIa?.toStringAsFixed(0) ?? 0}%)', valueColor: kOrange),
                ],
              ]),
            ),
            // IA diagnostic
            if (hasIa) ...[
              const SizedBox(height: 12),
              _SectionCard(icon: Icons.psychology_rounded, iconColor: kOrange, title: 'Diagnostic IA', child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                _IaBadge(label: 'Détection', value: 'Objets détectés', icon: Icons.visibility_rounded),
                const SizedBox(height: 6),
                _IaBadge(label: 'Confiance', value: '${s.confianceIa?.toStringAsFixed(0) ?? 0}%', icon: Icons.trending_up_rounded),
                const SizedBox(height: 6),
                _IaBadge(label: 'Classification', value: kCriticiteLabels[s.criticiteIa] ?? s.criticiteIa ?? '-', icon: Icons.category_rounded),
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(color: kOrangeLight, borderRadius: BorderRadius.circular(10)),
                  child: Row(children: [
                    Icon(Icons.info_outline_rounded, size: 14, color: kOrange),
                    const SizedBox(width: 6),
                    Expanded(child: Text('Modèle: YOLOv8n + MobileNetV2 (ONNX)', style: TextStyle(fontSize: 10, color: kOrange, fontWeight: FontWeight.w500))),
                  ]),
                ),
              ])),
            ],
            // Description
            const SizedBox(height: 12),
            _SectionCard(icon: Icons.description_rounded, iconColor: kBlue, title: 'Description agent', child: Text(
              s.description ?? 'Aucune description fournie', style: const TextStyle(fontSize: 13, color: kGray600, height: 1.5))),
            // Action corrective (EXPERT_HSE only)
            if (_isExpert && s.statut != 'CLOTURE' && s.statut != 'REJETE') ...[
              const SizedBox(height: 12),
              _SectionCard(icon: Icons.build_rounded, iconColor: const Color(0xFF1565C0), title: 'Action corrective', child: Column(children: [
                TextField(controller: _actionController, decoration: const InputDecoration(labelText: 'Action envisagée', hintText: 'Ex : Évacuation des déchets par le prestataire', prefixIcon: Icon(Icons.edit_rounded, size: 18))),
                const SizedBox(height: 12),
                InkWell(
                  onTap: () async {
                    final d = await showDatePicker(context: context, initialDate: DateTime.now().add(const Duration(days: 3)), firstDate: DateTime.now(), lastDate: DateTime.now().add(const Duration(days: 365)));
                    if (d != null) setState(() => _echeance = d);
                  },
                  child: InputDecorator(
                    decoration: const InputDecoration(labelText: 'Échéance', prefixIcon: Icon(Icons.event_rounded, size: 18)),
                    child: Text(_echeance != null ? _formatDate(_echeance!) : 'Sélectionner une date'),
                  ),
                ),
              ])),
              const SizedBox(height: 16),
              // Action buttons
              ElevatedButton(
                onPressed: () {
                  context.read<SignalementBloc>().add(AddActionCorrective(s.id!, _actionController.text, _echeance));
                  context.read<SignalementBloc>().add(UpdateStatut(s.id!, 'CLOTURE'));
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Signalement marqué comme traité'), backgroundColor: kBlue));
                  Navigator.pop(context);
                },
                child: const Row(mainAxisAlignment: MainAxisAlignment.center, children: [Icon(Icons.check_circle_rounded, size: 20), SizedBox(width: 8), Text('Marquer comme traité')]),
              ),
              const SizedBox(height: 8),
              OutlinedButton(
                onPressed: () => setState(() => _showRetour = !_showRetour),
                child: const Row(mainAxisAlignment: MainAxisAlignment.center, children: [Icon(Icons.undo_rounded, size: 20), SizedBox(width: 8), Text("Retourner à l'agent (incomplet)")]),
              ),
              if (_showRetour) ...[
                const SizedBox(height: 12),
                TextField(controller: _motifController, decoration: const InputDecoration(labelText: 'Motif du retour', hintText: 'Ex : Photo floue, GPS manquant...', prefixIcon: Icon(Icons.report_problem_rounded, size: 18))),
                const SizedBox(height: 8),
                ElevatedButton(
                  style: ElevatedButton.styleFrom(backgroundColor: kRed),
                  onPressed: () {
                    context.read<SignalementBloc>().add(RetournerAgent(s.id!, _motifController.text));
                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Signalement retourné à l\'agent'), backgroundColor: kOrange));
                    Navigator.pop(context);
                  },
                  child: const Row(mainAxisAlignment: MainAxisAlignment.center, children: [Icon(Icons.check_rounded, size: 18), SizedBox(width: 8), Text('Confirmer le retour')]),
                ),
              ],
            ],
            // Read-only for RESP_ENV
            if (!_isExpert && s.statut != 'CLOTURE' && s.statut != 'REJETE') ...[
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(color: kGray100, borderRadius: BorderRadius.circular(14)),
                child: Row(children: [
                  Icon(Icons.lock_outline_rounded, size: 18, color: kGray400),
                  const SizedBox(width: 10),
                  Expanded(child: Text('Les actions correctives sont réservées à l\'Expert HSE', style: TextStyle(fontSize: 12, color: kGray600))),
                ]),
              ),
            ],
            if (s.statut == 'CLOTURE') ...[
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(color: const Color(0xFFE8F5E9), borderRadius: BorderRadius.circular(14)),
                child: Row(children: [
                  const Icon(Icons.verified_rounded, size: 20, color: Color(0xFF2E7D32)),
                  const SizedBox(width: 10),
                  const Expanded(child: Text('Signalement traité et clôturé', style: TextStyle(fontSize: 13, color: Color(0xFF2E7D32), fontWeight: FontWeight.w600))),
                ]),
              ),
            ],
            if (s.statut == 'REJETE') ...[
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(color: kRedLight, borderRadius: BorderRadius.circular(14)),
                child: Row(children: [
                  const Icon(Icons.cancel_rounded, size: 20, color: kRed),
                  const SizedBox(width: 10),
                  const Expanded(child: Text('Signalement rejeté et retourné à l\'agent', style: TextStyle(fontSize: 13, color: kRed, fontWeight: FontWeight.w600))),
                ]),
              ),
            ],
          ]),
        ),
    );
  }

  IconData _iconForType(String type) {
    switch (type) {
      case 'Déchets de chantier': return Icons.delete_outline_rounded;
      case 'Eaux stagnantes': return Icons.water_drop_outlined;
      case 'Poussières': return Icons.air_rounded;
      case 'Bruit': return Icons.volume_up_outlined;
      case 'Dégradation végétation': return Icons.park_outlined;
      default: return Icons.warning_amber_rounded;
    }
  }

  IconData _critIcon(String crit) {
    switch (crit) {
      case 'FAIBLE': return Icons.eco_rounded;
      case 'MODERE': return Icons.warning_amber_rounded;
      case 'ELEVE': return Icons.dangerous_rounded;
      default: return Icons.info_rounded;
    }
  }

  IconData _statutIcon(String statut) {
    switch (statut) {
      case 'NOUVEAU': return Icons.fiber_new_rounded;
      case 'EN_TRAITEMENT': return Icons.pending_actions_rounded;
      case 'CLOTURE': return Icons.task_alt_rounded;
      case 'REJETE': return Icons.cancel_rounded;
      case 'PENDING_SYNC': return Icons.sync_rounded;
      default: return Icons.info_rounded;
    }
  }

  String _formatDate(DateTime d) => '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')}/${d.year} ${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}';
}

class _InfoTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color? valueColor;
  const _InfoTile({required this.icon, required this.label, required this.value, this.valueColor});

  @override
  Widget build(BuildContext context) {
    return Padding(padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      child: Row(children: [
        Container(width: 32, height: 32, decoration: BoxDecoration(color: kGray100, borderRadius: BorderRadius.circular(10)),
          child: Icon(icon, size: 16, color: kGray600)),
        const SizedBox(width: 10),
        Text(label, style: const TextStyle(fontSize: 12, color: kGray600)),
        const Spacer(),
        Flexible(child: Text(value, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: valueColor ?? kGray800), maxLines: 1, overflow: TextOverflow.ellipsis, textAlign: TextAlign.end)),
      ]));
  }
}

class _IaBadge extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  const _IaBadge({required this.label, required this.value, required this.icon});

  @override
  Widget build(BuildContext context) {
    return Row(children: [
      Icon(icon, size: 14, color: kOrange),
      const SizedBox(width: 6),
      Text(label, style: const TextStyle(fontSize: 11, color: kGray600)),
      const Spacer(),
      Text(value, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: kGray800)),
    ]);
  }
}

class _SectionCard extends StatelessWidget {
  final IconData icon;
  final Color iconColor;
  final String title;
  final Widget child;
  const _SectionCard({required this.icon, required this.iconColor, required this.title, required this.child});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(color: kWhite, borderRadius: BorderRadius.circular(16), border: Border.all(color: kGray200, width: 1)),
      child: Padding(padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Container(width: 30, height: 30, decoration: BoxDecoration(color: iconColor.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(8)),
              child: Icon(icon, size: 16, color: iconColor)),
            const SizedBox(width: 10),
            Text(title, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: kGray800)),
          ]),
          const SizedBox(height: 12),
          child,
        ])),
    );
  }
}
