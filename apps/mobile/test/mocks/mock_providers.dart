import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mockito/mockito.dart';

import 'package:icfes_mobile/core/network/api_client.dart';
import 'package:icfes_mobile/core/storage/question_cache.dart';
import 'package:icfes_mobile/core/auth/domain/entities/user.dart';
import 'package:icfes_mobile/features/auth/domain/repositories/auth_repository.dart';
import 'package:icfes_mobile/features/auth/presentation/providers/auth_provider.dart';
import 'package:icfes_mobile/core/providers/storage_providers.dart';

// To generate type-safe mocks using build_runner, run:
// flutter pub run build_runner build --delete-conflicting-outputs
//
// Then create a separate file mock_generators.dart with @GenerateMocks annotation
// For now, we use manual mock implementations below.

/// Mock API Client that simulates network responses
class FakeApiClient extends Mock implements ApiClient {
  final Map<String, dynamic> mockResponses = {};
  final List<String> errorEndpoints = [];

  void setMockResponse(String endpoint, dynamic data, {int statusCode = 200}) {
    mockResponses[endpoint] = {
      'data': data,
      'statusCode': statusCode,
    };
  }

  void setErrorEndpoint(String endpoint) {
    errorEndpoints.add(endpoint);
  }

  void clearMockResponse(String endpoint) {
    mockResponses.remove(endpoint);
  }

  void clearErrorEndpoint(String endpoint) {
    errorEndpoints.remove(endpoint);
  }

  void reset() {
    mockResponses.clear();
    errorEndpoints.clear();
  }

  @override
  Future<Response<T>> get<T>(String path, {Map<String, dynamic>? queryParameters, Options? options}) async {
    if (errorEndpoints.contains(path)) {
      throw DioException(
        requestOptions: RequestOptions(path: path),
        type: DioExceptionType.connectionError,
        message: 'Mock network error',
      );
    }

    final mockData = mockResponses[path];
    if (mockData != null) {
      return Response(
        data: mockData['data'] as T,
        statusCode: mockData['statusCode'],
        requestOptions: RequestOptions(path: path),
      );
    }

    return Response(
      data: <String, dynamic>{} as T,
      statusCode: 200,
      requestOptions: RequestOptions(path: path),
    );
  }

  @override
  Future<Response<T>> post<T>(String path, {dynamic data, Map<String, dynamic>? queryParameters, Options? options}) async {
    if (errorEndpoints.contains(path)) {
      throw DioException(
        requestOptions: RequestOptions(path: path),
        type: DioExceptionType.connectionError,
        message: 'Mock network error',
      );
    }

    final mockData = mockResponses[path];
    if (mockData != null) {
      return Response(
        data: mockData['data'] as T,
        statusCode: mockData['statusCode'],
        requestOptions: RequestOptions(path: path),
      );
    }

    return Response(
      data: <String, dynamic>{} as T,
      statusCode: 200,
      requestOptions: RequestOptions(path: path),
    );
  }

  @override
  Future<Response<T>> put<T>(String path, {dynamic data, Map<String, dynamic>? queryParameters, Options? options}) async {
    if (errorEndpoints.contains(path)) {
      throw DioException(
        requestOptions: RequestOptions(path: path),
        type: DioExceptionType.connectionError,
        message: 'Mock network error',
      );
    }

    final mockData = mockResponses[path];
    if (mockData != null) {
      return Response(
        data: mockData['data'] as T,
        statusCode: mockData['statusCode'],
        requestOptions: RequestOptions(path: path),
      );
    }

    return Response(
      data: <String, dynamic>{} as T,
      statusCode: 200,
      requestOptions: RequestOptions(path: path),
    );
  }

  @override
  Future<Response<T>> delete<T>(String path, {dynamic data, Map<String, dynamic>? queryParameters, Options? options}) async {
    if (errorEndpoints.contains(path)) {
      throw DioException(
        requestOptions: RequestOptions(path: path),
        type: DioExceptionType.connectionError,
        message: 'Mock network error',
      );
    }

    final mockData = mockResponses[path];
    if (mockData != null) {
      return Response(
        data: mockData['data'] as T,
        statusCode: mockData['statusCode'],
        requestOptions: RequestOptions(path: path),
      );
    }

    return Response(
      data: <String, dynamic>{} as T,
      statusCode: 200,
      requestOptions: RequestOptions(path: path),
    );
  }
}

/// Create a test user for testing
User createTestUser({
  String id = 'test-user-id',
  String email = 'test@example.com',
  String name = 'Test User',
  int level = 1,
  int xp = 100,
  String rank = 'E',
  int hearts = 5,
  int currentStreak = 7,
  bool diagnosticCompleted = true,
}) {
  return User(
    id: id,
    email: email,
    name: name,
    level: level,
    xp: xp,
    rank: rank,
    hearts: hearts,
    currentStreak: currentStreak,
    diagnosticCompleted: diagnosticCompleted,
  );
}

/// Create a mock ProviderContainer for testing with overrides
ProviderContainer createTestContainer({
  ApiClient? apiClient,
  AuthRepository? authRepository,
  QuestionCache? questionCache,
  List<Override>? additionalOverrides,
}) {
  final mockApiClient = apiClient ?? FakeApiClient();

  return ProviderContainer(
    overrides: [
      apiClientProvider.overrideWithValue(mockApiClient),
      if (authRepository != null)
        authRepositoryProvider.overrideWithValue(authRepository),
      if (questionCache != null)
        questionCacheProvider.overrideWithValue(questionCache),
      ...?additionalOverrides,
    ],
  );
}

/// Extension to help with testing StateNotifierProviders
extension StateNotifierProviderTestExtension<T extends StateNotifier<S>, S> on StateNotifierProvider<T, S> {
  /// Read current state from container
  S readState(ProviderContainer container) => container.read(this);

  /// Read notifier from container
  T readNotifier(ProviderContainer container) => container.read(notifier);
}

/// Helper class to track API call counts
class ApiCallTracker {
  final Map<String, int> _callCounts = {};

  void recordCall(String endpoint) {
    _callCounts[endpoint] = (_callCounts[endpoint] ?? 0) + 1;
  }

  int getCallCount(String endpoint) => _callCounts[endpoint] ?? 0;

  void reset() => _callCounts.clear();
}
