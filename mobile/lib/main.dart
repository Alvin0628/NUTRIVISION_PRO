import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:firebase_core/firebase_core.dart';
import 'core/network/api_client.dart';
import 'core/router/app_router.dart';
import 'features/auth/data/auth_repository.dart';
import 'features/auth/presentation/bloc/auth_bloc.dart';
import 'features/auth/presentation/bloc/auth_event.dart';
import 'features/profile/data/profile_repository.dart';
import 'features/profile/presentation/cubit/profile_cubit.dart';
import 'features/auth/presentation/bloc/auth_state.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  await Firebase.initializeApp();

  final apiClient = ApiClient();
  final authRepository = AuthRepository();
  final profileRepository = ProfileRepository(apiClient: apiClient);

  runApp(
    MyApp(authRepository: authRepository, profileRepository: profileRepository),
  );
}

class MyApp extends StatefulWidget {
  final AuthRepository authRepository;
  final ProfileRepository profileRepository;

  const MyApp({
    super.key,
    required this.authRepository,
    required this.profileRepository,
  });

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  late final AuthBloc _authBloc;
  late final ProfileCubit _profileCubit;
  late final AppRouter _appRouter;

  @override
  void initState() {
    super.initState();
    _authBloc = AuthBloc(authRepository: widget.authRepository);
    _profileCubit = ProfileCubit(repository: widget.profileRepository);

    _appRouter = AppRouter(authBloc: _authBloc, profileCubit: _profileCubit);

    // run auth via listener authStateChanges
    _authBloc.add(AuthCheckRequested());
  }

  @override
  void dispose() {
    _authBloc.close();
    _profileCubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider<AuthBloc>.value(value: _authBloc),
        BlocProvider<ProfileCubit>.value(value: _profileCubit),
      ],
      child: BlocListener<AuthBloc, AuthState>(
        listenWhen: (previous, current) => current is Authenticated,
        listener: (context, state) {
          // Otomatis cek profil backend saat status terautentikasi
          _profileCubit.checkProfile();
        },
        child: MaterialApp.router(
          title: 'NutriVision Pro',
          debugShowCheckedModeBanner: false,
          theme: ThemeData(
            colorScheme: ColorScheme.fromSeed(seedColor: Colors.green),
            useMaterial3: true,
          ),
          routerConfig: _appRouter.router,
        ),
      ),
    );
  }
}
