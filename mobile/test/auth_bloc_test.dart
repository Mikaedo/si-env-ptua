import 'package:flutter_test/flutter_test.dart';
import 'package:si_env/blocs/auth/auth_bloc.dart';
import 'package:si_env/services/api_service.dart';

void main() {
  group('AuthBloc', () {
    test('initial state is AuthInitial', () {
      final bloc = AuthBloc(ApiService());
      expect(bloc.state, isA<AuthInitial>());
      bloc.close();
    });
  });
}
