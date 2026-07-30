import 'package:flutter_test/flutter_test.dart';
import 'package:si_env/services/api_service.dart';
import 'package:si_env/main.dart';

void main() {
  testWidgets('SiEnvApp renders login screen initially', (WidgetTester tester) async {
    await tester.pumpWidget(SiEnvApp(api: ApiService()));
    await tester.pumpAndSettle(const Duration(seconds: 2));
    expect(find.text('SI-ENV'), findsWidgets);
  });
}
