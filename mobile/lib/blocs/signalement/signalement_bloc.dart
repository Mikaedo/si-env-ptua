import 'package:flutter_bloc/flutter_bloc.dart';
import '../../services/api_service.dart';
import '../../services/local_database.dart';
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

  final LocalDatabase _localDb = LocalDatabase();

  /// Ajoute a la liste du serveur les constats encore dans le telephone.
  ///
  /// Un rafraichissement reussi remplacait la liste par celle du
  /// serveur, qui ignore par construction ce qui ne lui est pas encore
  /// parvenu : les constats en attente disparaissaient de l'ecran de
  /// l'agent au premier retour de reseau, avant meme d'avoir ete
  /// transmis.
  ///
  /// Les constats sont classes par heure de terrain, toutes provenances
  /// confondues : c'est l'ordre des faits, non celui des arrivees.
  Future<List<Signalement>> _completerAvecLocaux(
      List<Signalement> duServeur) async {
    final locaux = await _localDb.getAllLocal();
    final dejaLa = duServeur.map((s) => s.uuidMobile).toSet();

    final fusion = <Signalement>[
      ...duServeur,
      ...locaux
          .map(Signalement.depuisBaseLocale)
          .where((s) => !s.transmis && !dejaLa.contains(s.uuidMobile)),
    ];

    fusion.sort((a, b) {
      final da = a.saisiLe ?? a.creeLe;
      final db = b.saisiLe ?? b.creeLe;
      if (da == null || db == null) return 0;
      return db.compareTo(da);
    });
    return fusion;
  }

  SignalementBloc(this._api) : super(SignalementInitial()) {
    on<LoadSignalements>((event, emit) async {
      // Stale-while-revalidate : si un cache local existe et qu'on charge
      // la liste sans filtre, on l'affiche instantanement puis on rafraichit
      // depuis le serveur en arriere-plan. Zero latence percue.
      final sansFiltre = event.statut == null &&
          event.criticite == null &&
          event.typeNuisance == null &&
          event.chantierId == null &&
          event.periodeJours == null;
      if (sansFiltre) {
        // La base locale d'abord, et non le cache du serveur.
        //
        // Le cache ne contenait que ce que le serveur avait deja
        // renvoye : un constat saisi hors couverture n'y figurait pas,
        // et l'agent ne le voyait donc qu'apres la synchronisation. Il
        // attendait, sans reseau, l'affichage de ce qu'il venait lui-meme
        // de saisir. La base locale, elle, porte tout : ce qui est parti
        // comme ce qui attend.
        final local = await _localDb.getAllLocal();
        if (local.isNotEmpty) {
          emit(SignalementsLoaded(
            local.map(Signalement.depuisBaseLocale).toList(),
          ));
        } else {
          final cache = await _api.signalementsEnCache();
          if (cache != null) emit(SignalementsLoaded(cache));
        }
      } else {
        emit(SignalementLoading());
      }
      try {
        final list = await _api.getSignalements(
          statut: event.statut,
          criticite: event.criticite,
          typeNuisance: event.typeNuisance,
          chantierId: event.chantierId,
          periodeJours: event.periodeJours,
        );
        // Les constats encore dans le telephone sont ajoutes a ce que
        // le serveur renvoie : sans cela, un rafraichissement reussi
        // les effacerait de l'ecran alors qu'ils n'ont pas encore ete
        // transmis.
        emit(SignalementsLoaded(await _completerAvecLocaux(list)));
      } catch (e) {
        // Si un cache a deja ete affiche, on garde l'affichage (pas d'erreur
        // ecran) : mieux vaut des donnees potentiellement datees que rien.
        if (state is! SignalementsLoaded) {
          emit(SignalementError(e.toString().replaceFirst('Exception: ', '')));
        }
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
