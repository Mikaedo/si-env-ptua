import 'package:flutter_test/flutter_test.dart';
import 'package:si_env/blocs/signalement/signalement_bloc.dart';
import 'package:si_env/blocs/sync/sync_bloc.dart';
import 'package:si_env/services/api_service.dart';
import 'package:si_env/services/local_database.dart';

void main() {
  group('SignalementBloc', () {
    test('initial state is SignalementInitial', () {
      final bloc = SignalementBloc(ApiService());
      expect(bloc.state, isA<SignalementInitial>());
      bloc.close();
    });
  });

  group('SyncBloc', () {
    test('initial state is SyncInitial', () {
      final bloc = SyncBloc(ApiService(), LocalDatabase());
      expect(bloc.state, isA<SyncInitial>());
      bloc.close();
    });
  });
}
