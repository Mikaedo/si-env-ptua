import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:google_fonts/google_fonts.dart';
import 'core/constants.dart';
import 'services/api_service.dart';
import 'services/local_database.dart';
import 'blocs/auth/auth_bloc.dart';
import 'blocs/signalement/signalement_bloc.dart';
import 'blocs/sync/sync_bloc.dart';
import 'screens/nouveau_signalement_screen.dart';
import 'screens/alertes_screen.dart';
import 'screens/splash_screen.dart';
import 'screens/login_screen.dart';

/// Cle du navigateur racine.
///
/// Elle permet de declencher une navigation depuis un endroit qui n'a pas de
/// BuildContext sous un Navigator, ce qui est le cas du listener global place
/// au-dessus du MaterialApp.
final GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final api = ApiService();
  await api.loadToken();
  runApp(SiEnvApp(api: api));
}

class SiEnvApp extends StatelessWidget {
  final ApiService api;
  const SiEnvApp({super.key, required this.api});

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider(create: (_) => AuthBloc(api)..add(CheckAuthStatus())),
        BlocProvider(create: (_) => SignalementBloc(api)),
        BlocProvider(create: (_) => SyncBloc(api, LocalDatabase())),
      ],
      // Listener global de deconnexion. Il vit au-dessus du MaterialApp, donc
      // il reste monte quel que soit l'ecran affiche : la deconnexion demandee
      // depuis le profil, les parametres ou n'importe ou ailleurs ramene
      // toujours a l'ecran de connexion, en vidant la pile de navigation pour
      // qu'un retour arriere ne reouvre pas une session fermee.
      child: BlocListener<AuthBloc, AuthState>(
        listenWhen: (_, etat) => etat is AuthLoggedOut,
        listener: (contexte, etat) {
          navigatorKey.currentState?.pushAndRemoveUntil(
            MaterialPageRoute(builder: (_) => const LoginScreen()),
            (route) => false,
          );
        },
        child: MaterialApp(
        navigatorKey: navigatorKey,
        title: 'SI-ENV',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          useMaterial3: true,
          colorScheme: ColorScheme.fromSeed(
            seedColor: kBlue,
            primary: kBlue,
            secondary: kOrange,
            surface: kWhite,
            error: kRed,
          ),
          textTheme: GoogleFonts.interTextTheme(
            const TextTheme(
              headlineLarge: TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: kGray800),
              headlineMedium: TextStyle(fontSize: 22, fontWeight: FontWeight.w700, color: kGray800),
              titleLarge: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: kGray800),
              titleMedium: TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: kGray800),
              titleSmall: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: kGray800),
              bodyLarge: TextStyle(fontSize: 14, color: kGray800),
              bodyMedium: TextStyle(fontSize: 12, color: kGray600),
              bodySmall: TextStyle(fontSize: 11, color: kGray600),
              labelLarge: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: kWhite),
              labelSmall: TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: kGray800),
            ),
          ),
          appBarTheme: const AppBarTheme(
            backgroundColor: kWhite,
            foregroundColor: kGray800,
            elevation: 0,
            centerTitle: false,
            titleTextStyle: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: kGray800),
            iconTheme: IconThemeData(color: kGray800),
          ),
          cardTheme: CardThemeData(
            elevation: 0,
            color: kWhite,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            margin: EdgeInsets.zero,
          ),
          elevatedButtonTheme: ElevatedButtonThemeData(
            style: ElevatedButton.styleFrom(
              backgroundColor: kBlue,
              foregroundColor: kWhite,
              minimumSize: const Size(double.infinity, 50),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
              textStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
              elevation: 0,
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
            ),
          ),
          outlinedButtonTheme: OutlinedButtonThemeData(
            style: OutlinedButton.styleFrom(
              foregroundColor: kGray800,
              backgroundColor: kGray100,
              minimumSize: const Size(double.infinity, 48),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              side: BorderSide.none,
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
            ),
          ),
          inputDecorationTheme: InputDecorationTheme(
            filled: true,
            fillColor: kGray50,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(color: kGray200, width: 1.5),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(color: kGray200, width: 1.5),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(color: kBlue, width: 1.5),
            ),
            errorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(color: kRed, width: 1.5),
            ),
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 13),
            labelStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: kGray600),
            hintStyle: const TextStyle(fontSize: 14, color: kGray400),
          ),
          dividerTheme: const DividerThemeData(
            color: kGray100,
            thickness: 1,
            space: 1,
          ),
          snackBarTheme: SnackBarThemeData(
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        ),
        home: const SplashScreen(),
        routes: {
          '/nouveau-signalement': (_) => const NouveauSignalementScreen(typeNuisance: 'Déchets de chantier'),
          '/alertes': (_) => const AlertesScreen(),
        },
        ),
      ),
    );
  }
}
