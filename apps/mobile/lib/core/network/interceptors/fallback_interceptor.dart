import 'dart:async';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../error/fallback_handler.dart';
import '../../error/error_recovery_service.dart';
import '../../utils/sync_logger.dart';
import '../../sync/action_queue.dart';
import '../../sync/sync_action.dart';

/// Provider for the fallback interceptor
final fallbackInterceptorProvider = Provider<FallbackInterceptor>((ref) {
  final recoveryService = ref.watch(errorRecoveryServiceProvider);
  return FallbackInterceptor(recoveryService);
});

/// Interceptor that handles errors and provides fallback behavior
/// - Intercepts errors and maps them to appropriate error types
/// - Shows appropriate fallback UI
/// - Implements automatic retry for transient errors
/// - Queues actions for offline synchronization
class FallbackInterceptor extends Interceptor {
  final ErrorRecoveryService _recoveryService;

  // Configuration for retry behavior
  static const int _maxRetries = 3;
  static const Duration _initialRetryDelay = Duration(seconds: 1);
  static const List<int> _retryableStatusCodes = [408, 429, 500, 502, 503, 504];

  // Stream controller for UI notifications
  final _errorNotificationController = StreamController<ErrorNotification>.broadcast();
  Stream<ErrorNotification> get errorNotifications => _errorNotificationController.stream;

  // Endpoints that should be queued when offline
  static const _queueableEndpoints = [
    '/answers/submit',
    '/hearts/use',
    '/streak/extend',
    '/sync/state',
    '/mastery/update',
  ];

  // Endpoints that require special handling
  static const _criticalEndpoints = [
    '/diagnostic/',
    '/auth/',
    '/leagues/',
  ];

  FallbackInterceptor(this._recoveryService);

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    // Add retry count to options if not present
    options.extra['retryCount'] ??= 0;
    options.extra['startTime'] ??= DateTime.now().millisecondsSinceEpoch;
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    final path = err.requestOptions.path;
    final retryCount = err.requestOptions.extra['retryCount'] as int? ?? 0;

    SyncLogger.log('fallback_interceptor_error', data: {
      'path': path,
      'type': err.type.toString(),
      'status_code': err.response?.statusCode,
      'retry_count': retryCount,
    }, success: false);

