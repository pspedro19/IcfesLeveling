import '../../../../core/auth/domain/entities/user.dart';
import '../../domain/repositories/auth_repository.dart';
import '../../../../core/auth/data/datasources/auth_local_datasource.dart';
import '../datasources/auth_remote_datasource.dart';

class AuthRepositoryImpl implements AuthRepository {
  final AuthRemoteDataSource _remoteDataSource;
  final AuthLocalDataSource _localDataSource;

  AuthRepositoryImpl(this._remoteDataSource, this._localDataSource);

  @override
  Future<User> login(String email, String password) async {
    final authResponse = await _remoteDataSource.login(email, password);
    await _localDataSource.saveTokens(authResponse.accessToken, authResponse.refreshToken);
    await _localDataSource.cacheUser(authResponse.user);
    return authResponse.user;
  }

  @override
  Future<User> register(String email, String password, String name) async {
    final authResponse = await _remoteDataSource.register(email, password, name);
    await _localDataSource.saveTokens(authResponse.accessToken, authResponse.refreshToken);
    await _localDataSource.cacheUser(authResponse.user);
    return authResponse.user;
  }

  @override
  Future<void> logout() async {
    await _localDataSource.clearTokens();
    await _localDataSource.clearCache();
  }

  @override
  Future<User?> getCurrentUser() async {
    // Try to get from cache first for fast startup
    final cached = await _localDataSource.getCachedUser();
    if (cached != null) return cached;

    // If online, try to get fresh data
    try {
      final user = await _remoteDataSource.getMe();
      await _localDataSource.cacheUser(user);
      return user;
    } catch (e) {
      return null;
    }
  }

  @override
  Future<String?> getAccessToken() async {
    return await _localDataSource.getAccessToken();
  }

  @override
  Future<void> refreshToken() async {
    final refresh = await _localDataSource.getRefreshToken();
    if (refresh == null) throw Exception('No refresh token available');
    
    final authResponse = await _remoteDataSource.refreshToken(refresh);
    await _localDataSource.saveTokens(authResponse.accessToken, authResponse.refreshToken);
    await _localDataSource.cacheUser(authResponse.user);
  }
}
