import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../constants/api_constants.dart';
import 'interceptors/auth_interceptor.dart';
import 'interceptors/offline_interceptor.dart';
import 'interceptors/retry_interceptor.dart';
import '../sync/action_queue.dart';
import '../auth/data/datasources/auth_local_datasource.dart';

import '../sync/connectivity_monitor.dart';
import '../sync/sync_manager.dart';
import '../sync/action_syncer.dart';
import '../sync/conflict_resolver.dart';
import '../../features/engagement/data/datasources/engagement_remote_datasource.dart';

final secureStorageProvider = Provider((ref) => const FlutterSecureStorage());

final authLocalDataSourceProvider = Provider((ref) {
  final secureStorage = ref.watch(secureStorageProvider);
  return AuthLocalDataSource(secureStorage);
});

final actionQueueProvider = Provider((ref) => ActionQueue());

final connectivityMonitorProvider = Provider((ref) => ConnectivityMonitor());

final apiClientProvider = Provider((ref) {
  final authLocal = ref.watch(authLocalDataSourceProvider);
  final queue = ref.watch(actionQueueProvider);
  return ApiClient(authLocal, queue);
});

final engagementRemoteDataSourceProvider = Provider((ref) {
  final api = ref.watch(apiClientProvider);
  return EngagementRemoteDataSource(api);
});


final actionSyncerProvider = Provider((ref) {
  final api = ref.watch(apiClientProvider);
  return ActionSyncer(api);
});

/// Provider for ConflictResolver - handles sync conflicts between client and server
final conflictResolverProvider = Provider((ref) => ConflictResolver());

final syncManagerProvider = ChangeNotifierProvider((ref) {
  final queue = ref.watch(actionQueueProvider);
  final connectivity = ref.watch(connectivityMonitorProvider);
  final syncer = ref.watch(actionSyncerProvider);
  final conflictResolver = ref.watch(conflictResolverProvider);

  final manager = SyncManager(
    queue,
    syncer,
    connectivity,
    conflictResolver,
  );

  manager.init();
  return manager;
});

class ApiClient {
  late final Dio _dio;

  ApiClient(AuthLocalDataSource authLocalDataSource, ActionQueue actionQueue) {
    _dio = Dio(BaseOptions(
      baseUrl: ApiConstants.baseUrl,
      connectTimeout: ApiConstants.connectTimeout,
      receiveTimeout: ApiConstants.receiveTimeout,
    ));

    _dio.interceptors.addAll([
      AuthInterceptor(authLocalDataSource),
      OfflineInterceptor(actionQueue),
      // Retry interceptor with exponential backoff for transient failures
      RetryInterceptor(
        dio: _dio,
        maxRetries: 3,
        initialDelay: const Duration(milliseconds: 500),
      ),
      if (kDebugMode)
        LogInterceptor(
          requestBody: false,
          responseBody: false,
          logPrint: (obj) => debugPrint(obj.toString())
        ),
    ]);
  }

  Future<Response<T>> get<T>(String path, {Map<String, dynamic>? queryParameters, Options? options}) async {
    return _dio.get<T>(path, queryParameters: queryParameters, options: options);
  }

  Future<Response<T>> post<T>(String path, {dynamic data, Map<String, dynamic>? queryParameters, Options? options}) async {
    return _dio.post<T>(path, data: data, queryParameters: queryParameters, options: options);
  }

  Future<Response<T>> put<T>(String path, {dynamic data, Map<String, dynamic>? queryParameters, Options? options}) async {
    return _dio.put<T>(path, data: data, queryParameters: queryParameters, options: options);
  }

  Future<Response<T>> delete<T>(String path, {dynamic data, Map<String, dynamic>? queryParameters, Options? options}) async {
    return _dio.delete<T>(path, data: data, queryParameters: queryParameters, options: options);
  }
}
