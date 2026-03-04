// tests/flutter/widget/test_all_screens.dart
// ═══════════════════════════════════════════════════════════════
// Widget Tests — Todas las pantallas principales del flujo
// Verifica rendering, interacciones, y estados visuales
// ═══════════════════════════════════════════════════════════════

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';

// Importar páginas y providers del proyecto
import 'package:icfes_leveling/features/auth/presentation/pages/login_page.dart';
import 'package:icfes_leveling/features/auth/presentation/pages/register_page.dart';
import 'package:icfes_leveling/features/onboarding/presentation/pages/welcome_page.dart';
import 'package:icfes_leveling/features/onboarding/presentation/pages/goal_page.dart';
import 'package:icfes_leveling/features/onboarding/presentation/pages/level_page.dart';
import 'package:icfes_leveling/features/onboarding/presentation/pages/subjects_page.dart';
import 'package:icfes_leveling/features/onboarding/presentation/pages/time_page.dart';
import 'package:icfes_leveling/features/onboarding/presentation/pages/quick_diagnostic_page.dart';
import 'package:icfes_leveling/features/onboarding/presentation/pages/results_reveal_page.dart';
import 'package:icfes_leveling/features/practice/presentation/pages/practice_session_page.dart';
import 'package:icfes_leveling/features/practice/presentation/widgets/question_card.dart';
import 'package:icfes_leveling/features/practice/presentation/widgets/feedback_overlay.dart';
import 'package:icfes_leveling/features/millionaire/presentation/pages/millionaire_page.dart';
import 'package:icfes_leveling/features/practice/presentation/pages/boss_raid_page.dart';
import 'package:icfes_leveling/features/home/presentation/pages/home_page.dart';
import 'package:icfes_leveling/features/mastery/presentation/pages/mastery_page.dart';
import 'package:icfes_leveling/features/leagues/presentation/pages/leagues_page.dart';
import 'package:icfes_leveling/features/shop/presentation/pages/shop_page.dart';
import 'package:icfes_leveling/shared/widgets/heart_display.dart';
import 'package:icfes_leveling/shared/widgets/streak_badge.dart';
import 'package:icfes_leveling/shared/widgets/combo_overlay.dart';
import 'package:icfes_leveling/shared/widgets/xp_bar.dart';
import 'package:icfes_leveling/shared/services/dopamine_engine.dart';

// ─── HELPERS ─────────────────────────────────────────────────

Widget wrapWithProviders(Widget child) {
  return ProviderScope(
    child: MaterialApp(
      home: Scaffold(body: child),
    ),
  );
}

// Mock data
final mockQuestion = {
  'id': 'q-001',
  'pregunta_texto': '¿Cuál es el valor de x en la ecuación 2x + 4 = 10?',
  'opcion_a_texto': 'x = 2',
  'opcion_b_texto': 'x = 3',
  'opcion_c_texto': 'x = 4',
  'opcion_d_texto': 'x = 5',
  'respuesta_correcta': 'b',
  'difficulty': 3,
  'subject_name': 'Matematicas',
  'topic_name': 'Algebra Basica',
};

final mockUser = {
  'username': 'cazador_test',
  'level': 15,
  'rank': 'D',
  'experience': 22000,
  'gold': 5000,
  'hearts': 4,
  'max_hearts': 5,
  'current_streak': 12,
  'daily_goal_xp': 20,
};


// ═══════════════════════════════════════════════════════════════
// 1. AUTH SCREENS
// ═══════════════════════════════════════════════════════════════

