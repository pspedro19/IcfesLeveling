import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:hive_flutter/hive_flutter.dart';
import '../models/user_model.dart';

// Note: authLocalDataSourceProvider is defined in core/network/api_client.dart
// to ensure proper dependency injection with secureStorageProvider

class AuthLocalDataSource {
  final FlutterSecureStorage _secureStorage;
  static const _boxName = 'user_box';
  static const _userKey = 'cached_user';
  static const _tokenKey = 'access_token';
  static const _refreshKey = 'refresh_token';

  AuthLocalDataSource(this._secureStorage);

  Future<void> saveTokens(String accessToken, String refreshToken) async {
    await _secureStorage.write(key: _tokenKey, value: accessToken);
    await _secureStorage.write(key: _refreshKey, value: refreshToken);
  }

  Future<String?> getAccessToken() async {
    return await _secureStorage.read(key: _tokenKey);
  }

  Future<String?> getRefreshToken() async {
    return await _secureStorage.read(key: _refreshKey);
  }

  Future<void> clearTokens() async {
    await _secureStorage.delete(key: _tokenKey);
    await _secureStorage.delete(key: _refreshKey);
  }

  Future<void> cacheUser(UserModel user) async {
    final box = await Hive.openBox(_boxName);
    await box.put(_userKey, jsonEncode(user.toJson()));
  }

  Future<UserModel?> getCachedUser() async {
    final box = await Hive.openBox(_boxName);
    final userData = box.get(_userKey);
    if (userData != null) {
      return UserModel.fromJson(jsonDecode(userData));
    }
    return null;
  }

  Future<void> clearCache() async {
    final box = await Hive.openBox(_boxName);
    await box.delete(_userKey);
  }
}
