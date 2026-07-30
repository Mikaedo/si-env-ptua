import 'package:flutter_bloc/flutter_bloc.dart';
import '../../services/api_service.dart';

abstract class AuthEvent {}

class CheckAuthStatus extends AuthEvent {}

class LoginRequested extends AuthEvent {
  final String email;
  final String password;
  LoginRequested(this.email, this.password);
}

class FirstLoginRequested extends AuthEvent {
  final String nom;
  final String telephone;
  final String password;
  FirstLoginRequested(this.nom, this.telephone, this.password);
}

class LogoutRequested extends AuthEvent {}

class AuthState {}

class AuthInitial extends AuthState {}

class AuthLoading extends AuthState {}

class AuthAuthenticated extends AuthState {
  final String role;
  final bool premiereConnexion;
  AuthAuthenticated({required this.role, required this.premiereConnexion});
}

class AuthError extends AuthState {
  final String message;
  AuthError(this.message);
}

class AuthBloc extends Bloc<AuthEvent, AuthState> {
  final ApiService _api;

  AuthBloc(this._api) : super(AuthInitial()) {
    on<CheckAuthStatus>((event, emit) {
      if (_api.token != null) {
        emit(AuthAuthenticated(
          role: _api.role ?? '',
          premiereConnexion: _api.premiereConnexion ?? false,
        ));
      } else {
        emit(AuthInitial());
      }
    });

    on<LoginRequested>((event, emit) async {
      emit(AuthLoading());
      try {
        final data = await _api.login(event.email, event.password);
        final role = data['role'] ?? '';
        const mobileRoles = ['RESP_ENV', 'EXPERT_HSE'];
        if (!mobileRoles.contains(role)) {
          await _api.clearToken();
          emit(AuthError('Email ou mot de passe incorrect'));
          return;
        }
        emit(AuthAuthenticated(
          role: role,
          premiereConnexion: data['premiere_connexion'] ?? false,
        ));
      } catch (e) {
        emit(AuthError(e.toString().replaceFirst('Exception: ', '')));
      }
    });

    on<FirstLoginRequested>((event, emit) async {
      emit(AuthLoading());
      try {
        await _api.firstLogin(event.nom, event.telephone, event.password);
        emit(AuthAuthenticated(role: _api.role ?? '', premiereConnexion: false));
      } catch (e) {
        emit(AuthError(e.toString().replaceFirst('Exception: ', '')));
      }
    });

    on<LogoutRequested>((event, emit) async {
      await _api.clearToken();
      emit(AuthInitial());
    });
  }
}
