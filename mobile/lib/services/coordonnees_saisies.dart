/// Lecture des coordonnees que l'agent saisit a la main.
///
/// La saisie manuelle repond au cas prevu par le memoire (figure 4.4) :
/// le GPS peut etre indisponible sur un chantier, et l'agent renseigne
/// alors la position lui-meme.
///
/// Il ne l'invente pas. Les coordonnees de reference de chaque chantier
/// sont relevees en amont et remises a l'agent avant sa mission : il les
/// recopie. C'est pourquoi la lecture accepte les formes qu'on recopie
/// depuis une fiche, et refuse ce qu'elle ne sait pas interpreter plutot
/// que de deviner. Une position fausse est pire qu'une position absente :
/// elle place un constat sur la carte du specialiste, qui n'a aucun moyen
/// de s'apercevoir de l'erreur.
///
/// Ce fichier n'importe rien de la plateforme, afin de rester testable
/// hors environnement Flutter.
library;

/// Une position lue dans une saisie, en degres decimaux.
class Position {
  final double latitude;
  final double longitude;

  const Position(this.latitude, this.longitude);

  @override
  bool operator ==(Object other) =>
      other is Position &&
      other.latitude == latitude &&
      other.longitude == longitude;

  @override
  int get hashCode => Object.hash(latitude, longitude);

  @override
  String toString() => 'Position($latitude, $longitude)';
}

/// Un nombre signe, suivi d'un hemisphere facultatif.
///
/// La virgule est admise comme separateur decimal : c'est celle du
/// clavier francais, et un agent la tapera naturellement.
final _motifNombre = RegExp(r'([+-]?\d{1,3}(?:[.,]\d+)?)\s*([NSEWOnsewo])?');

/// Les hemispheres qui portent les valeurs negatives. « O » est le
/// « Ouest » francais, qu'une fiche redigee en francais utilisera.
const _hemispheresNegatifs = {'S', 'W', 'O'};

/// Lit une position dans [saisie], ou renvoie null si elle est illisible.
///
/// Les formes reconnues sont celles d'une fiche de chantier, mises en
/// forme ou non :
///
///     5.36000 N, -4.01000 W     (la forme que l'application affiche)
///     5.36000, -4.01000
///     5,36000 ; -4,01000
///     5.36 -4.01
///
/// L'hemisphere donne le signe, si bien que « 4.01000 W » et
/// « -4.01000 » designent le meme meridien.
///
/// Renvoie null quand la saisie ne contient pas deux nombres lisibles, ou
/// quand elle sort des bornes terrestres : une latitude au-dela de 90
/// degres ou une longitude au-dela de 180 n'existent pas, et signalent une
/// faute de recopie.
Position? lireCoordonnees(String saisie) {
  final texte = saisie.trim();
  if (texte.isEmpty) return null;

  final trouves = _motifNombre.allMatches(texte).toList();
  if (trouves.length < 2) return null;

  final latitude = _valeur(trouves[0]);
  final longitude = _valeur(trouves[1]);
  if (latitude == null || longitude == null) return null;
  if (latitude.abs() > 90 || longitude.abs() > 180) return null;

  return Position(latitude, longitude);
}

/// Ecrit une position dans la forme que [lireCoordonnees] relit.
///
/// L'hemisphere est deduit du signe, jamais suppose : une position
/// relevee puis basculee en saisie manuelle doit se relire a l'identique.
/// Ecrire « W » en dur, comme le faisait l'ecran, place a l'ouest une
/// longitude qui pourrait etre a l'est, et un aller-retour par le champ
/// deplacerait alors le point.
///
/// Cinq decimales, soit environ un metre : la precision d'un GPS de
/// telephone, sans chiffres qui laisseraient croire a mieux.
String formaterPosition(double latitude, double longitude) {
  final ns = latitude < 0 ? 'S' : 'N';
  final ew = longitude < 0 ? 'W' : 'E';
  return '${latitude.abs().toStringAsFixed(5)} $ns, '
      '${longitude.abs().toStringAsFixed(5)} $ew';
}

double? _valeur(RegExpMatch trouve) {
  final nombre = double.tryParse(trouve.group(1)!.replaceAll(',', '.'));
  if (nombre == null) return null;

  final hemisphere = trouve.group(2)?.toUpperCase();
  if (hemisphere != null && _hemispheresNegatifs.contains(hemisphere)) {
    return -nombre.abs();
  }
  return nombre;
}
