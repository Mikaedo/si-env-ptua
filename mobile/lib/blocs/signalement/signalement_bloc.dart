import 'package:flutter_bloc/flutter_bloc.dart';
import '../../services/api_service.dart';
import '../../models/models.dart';

abstract class SignalementEvent {}

class LoadSignalements extends SignalementEvent {
  final String? statut;
  final String? criticite;
  final String? typeNuisance;
  final int? chantierId;
  final int? periodeJours;
  LoadSignalements({this.statut, this.criticite, this.typeNuisance, this.chantierId, this.periodeJours});
}

class LoadSignalementDetail extends SignalementEvent {
  final int id;
  LoadSignalementDetail(this.id);
}

class CreateSignalement extends SignalementEvent {
  final Signalement signalement;
  CreateSignalement(this.signalement);
}

class UpdateStatut extends SignalementEvent {
  final int id;
  final String statut;
  UpdateStatut(this.id, this.statut);
}

class AddActionCorrective extends SignalementEvent {
  final int signalementId;
  final String description;
  final DateTime? echeance;
  AddActionCorrective(this.signalementId, this.description, this.echeance);
}

class RetournerAgent extends SignalementEvent {
  final int signalementId;
  final String motif;
  RetournerAgent(this.signalementId, this.motif);
}

class SignalementState {}

class SignalementInitial extends SignalementState {}

class SignalementLoading extends SignalementState {}

class SignalementsLoaded extends SignalementState {
  final List<Signalement> signalements;
  SignalementsLoaded(this.signalements);
}

class SignalementDetailLoaded extends SignalementState {
  final Signalement signalement;
  SignalementDetailLoaded(this.signalement);
}

class SignalementCreated extends SignalementState {
  final Signalement signalement;
  SignalementCreated(this.signalement);
}

class SignalementError extends SignalementState {
  final String message;
  SignalementError(this.message);
}

class SignalementBloc extends Bloc<SignalementEvent, SignalementState> {
  final ApiService _api;

  SignalementBloc(this._api) : super(SignalementInitial()) {
    on<LoadSignalements>((event, emit) async {
      emit(SignalementLoading());
      try {
        final list = await _api.getSignalements(
          statut: event.statut,
          criticite: event.criticite,
          typeNuisance: event.typeNuisance,
          chantierId: event.chantierId,
          periodeJours: event.periodeJours,
        );
        emit(SignalementsLoaded(list));
      } catch (e) {
        emit(SignalementError(e.toString().replaceFirst('Exception: ', '')));
      }
    });

    on<LoadSignalementDetail>((event, emit) async {
      emit(SignalementLoading());
      try {
        final s = await _api.getSignalementDetail(event.id);
        emit(SignalementDetailLoaded(s));
      } catch (e) {
        emit(SignalementError(e.toString().replaceFirst('Exception: ', '')));
      }
    });

    on<CreateSignalement>((event, emit) async {
      emit(SignalementLoading());
      try {
        final s = await _api.createSignalement(event.signalement);
        emit(SignalementCreated(s));
      } catch (e) {
        emit(SignalementError(e.toString().replaceFirst('Exception: ', '')));
      }
    });

    on<UpdateStatut>((event, emit) async {
      try {
        await _api.updateStatut(event.id, event.statut);
      } catch (e) {
        emit(SignalementError(e.toString().replaceFirst('Exception: ', '')));
      }
    });

    on<AddActionCorrective>((event, emit) async {
      try {
        await _api.addActionCorrective(event.signalementId, event.description, event.echeance);
      } catch (e) {
        emit(SignalementError(e.toString().replaceFirst('Exception: ', '')));
      }
    });

    on<RetournerAgent>((event, emit) async {
      try {
        await _api.retournerAgent(event.signalementId, event.motif);
      } catch (e) {
        emit(SignalementError(e.toString().replaceFirst('Exception: ', '')));
      }
    });
  }
}
