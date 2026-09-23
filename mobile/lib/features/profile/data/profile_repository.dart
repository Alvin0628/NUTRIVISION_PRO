import '../../../core/network/api_client.dart';

class ProfileRepository {
  final ApiClient _apiClient;

  ProfileRepository({ApiClient? apiClient})
    : _apiClient = apiClient ?? ApiClient();

  Future<Map<String, dynamic>> fetchDailyTarget() async {
    final res = await _apiClient.dio.get('/users/target');
    return res.data;
  }

  Future<Map<String, dynamic>> createProfile({
    required String uid,
    required String gender,
    required int age,
    required double heightCm,
    required double weightKg,
    required String activityLevel,
    required String goal,
  }) async {
    final res = await _apiClient.dio.post(
      '/users',
      data: {
        'uid': uid,
        'gender': gender,
        'age': age,
        'height_cm': heightCm,
        'weight_kg': weightKg,
        'activity_level': activityLevel,
        'goal': goal,
      },
    );
    return res.data;
  }
}
