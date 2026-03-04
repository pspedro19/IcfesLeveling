import 'dart:async';
import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

/// Interceptor that provides automatic retry with exponential backoff
/// for failed network requests.
class RetryInterceptor extends Interceptor {
  final Dio dio;
  final int maxRetries;
  final Duration initialDelay;
  final double backoffFactor;

  /// Set of status codes that should trigger a retry
  static const Set<int> retryableStatusCodes = {
    408, // Request Timeout
    429, // Too Many Requests
    500, // Internal Server Error
    502, // Bad Gateway
    503, // Service Unavailable
    504, // Gateway Timeout
  };

  RetryInterceptor({
    required this.dio,
    this.maxRetries = 3,
    this.initialDelay = const Duration(milliseconds: 500),
    this.backoffFactor = 2.0,
  });

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    // Get current retry count from request options
    final retryCount = err.requestOptions.extra['retryCount'] ?? 0;

    // Check if we should retry
    if (_shouldRetry(err) && retryCount < maxRetries) {
      // Calculate delay with exponential backoff
      final delay = _calculateDelay(retryCount);

      if (kDebugMode) {
        debugPrint(
          'Retry ${retryCount + 1}/$maxRetries for ${err.requestOptions.path} '
          'after ${delay.inMilliseconds}ms (${err.type})',
        );
      }

      // Wait before retrying
      await Future.delayed(delay);

      // Update retry count
      err.requestOptions.extra['retryCount'] = retryCount + 1;

      try {
        // Retry the request
        final response = await dio.fetch(err.requestOptions);
        return handler.resolve(response);
      } on DioException catch (e) {
        // If retry fails, pass error to handler
        return handler.next(e);
      }
    }

    // Don't retry - pass error along
    return handler.next(err);
  }

  /// Determine if the error is retryable
  bool _shouldRetry(DioException err) {
    // Don't retry if request was cancelled
    if (err.type == DioExceptionType.cancel) {
      return false;
    }

    // Retry on connection/timeout errors
    if (err.type == DioExceptionType.connectionTimeout ||
        err.type == DioExceptionType.sendTimeout ||
        err.type == DioExceptionType.receiveTimeout ||
        err.type == DioExceptionType.connectionError) {
      return true;
    }

    // Check if it's a SocketException (network unreachable, etc.)
    if (err.error is SocketException) {
      return true;
    }

    // Check response status code
    final statusCode = err.response?.statusCode;
    if (statusCode != null && retryableStatusCodes.contains(statusCode)) {
      return true;
    }

    // Don't retry for other errors (4xx client errors, etc.)
    return false;
  }

  /// Calculate delay with exponential backoff
  Duration _calculateDelay(int retryCount) {
    // Exponential backoff: delay = initialDelay * (backoffFactor ^ retryCount)
    final multiplier = (backoffFactor).toInt();
    int factor = 1;
    for (int i = 0; i < retryCount; i++) {
      factor *= multiplier;
    }
    return initialDelay * factor;
  }
}