group('Login Page', () {
  testWidgets('renders email and password fields', (tester) async {
    await tester.pumpWidget(wrapWithProviders(const LoginPage()));

    expect(find.byType(TextFormField), findsAtLeast(2));
    expect(find.text('Email'), findsOneWidget);
    expect(find.text('Contraseña'), findsOneWidget);
    expect(find.text('Iniciar Sesión'), findsOneWidget);
  });

  testWidgets('shows error on empty email submit', (tester) async {
    await tester.pumpWidget(wrapWithProviders(const LoginPage()));

    await tester.tap(find.text('Iniciar Sesión'));
    await tester.pumpAndSettle();

    expect(find.text('Email requerido'), findsOneWidget);
  });

  testWidgets('shows Google and Apple social login buttons', (tester) async {
    await tester.pumpWidget(wrapWithProviders(const LoginPage()));

    expect(find.text('Continuar con Google'), findsOneWidget);
    expect(find.text('Continuar con Apple'), findsOneWidget);
  });

  testWidgets('navigates to register page', (tester) async {
    await tester.pumpWidget(wrapWithProviders(const LoginPage()));

    expect(find.text('¿No tienes cuenta? Regístrate'), findsOneWidget);
  });
});

group('Register Page', () {
  testWidgets('renders all required fields', (tester) async {
    await tester.pumpWidget(wrapWithProviders(const RegisterPage()));

    expect(find.text('Username'), findsOneWidget);
    expect(find.text('Email'), findsOneWidget);
    expect(find.text('Contraseña'), findsOneWidget);
    expect(find.text('Crear Cuenta'), findsOneWidget);
  });

  testWidgets('validates password minimum length', (tester) async {
    await tester.pumpWidget(wrapWithProviders(const RegisterPage()));

    final passwordField = find.byKey(const Key('password_field'));
    await tester.enterText(passwordField, '1234');
    await tester.tap(find.text('Crear Cuenta'));
    await tester.pumpAndSettle();

    expect(find.text('Mínimo 8 caracteres'), findsOneWidget);
  });
});


// ═══════════════════════════════════════════════════════════════
// 2. ONBOARDING SCREENS
// ═══════════════════════════════════════════════════════════════

group('Onboarding Flow', () {
  testWidgets('Welcome page shows RPG-style welcome message', (tester) async {
    await tester.pumpWidget(wrapWithProviders(const WelcomePage()));

    expect(find.textContaining('Bienvenido'), findsOneWidget);
    expect(find.text('Comenzar'), findsOneWidget);
  });

  testWidgets('Goal page allows selecting ICFES target score', (tester) async {
    await tester.pumpWidget(wrapWithProviders(const GoalPage()));

    // Slider o selector de puntaje 0-500
    expect(find.text('¿Qué puntaje quieres lograr?'), findsOneWidget);
    expect(find.byType(Slider), findsOneWidget);
  });

  testWidgets('Level page shows 3 options', (tester) async {
    await tester.pumpWidget(wrapWithProviders(const LevelPage()));

    expect(find.text('Principiante'), findsOneWidget);
    expect(find.text('Intermedio'), findsOneWidget);
    expect(find.text('Avanzado'), findsOneWidget);
  });

  testWidgets('Subjects page shows 5 ICFES subjects', (tester) async {
    await tester.pumpWidget(wrapWithProviders(const SubjectsPage()));

    expect(find.text('Matemáticas'), findsOneWidget);
    expect(find.text('Lectura Crítica'), findsOneWidget);
    expect(find.text('Ciencias Naturales'), findsOneWidget);
    expect(find.text('Sociales y Ciudadanas'), findsOneWidget);
    expect(find.text('Inglés'), findsOneWidget);
  });

  testWidgets('Time page allows selecting daily minutes', (tester) async {
    await tester.pumpWidget(wrapWithProviders(const TimePage()));

    expect(find.text('15 min'), findsOneWidget);
    expect(find.text('30 min'), findsOneWidget);
    expect(find.text('60 min'), findsOneWidget);
  });
});


// ═══════════════════════════════════════════════════════════════
// 3. DIAGNOSTIC SCREENS
// ═══════════════════════════════════════════════════════════════

