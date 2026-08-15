import 'package:flutter/material.dart';

import '../core/constants.dart';
import 'api_citoyen.dart';
import 'navigation_citoyen.dart';
import 'theme_citoyen.dart';

/// Connexion d'un riverain déjà inscrit.
///
/// Aucune vérification de position n'est faite ici : le rattachement au
/// chantier a été établi lors de l'inscription et n'a pas à être rejoué. Une
/// personne peut consulter ses doléances depuis son lieu de travail sans que
/// cela remette en cause sa qualité de riverain.
class EcranConnexionCitoyen extends StatefulWidget {
  const EcranConnexionCitoyen({super.key});

  @override
  State<EcranConnexionCitoyen> createState() => _EcranConnexionCitoyenState();
}

class _EcranConnexionCitoyenState extends State<EcranConnexionCitoyen> {
  final _email = TextEditingController();
  final _motDePasse = TextEditingController();

  bool _masque = true;
  bool _envoi = false;
  String _erreur = '';

  @override
  void dispose() {
    _email.dispose();
    _motDePasse.dispose();
    super.dispose();
  }

  Future<void> _connecter() async {
    if (_email.text.trim().isEmpty || _motDePasse.text.isEmpty) {
      setState(() => _erreur = 'Veuillez saisir votre adresse et votre mot de passe.');
      return;
    }

    setState(() {
      _envoi = true;
      _erreur = '';
    });

    try {
      await ApiCitoyen().connecter(_email.text.trim(), _motDePasse.text);
      // Le rattachement est rechargé pour l'afficher sur le profil, sans
      // bloquer l'entrée si le réseau se montre capricieux.
      try {
        await ApiCitoyen().monChantier();
      } catch (_) {}

      if (!mounted) return;
      Navigator.of(context).pushAndRemoveUntil(
        routeCitoyenne(const NavigationCitoyen()),
        (route) => false,
      );
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _envoi = false;
        _erreur = e.toString().replaceFirst('Exception: ', '');
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Connexion'), backgroundColor: kGray50),
      backgroundColor: kGray50,
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(22, 12, 22, 32),
          children: [
            const Text(
              'Content de vous revoir',
              style: TextStyle(
                fontSize: 24, fontWeight: FontWeight.w800, color: kGray900,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Connectez-vous pour déposer une doléance ou suivre celles que '
              'vous avez déjà transmises.',
              style: TextStyle(fontSize: 14.5, height: 1.55, color: kGray600),
            ),
            const SizedBox(height: 30),

            const Text('Adresse e-mail', style: _styleLibelle),
            const SizedBox(height: 7),
            TextField(
              controller: _email,
              keyboardType: TextInputType.emailAddress,
              decoration: const InputDecoration(hintText: 'exemple@courriel.com'),
            ),
            const SizedBox(height: 16),

            const Text('Mot de passe', style: _styleLibelle),
            const SizedBox(height: 7),
            TextField(
              controller: _motDePasse,
              obscureText: _masque,
              onSubmitted: (_) => _connecter(),
              decoration: InputDecoration(
                hintText: 'Votre mot de passe',
                suffixIcon: IconButton(
                  icon: Icon(
                    _masque
                        ? Icons.visibility_off_outlined
                        : Icons.visibility_outlined,
                    color: kGray400,
                  ),
                  onPressed: () => setState(() => _masque = !_masque),
                ),
              ),
            ),

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
              onPressed: _envoi ? null : _connecter,
              child: _envoi
                  ? const SizedBox(
                      width: 22, height: 22,
                      child: CircularProgressIndicator(
                          color: kWhite, strokeWidth: 2.4),
                    )
                  : const Text('Me connecter'),
            ),
            const SizedBox(height: 14),
            OutlinedButton(
              onPressed: _envoi ? null : () => Navigator.of(context).pop(),
              child: const Text('Je n\'ai pas encore de compte'),
            ),
          ],
        ),
      ),
    );
  }

  static const TextStyle _styleLibelle = TextStyle(
    fontSize: 13.5, fontWeight: FontWeight.w600, color: kGray800,
  );
}
