import '../../../../core/auth/data/models/user_model.dart';

class AuthResponseModel {
  final String accessToken;
  final String refreshToken;
  final int expiresIn;
  final UserModel user;

  AuthResponseModel({
    required this.accessToken,
    required this.refreshToken,
    required this.expiresIn,
    required this.user,
  });

  factory AuthResponseModel.fromJson(Map<String, dynamic> json) {
    // Note: The API contract says the response might be wrapped in a "data" field
    final data = json['data'] ?? json;
    
    // Validate required fields exist
    if (data['access_token'] == null || data['user'] == null) {
      throw const FormatException('Malformed auth response: missing access_token or user info');
    }

    return AuthResponseModel(
      accessToken: data['access_token'] as String,
      refreshToken: (data['refresh_token'] as String?) ?? '',
      expiresIn: (data['expires_in'] as int?) ?? 3600,
      user: UserModel.fromJson(data['user'] as Map<String, dynamic>),
    );
  }
}
