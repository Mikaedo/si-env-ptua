import 'package:flutter/material.dart';

import '../core/constants.dart';
import '../services/gps_service.dart';
import 'api_citoyen.dart';
import 'ecran_connexion.dart';
import 'ecran_inscription.dart';
import 'navigation_citoyen.dart';
import 'theme_citoyen.dart';

/// Premier écran de l'application citoyenne.
///
/// Il enchaîne trois choses avant de laisser entrer qui que ce soit : il
/// vérifie qu'une session existe déjà, sinon il demande la position, puis il
/// interroge le serveur pour savoir si cette position ouvre droit à l'accès.
///
/// Ce contrôle géographique est la règle de fond de l'application. Une plainte
/// environnementale n'a de sens que si elle émane de quelqu'un qui subit
/// réellement la nuisance, et le dispositif serait vite saturé s'il acceptait
/// des dépôts venus de n'importe où. Le périmètre retenu n'est pas arbitraire :
/// il correspond à la zone d'influence que le spécialiste du suivi
/// environnemental fixe chantier par chantier, notion que tout PGES manipule
/// sous le nom d'aire d'étude.
class EcranAccueilCitoyen extends StatefulWidget {
  const EcranAccueilCitoyen({super.key});

  @override
  State<EcranAccueilCitoyen> createState() => _EcranAccueilCitoyenState();
}

enum _Etape { demarrage, explication, localisation, refuse, erreur }

