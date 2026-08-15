import 'package:flutter/material.dart';

import '../core/constants.dart';
import 'api_citoyen.dart';
import 'ecran_accueil.dart';
import 'theme_citoyen.dart';

/// Profil du riverain : ses informations, son rattachement, son compte.
class EcranProfilCitoyen extends StatefulWidget {
  const EcranProfilCitoyen({super.key});

  @override
  State<EcranProfilCitoyen> createState() => _EcranProfilCitoyenState();
}

class _EcranProfilCitoyenState extends State<EcranProfilCitoyen> {
  String? _chantier;

  @override
  void initState() {
    super.initState();
    _chantier = ApiCitoyen().chantierRattachement;
    _rafraichirChantier();
  }

  /// Recharge le rattachement en arrière-plan.
  ///
  /// La valeur mise en cache s'affiche immédiatement, l'appel réseau ne sert
  /// qu'à la corriger si le spécialiste a modifié le référentiel.
  Future<void> _rafraichirChantier() async {
    try {
      final libelle = await ApiCitoyen().monChantier();
      if (mounted) setState(() => _chantier = libelle);
    } catch (_) {
      // Sans réseau, la valeur en cache reste affichée : elle est exacte dans
      // l'immense majorité des cas, un rattachement ne changeant pas.
    }
  }