group('Quick Diagnostic', () {
  testWidgets('shows 15 questions without immediate feedback', (tester) async {
    await tester.pumpWidget(wrapWithProviders(const QuickDiagnosticPage()));
    await tester.pumpAndSettle();

    // Debe mostrar progreso 1/15
    expect(find.textContaining('1'), findsAtLeast(1));
    expect(find.textContaining('15'), findsAtLeast(1));

    // NO debe mostrar feedback (✅ o ❌) después de responder
    await tester.tap(find.text('A').first);
    await tester.pumpAndSettle();

    expect(find.byIcon(Icons.check_circle), findsNothing);
    expect(find.byIcon(Icons.cancel), findsNothing);
  });

  testWidgets('shows timer counting down from 10 minutes', (tester) async {
    await tester.pumpWidget(wrapWithProviders(const QuickDiagnosticPage()));
    await tester.pumpAndSettle();

    expect(find.textContaining('10:00'), findsOneWidget);
  });
});

group('Results Reveal', () {
  testWidgets('shows animated sequence with rank', (tester) async {
    await tester.pumpWidget(wrapWithProviders(ResultsRevealPage(
      results: {
        'overall_rank': 'C',
        'theta': 0.15,
        'percentile': 56,
        'subject_scores': {},
        'weak_areas': [],
      },
    )));

    // Inicialmente muestra texto de evaluación
    expect(find.textContaining('EVALUADO'), findsOneWidget);

    // Después de la animación, muestra el rango
    await tester.pump(const Duration(seconds: 4));
    expect(find.text('C'), findsOneWidget);
  });

  testWidgets('shows radar chart with 5 subjects', (tester) async {
    await tester.pumpWidget(wrapWithProviders(ResultsRevealPage(
      results: {
        'overall_rank': 'D',
        'theta': -0.5,
        'percentile': 30,
        'subject_scores': {
          'Matematicas': {'theta': 0.3, 'rank': 'C'},
          'Lenguaje': {'theta': -0.8, 'rank': 'D'},
          'Ciencias Naturales': {'theta': 0.1, 'rank': 'C'},
          'Sociales': {'theta': -1.0, 'rank': 'D'},
          'Ingles': {'theta': 0.5, 'rank': 'B'},
        },
        'weak_areas': [
          {'subject': 'Sociales', 'score': 0.33, 'priority': 'HIGH'},
          {'subject': 'Lenguaje', 'score': 0.45, 'priority': 'MEDIUM'},
        ],
      },
    )));

    await tester.pump(const Duration(seconds: 5));

    // Debe mostrar áreas débiles priorizadas
    expect(find.textContaining('Sociales'), findsAtLeast(1));
    expect(find.textContaining('HIGH'), findsAtLeast(1));
  });
});


// ═══════════════════════════════════════════════════════════════
// 4. PRACTICE SESSION SCREEN
// ═══════════════════════════════════════════════════════════════

