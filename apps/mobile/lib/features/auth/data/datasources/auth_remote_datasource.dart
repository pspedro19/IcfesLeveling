import 'package:dio/dio.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/constants/api_constants.dart';
import '../models/auth_response_model.dart';
import '../../../../core/auth/data/models/user_model.dart';

class AuthRemoteDataSource {
  final ApiClient _apiClient;

  AuthRemoteDataSource(this._apiClient);

  Future<AuthResponseModel> login(String email, String password) async {
    final response = await _apiClient.post(
      ApiConstants.login,
      data: 'username=$email&password=$password',
      options: Options(
        contentType: 'application/x-www-form-urlencoded',
      ),
    );

    if (response.statusCode == 200) {
      return AuthResponseModel.fromJson(response.data);
    } else {
      throw Exception('Login failed: ${response.data['detail']}');
    }
  }

  Future<AuthResponseModel> register(String email, String password, String name) async {
    final response = await _apiClient.post(
      ApiConstants.register,
      data: {
        'email': email,
        'password': password,
        'username': email.contains('@') ? email.split('@')[0] : email,
        'display_name': name,
      },
    );

    if (response.statusCode == 201 || response.statusCode == 200) {
      return AuthResponseModel.fromJson(response.data);
    } else {
      throw Exception('Registration failed: ${response.data['detail']}');
    }
  }

  Future<AuthResponseModel> refreshToken(String refreshToken) async {
    final response = await _apiClient.post(
      '/auth/refresh',
      data: {'refresh_token': refreshToken},
    );

    if (response.statusCode == 200) {
      return AuthResponseModel.fromJson(response.data);
    } else {
      throw Exception('Failed to refresh token');
    }
  }

  Future<UserModel> getMe() async {
    final response = await _apiClient.get('/auth/me');
    
    if (response.statusCode == 200) {
      final data = response.data['data'] ?? response.data;
      return UserModel.fromJson(data['user'] ?? data);
    } else {
      throw Exception('Failed to get user info');
    }
  }
}
