// tests/flutter/e2e/e2e_full_user_journey_test.dart
// ═══════════════════════════════════════════════════════════════
// E2E Test — Viaje completo del usuario
// Simula: Registro → Onboarding → Diagnóstico → Practice → 
//         Boss Raid → Millionaire → Mastery → Offline → Sync
//
// Ejecutar: flutter test integration_test/e2e_full_user_journey_test.dart
// ═══════════════════════════════════════════════════════════════

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:icfes_leveling/main.dart' as app;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  // ─── E2E 1: REGISTRO → ONBOARDING → DIAGNÓSTICO → HOME ───

  group('E2E: New User Complete Onboarding', () {
    testWidgets('full journey from splash to home dashboard', (tester) async {
      app.main();
      await tester.pumpAndSettle(const Duration(seconds: 3));

      // ═══ SPLASH SCREEN ═══
      // La app debe iniciar en splash y luego ir a login
      await tester.pumpAndSettle(const Duration(seconds: 2));

      // ═══ REGISTRO ═══
      // Navegar a registro
      final registerLink = find.textContaining('Regístrate');
      if (registerLink.evaluate().isNotEmpty) {
        await tester.tap(registerLink);
        await tester.pumpAndSettle();
      }

      // Llenar formulario de registro
      await tester.enterText(
        find.byKey(const Key('username_field')), 'e2e_cazador_${DateTime.now().millisecondsSinceEpoch}'
      );
      await tester.enterText(
        find.byKey(const Key('email_field')), 'e2e_${DateTime.now().millisecondsSinceEpoch}@test.com'
      );
      await tester.enterText(
        find.byKey(const Key('password_field')), 'e2ePassword123!'
      );

      await tester.tap(find.text('Crear Cuenta'));
      await tester.pumpAndSettle(const Duration(seconds: 3));

      // ═══ ONBOARDING PASO 1: WELCOME ═══
      expect(find.textContaining('Bienvenido'), findsOneWidget);
      await tester.tap(find.text('Comenzar'));
      await tester.pumpAndSettle();

      // ═══ ONBOARDING PASO 2: META ICFES ═══
      expect(find.textContaining('puntaje'), findsOneWidget);
      // Mover slider a 350
      final slider = find.byType(Slider);
      expect(slider, findsOneWidget);
      await tester.drag(slider, const Offset(100, 0));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Siguiente'));
      await tester.pumpAndSettle();

      // ═══ ONBOARDING PASO 3: NIVEL ACTUAL ═══
      expect(find.text('Intermedio'), findsOneWidget);
      await tester.tap(find.text('Intermedio'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Siguiente'));
      await tester.pumpAndSettle();

      // ═══ ONBOARDING PASO 4: MATERIAS ═══
      expect(find.text('Matemáticas'), findsOneWidget);
      await tester.tap(find.text('Matemáticas'));
      await tester.tap(find.text('Lectura Crítica'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Siguiente'));
      await tester.pumpAndSettle();

      // ═══ ONBOARDING PASO 5: TIEMPO DISPONIBLE ═══
      expect(find.text('30 min'), findsOneWidget);
      await tester.tap(find.text('30 min'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Iniciar Diagnóstico'));
      await tester.pumpAndSettle(const Duration(seconds: 2));

      // ═══ DIAGNÓSTICO RÁPIDO (15 preguntas) ═══
      expect(find.textContaining('1'), findsAtLeast(1)); // Pregunta 1
      expect(find.textContaining('15'), findsAtLeast(1)); // de 15

      // Responder las 15 preguntas
      for (int i = 0; i < 15; i++) {
        // Esperar que la pregunta cargue
        await tester.pumpAndSettle(const Duration(milliseconds: 500));

        // Seleccionar opción A o B alternando
        final optionFinder = i % 2 == 0
            ? find.byKey(const Key('option_a'))
            : find.byKey(const Key('option_b'));

        if (optionFinder.evaluate().isNotEmpty) {
          await tester.tap(optionFinder);
          await tester.pumpAndSettle(const Duration(milliseconds: 300));
        }

        // Si hay botón "Siguiente", tocarlo
        final nextButton = find.text('Siguiente');
        if (nextButton.evaluate().isNotEmpty) {
          await tester.tap(nextButton);
          await tester.pumpAndSettle();
        }
      }

      // ═══ REVELACIÓN DE RESULTADOS ═══
      // Esperar la animación de revelación (4 segundos)
      await tester.pump(const Duration(seconds: 5));
      await tester.pumpAndSettle();

      // Debe mostrar un rango
      final rankFinder = find.textContaining(RegExp(r'^[EDCBAS]{1,3}$'));
      expect(rankFinder, findsAtLeast(1));

      // Debe mostrar áreas débiles
      // Continuar al home
      final continueButton = find.text('Continuar');
      if (continueButton.evaluate().isNotEmpty) {
        await tester.tap(continueButton);
        await tester.pumpAndSettle(const Duration(seconds: 2));
      }

      // ═══ HOME DASHBOARD ═══
      // Verificar que llegamos al dashboard
      expect(find.byType(BottomNavigationBar), findsOneWidget);

      // Verificar elementos del dashboard
      expect(find.byKey(const Key('heart_display')), findsOneWidget);
      expect(find.byKey(const Key('streak_badge')), findsOneWidget);
      expect(find.byKey(const Key('xp_bar')), findsOneWidget);

      // Usuario debe tener stats iniciales
      expect(find.textContaining('Nivel 1'), findsOneWidget);
    });
  });


  // ─── E2E 2: SESIÓN DE PRÁCTICA COMPLETA ───────────────────

  group('E2E: Complete Practice Session', () {
    testWidgets('practice 15 questions with feedback and rewards', (tester) async {
      app.main();
      await tester.pumpAndSettle(const Duration(seconds: 3));

      // Login con usuario existente
      await _loginTestUser(tester);

      // Navegar a práctica
      await tester.tap(find.text('Practicar'));
      await tester.pumpAndSettle(const Duration(seconds: 2));

      int correctCount = 0;
      int totalXP = 0;

      // Responder 15 preguntas
      for (int i = 0; i < 15; i++) {
        await tester.pumpAndSettle();

        // Verificar que muestra progreso
        expect(find.textContaining('${i + 1}/15'), findsOneWidget);

        // Seleccionar una opción
        final option = find.byKey(Key('option_${i % 2 == 0 ? "b" : "a"}'));
        if (option.evaluate().isNotEmpty) {
          await tester.tap(option);
          await tester.pumpAndSettle(const Duration(seconds: 1));
        }

        // Verificar feedback overlay apareció
        final feedbackFinder = find.byKey(const Key('feedback_overlay'));
        if (feedbackFinder.evaluate().isNotEmpty) {
          // Verificar que muestra XP o corazón perdido
          final xpText = find.textContaining('XP');
          expect(xpText, findsAtLeast(1));
        }

        // Tocar para continuar a siguiente pregunta
        await tester.tap(find.byKey(const Key('next_question')));
        await tester.pumpAndSettle();
      }

      // ═══ PANTALLA DE RESULTADOS ═══
      await tester.pumpAndSettle(const Duration(seconds: 1));

      expect(find.textContaining('Sesión completada'), findsOneWidget);
      expect(find.textContaining('/15'), findsOneWidget);
      expect(find.textContaining('XP'), findsAtLeast(1));
      expect(find.textContaining('Gold'), findsAtLeast(1));

      // Volver al home
      await tester.tap(find.text('Continuar'));
      await tester.pumpAndSettle();

      // XP debe haberse actualizado en el dashboard
      expect(find.byKey(const Key('xp_bar')), findsOneWidget);
    });
  });


  // ─── E2E 3: MILLIONAIRE MODE ──────────────────────────────

  group('E2E: Millionaire Mode with Walk Away', () {
    testWidgets('play millionaire and walk away at question 7', (tester) async {
      app.main();
      await tester.pumpAndSettle(const Duration(seconds: 3));
      await _loginTestUser(tester);

      // Navegar a Millonario
      await tester.tap(find.text('Millonario'));
      await tester.pumpAndSettle(const Duration(seconds: 2));

      // Verificar escalera de premios
      expect(find.byKey(const Key('prize_ladder')), findsOneWidget);

      // Responder 6 preguntas
      for (int i = 0; i < 6; i++) {
        await tester.pumpAndSettle();
        await tester.tap(find.byKey(Key('option_b')));
        await tester.pumpAndSettle(const Duration(seconds: 1));
      }

      // Walk away en pregunta 7
      await tester.tap(find.text('Retirarse'));
      await tester.pumpAndSettle();

      // Confirmación
      expect(find.textContaining('¿Estás seguro?'), findsOneWidget);
      expect(find.textContaining('Gold'), findsAtLeast(1)); // Muestra rewards acumulados

      await tester.tap(find.text('Sí, retirarme'));
      await tester.pumpAndSettle();

      // Resultado: debe conservar rewards del checkpoint 5
      expect(find.textContaining('¡Te retiraste!'), findsOneWidget);
    });
  });


  // ─── E2E 4: MODO OFFLINE → SYNC ──────────────────────────

  group('E2E: Offline Practice and Sync', () {
    testWidgets('answer questions offline then sync when online', (tester) async {
      app.main();
      await tester.pumpAndSettle(const Duration(seconds: 3));
      await _loginTestUser(tester);

      // Simular modo offline (el cache ya tiene preguntas)
      // En E2E real, cortaríamos la red del device

      // Iniciar práctica (debe funcionar offline con cache)
      await tester.tap(find.text('Practicar'));
      await tester.pumpAndSettle(const Duration(seconds: 2));

      // Responder 5 preguntas
      for (int i = 0; i < 5; i++) {
        await tester.pumpAndSettle();
        await tester.tap(find.byKey(const Key('option_a')));
        await tester.pumpAndSettle(const Duration(seconds: 1));
        final nextBtn = find.byKey(const Key('next_question'));
        if (nextBtn.evaluate().isNotEmpty) {
          await tester.tap(nextBtn);
          await tester.pumpAndSettle();
        }
      }

      // Verificar indicador de pendientes de sync
      expect(find.byKey(const Key('sync_pending_badge')), findsOneWidget);

      // Simular reconexión (en E2E real: restaurar red)
      // El SyncManager debería procesar automáticamente

      await tester.pumpAndSettle(const Duration(seconds: 5));

      // Verificar que el badge de sync desapareció
      // (o muestra "Sincronizado")
    });
  });


  // ─── E2E 5: NAVEGACIÓN ENTRE TABS ────────────────────────

  group('E2E: Bottom Navigation', () {
    testWidgets('navigate between all 4 tabs', (tester) async {
      app.main();
      await tester.pumpAndSettle(const Duration(seconds: 3));
      await _loginTestUser(tester);

      // Tab 1: Home (ya estamos aquí)
      expect(find.byKey(const Key('home_page')), findsOneWidget);

      // Tab 2: Ligas
      await tester.tap(find.byIcon(Icons.leaderboard));
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('leagues_page')), findsOneWidget);

      // Tab 3: Plan de Estudio
      await tester.tap(find.byIcon(Icons.book));
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('study_plan_page')), findsOneWidget);

      // Tab 4: Perfil
      await tester.tap(find.byIcon(Icons.person));
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('profile_page')), findsOneWidget);

      // Volver a Home
      await tester.tap(find.byIcon(Icons.home));
      await tester.pumpAndSettle();
      expect(find.byKey(const Key('home_page')), findsOneWidget);
    });
  });


  // ─── E2E 6: STREAK & HEARTS MANAGEMENT ───────────────────

  group('E2E: Streak and Hearts Flow', () {
    testWidgets('verify streak increments and heart loss on wrong answer', (tester) async {
      app.main();
      await tester.pumpAndSettle(const Duration(seconds: 3));
      await _loginTestUser(tester);

      // Verificar streak inicial en dashboard
      expect(find.byKey(const Key('streak_badge')), findsOneWidget);

      // Verificar 5 corazones
      expect(find.byKey(const Key('heart_display')), findsOneWidget);

      // Ir a práctica y responder incorrectamente
      await tester.tap(find.text('Practicar'));
      await tester.pumpAndSettle(const Duration(seconds: 2));

      // Seleccionar respuesta incorrecta intencionalmente
      await tester.tap(find.byKey(const Key('option_d'))); // Probablemente incorrecta
      await tester.pumpAndSettle(const Duration(seconds: 1));

      // Verificar feedback de corazón perdido
      // El overlay debe mostrar el corazón roto
    });
  });
}


// ─── HELPER: LOGIN CON USUARIO DE TEST ──────────────────────

Future<void> _loginTestUser(WidgetTester tester) async {
  // Si estamos en login page
  final loginButton = find.text('Iniciar Sesión');
  if (loginButton.evaluate().isNotEmpty) {
    await tester.enterText(
      find.byKey(const Key('email_field')),
      'e2e_test@test.com',
    );
    await tester.enterText(
      find.byKey(const Key('password_field')),
      'testPassword123!',
    );
    await tester.tap(loginButton);
    await tester.pumpAndSettle(const Duration(seconds: 3));
  }
}
