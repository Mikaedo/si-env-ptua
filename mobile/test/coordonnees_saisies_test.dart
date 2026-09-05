import 'package:flutter_test/flutter_test.dart';
import 'package:si_env/services/coordonnees_saisies.dart';

/// La saisie manuelle de la position, cas par cas.
///
/// Elle repond au cas prevu par la figure 4.4 du memoire : le GPS peut
/// etre indisponible sur un chantier, et l'agent renseigne alors la
/// position en recopiant les coordonnees de reference qu'on lui a
/// remises. Ces tests couvrent donc ce qu'une recopie produit vraiment,
/// fautes comprises.
void main() {
  group('Formes qu\'une fiche de chantier produit', () {
    test('la forme que l\'application affiche elle-meme', () {
      // C'est le texte que le champ propose en exemple : il doit se
      // relire, sans quoi l'agent qui recopie l'exemple echouerait.
      final p = lireCoordonnees('5.36000 N, -4.01000 W');
      expect(p, isNotNull);
      expect(p!.latitude, closeTo(5.36, 0.00001));
      expect(p.longitude, closeTo(-4.01, 0.00001));
    });

    test('deux nombres signes, sans hemisphere', () {
      final p = lireCoordonnees('5.36000, -4.01000');
      expect(p!.latitude, closeTo(5.36, 0.00001));
      expect(p.longitude, closeTo(-4.01, 0.00001));
    });

    test('virgule decimale et point-virgule, clavier francais', () {
      final p = lireCoordonnees('5,36000 ; -4,01000');
      expect(p!.latitude, closeTo(5.36, 0.00001));
      expect(p.longitude, closeTo(-4.01, 0.00001));
    });

    test('separes par une simple espace', () {
      final p = lireCoordonnees('5.36 -4.01');
      expect(p!.latitude, closeTo(5.36, 0.00001));
      expect(p.longitude, closeTo(-4.01, 0.00001));
    });

    test('espaces superflus avant et apres', () {
      final p = lireCoordonnees('   5.36000 N, -4.01000 W   ');
      expect(p!.latitude, closeTo(5.36, 0.00001));
      expect(p.longitude, closeTo(-4.01, 0.00001));
    });

    test('hemispheres en minuscules', () {
      final p = lireCoordonnees('5.36000 n, 4.01000 w');
      expect(p!.latitude, closeTo(5.36, 0.00001));
      expect(p.longitude, closeTo(-4.01, 0.00001));
    });

    test('un signe plus explicite', () {
      final p = lireCoordonnees('+5.36000, -4.01000');
      expect(p!.latitude, closeTo(5.36, 0.00001));
      expect(p.longitude, closeTo(-4.01, 0.00001));
    });

    test('des entiers, sans decimale', () {
      final p = lireCoordonnees('5 N, 4 W');
      expect(p!.latitude, 5);
      expect(p.longitude, -4);
    });
  });

  group('L\'hemisphere donne le signe', () {
    test('W rend la longitude negative, meme ecrite en positif', () {
      // Abidjan est a l'ouest du meridien de Greenwich : « 4.01 W » et
      // « -4.01 » designent le meme meridien. Une fiche peut employer
      // l'une ou l'autre notation.
      expect(lireCoordonnees('5.36 N, 4.01 W')!.longitude,
          closeTo(-4.01, 0.00001));
    });

    test('O, le « Ouest » d\'une fiche redigee en francais', () {
      expect(lireCoordonnees('5.36 N, 4.01 O')!.longitude,
          closeTo(-4.01, 0.00001));
    });

    test('S rend la latitude negative', () {
      expect(lireCoordonnees('5.36 S, 4.01 E')!.latitude,
          closeTo(-5.36, 0.00001));
    });

    test('E laisse la longitude positive', () {
      expect(lireCoordonnees('5.36 N, 4.01 E')!.longitude,
          closeTo(4.01, 0.00001));
    });

    test('un hemisphere ne contredit pas un signe deja negatif', () {
      // « -4.01 W » est redondant mais coherent : le resultat reste a
      // l'ouest, il ne redevient pas positif.
      expect(lireCoordonnees('5.36 N, -4.01 W')!.longitude,
          closeTo(-4.01, 0.00001));
    });
  });

  group('Saisies refusees', () {
    test('un champ vide', () {
      expect(lireCoordonnees(''), isNull);
    });

    test('des espaces seulement', () {
      expect(lireCoordonnees('    '), isNull);
    });

    test('du texte, sans aucun nombre', () {
      // Le cas que le memoire denonce : « pres du pont » n'est pas une
      // position, et le systeme ne doit pas faire semblant de le lire.
      expect(lireCoordonnees('pres du pont'), isNull);
    });

    test('un seul nombre : il manque la seconde coordonnee', () {
      expect(lireCoordonnees('5.36000'), isNull);
      expect(lireCoordonnees('5.36000 N'), isNull);
    });

    test('une latitude au-dela du pole', () {
      // 91 degres de latitude n'existent pas : c'est une faute de
      // recopie, et la refuser vaut mieux que placer un point faux.
      expect(lireCoordonnees('91.0, -4.01'), isNull);
      expect(lireCoordonnees('-91.0, -4.01'), isNull);
    });

    test('une longitude au-dela de l\'antimeridien', () {
      expect(lireCoordonnees('5.36, 181.0'), isNull);
      expect(lireCoordonnees('5.36, -181.0'), isNull);
    });
  });

  group('Bornes admises', () {
    test('les valeurs extremes exactes passent', () {
      expect(lireCoordonnees('90.0, 180.0'), const Position(90, 180));
      expect(lireCoordonnees('-90.0, -180.0'), const Position(-90, -180));
    });

    test('le point zero passe', () {
      // Le golfe de Guinee, au sud de la Cote d'Ivoire : une position
      // improbable mais valide, qu'on ne doit pas confondre avec une
      // absence de saisie.
      expect(lireCoordonnees('0, 0'), const Position(0, 0));
    });
  });

  group('Ecriture et relecture', () {
    test('Abidjan s\'ecrit N et W', () {
      // L'hemisphere porte le signe, le nombre reste positif : « W »
      // dit deja l'ouest, un moins devant serait redondant.
      expect(formaterPosition(5.3547, -3.8853), '5.35470 N, 3.88530 W');
    });

    test('l\'hemisphere suit le signe, il n\'est pas suppose', () {
      // L'ecran ecrivait « N » et « W » en dur. Une longitude positive
      // s'affichait alors « W », et la relecture la rendait negative :
      // un aller-retour par le champ deplacait le point.
      expect(formaterPosition(5.3547, 3.8853), '5.35470 N, 3.88530 E');
      expect(formaterPosition(-5.3547, 3.8853), '5.35470 S, 3.88530 E');
    });

    test('ce qui est ecrit se relit a l\'identique', () {
      // La propriete qui compte : l'agent qui releve par GPS puis
      // bascule en saisie manuelle retrouve sa position, inchangee.
      for (final p in [
        const Position(5.3547, -3.8853),
        const Position(5.36, -4.01),
        const Position(-12.5, 45.75),
        const Position(0, 0),
        const Position(90, 180),
        const Position(-90, -180),
      ]) {
        final relu = lireCoordonnees(
          formaterPosition(p.latitude, p.longitude),
        );
        expect(relu, isNotNull, reason: 'illisible : $p');
        expect(relu!.latitude, closeTo(p.latitude, 0.00001), reason: '$p');
        expect(relu.longitude, closeTo(p.longitude, 0.00001), reason: '$p');
      }
    });
  });

  group('Le chantier de demonstration', () {
    test('les coordonnees de l\'UPB Bingerville se relisent', () {
      // Le site de demonstration de la soutenance. Si cette lecture
      // echouait, la demonstration de la saisie manuelle echouerait
      // devant le jury.
      final p = lireCoordonnees('5.35470 N, -3.88530 W');
      expect(p!.latitude, closeTo(5.3547, 0.00001));
      expect(p.longitude, closeTo(-3.8853, 0.00001));
    });
  });
}