  Future<void> _deconnecter() async {
    final confirme = await showModalBottomSheet<bool>(
      context: context,
      backgroundColor: kWhite,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(26)),
      ),
      builder: (contexte) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(26, 26, 26, 20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 62, height: 62,
                decoration: BoxDecoration(
                  color: kRedLight,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const Icon(Icons.logout_rounded, color: kRed, size: 28),
              ),
              const SizedBox(height: 18),
              const Text(
                'Se déconnecter ?',
                style: TextStyle(
                  fontSize: 19, fontWeight: FontWeight.w800, color: kGray900,
                ),
              ),
              const SizedBox(height: 9),
              const Text(
                'Vos doléances restent enregistrées. Vous les retrouverez en '
                'vous reconnectant avec la même adresse.',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 14, height: 1.55, color: kGray600),
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                style: ElevatedButton.styleFrom(backgroundColor: kRed),
                onPressed: () => Navigator.pop(contexte, true),
                child: const Text('Me déconnecter'),
              ),
              const SizedBox(height: 10),
              OutlinedButton(
                onPressed: () => Navigator.pop(contexte, false),
                child: const Text('Annuler'),
              ),
            ],
          ),
        ),
      ),
    );

    if (confirme != true || !mounted) return;

    await ApiCitoyen().deconnecter();
    if (!mounted) return;
    Navigator.of(context).pushAndRemoveUntil(
      routeCitoyenne(const EcranAccueilCitoyen()),
      (route) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    final api = ApiCitoyen();

    return Scaffold(
      backgroundColor: kGray50,
      body: SafeArea(
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            _enTete(api),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 24, 20, 32),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Mon rattachement', style: _styleSection),
                  const SizedBox(height: 11),
                  _carteRattachement(),

                  const SizedBox(height: 26),
                  const Text('Mes informations', style: _styleSection),
                  const SizedBox(height: 11),
                  _bloc([
                    _ligne(Icons.person_outline_rounded, 'Nom',
                        api.nom ?? 'Non renseigné'),
                    _separateur(),
                    _ligne(Icons.mail_outline_rounded, 'Adresse e-mail',
                        api.email ?? 'Non renseignée'),
                  ]),

                  const SizedBox(height: 26),
                  const Text('Mon compte', style: _styleSection),
                  const SizedBox(height: 11),
                  _bloc([
                    _action(Icons.logout_rounded, 'Me déconnecter',
                        'Quitter l\'application', _deconnecter, couleur: kRed),
                  ]),

                  const SizedBox(height: 30),
                  Center(
                    child: Column(
                      children: [
                        Text(
                          'SI-ENV Citoyen',
                          style: TextStyle(
                            fontSize: 13, fontWeight: FontWeight.w700,
                            color: kGray500,
                          ),
                        ),
                        const SizedBox(height: 5),
                        Text(
                          'AGEROUTE · Mécanisme de Gestion des Plaintes\n'
                          'Projet de Transport Urbain d\'Abidjan',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: 11.5, height: 1.6, color: kGray400,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _enTete(ApiCitoyen api) {
    final nom = api.nom ?? '';
    final initiales = nom.trim().isEmpty
        ? '?'
        : nom.trim().split(RegExp(r'\s+')).take(2).map((m) => m[0]).join().toUpperCase();

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(24, 30, 24, 32),
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: kDegradeAccueil,
        ),
      ),
      child: Column(
        children: [
          Container(
            width: 78, height: 78,
            decoration: BoxDecoration(
              color: kWhite.withValues(alpha: 0.17),
              shape: BoxShape.circle,
              border: Border.all(color: kWhite.withValues(alpha: 0.35), width: 2),
            ),
            child: Center(
              child: Text(
                initiales,
                style: const TextStyle(
                  fontSize: 27, fontWeight: FontWeight.w800, color: kWhite,
                ),
              ),
            ),
          ),
          const SizedBox(height: 14),
          Text(
            nom.isEmpty ? 'Riverain' : nom,
            style: const TextStyle(
              fontSize: 20, fontWeight: FontWeight.w800, color: kWhite,
            ),
          ),
          const SizedBox(height: 5),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 5),
            decoration: BoxDecoration(
              color: kWhite.withValues(alpha: 0.18),
              borderRadius: BorderRadius.circular(20),
            ),
            child: const Text(
              'Riverain de chantier',
              style: TextStyle(
                fontSize: 12, fontWeight: FontWeight.w600, color: kWhite,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _carteRattachement() {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: kCiviqueLight,
        borderRadius: BorderRadius.circular(kRayonCitoyen + 2),
        border: Border.all(color: kCivique.withValues(alpha: 0.22)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.construction_rounded, color: kCivique, size: 23),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _chantier ?? 'Chantier en cours de chargement',
                  style: const TextStyle(
                    fontSize: 15.5, fontWeight: FontWeight.w700, color: kGray900,
                  ),
                ),
                const SizedBox(height: 6),
                const Text(
                  'Vos doléances sont orientées vers ce chantier, déterminé '
                  'automatiquement lors de votre inscription.',
                  style: TextStyle(fontSize: 13, height: 1.5, color: kGray600),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _bloc(List<Widget> enfants) => Container(
        decoration: BoxDecoration(
          color: kWhite,
          borderRadius: BorderRadius.circular(kRayonCitoyen + 2),
          border: Border.all(color: kGray200),
        ),
        child: Column(children: enfants),
      );

  Widget _separateur() => const Divider(height: 1, indent: 62, color: kGray100);

  Widget _ligne(IconData icone, String libelle, String valeur) => Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 15),
        child: Row(
          children: [
            Container(
              width: 38, height: 38,
              decoration: BoxDecoration(
                color: kBlueLight,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icone, color: kBlue, size: 19),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(libelle,
                      style: const TextStyle(fontSize: 12, color: kGray500)),
                  const SizedBox(height: 2),
                  Text(valeur,
                      style: const TextStyle(
                        fontSize: 14.5, fontWeight: FontWeight.w600,
                        color: kGray800,
                      )),
                ],
              ),
            ),
          ],
        ),
      );

  Widget _action(IconData icone, String libelle, String sous,
          VoidCallback surTap, {Color couleur = kBlue}) =>
      InkWell(
        onTap: surTap,
        borderRadius: BorderRadius.circular(kRayonCitoyen + 2),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 15),
          child: Row(
            children: [
              Container(
                width: 38, height: 38,
                decoration: BoxDecoration(
                  color: couleur.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icone, color: couleur, size: 19),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(libelle,
                        style: const TextStyle(
                          fontSize: 14.5, fontWeight: FontWeight.w600,
                          color: kGray800,
                        )),
                    Text(sous,
                        style: const TextStyle(fontSize: 12, color: kGray500)),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right_rounded, color: kGray400, size: 20),
            ],
          ),
        ),
      );

  static const TextStyle _styleSection = TextStyle(
    fontSize: 13, fontWeight: FontWeight.w700, color: kGray800,
    letterSpacing: 0.2,
  );
}
