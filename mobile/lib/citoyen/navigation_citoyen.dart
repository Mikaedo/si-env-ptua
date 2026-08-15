import 'package:flutter/material.dart';

import '../core/constants.dart';
import 'ecran_depot.dart';
import 'ecran_mes_doleances.dart';
import 'ecran_profil.dart';

/// Coque de navigation de l'application citoyenne.
///
/// Trois onglets, pas un de plus. L'application des agents en compte quatre
/// plus un bouton central, parce qu'un agent y passe ses journées et a besoin
/// d'une carte, de statistiques et de filtres. Un riverain, lui, vient
/// signaler une gêne et savoir où en est son dossier : au-delà de ces deux
/// besoins et de son profil, tout ajout ne ferait que le perdre.
class NavigationCitoyen extends StatefulWidget {
  const NavigationCitoyen({super.key});

  @override
  State<NavigationCitoyen> createState() => _NavigationCitoyenState();
}

class _NavigationCitoyenState extends State<NavigationCitoyen> {
  int _onglet = 0;

  // Les écrans sont conservés vivants d'un onglet à l'autre : basculer sur le
  // profil puis revenir ne doit pas effacer une doléance en cours de saisie.
  final _ecrans = const [
    EcranDepot(),
    EcranMesDoleances(),
    EcranProfilCitoyen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: _onglet, children: _ecrans),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: kWhite,
          border: Border(top: BorderSide(color: kGray200, width: 1)),
          boxShadow: const [
            BoxShadow(color: kShadowColor, blurRadius: 12, offset: Offset(0, -2)),
          ],
        ),
        child: SafeArea(
          top: false,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
            child: Row(
              children: [
                _bouton(0, Icons.add_circle_outline_rounded,
                    Icons.add_circle_rounded, 'Signaler'),
                _bouton(1, Icons.list_alt_outlined,
                    Icons.list_alt_rounded, 'Mes doléances'),
                _bouton(2, Icons.person_outline_rounded,
                    Icons.person_rounded, 'Profil'),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _bouton(int index, IconData icone, IconData iconeActive, String libelle) {
    final actif = _onglet == index;
    return Expanded(
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: () => setState(() => _onglet = index),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(vertical: 9),
          decoration: BoxDecoration(
            color: actif ? kBlueLight : Colors.transparent,
            borderRadius: BorderRadius.circular(14),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                actif ? iconeActive : icone,
                size: 23,
                color: actif ? kBlue : kGray400,
              ),
              const SizedBox(height: 4),
              Text(
                libelle,
                style: TextStyle(
                  fontSize: 11.5,
                  fontWeight: actif ? FontWeight.w700 : FontWeight.w500,
                  color: actif ? kBlue : kGray500,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
