import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mockito/mockito.dart';

import 'package:icfes_mobile/features/practice/presentation/pages/practice_session_page.dart';
import 'package:icfes_mobile/core/network/api_client.dart';
import 'package:icfes_mobile/core/storage/question_cache.dart';
import 'package:icfes_mobile/core/providers/storage_providers.dart';
import 'package:icfes_mobile/core/sync/connectivity_monitor.dart'
    show connectivityMonitorProvider, connectivityProvider;
import 'package:icfes_mobile/features/auth/presentation/providers/auth_provider.dart';
import 'package:icfes_mobile/core/services/sound_service.dart';

import '../mocks/mock_providers.dart';
import 'golden_test_helper.dart';

/// QuestionCache that returns fake questions for golden tests
class GoldenQuestionCache extends Mock implements QuestionCache {
  @override
  Future<void> init() async {}

  @override
  Future<void> warmUp(ApiClient apiClient) async {}

  @override
  Future<List<Map<String, dynamic>>> getCachedQuestions({String? subjectId}) async {
    return [
      {
        'id': 'q1',
        'subject_id': 'matematicas',
        'topic_id': 'algebra',
        'pregunta_texto': '¿Cuál es el valor de x en la ecuación 2x + 5 = 15?',
        'opcion_a_texto': 'x = 3',
        'opcion_b_texto': 'x = 5',
        'opcion_c_texto': 'x = 7',
        'opcion_d_texto': 'x = 10',
        'respuesta_correcta': 'B',
        'difficulty_rating': 'E',
        'puntos_xp': 10,
        'topic_name': 'Álgebra básica',
        'subject_name': 'Matemáticas',
        'explicacion_texto': 'Restamos 5 de ambos lados: 2x = 10, luego dividimos: x = 5',
      },
      {
        'id': 'q2',
        'subject_id': 'matematicas',
        'topic_id': 'geometria',
        'pregunta_texto': '¿Cuántos lados tiene un pentágono?',
        'opcion_a_texto': '3',
        'opcion_b_texto': '4',
        'opcion_c_texto': '5',
        'opcion_d_texto': '6',
        'respuesta_correcta': 'C',
        'difficulty_rating': 'E',
        'puntos_xp': 10,
        'topic_name': 'Geometría',
        'subject_name': 'Matemáticas',
      },
    ];
  }

  @override
  Future<void> markAnswered(String questionId) async {}
}

void main() {
  group('Practice Golden Tests', () {
    late FakeApiClient fakeApiClient;
    late GoldenQuestionCache goldenCache;

    setUp(() async {
      await goldenSetUp();
      // Disable sounds to minimize AudioPlayer side effects
      SoundService().setEnabled(false);
      fakeApiClient = FakeApiClient();
      setupAllGoldenMocks(fakeApiClient);
      goldenCache = GoldenQuestionCache();
    });

    tearDown(() {
      goldenTearDown();
      SoundService().setEnabled(true);
    });

    testWidgets('practice_session golden', (tester) async {
      await tester.binding.setSurfaceSize(goldenSize);
      addTearDown(() => tester.binding.setSurfaceSize(null));

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            apiClientProvider.overrideWithValue(fakeApiClient),
            authRepositoryProvider.overrideWithValue(
              MockAuthRepository(user: createTestUser(name: 'Hunter Pro')),
            ),
            questionCacheProvider.overrideWithValue(goldenCache),
            connectivityMonitorProvider.overrideWithValue(MockConnectivityMonitor()),
            connectivityProvider.overrideWith((ref) => Stream.value(true)),
          ],
          child: MaterialApp(
            theme: goldenDarkTheme,
            debugShowCheckedModeBanner: false,
            home: const PracticeSessionPage(),
          ),
        ),
      );

      // Allow time for startSession to complete and UI to update
      await pumpAndWait(tester);
      await pumpAndWait(tester);

      await expectLater(
        find.byType(PracticeSessionPage),
        matchesGoldenFile('screenshots/practice_session.png'),
      );
    });
  });
}
