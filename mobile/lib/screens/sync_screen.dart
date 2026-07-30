import 'package:flutter/material.dart';
import '../widgets/ptua_logo.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../blocs/sync/sync_bloc.dart';
import '../core/constants.dart';
import '../services/local_database.dart';

class SyncScreen extends StatefulWidget {
  const SyncScreen({super.key});

  @override
  State<SyncScreen> createState() => _SyncScreenState();
}

class _SyncScreenState extends State<SyncScreen> {
  List<Map<String, dynamic>> _pending = [];
  int _pendingCount = 0;

  @override
  void initState() {
    super.initState();
    _loadPending();
  }

  Future<void> _loadPending() async {
    final items = await LocalDatabase().getPendingSignalements();
    final count = await LocalDatabase().pendingCount();
    setState(() { _pending = items; _pendingCount = count; });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        titleSpacing: 0,
        title: Row(children: [
          Container(margin: const EdgeInsets.only(right: 12), child: const PtuaLogo(size: 40)),
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Synchronisation', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontSize: 17)),
            Text('$_pendingCount signalements a envoyer', style: const TextStyle(fontSize: 11, color: kGray600)),
          ]),
        ]),
      ),
      body: SafeArea(
        child: Column(children: [
          Container(
            margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(color: kBlueLight, borderRadius: BorderRadius.circular(20)),
            child: Column(children: [
              Container(width: 56, height: 56, decoration: BoxDecoration(borderRadius: BorderRadius.circular(16), gradient: const LinearGradient(colors: [kBlue, kBlueDark])),
                child: const Icon(Icons.sync, color: kWhite, size: 28)),
              const SizedBox(height: 12),
              const Text('Synchronisation', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: kGray800)),
              const SizedBox(height: 4),
              Text('$_pendingCount signalements en attente', style: const TextStyle(fontSize: 12, color: kGray600)),
              const SizedBox(height: 16),
              BlocConsumer<SyncBloc, SyncState>(
                listener: (context, state) {
                  if (state is SyncComplete) {
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('${state.synced} signalements synchronises'), backgroundColor: kBlue));
                    _loadPending();
                  }
                },
                builder: (context, state) {
                  if (state is SyncInProgress) {
                    return Column(children: [
                      LinearProgressIndicator(value: state.total > 0 ? state.sent / state.total : 0, color: kBlue, backgroundColor: kGray100),
                      const SizedBox(height: 4),
                      Text('${state.sent}/${state.total} envoyes', style: const TextStyle(fontSize: 11, color: kGray600)),
                    ]);
                  }
                  return ElevatedButton(
                    onPressed: _pendingCount > 0 ? () => context.read<SyncBloc>().add(StartSync()) : null,
                    child: const Row(mainAxisSize: MainAxisSize.min, children: [Icon(Icons.sync, size: 18), SizedBox(width: 8), Text('Synchroniser maintenant')]),
                  );
                },
              ),
            ]),
          ),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              itemCount: _pending.length,
              itemBuilder: (_, i) {
                final item = _pending[i];
                return Container(
                  margin: const EdgeInsets.only(bottom: 10),
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(color: kWhite, borderRadius: BorderRadius.circular(16), border: Border.all(color: kGray200, width: 1)),
                  child: Row(children: [
                    Container(width: 40, height: 40, decoration: BoxDecoration(color: kOrangeLight, borderRadius: BorderRadius.circular(12)),
                      child: const Icon(Icons.sync, color: kOrange, size: 20)),
                    const SizedBox(width: 12),
                    Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text(item['type_nuisance'], style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: kGray800)),
                      Text('En attente • ${item['uuid_mobile'].toString().substring(0, 8)}...',
                        style: const TextStyle(fontSize: 11, color: kGray600)),
                    ])),
                  ]),
                );
              },
            ),
          ),
        ]),
      ),
    );
  }
}
