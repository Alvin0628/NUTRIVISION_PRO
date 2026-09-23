import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../data/auth_repository.dart';
import 'auth_event.dart';
import 'auth_state.dart';

class AuthBloc extends Bloc<AuthEvent, AuthState> {
  final AuthRepository _authRepository;

  AuthBloc({required AuthRepository authRepository})
    : _authRepository = authRepository,
      super(AuthInitial()) {
    // Listener stream inline sesuai rekomendasi mentor
    on<AuthCheckRequested>((event, emit) async {
      await emit.forEach<User?>(
        _authRepository.authStateChanges,
        onData: (user) => user != null
            ? Authenticated(uid: user.uid, email: user.email)
            : Unauthenticated(),
      );
    });

    on<SignInRequested>(_onSignInRequested);
    on<SignUpRequested>(_onSignUpRequested);
    on<GoogleSignInRequested>(_onGoogleSignInRequested);
    on<SignOutRequested>(_onSignOutRequested);
  }

  Future<void> _onSignInRequested(
    SignInRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(AuthLoading());
    try {
      final credential = await _authRepository.signInWithEmail(
        email: event.email,
        password: event.password,
      );
      final user = credential.user!;
      emit(Authenticated(uid: user.uid, email: user.email));
    } catch (e) {
      emit(AuthError(e.toString()));
    }
  }

  Future<void> _onSignUpRequested(
    SignUpRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(AuthLoading());
    try {
      final credential = await _authRepository.signUpWithEmail(
        email: event.email,
        password: event.password,
      );
      final user = credential.user!;
      emit(Authenticated(uid: user.uid, email: user.email));
    } catch (e) {
      emit(AuthError(e.toString()));
    }
  }

  Future<void> _onGoogleSignInRequested(
    GoogleSignInRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(AuthLoading());
    try {
      final credential = await _authRepository.signInWithGoogle();
      final user = credential.user!;
      emit(Authenticated(uid: user.uid, email: user.email));
    } catch (e) {
      emit(AuthError(e.toString()));
    }
  }

  Future<void> _onSignOutRequested(
    SignOutRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(AuthLoading());
    await _authRepository.signOut();
    emit(Unauthenticated());
  }
}