class _EcranAccueilCitoyenState extends State<EcranAccueilCitoyen>
    with SingleTickerProviderStateMixin {
  _Etape _etape = _Etape.demarrage;
  ZoneVerifiee? _zone;
  String _message = '';

  late final AnimationController _anim;
  late final Animation<double> _fondu;

  @override
  void initState() {
    super.initState();
    _anim = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 700),
    );
    _fondu = CurvedAnimation(parent: _anim, curve: Curves.easeOut);
    _demarrer();
  }

  @override
  void dispose() {
    _anim.dispose();
    super.dispose();
  }

  Future<void> _demarrer() async {
    await ApiCitoyen().charger();
    if (!mounted) return;

    // Session déjà ouverte : on ne redemande pas la position à chaque
    // lancement, le rattachement au chantier ayant été établi une fois pour
    // toutes à l'inscription.
    if (ApiCitoyen().connecte) {
      await Future.delayed(const Duration(milliseconds: 600));
      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        routeCitoyenne(const NavigationCitoyen()),
      );
      return;
    }

    setState(() => _etape = _Etape.explication);
    _anim.forward();
  }

  Future<void> _verifierPosition() async {
    setState(() => _etape = _Etape.localisation);

    final position = await GpsService.getCurrentPosition();
    if (!mounted) return;

    if (position == null) {
      setState(() {
        _etape = _Etape.erreur;
        _message = "Nous n'avons pas pu obtenir votre position. "
            "Vérifiez que la localisation est activée sur votre téléphone, "
            "puis réessayez.";
      });
      return;
    }

    try {
      final zone = await ApiCitoyen()
          .verifierZone(position.latitude, position.longitude);
      if (!mounted) return;

      if (!zone.autorise) {
        setState(() {
          _zone = zone;
          _etape = _Etape.refuse;
        });
        return;
      }

      Navigator.of(context).push(
        routeCitoyenne(EcranInscription(
          zone: zone,
          latitude: position.latitude,
          longitude: position.longitude,
        )),
      );
      setState(() => _etape = _Etape.explication);
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _etape = _Etape.erreur;
        _message = e.toString().replaceFirst('Exception: ', '');
      });
    }
  }

  void _versConnexion() {
    Navigator.of(context).push(routeCitoyenne(const EcranConnexionCitoyen()));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: kDegradeAccueil,
          ),
        ),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(26, 20, 26, 26),
            child: _etape == _Etape.demarrage
                ? const Center(
                    child: CircularProgressIndicator(color: kWhite),
                  )
                : FadeTransition(opacity: _fondu, child: _contenu()),
          ),
        ),
      ),
    );
  }

  Widget _contenu() {
    // La mise en page reposait sur des proportions fixes, un Spacer et un
    // Expanded se partageant la hauteur. Sur un ecran moins haut que celui de
    // reference, le bloc central debordait de la part qui lui etait allouee et
    // se retrouvait rogne : la premiere ligne du titre disparaissait.
    //
    // Le contenu defile donc desormais librement, et n'occupe la hauteur
    // disponible que lorsqu'elle suffit. Le pied reste ancre en bas, ce qui
    // maintient le bouton d'action a portee de pouce.
    return LayoutBuilder(
      builder: (contexte, contraintes) {
        return Column(
          children: [
            Expanded(
              child: SingleChildScrollView(
                child: ConstrainedBox(
                  constraints: BoxConstraints(minHeight: contraintes.maxHeight),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const SizedBox(height: 24),
                      _enTete(),
                      const SizedBox(height: 30),
                      _corps(),
                      const SizedBox(height: 24),
                    ],
                  ),
                ),
              ),
            ),
            _pied(),
          ],
        );
      },
    );
  }

  Widget _enTete() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 62,
          height: 62,
          decoration: BoxDecoration(
            color: kWhite.withValues(alpha: 0.16),
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: kWhite.withValues(alpha: 0.3), width: 1.5),
          ),
          child: const Icon(Icons.campaign_outlined, color: kWhite, size: 30),
        ),
        const SizedBox(height: 18),
        const Text(
          'SI-ENV Citoyen',
          style: TextStyle(
            fontSize: 28, fontWeight: FontWeight.w800, color: kWhite,
            letterSpacing: -0.4,
          ),
        ),
        const SizedBox(height: 7),
        Text(
          'Signalez les nuisances des chantiers\ndu Projet de Transport Urbain d\'Abidjan',
          style: TextStyle(
            fontSize: 15, height: 1.5,
            color: kWhite.withValues(alpha: 0.78),
          ),
        ),
      ],
    );
  }

  Widget _corps() {
    switch (_etape) {
      case _Etape.localisation:
        return _bloc(
          icone: Icons.my_location_rounded,
          titre: 'Localisation en cours',
          texte: 'Nous recherchons le chantier le plus proche de vous. '
              'Cette opération prend quelques secondes.',
          enCours: true,
        );

      case _Etape.refuse:
        final z = _zone!;
        return _bloc(
          icone: Icons.location_off_outlined,
          titre: 'Vous n\'êtes pas dans une zone couverte',
          texte: 'Le chantier le plus proche, ${z.chantierNom}, se situe à '
              '${z.distanceLisible} de votre position.\n\n'
              'Cette application est réservée aux riverains des chantiers du '
              'PTUA, afin que les doléances proviennent bien des personnes '
              'qui subissent les nuisances.',
          couleur: kOrange,
        );

      case _Etape.erreur:
        return _bloc(
          icone: Icons.error_outline_rounded,
          titre: 'Nous n\'avons pas pu vous localiser',
          texte: _message,
          couleur: kRed,
        );

      case _Etape.explication:
      default:
        return _bloc(
          icone: Icons.place_outlined,
          titre: 'Nous avons besoin de votre position',
          texte: 'Elle nous sert à vérifier que vous résidez à proximité d\'un '
              'chantier du programme, et à vous rattacher automatiquement au '
              'bon site.\n\n'
              'Votre position n\'est utilisée que pour cette vérification et '
              'pour situer les nuisances que vous signalerez.',
        );
    }
  }

  Widget _bloc({
    required IconData icone,
    required String titre,
    required String texte,
    Color couleur = kWhite,
    bool enCours = false,
  }) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: kWhite.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(kRayonCitoyen + 4),
        border: Border.all(color: kWhite.withValues(alpha: 0.16)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              if (enCours)
                const SizedBox(
                  width: 22, height: 22,
                  child: CircularProgressIndicator(color: kWhite, strokeWidth: 2.4),
                )
              else
                Icon(icone, color: couleur, size: 24),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  titre,
                  style: const TextStyle(
                    fontSize: 17, fontWeight: FontWeight.w700, color: kWhite,
                    height: 1.3,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Text(
            texte,
            style: TextStyle(
              fontSize: 14.5, height: 1.6,
              color: kWhite.withValues(alpha: 0.82),
            ),
          ),
        ],
      ),
    );
  }

  Widget _pied() {
    final enCours = _etape == _Etape.localisation;

    return Column(
      children: [
        SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: enCours ? null : _verifierPosition,
            style: ElevatedButton.styleFrom(
              backgroundColor: kWhite,
              foregroundColor: kBlue,
              disabledBackgroundColor: kWhite.withValues(alpha: 0.5),
            ),
            child: Text(
              switch (_etape) {
                _Etape.refuse => 'Vérifier à nouveau',
                _Etape.erreur => 'Réessayer',
                _Etape.localisation => 'Localisation...',
                _ => 'Autoriser ma position',
              },
            ),
          ),
        ),
        const SizedBox(height: 12),
        TextButton(
          onPressed: enCours ? null : _versConnexion,
          child: Text(
            'J\'ai déjà un compte',
            style: TextStyle(
              fontSize: 14.5,
              fontWeight: FontWeight.w600,
              color: kWhite.withValues(alpha: 0.9),
            ),
          ),
        ),
        const SizedBox(height: 6),
        Text(
          'AGEROUTE · Mécanisme de Gestion des Plaintes',
          style: TextStyle(
            fontSize: 11.5,
            color: kWhite.withValues(alpha: 0.5),
          ),
        ),
      ],
    );
  }
}
