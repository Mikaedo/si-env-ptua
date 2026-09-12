import 'package:flutter_test/flutter_test.dart';
import 'package:si_env/services/ia_service.dart';

/// Verifie que le decompte des dechets ne compte chaque objet qu'une fois.
///
/// La criticite d'un signalement est deduite de ce nombre : un ou deux
/// dechets pour une accumulation faible, trois a cinq pour moderee, six
/// ou plus pour importante. Un doublon suffit donc a faire changer de
/// classe un constat, sans qu'aucun dechet supplementaire soit sur le
/// terrain.
void main() {
  DetectionBox boite(
    double x,
    double y,
    double cote,
    String etiquette,
    double confiance,
  ) =>
      DetectionBox(
        x: x,
        y: y,
        width: cote,
        height: cote,
        label: etiquette,
        confidence: confiance,
      );

  group('Suppression des doublons de detection', () {
    test('deux cadres sur le meme dechet ne comptent que pour un', () {
      // YOLOv8 evalue 2100 ancres : plusieurs se declenchent sur un meme
      // objet et produisent des cadres presque superposes.
      final brut = [
        boite(0.10, 0.10, 0.20, 'plastique', 0.91),
        boite(0.11, 0.11, 0.20, 'plastique', 0.84),
        boite(0.105, 0.10, 0.20, 'plastique', 0.77),
      ];
      expect(IaService.filtrerDoublons(brut).length, 1);
    });

    test('la meilleure confiance est celle qui est retenue', () {
      final brut = [
        boite(0.10, 0.10, 0.20, 'plastique', 0.62),
        boite(0.11, 0.11, 0.20, 'plastique', 0.93),
      ];
      final gardees = IaService.filtrerDoublons(brut);
      expect(gardees.length, 1);
      expect(gardees.first.confidence, closeTo(0.93, 1e-9));
    });

    test('un objet reconnu sous deux categories reste un objet', () {
      // C'est le cas signale : la meme zone se voit attribuer deux
      // etiquettes concurrentes, et la categorie apparaissait deux fois.
      final brut = [
        boite(0.30, 0.30, 0.25, 'plastique', 0.72),
        boite(0.31, 0.30, 0.25, 'verre', 0.68),
      ];
      expect(IaService.filtrerDoublons(brut).length, 1);
    });

    test('deux dechets distincts restent comptes separement', () {
      final brut = [
        boite(0.05, 0.05, 0.15, 'carton', 0.88),
        boite(0.60, 0.60, 0.15, 'carton', 0.85),
      ];
      expect(IaService.filtrerDoublons(brut).length, 2);
    });

    test('six dechets distincts donnent bien six objets', () {
      // Le seuil de l'accumulation importante : le comptage doit y mener
      // sans le franchir par accident.
      final brut = [
        boite(0.02, 0.02, 0.10, 'metal', 0.80),
        boite(0.20, 0.02, 0.10, 'papier', 0.80),
        boite(0.40, 0.02, 0.10, 'verre', 0.80),
        boite(0.02, 0.40, 0.10, 'carton', 0.80),
        boite(0.20, 0.40, 0.10, 'organique', 0.80),
        boite(0.40, 0.40, 0.10, 'plastique', 0.80),
      ];
      expect(IaService.filtrerDoublons(brut).length, 6);
    });

    test('un chevauchement partiel reste deux dechets', () {
      // Deux sacs poses cote a cote se touchent sans se confondre :
      // les ecarter serait sous-compter le tas.
      final brut = [
        boite(0.10, 0.10, 0.20, 'plastique', 0.90),
        boite(0.26, 0.10, 0.20, 'plastique', 0.86),
      ];
      expect(IaService.filtrerDoublons(brut).length, 2);
    });

    test('une liste vide ou unique passe sans modification', () {
      expect(IaService.filtrerDoublons(const []), isEmpty);
      expect(
        IaService.filtrerDoublons([boite(0.1, 0.1, 0.2, 'metal', 0.7)]).length,
        1,
      );
    });
  });
}