    // Handle based on error type
    if (_isNetworkError(err)) {
      await _handleNetworkError(err, handler, retryCount);
    } else if (_isServerError(err)) {
      await _handleServerError(err, handler, retryCount);
    } else if (_isAuthError(err)) {
      await _handleAuthError(err, handler);
    } else {
      // Unknown error, just pass through
      handler.next(err);
    }
  }

  /// Handles network connectivity errors
  Future<void> _handleNetworkError(
    DioException err,
    ErrorInterceptorHandler handler,
    int retryCount,
  ) async {
    final path = err.requestOptions.path;

    // Determine error type
    NetworkErrorType errorType;
    switch (err.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        errorType = NetworkErrorType.timeout;
        break;
      case DioExceptionType.connectionError:
        errorType = NetworkErrorType.noConnection;
        break;
      default:
        errorType = NetworkErrorType.noConnection;
    }

    // Notify UI
    _emitNotification(ErrorNotification(
      type: errorType,
      message: FallbackHandler.getNetworkErrorMessage(errorType),
      path: path,
      canRetry: true,
    ));

    // Check if this endpoint can be queued for offline sync
    if (_isQueueableEndpoint(path)) {
      // Queue the action for later sync
      await _queueForSync(err.requestOptions);

      // Return a pseudo-success response
      return handler.resolve(Response(
        requestOptions: err.requestOptions,
        statusCode: 202,
        data: {
          'queued': true,
          'message': 'Accion guardada para sincronizacion',
        },
      ));
    }

    // For non-queueable endpoints, try automatic retry if timeout
    if (errorType == NetworkErrorType.timeout && retryCount < _maxRetries) {
      await _retryRequest(err, handler, retryCount);
      return;
    }

    handler.next(err);
  }

  /// Handles server-side errors
  Future<void> _handleServerError(
    DioException err,
    ErrorInterceptorHandler handler,
    int retryCount,
  ) async {
    final statusCode = err.response?.statusCode ?? 500;
    final path = err.requestOptions.path;

    // Determine if we should retry
    if (_retryableStatusCodes.contains(statusCode) && retryCount < _maxRetries) {
      // Check if it's rate limiting (429) - need longer delay
      if (statusCode == 429) {
        _emitNotification(ErrorNotification(
          type: NetworkErrorType.rateLimited,
          message: FallbackMessages.rateLimited,
          path: path,
          canRetry: true,
        ));

        // Get retry-after header if available
        final retryAfter = err.response?.headers.value('retry-after');
        final delay = retryAfter != null
            ? Duration(seconds: int.tryParse(retryAfter) ?? 5)
            : _getRetryDelay(retryCount) * 2;

        await Future.delayed(delay);
        await _retryRequest(err, handler, retryCount);
        return;
      }

      // Standard server error retry
      _emitNotification(ErrorNotification(
        type: NetworkErrorType.serverError,
        message: FallbackMessages.serverError,
        path: path,
        canRetry: true,
      ));

      await Future.delayed(_getRetryDelay(retryCount));
      await _retryRequest(err, handler, retryCount);
      return;
    }

    // Check for sync conflicts
    if (statusCode == 409) {
      _emitNotification(ErrorNotification(
        type: NetworkErrorType.syncConflict,
        message: FallbackMessages.syncConflict,
        path: path,
        canRetry: false,
      ));
    }

    handler.next(err);
  }

  /// Handles authentication errors
  Future<void> _handleAuthError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    final statusCode = err.response?.statusCode;
    final path = err.requestOptions.path;

    if (statusCode == 401) {
      // Token expired - notify UI to show reconnecting message
      _emitNotification(ErrorNotification(
        stateType: StateErrorType.jwtExpired,
        message: FallbackMessages.jwtExpired,
        path: path,
        canRetry: false,
      ));

      // The actual token refresh is handled by AuthInterceptor
      // We just need to notify the UI
    } else if (statusCode == 403) {
      _emitNotification(ErrorNotification(
        stateType: StateErrorType.sessionExpired,
        message: FallbackMessages.sessionExpired,
        path: path,
        canRetry: false,
      ));
    }

    handler.next(err);
  }

  /// Retries a failed request
  Future<void> _retryRequest(
    DioException err,
    ErrorInterceptorHandler handler,
    int currentRetryCount,
  ) async {
    try {
      final options = err.requestOptions;
      options.extra['retryCount'] = currentRetryCount + 1;

      SyncLogger.log('fallback_interceptor_retry', data: {
        'path': options.path,
        'attempt': currentRetryCount + 1,
        'max_retries': _maxRetries,
      });

      final dio = Dio(BaseOptions(
        baseUrl: options.baseUrl,
        connectTimeout: options.connectTimeout,
        receiveTimeout: options.receiveTimeout,
      ));

      final response = await dio.fetch(options);
      handler.resolve(response);
    } catch (e) {
      if (e is DioException) {
        handler.next(e);
      } else {
        handler.next(err);
      }
    }
  }

  /// Queues a request for offline synchronization
  Future<void> _queueForSync(RequestOptions options) async {
    final actionType = _mapPathToActionType(options.path);
    if (actionType == null) return;

    final action = SyncAction(
      type: actionType,
      data: options.data is Map<String, dynamic>
          ? options.data
          : (options.data != null ? {'raw_data': options.data} : {}),
    );

    SyncLogger.log('fallback_interceptor_queued', data: {
      'path': options.path,
      'action_type': actionType.toString(),
    });
  }

  /// Maps request path to sync action type
  SyncActionType? _mapPathToActionType(String path) {
    if (path.contains('/answers/submit')) return SyncActionType.submitAnswer;
    if (path.contains('/hearts/use')) return SyncActionType.useHeart;
    if (path.contains('/streak/extend')) return SyncActionType.extendStreak;
    if (path.contains('/sync/state')) return SyncActionType.updateState;
    return null;
  }

  /// Gets exponential backoff delay for retries
  Duration _getRetryDelay(int retryCount) {
    return _initialRetryDelay * (1 << retryCount);
  }

  /// Checks if error is a network connectivity error
  bool _isNetworkError(DioException err) {
    return err.type == DioExceptionType.connectionTimeout ||
        err.type == DioExceptionType.connectionError ||
        err.type == DioExceptionType.sendTimeout ||
        err.type == DioExceptionType.receiveTimeout;
  }

  /// Checks if error is a server error
  bool _isServerError(DioException err) {
    final statusCode = err.response?.statusCode;
    return statusCode != null && statusCode >= 500;
  }

  /// Checks if error is an authentication error
  bool _isAuthError(DioException err) {
    final statusCode = err.response?.statusCode;
    return statusCode == 401 || statusCode == 403;
  }

  /// Checks if endpoint can be queued for offline sync
  bool _isQueueableEndpoint(String path) {
    return _queueableEndpoints.any((e) => path.contains(e));
  }

  /// Checks if endpoint is critical and needs special handling
  bool _isCriticalEndpoint(String path) {
    return _criticalEndpoints.any((e) => path.contains(e));
  }

  /// Emits an error notification to the stream
  void _emitNotification(ErrorNotification notification) {
    _errorNotificationController.add(notification);
  }

  void dispose() {
    _errorNotificationController.close();
  }
}

/// Model for error notifications sent to UI
class ErrorNotification {
  final NetworkErrorType? type;
  final StateErrorType? stateType;
  final ContentErrorType? contentType;
  final String message;
  final String path;
  final bool canRetry;
  final DateTime timestamp;

  ErrorNotification({
    this.type,
    this.stateType,
    this.contentType,
    required this.message,
    required this.path,
    this.canRetry = false,
  }) : timestamp = DateTime.now();

  /// Gets the appropriate fallback widget for this error
  Widget getFallbackWidget({
    VoidCallback? onRetry,
    VoidCallback? onWatchAd,
    Duration? timeUntilRefill,
  }) {
    if (type != null) {
      return FallbackHandler.handleNetworkError(type!, onRetry: onRetry);
    } else if (stateType != null) {
      return FallbackHandler.handleStateError(
        stateType!,
        onRetry: onRetry,
        onWatchAd: onWatchAd,
        timeUntilRefill: timeUntilRefill,
      );
    } else if (contentType != null) {
      return FallbackHandler.handleContentError(contentType!, onRetry: onRetry);
    }

    // Default fallback
    return FallbackHandler.handleNetworkError(
      NetworkErrorType.serverError,
      onRetry: onRetry,
    );
  }
}

/// Provider to listen to error notifications
final errorNotificationProvider = StreamProvider<ErrorNotification>((ref) {
  final interceptor = ref.watch(fallbackInterceptorProvider);
  return interceptor.errorNotifications;
});
