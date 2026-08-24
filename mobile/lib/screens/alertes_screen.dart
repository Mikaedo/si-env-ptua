import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../widgets/ptua_logo.dart';
import '../core/constants.dart';
import '../services/api_service.dart';
import '../models/models.dart';

class AlertesScreen extends StatefulWidget {
  const AlertesScreen({super.key});

  @override
  State<AlertesScreen> createState() => _AlertesScreenState();
}

class _AlertesScreenState extends State<AlertesScreen> {
  List<Alerte> _alertes = [];
  bool _loading = true;
  bool _hasError = false;

  @override
  void initState() {
    super.initState();
    _loadAlertes();
  }

  Future<void> _loadAlertes() async {
    setState(() { _loading = true; _hasError = false; });
    try {
      final list = await ApiService().getAlertes();
      setState(() { _alertes = list; _loading = false; });
    } catch (_) {
      // Auparavant silencieux : la liste restait simplement vide, sans dire
      // a l'agent qu'il s'agissait d'un echec reseau et non d'une absence
      // reelle d'alertes.
      setState(() { _loading = false; _hasError = true; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        titleSpacing: 0,
        title: Row(children: [
          Container(margin: const EdgeInsets.only(right: 12), child: const PtuaLogo(size: 40)),
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Alertes', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontSize: 17)),
            Text('${_alertes.where((a) => !a.recue).length} nouvelles notifications', style: const TextStyle(fontSize: 11, color: kGray600)),
          ]),
        ]),
        actions: [
          IconButton(
            onPressed: _loadAlertes,
            icon: const Icon(Icons.refresh_rounded, color: kGray600),
          ),
        ],
      ),
      body: SafeArea(
        child: _loading
            ? const Center(child: CircularProgressIndicator(color: kBlue))
            : _hasError
                ? Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
                    Container(width: 72, height: 72,
                      decoration: BoxDecoration(color: kRedLight, borderRadius: BorderRadius.circular(22)),
                      child: const Icon(LucideIcons.cloudOff, color: kRed, size: 32)),
                    const SizedBox(height: 16),
                    const Text('Alertes indisponibles', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: kGray800)),
                    const SizedBox(height: 8),
                    const Text('Vérifiez votre connexion\net reconnectez-vous si nécessaire.',
                      textAlign: TextAlign.center, style: TextStyle(fontSize: 13, color: kGray500)),
                    const SizedBox(height: 24),
                    SizedBox(width: 180, child: ElevatedButton.icon(
                      onPressed: _loadAlertes,
                      icon: const Icon(LucideIcons.refreshCw, size: 16),
                      label: const Text('Réessayer'),
                    )),
                  ]))
                : ListView.builder(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                itemCount: _alertes.length,
                itemBuilder: (_, i) {
                  final a = _alertes[i];
                  final isCritical = a.niveau == 'CRITIQUE';
                  final color = isCritical ? kRed : a.niveau == 'ATTENTION' ? kOrange : kBlue;
                  return Container(
                    margin: const EdgeInsets.only(bottom: 10),
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: !a.recue && isCritical ? kRedLight : kWhite,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: kGray200, width: 1),
                    ),
                    child: Row(children: [
                      Container(
                        width: 40, height: 40,
                        decoration: BoxDecoration(color: color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(12)),
                        child: Icon(isCritical ? Icons.warning_rounded : Icons.info_outline_rounded, color: color, size: 20),
                      ),
                      const SizedBox(width: 12),
                      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text(a.message, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13, color: kGray800)),
                        const SizedBox(height: 2),
                        Text('Niveau: ${a.niveau}${a.valeur != null ? " • Valeur: ${a.valeur}" : ""}',
                          style: const TextStyle(fontSize: 11, color: kGray600)),
                      ])),
                      if (!a.recue)
                        TextButton(
                          onPressed: () async {
                            await ApiService().accuserReception(a.id);
                            _loadAlertes();
                          },
                          child: const Text('Accuser', style: TextStyle(color: kBlue, fontSize: 12, fontWeight: FontWeight.w600)),
                        ),
                    ]),
                  );
                },
              ),
      ),
    );
  }
}
