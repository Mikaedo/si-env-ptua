import 'dart:async';

import 'package:flutter_bloc/flutter_bloc.dart';
import '../../services/api_service.dart';
import '../../services/local_database.dart';
import '../../models/models.dart';

abstract class SyncEvent {}

class StartSync extends SyncEvent {}

/// Emis par la minuterie interne du bloc : declenche un envoi seulement si des
/// signalements sont en attente et si le serveur repond (section 4.6).
class AutoSyncTick extends SyncEvent {}

class CheckPendingCount extends SyncEvent {}

class SyncState {}

class SyncInitial extends SyncState {}

class SyncInProgress extends SyncState {
  final int total;
  final int sent;
  SyncInProgress(this.total, this.sent);
}

class SyncComplete extends SyncState {
  final int synced;
  SyncComplete(this.synced);
}

class SyncIdle extends SyncState {
  final int pendingCount;
  SyncIdle(this.pendingCount);
}

class SyncBloc extends Bloc<SyncEvent, SyncState> {
  /// Periode de la veille reseau. Assez courte pour que la remontee des
  /// signalements suive de pres le retour de la couverture, assez longue pour
  /// ne pas peser sur la batterie ni sur le forfait de donnees de l'agent.
  static const Duration periodeVeille = Duration(seconds: 60);

  final ApiService _api;
  final LocalDatabase _localDb;
  Timer? _veille;
  bool _envoiEnCours = false;

  SyncBloc(this._api, this._localDb) : super(SyncInitial()) {
    on<CheckPendingCount>((event, emit) async {
      final count = await _localDb.pendingCount();
      emit(SyncIdle(count));
    });

    on<StartSync>((event, emit) async {
      await _envoyerLot(emit, silencieux: false);
    });

    // Synchronisation automatique : le service de veille verifie periodiquement
    // la disponibilite du reseau et vide la file d'attente des qu'une connexion
    // est detectee, sans intervention de l'agent. Le bouton « Synchroniser
    // maintenant » reste disponible pour forcer l'envoi.
    on<AutoSyncTick>((event, emit) async {
      if (_envoiEnCours) return;
      if (await _localDb.pendingCount() == 0) return;
      if (!await _api.reseauDisponible()) return;
      await _envoyerLot(emit, silencieux: true);
    });

    _veille = Timer.periodic(periodeVeille, (_) {
      if (!isClosed) add(AutoSyncTick());
    });
  }

  /// Envoi par lot de la file d'attente locale. En mode silencieux (veille
  /// automatique), aucun etat n'est emis quand il n'y a rien a transmettre,
  /// afin de ne pas perturber l'ecran affiche.
  Future<void> _envoyerLot(Emitter<SyncState> emit, {required bool silencieux}) async {
    final pending = await _localDb.getPendingSignalements();
    if (pending.isEmpty) {
      if (!silencieux) emit(SyncComplete(0));
      return;
    }
    _envoiEnCours = true;
    try {
      emit(SyncInProgress(pending.length, 0));
      int sent = 0;
      for (final row in pending) {
        try {
          final s = Signalement(
            uuidMobile: row['uuid_mobile'],
            typeNuisance: row['type_nuisance'],
            description: row['description'],
            criticite: row['criticite'],
            criticiteIa: row['criticite_ia'],
            confianceIa: row['confiance_ia'],
            gpsSource: row['gps_source'] ?? 'AUTO',
            latitude: row['latitude'],
            longitude: row['longitude'],
            chantierId: row['chantier_id'],
          );
          await _api.createSignalement(s);
          await _localDb.markSynced(row['uuid_mobile']);
          sent++;
          emit(SyncInProgress(pending.length, sent));
        } catch (_) {
          // On continue avec les suivants
        }
      }
      emit(SyncComplete(sent));
    } finally {
      _envoiEnCours = false;
    }
  }

  @override
  Future<void> close() {
    _veille?.cancel();
    return super.close();
  }
}
