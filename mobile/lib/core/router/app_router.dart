import 'dart:async';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../features/auth/presentation/bloc/auth_bloc.dart';
import '../../features/auth/presentation/bloc/auth_state.dart';
import '../../features/auth/presentation/pages/login_page.dart';
import '../../features/profile/presentation/cubit/profile_cubit.dart';
import '../../features/profile/presentation/cubit/profile_state.dart';
import '../../features/profile/presentation/pages/dashboard_page.dart';
import '../../features/profile/presentation/pages/onboarding_page.dart';

import 'package:flutter_bloc/flutter_bloc.dart';
import '../../features/scanner/data/scanner_repository.dart';
import '../../features/scanner/presentation/bloc/scanner_bloc.dart';
import '../../features/scanner/presentation/pages/scan_page.dart';

import 'package:mobile/features/scanner/presentation/bloc/scanner_state.dart';
import 'package:mobile/features/scanner/presentation/pages/scan_result_page.dart';

class AppRouter {
  final AuthBloc authBloc;
  final ProfileCubit profileCubit;

  AppRouter({required this.authBloc, required this.profileCubit});

  late final GoRouter router = GoRouter(
    initialLocation: '/login',
    refreshListenable: Listenable.merge([
      GoRouterRefreshStream(authBloc.stream),
      GoRouterRefreshStream(profileCubit.stream),
    ]),
    redirect: (context, state) {
      final authState = authBloc.state;
      final profileState = profileCubit.state;

      final isLoggingIn = state.matchedLocation == '/login';
      final isOnboarding = state.matchedLocation == '/onboarding';

      // 1. Not logged in -> Redirect to /login
      if (authState is Unauthenticated || authState is AuthInitial) {
        return isLoggingIn ? null : '/login';
      }

      // 2. Authenticated
      if (authState is Authenticated) {
        if (profileState is ProfileMissing) {
          return isOnboarding ? null : '/onboarding';
        }

        if (profileState is ProfileLoaded) {
          if (isLoggingIn || isOnboarding) {
            return '/dashboard';
          }
          return null;
        }
      }

      return null;
    },
    routes: [
      GoRoute(path: '/login', builder: (context, state) => const LoginPage()),
      GoRoute(
        path: '/onboarding',
        builder: (context, state) => const OnboardingPage(),
      ),
      GoRoute(
        path: '/dashboard',
        builder: (context, state) => const DashboardPage(),
      ),
      GoRoute(
        path: '/scan',
        name: 'scan',
        builder: (context, state) {
          return BlocProvider(
            create: (context) => ScannerBloc(repository: ScannerRepository()),
            child: const ScanPage(),
          );
        },
      ),
      GoRoute(
        path: '/scan/result',
        builder: (context, state) {
          final scannerState = state.extra as ScannerSuccess;
          return ScanResultPage(
            imageFile: scannerState.imageFile, // Sesuaikan dengan properti file gambar di state kamu
            initialPredictionResult: scannerState.predictionData, // Sesuaikan dengan map hasil prediksi backend
            baseUrl: "http://10.0.2.2:8000", // Atau ambil dari environment/config base URL kamu
          );
        },
      ),
    ],
  );
}

// Helper Class to change Stream Bloc/Cubit into Listenable GoRouter
class GoRouterRefreshStream extends ChangeNotifier {
  late final StreamSubscription<dynamic> _subscription;

  GoRouterRefreshStream(Stream<dynamic> stream) {
    notifyListeners();
    _subscription = stream.asBroadcastStream().listen(
      (dynamic _) => notifyListeners(),
    );
  }

  @override
  void dispose() {
    _subscription.cancel();
    super.dispose();
  }
}
