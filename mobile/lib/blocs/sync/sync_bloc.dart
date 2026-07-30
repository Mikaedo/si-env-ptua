import 'package:flutter_bloc/flutter_bloc.dart';
import '../../services/api_service.dart';
import '../../services/local_database.dart';
import '../../models/models.dart';

abstract class SyncEvent {}

class StartSync extends SyncEvent {}

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
  final ApiService _api;
  final LocalDatabase _localDb;

  SyncBloc(this._api, this._localDb) : super(SyncInitial()) {
    on<CheckPendingCount>((event, emit) async {
      final count = await _localDb.pendingCount();
      emit(SyncIdle(count));
    });

    on<StartSync>((event, emit) async {
      final pending = await _localDb.getPendingSignalements();
      if (pending.isEmpty) {
        emit(SyncComplete(0));
        return;
      }
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
    });
  }
}
