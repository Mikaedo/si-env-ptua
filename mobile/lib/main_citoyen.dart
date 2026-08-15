import 'package:flutter/material.dart';

import 'citoyen/api_citoyen.dart';
import 'citoyen/ecran_accueil.dart';
import 'citoyen/theme_citoyen.dart';

/// Point d'entrée de l'application destinée aux riverains des chantiers.
///
/// Deux applications coexistent dans ce dépôt, bâties sur un socle commun. Les
/// agents de l'AGEROUTE et les habitants voisins des travaux ne relèvent ni du
/// même public, ni du même canal de distribution, ni du même rythme de mise à
/// jour : l'application des agents se déploie en interne, celle-ci a vocation
/// à être téléchargée librement. Les variantes de production Android
/// permettent de les installer côte à côte sur un même téléphone tout en
/// partageant le service d'API, les modèles de données, la géolocalisation et
/// la charte graphique.
///
/// Cette variante n'embarque aucun modèle de reconnaissance d'images. Un
/// riverain décrit une gêne, il ne pose pas de diagnostic environnemental :
/// la qualification relève du spécialiste chargé du volet social, qui dispose
/// du contexte du chantier.
///
/// Construction : flutter build apk --release --flavor citoyen -t lib/main_citoyen.dart
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await ApiCitoyen().charger();
  runApp(const ApplicationCitoyenne());
}

class ApplicationCitoyenne extends StatelessWidget {
  const ApplicationCitoyenne({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SI-ENV Citoyen',
      debugShowCheckedModeBanner: false,
      theme: themeCitoyen(),
      home: const EcranAccueilCitoyen(),
    );
  }
}
