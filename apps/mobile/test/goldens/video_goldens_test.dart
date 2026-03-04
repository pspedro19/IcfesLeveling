import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:icfes_mobile/features/video/presentation/pages/video_player_page.dart';
import 'package:icfes_mobile/core/network/api_client.dart';
import 'package:icfes_mobile/core/providers/storage_providers.dart';
import 'package:icfes_mobile/core/sync/connectivity_monitor.dart';
import 'package:icfes_mobile/features/auth/domain/repositories/auth_repository.dart';
import 'package:icfes_mobile/features/auth/presentation/providers/auth_provider.dart';

import '../mocks/mock_providers.dart';
import 'golden_test_helper.dart';

void main() {
  group('Video Golden Tests', () {
    late FakeApiClient fakeApiClient;

    setUp(() async {
      await goldenSetUp();
      fakeApiClient = FakeApiClient();
      setupAllGoldenMocks(fakeApiClient);
    });

    tearDown(goldenTearDown);

    testWidgets('video_player_page golden', (tester) async {
      await tester.binding.setSurfaceSize(goldenSize);
      addTearDown(() => tester.binding.setSurfaceSize(null));

      // Mock video-specific endpoints
      // getTracking: GET /videos/tracking/dQw4w9WgXcQ → null (no existing tracking)
      // Since FakeApiClient returns empty map by default, getTracking returns null.
      // createTracking: POST /videos/tracking → new tracking record
      fakeApiClient.setMockResponse('/videos/tracking', {
        'id': 'tracking-1',
        'video_id': 'dQw4w9WgXcQ',
        'watched_seconds': 0,
        'percentage_watched': 0.0,
        'completed': false,
        'created_at': '2026-02-20T10:00:00Z',
        'updated_at': '2026-02-20T10:00:00Z',
      }, statusCode: 200);

      // getVideoInfo: GET /videos/dQw4w9WgXcQ → video metadata
      fakeApiClient.setMockResponse('/videos/dQw4w9WgXcQ', {
        'id': 'dQw4w9WgXcQ',
        'video_id': 'dQw4w9WgXcQ',
        'youtube_id': 'dQw4w9WgXcQ',
        'title': 'Ecuaciones de Primer Grado',
        'description': 'Aprende a resolver ecuaciones lineales paso a paso.',
        'thumbnail_url': null,
        'duration_seconds': 720,
      }, statusCode: 200);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiClientProvider.overrideWithValue(fakeApiClient),
            authRepositoryProvider.overrideWithValue(
              MockAuthRepository(user: createTestUser(name: 'Hunter Pro')),
            ),
            questionCacheProvider.overrideWithValue(MockQuestionCache()),
            connectivityMonitorProvider.overrideWithValue(MockConnectivityMonitor()),
          ],
          child: MaterialApp(
            theme: goldenDarkTheme,
            debugShowCheckedModeBanner: false,
            home: VideoPlayerPage(
              videoId: 'dQw4w9WgXcQ',
              title: 'Ecuaciones de Primer Grado',
              description: 'Aprende a resolver ecuaciones lineales paso a paso.',
            ),
          ),
        ),
      );

      await pumpAndWait(tester);
      await pumpAndWait(tester);

      await expectLater(
        find.byType(VideoPlayerPage),
        matchesGoldenFile('screenshots/video_player_page.png'),
      );
    });

    testWidgets('video_player_completed golden', (tester) async {
      await tester.binding.setSurfaceSize(goldenSize);
      addTearDown(() => tester.binding.setSurfaceSize(null));

      // Mock video as already completed
      fakeApiClient.setMockResponse('/videos/tracking/abc123video', {
        'id': 'tracking-2',
        'video_id': 'abc123video',
        'watched_seconds': 720,
        'percentage_watched': 100.0,
        'completed': true,
        'completed_at': '2026-02-20T11:00:00Z',
        'created_at': '2026-02-20T10:00:00Z',
        'updated_at': '2026-02-20T11:00:00Z',
      }, statusCode: 200);

      fakeApiClient.setMockResponse('/videos/abc123video', {
        'id': 'abc123video',
        'video_id': 'abc123video',
        'youtube_id': 'abc123video',
        'title': 'Funciones Cuadráticas',
        'description': 'Domina las funciones cuadráticas para el ICFES.',
        'thumbnail_url': null,
        'duration_seconds': 900,
      }, statusCode: 200);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiClientProvider.overrideWithValue(fakeApiClient),
            authRepositoryProvider.overrideWithValue(
              MockAuthRepository(user: createTestUser(name: 'Hunter Pro')),
            ),
            questionCacheProvider.overrideWithValue(MockQuestionCache()),
            connectivityMonitorProvider.overrideWithValue(MockConnectivityMonitor()),
          ],
          child: MaterialApp(
            theme: goldenDarkTheme,
            debugShowCheckedModeBanner: false,
            home: VideoPlayerPage(
              videoId: 'abc123video',
              title: 'Funciones Cuadráticas',
              description: 'Domina las funciones cuadráticas para el ICFES.',
            ),
          ),
        ),
      );

      await pumpAndWait(tester);
      await pumpAndWait(tester);

      await expectLater(
        find.byType(VideoPlayerPage),
        matchesGoldenFile('screenshots/video_player_completed.png'),
      );
    });
  });
}
