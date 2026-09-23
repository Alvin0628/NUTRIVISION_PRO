import 'package:dio/dio.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../data/profile_repository.dart';
import 'profile_state.dart';

class ProfileCubit extends Cubit<ProfileState> {
  final ProfileRepository _repository;

  ProfileCubit({required ProfileRepository repository})
      : _repository = repository,
        super(ProfileInitial());

  /// check status profile & nutrition
  Future<void> checkProfile() async {
    emit(ProfileChecking());
    try {
      final target = await _repository.fetchDailyTarget();
      emit(ProfileLoaded(target));
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) {
        emit(ProfileMissing());
      } else {
        emit(ProfileError(_extractErrorMessage(e)));
      }
    } catch (e) {
      emit(ProfileError(e.toString()));
    }
  }

  /// Send onboarding data to backend to create new profile
  Future<void> submitOnboarding(Map<String, dynamic> profileData) async {
    emit(ProfileChecking());
    try {
      await _repository.createProfile(
        uid: profileData['uid'],
        gender: profileData['gender'],
        age: profileData['age'],
        heightCm: profileData['height_cm'],
        weightKg: profileData['weight_kg'],
        activityLevel: profileData['activity_level'],
        goal: profileData['goal'],
      );
      // Refresh status -> automatically move to ProfileLoaded
      await checkProfile();
    } on DioException catch (e) {
      emit(ProfileError(_extractErrorMessage(e)));
    } catch (e) {
      emit(ProfileError(e.toString()));
    }
  }

  /// Helper for extract error messages from FastApi/Dio
  String _extractErrorMessage(DioException e) {
    if (e.response != null && e.response?.data != null) {
      final data = e.response!.data;

      if (data is Map<String, dynamic> && data.containsKey('detail')) {
        final detail = data['detail'];

        if (detail is List) {
          final errors = detail.map((err) {
            if (err is Map) {
              final loc = (err['loc'] as List?)?.last ?? 'field';
              final msg = err['msg'] ?? 'invalid value';
              return '$loc ($msg)';
            }
            return err.toString();
          }).join(', ');
          return 'Validation Error: $errors';
        }

        // Error message string from FastAPI detail
        return detail.toString();
      }

      return data.toString();
    }
    return e.message ?? 'A network error occurred. Please try again.';
  }
}