group('Practice Session', () {
  testWidgets('QuestionCard displays question with 4 options', (tester) async {
    await tester.pumpWidget(wrapWithProviders(QuestionCard(
      question: mockQuestion,
      onAnswerSelected: (_) {},
    )));

    expect(find.text('¿Cuál es el valor de x en la ecuación 2x + 4 = 10?'), findsOneWidget);
    expect(find.text('x = 2'), findsOneWidget);
    expect(find.text('x = 3'), findsOneWidget);
    expect(find.text('x = 4'), findsOneWidget);
    expect(find.text('x = 5'), findsOneWidget);
  });

  testWidgets('QuestionCard triggers callback on answer tap', (tester) async {
    String? selected;
    await tester.pumpWidget(wrapWithProviders(QuestionCard(
      question: mockQuestion,
      onAnswerSelected: (answer) => selected = answer,
    )));

    await tester.tap(find.text('x = 3'));
    expect(selected, equals('b'));
  });

  testWidgets('FeedbackOverlay shows XP breakdown for correct answer', (tester) async {
    await tester.pumpWidget(wrapWithProviders(FeedbackOverlay(
      isCorrect: true,
      xpEarned: 15,
      goldEarned: 10,
      attemptType: 'new',
      streakMultiplier: 1.2,
      comboCount: 3,
    )));

    expect(find.textContaining('15'), findsAtLeast(1));  // XP
    expect(find.textContaining('10'), findsAtLeast(1));  // Gold
    expect(find.textContaining('1.2x'), findsAtLeast(1)); // Streak mult
  });

  testWidgets('FeedbackOverlay shows heart loss for incorrect answer', (tester) async {
    await tester.pumpWidget(wrapWithProviders(FeedbackOverlay(
      isCorrect: false,
      xpEarned: 0,
      goldEarned: 0,
      attemptType: 'new',
      heartsRemaining: 3,
    )));

    expect(find.textContaining('-1'), findsAtLeast(1));  // Heart loss
    expect(find.byIcon(Icons.favorite), findsAtLeast(1));
  });

  testWidgets('Anti-gaming badge shows for invalid repeat', (tester) async {
    await tester.pumpWidget(wrapWithProviders(FeedbackOverlay(
      isCorrect: true,
      xpEarned: 0,
      goldEarned: 0,
      attemptType: 'invalid_repeat',
    )));

    expect(find.textContaining('REPETIDA'), findsOneWidget);
    expect(find.textContaining('0 XP'), findsOneWidget);
  });

  testWidgets('shows 3 lifelines initially available', (tester) async {
    await tester.pumpWidget(wrapWithProviders(const PracticeSessionPage()));
    await tester.pumpAndSettle();

    expect(find.text('50/50'), findsOneWidget);
    expect(find.text('AI'), findsOneWidget);
    expect(find.text('Skip'), findsOneWidget);
  });

  testWidgets('progress shows N/15 questions', (tester) async {
    await tester.pumpWidget(wrapWithProviders(const PracticeSessionPage()));
    await tester.pumpAndSettle();

    expect(find.textContaining('/15'), findsOneWidget);
  });
});

group('Combo Overlay', () {
  testWidgets('combo overlay appears at combo >= 2', (tester) async {
    await tester.pumpWidget(wrapWithProviders(
      const ComboOverlay(comboCount: 2),
    ));

    expect(find.textContaining('COMBO'), findsOneWidget);
    expect(find.textContaining('x2'), findsOneWidget);
  });

  testWidgets('combo overlay hidden at combo < 2', (tester) async {
    await tester.pumpWidget(wrapWithProviders(
      const ComboOverlay(comboCount: 1),
    ));

    expect(find.textContaining('COMBO'), findsNothing);
  });
});


// ═══════════════════════════════════════════════════════════════
// 5. SHARED WIDGETS
// ═══════════════════════════════════════════════════════════════

group('Heart Display', () {
  testWidgets('shows correct number of filled/empty hearts', (tester) async {
    await tester.pumpWidget(wrapWithProviders(
      const HeartDisplay(current: 3, max: 5),
    ));

    // 3 filled hearts + 2 empty hearts
    expect(find.byIcon(Icons.favorite), findsNWidgets(3));
    expect(find.byIcon(Icons.favorite_border), findsNWidgets(2));
  });

  testWidgets('shows unlimited icon for premium', (tester) async {
    await tester.pumpWidget(wrapWithProviders(
      const HeartDisplay(current: 5, max: 5, isUnlimited: true),
    ));

    expect(find.byIcon(Icons.all_inclusive), findsOneWidget);
  });
});

group('Streak Badge', () {
  testWidgets('shows streak count with fire emoji', (tester) async {
    await tester.pumpWidget(wrapWithProviders(
      const StreakBadge(days: 15, multiplier: 1.5),
    ));

    expect(find.textContaining('15'), findsOneWidget);
    expect(find.textContaining('1.5x'), findsOneWidget);
  });

  testWidgets('shows 0 streak without multiplier', (tester) async {
    await tester.pumpWidget(wrapWithProviders(
      const StreakBadge(days: 0, multiplier: 1.0),
    ));

    expect(find.textContaining('0'), findsOneWidget);
  });
});

group('XP Bar', () {
  testWidgets('shows level and progress bar', (tester) async {
    await tester.pumpWidget(wrapWithProviders(
      const XpBar(currentXp: 500, level: 3),
    ));

    expect(find.textContaining('Nivel 3'), findsOneWidget);
    expect(find.byType(LinearProgressIndicator), findsOneWidget);
  });
});


