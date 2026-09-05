import 'dart:async';
import 'dart:io';

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

    // Le bouton « Synchroniser maintenant » : `_envoyerLot` reprend
    // les photographies restees en arriere, l'agent qui force l'envoi
    // attend que tout parte, pas seulement les saisies.
    on<StartSync>((event, emit) async {
      await _envoyerLot(emit, silencieux: false);
    });

    // Synchronisation automatique : le service de veille verifie periodiquement
    // la disponibilite du reseau et vide la file d'attente des qu'une connexion
    // est detectee, sans intervention de l'agent. Le bouton « Synchroniser
    // maintenant » reste disponible pour forcer l'envoi.
    on<AutoSyncTick>((event, emit) async {
      if (_envoiEnCours) return;

      // Une photographie peut rester seule a envoyer, son signalement
      // etant deja parti : la veille interroge donc les deux files,
      // sans quoi elle sortirait ici et ne la reprendrait jamais.
      final signalements = await _localDb.pendingCount();
      final photos = await _localDb.nombrePhotosEnAttente();
      if (signalements == 0 && photos == 0) return;
      if (!await _api.reseauDisponible()) return;

      // `_envoyerLot` reprend les photographies, file vide comprise.
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
      // Aucune saisie a transmettre ne veut pas dire rien a faire : une
      // photographie peut rester seule, son signalement etant deja
      // parti.
      await _reprendrePhotos();
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
          final cree = await _api.createSignalement(s);
          // L'identifiant attribue par le serveur est conserve : c'est
          // lui qui permettra de rattacher la photographie, y compris si
          // son envoi doit etre repris plus tard.
          await _localDb.markSynced(row['uuid_mobile'],
              serveurId: cree.id);
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

    // Les photographies partent apres, et hors du drapeau : leur envoi
    // a besoin de l'identifiant que le serveur vient d'attribuer, et
    // c'est ce qui les rendait intransmissibles hors ligne.
    //
    // Elles sont volontairement transmises apres le bilan : un fichier
    // est lourd, et Bloc interdit d'emettre un etat depuis un
    // gestionnaire deja clos. L'agent voit donc ses saisies parties
    // sans attendre les fichiers, qui suivent.
    await _reprendrePhotos();
  }

  /// Reprend les photographies dont le signalement est deja parti.
  ///
  /// Le fichier d'une photographie est plus lourd que la saisie : sur un
  /// reseau qui revient a peine, il peut echouer alors que le
  /// signalement est bien passe. Cette reprise s'en occupe au tour
  /// suivant, sans renvoyer le signalement une seconde fois.
  ///
  /// Le drapeau couvre toute la reprise : l'envoi d'un fichier peut
  /// depasser la periode de veille, et sans lui le battement suivant
  /// reprendrait les memes photographies, qui partiraient en double.
  Future<void> _reprendrePhotos() async {
    if (_envoiEnCours) return;
    _envoiEnCours = true;
    try {
      for (final row in await _localDb.photosEnAttente()) {
        await _envoyerPhoto(
          row['uuid_mobile'] as String,
          row['photo_path'] as String?,
          row['serveur_id'] as int?,
        );
      }
    } finally {
      _envoiEnCours = false;
    }
  }

  /// Envoie la photographie d'un signalement qui vient d'etre transmis.
  ///
  /// Rien a faire si le signalement n'en portait pas, ou si le serveur
  /// n'a pas renvoye d'identifiant.
  ///
  /// Le fichier peut avoir disparu : Android vide le cache de l'appareil
  /// photo, et un signalement peut attendre plusieurs jours dans la file
  /// si l'agent reste hors couverture. Dans ce cas on oublie la
  /// photographie plutot que de reessayer indefiniment un envoi qui ne
  /// reussira jamais.
  ///
  /// Un echec reseau, lui, laisse le chemin en place : la photographie
  /// est reprise a la prochaine veille.
  Future<void> _envoyerPhoto(
      String uuidMobile, String? chemin, int? signalementId) async {
    if (chemin == null || chemin.isEmpty || signalementId == null) return;

    if (!await File(chemin).exists()) {
      await _localDb.oublierPhoto(uuidMobile);
      return;
    }

    try {
      await _api.uploadPhoto(signalementId, chemin);
      await _localDb.oublierPhoto(uuidMobile);
    } catch (_) {
      // Reseau encore instable : on garde le chemin, la prochaine
      // veille reprendra la photographie.
    }
  }

  @override
  Future<void> close() {
    _veille?.cancel();
    return super.close();
  }
}
