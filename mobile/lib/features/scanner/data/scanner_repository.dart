import 'dart:io';
import 'package:dio/dio.dart';
import '../../../core/network/api_client.dart';

class ScannerRepository {
  final ApiClient _apiClient;

  ScannerRepository({ApiClient? apiClient}) 
      : _apiClient = apiClient ?? ApiClient();

  /// Send photo to endpoint FastAPI POST /predict
  Future<Map<String, dynamic>> predictFoodImage(File imageFile) async {
    try {
      String fileName = imageFile.path.split('/').last;
      
      FormData formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(
          imageFile.path,
          filename: fileName,
        ),
      });

      // Endpoint /predict return bounding box & list detected food
      final response = await _apiClient.post('/predict', data: formData);
      return response.data as Map<String, dynamic>;
    } catch (e) {
      throw Exception('Gagal mendeteksi makanan: $e');
    }
  }
}