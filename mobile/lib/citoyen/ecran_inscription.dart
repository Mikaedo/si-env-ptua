import 'package:flutter/material.dart';

import '../core/constants.dart';
import 'api_citoyen.dart';
import 'navigation_citoyen.dart';
import 'theme_citoyen.dart';

/// Création du compte riverain, une fois la position validée.
///
/// Le chantier de rattachement est déjà connu à ce stade : il a été déduit de
/// la position et non choisi dans une liste. Un habitant n'a aucune raison de
/// connaître les dénominations administratives des ouvrages, et lui demander
/// de s'y retrouver reviendrait à lui faire porter une complexité qui ne le
/// concerne pas.
class EcranInscription extends StatefulWidget {
  final ZoneVerifiee zone;
  final double latitude;
  final double longitude;

  const EcranInscription({
    super.key,
    required this.zone,
    required this.latitude,
    required this.longitude,
  });

  @override
  State<EcranInscription> createState() => _EcranInscriptionState();
}

class _EcranInscriptionState extends State<EcranInscription> {
  final _nom = TextEditingController();
  final _email = TextEditingController();
  final _telephone = TextEditingController();
  final _motDePasse = TextEditingController();
  final _confirmation = TextEditingController();

  bool _masque = true;
  bool _envoi = false;
  String _erreur = '';

  @override
  void dispose() {
    _nom.dispose();
    _email.dispose();
    _telephone.dispose();
    _motDePasse.dispose();
    _confirmation.dispose();
    super.dispose();
  }

  Future<void> _creer() async {
    if (_nom.text.trim().isEmpty) {
      setState(() => _erreur = 'Veuillez indiquer votre nom.');
      return;
    }
    if (!_email.text.contains('@')) {
      setState(() => _erreur = 'Veuillez saisir une adresse e-mail valide.');
      return;
    }
    if (_motDePasse.text.length < 8) {
      setState(() => _erreur = 'Le mot de passe doit compter au moins 8 caractères.');
      return;
    }
    if (_motDePasse.text != _confirmation.text) {
      setState(() => _erreur = 'Les deux mots de passe ne correspondent pas.');
      return;
    }

    setState(() {
      _envoi = true;
      _erreur = '';
    });

    try {
      await ApiCitoyen().inscrire(
        nom: _nom.text.trim(),
        email: _email.text.trim(),
        motDePasse: _motDePasse.text,
        telephone: _telephone.text.trim().isEmpty ? null : _telephone.text.trim(),
        latitude: widget.latitude,
        longitude: widget.longitude,
      );
      final libelle = widget.zone.commune != null && widget.zone.commune!.isNotEmpty
          ? '${widget.zone.chantierNom}, ${widget.zone.commune}'
          : widget.zone.chantierNom;
      await ApiCitoyen().enregistrerChantier(libelle);

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
      appBar: AppBar(
        title: const Text('Créer mon compte'),
        backgroundColor: kGray50,
      ),
      backgroundColor: kGray50,
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(22, 8, 22, 32),
          children: [
            _bandeauRattachement(),
            const SizedBox(height: 24),

            _champ('Nom complet', _nom, 'Votre nom et prénom',
                clavier: TextInputType.name),
            _champ('Adresse e-mail', _email, 'exemple@courriel.com',
                clavier: TextInputType.emailAddress),
            _champ('Téléphone', _telephone, '07 00 00 00 00',
                clavier: TextInputType.phone, facultatif: true),

            _champMotDePasse('Mot de passe', _motDePasse,
                '8 caractères minimum'),
            _champMotDePasse('Confirmation', _confirmation,
                'Saisissez à nouveau le mot de passe', masqueLie: true),

            if (_erreur.isNotEmpty) ...[
              const SizedBox(height: 6),
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

            const SizedBox(height: 22),
            ElevatedButton(
              onPressed: _envoi ? null : _creer,
              child: _envoi
                  ? const SizedBox(
                      width: 22, height: 22,
                      child: CircularProgressIndicator(
                          color: kWhite, strokeWidth: 2.4),
                    )
                  : const Text('Créer mon compte'),
            ),
            const SizedBox(height: 16),
            Text(
              'Vos coordonnées ne servent qu\'au suivi de vos doléances par le '
              'spécialiste chargé du volet social du projet.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 12.5, height: 1.55, color: kGray500,
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Rappelle au riverain le chantier auquel il va être rattaché.
  ///
  /// Il n'a rien à choisir, mais il doit savoir : c'est ce rattachement qui
  /// déterminera vers quel site ses doléances seront orientées.
  Widget _bandeauRattachement() {
    final z = widget.zone;
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: kCiviqueLight,
        borderRadius: BorderRadius.circular(kRayonCitoyen),
        border: Border.all(color: kCivique.withValues(alpha: 0.22)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.check_circle_outline_rounded, color: kCivique, size: 22),
          const SizedBox(width: 13),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Vous êtes riverain de',
                  style: TextStyle(
                    fontSize: 12.5, color: kCivique, fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  z.commune != null && z.commune!.isNotEmpty
                      ? '${z.chantierNom}, ${z.commune}'
                      : z.chantierNom,
                  style: const TextStyle(
                    fontSize: 16, fontWeight: FontWeight.w700, color: kGray900,
                  ),
                ),
                const SizedBox(height: 5),
                Text(
                  'à ${z.distanceLisible} de votre position',
                  style: const TextStyle(fontSize: 13, color: kGray600),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _champ(String libelle, TextEditingController controleur, String indice,
      {TextInputType? clavier, bool facultatif = false}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(libelle, style: _styleLibelle),
              if (facultatif) ...[
                const SizedBox(width: 6),
                const Text('facultatif',
                    style: TextStyle(fontSize: 12.5, color: kGray400)),
              ],
            ],
          ),
          const SizedBox(height: 7),
          TextField(
            controller: controleur,
            keyboardType: clavier,
            decoration: InputDecoration(hintText: indice),
          ),
        ],
      ),
    );
  }

  Widget _champMotDePasse(String libelle, TextEditingController controleur,
      String indice, {bool masqueLie = false}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(libelle, style: _styleLibelle),
          const SizedBox(height: 7),
          TextField(
            controller: controleur,
            obscureText: _masque,
            decoration: InputDecoration(
              hintText: indice,
              suffixIcon: masqueLie
                  ? null
                  : IconButton(
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
        ],
      ),
    );
  }

  static const TextStyle _styleLibelle = TextStyle(
    fontSize: 13.5, fontWeight: FontWeight.w600, color: kGray800,
  );
}
