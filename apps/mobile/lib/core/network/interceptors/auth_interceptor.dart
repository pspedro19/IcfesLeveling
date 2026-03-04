import 'dart:async';
import 'package:dio/dio.dart';
import '../../auth/data/datasources/auth_local_datasource.dart';
import '../../utils/sync_logger.dart';
import '../../constants/api_constants.dart';
import '../../error/fallback_handler.dart';

/// Stream controller for auth status updates
final authStatusController = StreamController<AuthStatus>.broadcast();

/// Authentication status enum
enum AuthStatus {
  authenticated,
  refreshing,
  expired,
  unauthenticated,
}

class AuthInterceptor extends Interceptor {
  final AuthLocalDataSource _localDataSource;
  bool _isRefreshing = false;

  AuthInterceptor(this._localDataSource);

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    final token = await _localDataSource.getAccessToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    // Loop protection
    if (err.requestOptions.extra['isRetry'] == true) {
      await _handleSessionExpired();
      return handler.next(err);
    }

    // Check if it's a 401 and we aren't already refreshing
    if (err.response?.statusCode == 401 && !_isRefreshing) {
      _isRefreshing = true;
      SyncLogger.log('token_expired_detected', success: false);

      // Notify UI that we're reconnecting
      authStatusController.add(AuthStatus.refreshing);

      try {
        final refreshToken = await _localDataSource.getRefreshToken();
        if (refreshToken != null) {
          final dio = Dio(BaseOptions(baseUrl: ApiConstants.baseUrl));
          final response = await dio.post(ApiConstants.authRefresh, data: {
            'refresh_token': refreshToken,
          });

          if (response.statusCode == 200) {
            final data = response.data;
            final newAccessToken = data['access_token'];
            final newRefreshToken = data['refresh_token'];

            await _localDataSource.saveTokens(newAccessToken, newRefreshToken);
            SyncLogger.log('token_refresh_success');

            // Notify UI that we're back online
            authStatusController.add(AuthStatus.authenticated);

            // Retry the original request
            final options = err.requestOptions;
            options.headers['Authorization'] = 'Bearer $newAccessToken';
            options.extra['isRetry'] = true; // Mark as retry

            // Re-fetch using a internal call
            final retryResponse = await dio.fetch(options);
            _isRefreshing = false;
            return handler.resolve(retryResponse);
          }
        }
      } catch (e) {
        SyncLogger.log('token_refresh_failed', error: e.toString(), success: false);
        await _handleSessionExpired();
      } finally {
        _isRefreshing = false;
      }
    }
    handler.next(err);
  }

  Future<void> _handleSessionExpired() async {
    await _localDataSource.clearTokens();
    // Notify UI that session has expired
    authStatusController.add(AuthStatus.expired);
    SyncLogger.log('session_expired_handled', data: {
      'message': FallbackMessages.sessionExpired,
    });
  }
}
