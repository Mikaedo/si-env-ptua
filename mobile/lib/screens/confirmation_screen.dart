import 'package:flutter/material.dart';
import '../widgets/ptua_logo.dart';
import '../core/constants.dart';
import '../models/models.dart';

class ConfirmationScreen extends StatelessWidget {
  final Signalement signalement;
  const ConfirmationScreen({super.key, required this.signalement});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        titleSpacing: 0,
        title: Row(children: [
          Container(margin: const EdgeInsets.only(right: 12), child: const PtuaLogo(size: 40)),
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Signalement cree', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontSize: 17)),
            Text('SIG-${DateTime.now().year}-${signalement.id ?? 0}', style: const TextStyle(fontSize: 11, color: kGray600)),
          ]),
        ]),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(color: kWhite, borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: kGray200, width: 1)),
                child: Column(children: [
                  Container(width: 72, height: 72,
                    decoration: BoxDecoration(borderRadius: BorderRadius.circular(24), gradient: const LinearGradient(colors: [kBlue, kBlueDark]),
                      boxShadow: [BoxShadow(color: kBlue.withValues(alpha: 0.2), blurRadius: 24)]),
                    child: const Icon(Icons.check, color: kWhite, size: 36)),
                  const SizedBox(height: 16),
                  Text('Signalement enregistre', style: Theme.of(context).textTheme.titleLarge),
                  const SizedBox(height: 6),
                  Text('Votre signalement a ete enregistre localement. Il sera synchronise des que le reseau sera disponible.',
                    textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodyMedium),
                  const SizedBox(height: 16),
                  _InfoRow(label: 'Type', value: signalement.typeNuisance),
                  _InfoRow(label: 'Statut', value: 'PENDING_SYNC', valueColor: kOrange),
                ]),
              ),
              const SizedBox(height: 20),
              ElevatedButton(
                onPressed: () => Navigator.pushNamedAndRemoveUntil(context, '/', (r) => false),
                child: const Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                  Icon(Icons.add, size: 18), SizedBox(width: 8), Text('Nouveau signalement'),
                ]),
              ),
              const SizedBox(height: 8),
              OutlinedButton(
                onPressed: () => Navigator.pushNamedAndRemoveUntil(context, '/', (r) => false),
                child: const Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                  Icon(Icons.description, size: 18), SizedBox(width: 8), Text('Voir mes signalements'),
                ]),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final String label;
  final String value;
  final Color? valueColor;
  const _InfoRow({required this.label, required this.value, this.valueColor});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
        Text(label, style: const TextStyle(fontSize: 12, color: kGray600)),
        Text(value, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: valueColor ?? kGray800)),
      ]),
    );
  }
}
