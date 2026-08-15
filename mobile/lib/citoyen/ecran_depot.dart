import 'package:flutter/material.dart';

import '../core/constants.dart';
import '../services/gps_service.dart';
import 'api_citoyen.dart';
import 'theme_citoyen.dart';

/// Dépôt d'une doléance.
///
/// L'écran tient en une page et ne demande que l'essentiel : de quoi il
/// s'agit, et ce que la personne veut dire. La position est relevée en arrière
/// plan, sans qu'elle ait à s'en occuper.
///
/// Aucune reconnaissance automatique n'intervient ici, contrairement à
/// l'application des agents qui embarque des modèles de détection. Un riverain
/// décrit une gêne, il ne réalise pas un diagnostic : le tri relève du
/// spécialiste chargé du volet social, qui dispose du contexte nécessaire.
class EcranDepot extends StatefulWidget {
  const EcranDepot({super.key});

  @override
  State<EcranDepot> createState() => _EcranDepotState();
}

class _EcranDepotState extends State<EcranDepot> {
  final _description = TextEditingController();
  String _categorie = 'bruit';
  bool _envoi = false;
  String _erreur = '';

  double? _latitude;
  double? _longitude;
  bool _positionEnCours = true;

  @override
  void initState() {
    super.initState();
    _releverPosition();
  }

  @override
  void dispose() {
    _description.dispose();
    super.dispose();
  }

  /// Relève la position en arrière-plan, sans bloquer la saisie.
  ///
  /// Si elle n'est pas obtenue, la doléance part quand même : elle sera
  /// rattachée au chantier de rattachement du riverain. Mieux vaut une
  /// doléance sans coordonnées précises que pas de doléance du tout.
  Future<void> _releverPosition() async {
    final position = await GpsService.getCurrentPosition();
    if (!mounted) return;
    setState(() {
      _latitude = position?.latitude;
      _longitude = position?.longitude;
      _positionEnCours = false;
    });
  }

  Future<void> _envoyer() async {
    if (_description.text.trim().length < 5) {
      setState(() => _erreur = 'Décrivez la gêne en quelques mots.');
      return;
    }

    setState(() {
      _envoi = true;
      _erreur = '';
    });

    try {
      await ApiCitoyen().deposer(
        description: _description.text.trim(),
        categorie: _categorie,
        latitude: _latitude,
        longitude: _longitude,
      );
      if (!mounted) return;
      _afficherConfirmation();
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _envoi = false;
        _erreur = e.toString().replaceFirst('Exception: ', '');
      });
    }
  }

  /// Confirme le dépôt de manière franche.
  ///
  /// Le moment compte : la personne vient de faire une démarche vis-à-vis
  /// d'une administration et doit être certaine qu'elle a abouti. Un simple
  /// bandeau discret laisserait un doute.
  void _afficherConfirmation() {
    showModalBottomSheet(
      context: context,
      isDismissible: false,
      enableDrag: false,
      backgroundColor: kWhite,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(26)),
      ),
      builder: (contexte) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(26, 28, 26, 22),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 68, height: 68,
                decoration: BoxDecoration(
                  color: kCiviqueLight,
                  borderRadius: BorderRadius.circular(22),
                ),
                child: const Icon(Icons.check_rounded, color: kCivique, size: 34),
              ),
              const SizedBox(height: 20),
              const Text(
                'Votre doléance est enregistrée',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 20, fontWeight: FontWeight.w800, color: kGray900,
                ),
              ),
              const SizedBox(height: 10),
              const Text(
                'Elle a été transmise au spécialiste chargé du suivi social du '
                'projet. Vous pouvez suivre son traitement depuis l\'onglet '
                '« Mes doléances ».',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 14.5, height: 1.55, color: kGray600),
              ),
              const SizedBox(height: 26),
              ElevatedButton(
                onPressed: () {
                  Navigator.pop(contexte);
                  _description.clear();
                  setState(() {
                    _envoi = false;
                    _categorie = 'bruit';
                  });
                },
                child: const Text('Terminé'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kGray50,
      appBar: AppBar(
        title: const Text('Signaler une gêne'),
        backgroundColor: kGray50,
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(22, 6, 22, 32),
          children: [
            Text(
              'Décrivez ce qui vous dérange autour du chantier. Votre '
              'signalement parvient directement à l\'équipe chargée du suivi.',
              style: TextStyle(fontSize: 14.5, height: 1.55, color: kGray600),
            ),
            const SizedBox(height: 26),

            const Text('De quoi s\'agit-il ?', style: _styleLibelle),
            const SizedBox(height: 12),
            Wrap(
              spacing: 9,
              runSpacing: 9,
              children: kCategoriesDoleance.entries.map((e) {
                final actif = _categorie == e.key;
                return GestureDetector(
                  onTap: () => setState(() => _categorie = e.key),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 180),
                    padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                    decoration: BoxDecoration(
                      color: actif ? kBlue : kWhite,
                      borderRadius: BorderRadius.circular(30),
                      border: Border.all(
                        color: actif ? kBlue : kGray200,
                        width: 1.5,
                      ),
                    ),
                    child: Text(
                      e.value,
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: actif ? kWhite : kGray800,
                      ),
                    ),
                  ),
                );
              }).toList(),
            ),

            const SizedBox(height: 26),
            const Text('Décrivez la situation', style: _styleLibelle),
            const SizedBox(height: 10),
            TextField(
              controller: _description,
              maxLines: 6,
              textCapitalization: TextCapitalization.sentences,
              decoration: const InputDecoration(
                hintText: 'Par exemple : les engins travaillent la nuit et le '
                    'bruit empêche de dormir depuis une semaine.',
              ),
            ),

            const SizedBox(height: 18),
            _bandeauPosition(),

            if (_erreur.isNotEmpty) ...[
              const SizedBox(height: 18),
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: kRedLight,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: kRed.withValues(alpha: 0.25)),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.error_outline_rounded, color: kRed, size: 19),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        _erreur,
                        style: const TextStyle(
                          fontSize: 13.5, color: kRed, height: 1.5,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],

            const SizedBox(height: 26),
            ElevatedButton(
              onPressed: _envoi ? null : _envoyer,
              child: _envoi
                  ? const SizedBox(
                      width: 22, height: 22,
                      child: CircularProgressIndicator(
                          color: kWhite, strokeWidth: 2.4),
                    )
                  : const Text('Envoyer ma doléance'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _bandeauPosition() {
    final localisee = _latitude != null;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: kWhite,
        borderRadius: BorderRadius.circular(kRayonCitoyen),
        border: Border.all(color: kGray200),
      ),
      child: Row(
        children: [
          if (_positionEnCours)
            const SizedBox(
              width: 19, height: 19,
              child: CircularProgressIndicator(strokeWidth: 2.2, color: kBlue),
            )
          else
            Icon(
              localisee ? Icons.place_rounded : Icons.place_outlined,
              size: 21,
              color: localisee ? kCivique : kGray400,
            ),
          const SizedBox(width: 13),
          Expanded(
            child: Text(
              _positionEnCours
                  ? 'Relevé de votre position...'
                  : localisee
                      ? 'Position relevée, elle situera la nuisance sur la carte'
                      : 'Position indisponible, votre doléance sera rattachée '
                        'à votre chantier',
              style: const TextStyle(
                fontSize: 13, height: 1.45, color: kGray600,
              ),
            ),
          ),
        ],
      ),
    );
  }

  static const TextStyle _styleLibelle = TextStyle(
    fontSize: 15, fontWeight: FontWeight.w700, color: kGray900,
  );
}
