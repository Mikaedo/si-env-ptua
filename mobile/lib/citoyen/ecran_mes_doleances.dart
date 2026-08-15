import 'package:flutter/material.dart';

import '../core/constants.dart';
import 'api_citoyen.dart';
import 'theme_citoyen.dart';

/// Suivi des doléances déposées par le riverain connecté.
///
/// Le statut est traduit en langage courant : personne ne sait ce qu'est une
/// doléance « OUVERTE ». Un habitant attend d'une administration qu'elle lui
/// dise si son dossier a été reçu, s'il est examiné, ou s'il est réglé.
class EcranMesDoleances extends StatefulWidget {
  const EcranMesDoleances({super.key});

  @override
  State<EcranMesDoleances> createState() => _EcranMesDoleancesState();
}

class _EcranMesDoleancesState extends State<EcranMesDoleances> {
  List<Doleance> _doleances = [];
  bool _chargement = true;
  String _erreur = '';

  @override
  void initState() {
    super.initState();
    _charger();
  }

  /// Affiche d'abord le contenu mis en cache, puis rafraîchit en arrière-plan.
  ///
  /// Sur un réseau mobile ivoirien, attendre la réponse du serveur avant
  /// d'afficher quoi que ce soit se traduit par plusieurs secondes d'écran
  /// vide. Les doléances déjà connues s'affichent donc immédiatement.
  Future<void> _charger() async {
    final cache = await ApiCitoyen().mesDoleancesEnCache();
    if (cache != null && mounted) {
      setState(() {
        _doleances = cache;
        _chargement = false;
      });
    }

    try {
      final fraiches = await ApiCitoyen().mesDoleances();
      if (!mounted) return;
      setState(() {
        _doleances = fraiches;
        _chargement = false;
        _erreur = '';
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _chargement = false;
        // Si des doléances sont déjà affichées, on garde l'affichage : des
        // données un peu datées valent mieux qu'un écran d'erreur.
        if (_doleances.isEmpty) {
          _erreur = e.toString().replaceFirst('Exception: ', '');
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kGray50,
      appBar: AppBar(
        title: const Text('Mes doléances'),
        backgroundColor: kGray50,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: _charger,
            tooltip: 'Actualiser',
          ),
        ],
      ),
      body: SafeArea(child: _corps()),
    );
  }

  Widget _corps() {
    if (_chargement && _doleances.isEmpty) {
      return const Center(child: CircularProgressIndicator(color: kBlue));
    }

    if (_erreur.isNotEmpty && _doleances.isEmpty) {
      return _messageCentre(
        icone: Icons.cloud_off_rounded,
        titre: 'Chargement impossible',
        texte: _erreur,
        action: 'Réessayer',
        surAction: _charger,
      );
    }

    if (_doleances.isEmpty) {
      return _messageCentre(
        icone: Icons.inbox_outlined,
        titre: 'Aucune doléance pour le moment',
        texte: 'Lorsque vous signalerez une gêne liée au chantier, elle '
            'apparaîtra ici avec son avancement.',
      );
    }

    return RefreshIndicator(
      color: kBlue,
      onRefresh: _charger,
      child: ListView.separated(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 28),
        itemCount: _doleances.length,
        separatorBuilder: (_, _) => const SizedBox(height: 12),
        itemBuilder: (_, i) => _carte(_doleances[i]),
      ),
    );
  }

  Widget _carte(Doleance d) {
    final couleur = _couleurStatut(d.statut);

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: kWhite,
        borderRadius: BorderRadius.circular(kRayonCitoyen + 2),
        border: Border.all(color: kGray200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              if (d.categorie != null)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 5),
                  decoration: BoxDecoration(
                    color: kBlueLight,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    kCategoriesDoleance[d.categorie] ?? d.categorie!,
                    style: const TextStyle(
                      fontSize: 12, fontWeight: FontWeight.w700, color: kBlue,
                    ),
                  ),
                ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 5),
                decoration: BoxDecoration(
                  color: couleur.withValues(alpha: 0.11),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  d.statutLisible,
                  style: TextStyle(
                    fontSize: 12, fontWeight: FontWeight.w700, color: couleur,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 13),
          Text(
            d.description,
            style: const TextStyle(
              fontSize: 14.5, height: 1.55, color: kGray800,
            ),
          ),
          if (d.creeLe != null) ...[
            const SizedBox(height: 12),
            Row(
              children: [
                const Icon(Icons.schedule_rounded, size: 14, color: kGray400),
                const SizedBox(width: 6),
                Text(
                  'Déposée le ${_dateLisible(d.creeLe!)}',
                  style: const TextStyle(fontSize: 12.5, color: kGray500),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Color _couleurStatut(String statut) => switch (statut) {
        'RESOLU' => kCivique,
        'EN_COURS' => kOrange,
        'REJETE' => kGray500,
        _ => kBlue,
      };

  String _dateLisible(DateTime d) {
    const mois = [
      'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
      'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre',
    ];
    return '${d.day} ${mois[d.month - 1]} ${d.year}';
  }

  Widget _messageCentre({
    required IconData icone,
    required String titre,
    required String texte,
    String? action,
    VoidCallback? surAction,
  }) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 40),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 74, height: 74,
              decoration: BoxDecoration(
                color: kGray100,
                borderRadius: BorderRadius.circular(24),
              ),
              child: Icon(icone, size: 34, color: kGray400),
            ),
            const SizedBox(height: 22),
            Text(
              titre,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 18, fontWeight: FontWeight.w700, color: kGray900,
              ),
            ),
            const SizedBox(height: 10),
            Text(
              texte,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 14.5, height: 1.55, color: kGray600,
              ),
            ),
            if (action != null) ...[
              const SizedBox(height: 26),
              SizedBox(
                width: 200,
                child: ElevatedButton(onPressed: surAction, child: Text(action)),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
