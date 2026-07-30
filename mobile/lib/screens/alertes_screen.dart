import 'package:flutter/material.dart';
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

  @override
  void initState() {
    super.initState();
    _loadAlertes();
  }

  Future<void> _loadAlertes() async {
    try {
      final list = await ApiService().getAlertes();
      setState(() { _alertes = list; _loading = false; });
    } catch (_) {
      setState(() => _loading = false);
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
            onPressed: () { setState(() => _loading = true); _loadAlertes(); },
            icon: const Icon(Icons.refresh_rounded, color: kGray600),
          ),
        ],
      ),
      body: SafeArea(
        child: _loading
            ? const Center(child: CircularProgressIndicator(color: kBlue))
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