// ═══════════════════════════════════════════════════════════════
// 6. MILLIONAIRE & BOSS RAID SCREENS
// ═══════════════════════════════════════════════════════════════

group('Millionaire Page', () {
  testWidgets('shows prize ladder with 15 levels', (tester) async {
    await tester.pumpWidget(wrapWithProviders(const MillionairePage()));
    await tester.pumpAndSettle();

    // Debe mostrar escalera de premios
    expect(find.textContaining('1'), findsAtLeast(1));
    expect(find.textContaining('15'), findsAtLeast(1));
  });

  testWidgets('shows walk away button', (tester) async {
    await tester.pumpWidget(wrapWithProviders(const MillionairePage()));
    await tester.pumpAndSettle();

    expect(find.text('Retirarse'), findsOneWidget);
  });

  testWidgets('shows 3 lifelines with costs', (tester) async {
    await tester.pumpWidget(wrapWithProviders(const MillionairePage()));
    await tester.pumpAndSettle();

    expect(find.text('50/50'), findsOneWidget);
    expect(find.textContaining('AI'), findsOneWidget);
    expect(find.textContaining('50'), findsAtLeast(1)); // AI Hint cost
  });
});

group('Boss Raid Page', () {
  testWidgets('shows boss with HP bar', (tester) async {
    await tester.pumpWidget(wrapWithProviders(BossRaidPage(
      bossData: {
        'name': 'Dragón de Álgebra',
        'hp': 10000,
        'current_hp': 7500,
        'subject': 'Matematicas',
        'image_url': '',
      },
    )));
    await tester.pumpAndSettle();

    expect(find.textContaining('Dragón'), findsOneWidget);
    expect(find.byType(LinearProgressIndicator), findsOneWidget);
  });

  testWidgets('shows combo counter', (tester) async {
    await tester.pumpWidget(wrapWithProviders(BossRaidPage(
      bossData: {'name': 'Boss', 'hp': 10000, 'current_hp': 5000},
    )));
    await tester.pumpAndSettle();

    expect(find.textContaining('Combo'), findsOneWidget);
  });
});


// ═══════════════════════════════════════════════════════════════
// 7. HOME, MASTERY, LEAGUES, SHOP
// ═══════════════════════════════════════════════════════════════

group('Home Dashboard', () {
  testWidgets('shows user stats: level, hearts, streak, gold', (tester) async {
    await tester.pumpWidget(wrapWithProviders(const HomePage()));
    await tester.pumpAndSettle();

    expect(find.byType(HeartDisplay), findsOneWidget);
    expect(find.byType(StreakBadge), findsOneWidget);
    expect(find.byType(XpBar), findsOneWidget);
  });

  testWidgets('shows practice, millionaire, boss raid buttons', (tester) async {
    await tester.pumpWidget(wrapWithProviders(const HomePage()));
    await tester.pumpAndSettle();

    expect(find.textContaining('Practicar'), findsOneWidget);
    expect(find.textContaining('Millonario'), findsOneWidget);
  });
});

group('Mastery Page', () {
  testWidgets('shows mastery cards for each topic', (tester) async {
    await tester.pumpWidget(wrapWithProviders(const MasteryPage()));
    await tester.pumpAndSettle();

    expect(find.byType(LinearProgressIndicator), findsAtLeast(1));
  });
});

group('Leagues Page', () {
  testWidgets('shows current division and group ranking', (tester) async {
    await tester.pumpWidget(wrapWithProviders(const LeaguesPage()));
    await tester.pumpAndSettle();

    // División actual
    expect(find.textContaining(RegExp(r'Bronce|Plata|Oro|Platino|Diamante|Leyenda')),
        findsAtLeast(1));
  });
});

group('Shop Page', () {
  testWidgets('shows items with prices', (tester) async {
    await tester.pumpWidget(wrapWithProviders(const ShopPage()));
    await tester.pumpAndSettle();

    expect(find.textContaining('Gold'), findsAtLeast(1));
  });
});
