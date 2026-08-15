import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../core/constants.dart';

/// Identité visuelle de l'application destinée aux riverains.
///
/// Elle reste de la même famille que celle des agents : mêmes bleu et orange
/// AGEROUTE, puisqu'il s'agit du même programme et que le riverain doit
/// reconnaître l'institution à laquelle il s'adresse. Le ton diffère en
/// revanche. L'application des agents est volontairement sobre, presque
/// austère : c'est un outil de travail que l'on ouvre vingt fois par jour.
/// Celle-ci s'adresse à quelqu'un qui l'ouvrira peut-être trois fois dans sa
/// vie, souvent contrarié par une nuisance, parfois peu familier des
/// applications administratives. D'où des surfaces plus larges, des angles
/// plus doux, des libellés plus longs et une hiérarchie plus explicite.

/// Vert civique, réservé aux confirmations. Il signale au riverain que sa
/// démarche a abouti, moment qui compte davantage ici que dans un outil
/// professionnel où l'enregistrement va de soi.
const Color kCivique = Color(0xFF0F766E);
const Color kCiviqueLight = Color(0xFFECFDF5);

/// Dégradé de l'écran d'accueil, repris de la page de connexion du tableau
/// de bord pour que les deux faces du système se répondent.
const List<Color> kDegradeAccueil = [kBlue, kBlueDark];

/// Rayon de bordure généreux : les cibles tactiles doivent rester confortables
/// pour une saisie faite debout, dehors, parfois d'une seule main.
const double kRayonCitoyen = 16;

ThemeData themeCitoyen() {
  final base = ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: kBlue,
      primary: kBlue,
      secondary: kOrange,
      surface: kWhite,
      error: kRed,
    ),
  );

  return base.copyWith(
    scaffoldBackgroundColor: kGray50,
    textTheme: GoogleFonts.interTextTheme(
      const TextTheme(
        // Tailles supérieures à celles de l'application des agents : le
        // riverain n'est pas un utilisateur entraîné, et la lisibilité prime
        // sur la densité d'information.
        headlineLarge: TextStyle(fontSize: 26, fontWeight: FontWeight.w800, color: kGray900),
        headlineMedium: TextStyle(fontSize: 22, fontWeight: FontWeight.w700, color: kGray900),
        titleLarge: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: kGray900),
        titleMedium: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: kGray800),
        bodyLarge: TextStyle(fontSize: 15, color: kGray800, height: 1.5),
        bodyMedium: TextStyle(fontSize: 14, color: kGray600, height: 1.5),
        bodySmall: TextStyle(fontSize: 12.5, color: kGray500, height: 1.45),
        labelLarge: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: kWhite),
      ),
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: kWhite,
      foregroundColor: kGray900,
      elevation: 0,
      centerTitle: false,
      titleTextStyle: TextStyle(
        fontSize: 18, fontWeight: FontWeight.w700, color: kGray900,
      ),
      iconTheme: IconThemeData(color: kGray800),
    ),
    cardTheme: CardThemeData(
      elevation: 0,
      color: kWhite,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(kRayonCitoyen + 2),
        side: const BorderSide(color: kGray200),
      ),
      margin: EdgeInsets.zero,
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: kBlue,
        foregroundColor: kWhite,
        // Hauteur supérieure au minimum recommandé : la saisie se fait
        // souvent en marchant ou d'une seule main.
        minimumSize: const Size(double.infinity, 56),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(kRayonCitoyen),
        ),
        textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
        elevation: 0,
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: kBlue,
        minimumSize: const Size(double.infinity, 54),
        side: const BorderSide(color: kGray200, width: 1.5),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(kRayonCitoyen),
        ),
        textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: kWhite,
      contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 17),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(kRayonCitoyen),
        borderSide: const BorderSide(color: kGray200, width: 1.5),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(kRayonCitoyen),
        borderSide: const BorderSide(color: kGray200, width: 1.5),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(kRayonCitoyen),
        borderSide: const BorderSide(color: kBlue, width: 2),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(kRayonCitoyen),
        borderSide: const BorderSide(color: kRed, width: 1.5),
      ),
      labelStyle: const TextStyle(fontSize: 14, color: kGray600),
      hintStyle: const TextStyle(fontSize: 14.5, color: kGray400),
    ),
    snackBarTheme: SnackBarThemeData(
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
    ),
  );
}

/// Transition employée dans tout le parcours citoyen.
///
/// Le glissement latéral accompagné d'un fondu donne le sentiment d'avancer
/// dans une démarche, là où une bascule sèche laisse croire que l'écran a
/// simplement changé. Sur un parcours en plusieurs étapes, cette continuité
/// aide à comprendre où l'on se situe.
Route<T> routeCitoyenne<T>(Widget page) {
  return PageRouteBuilder<T>(
    transitionDuration: const Duration(milliseconds: 380),
    reverseTransitionDuration: const Duration(milliseconds: 280),
    pageBuilder: (contexte, animation, secondaire) => page,
    transitionsBuilder: (contexte, animation, secondaire, child) {
      final adoucie = CurvedAnimation(
        parent: animation,
        curve: Curves.easeOutCubic,
        reverseCurve: Curves.easeInCubic,
      );
      return FadeTransition(
        opacity: adoucie,
        child: SlideTransition(
          position: Tween<Offset>(
            begin: const Offset(0.06, 0),
            end: Offset.zero,
          ).animate(adoucie),
          child: child,
        ),
      );
    },
  );
}
