import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../features/shell/main_shell.dart';

// Feature Pages
import '../../features/auth/presentation/pages/splash_page.dart';
import '../../features/auth/presentation/pages/login_page.dart';
import '../../features/auth/presentation/pages/register_page.dart';
import '../../features/home/presentation/pages/home_page.dart';
import '../../features/home/presentation/pages/study_plan_page.dart';
import '../../features/leagues/presentation/pages/leagues_page.dart';
import '../../features/profile/presentation/pages/profile_page.dart';
import '../../features/settings/presentation/pages/settings_page.dart';
import '../../features/shop/presentation/pages/shop_page.dart';
import '../../features/practice/presentation/pages/boss_raid_page.dart';
import '../../features/practice/presentation/pages/boss_raid_battle_page.dart';
import '../../features/practice/presentation/pages/practice_session_page.dart';
import '../../features/practice/presentation/pages/subject_selection_page.dart';
import '../../features/auth/presentation/providers/auth_provider.dart';

// Millionaire Mode
import '../../features/millionaire/presentation/pages/millionaire_page.dart';

// Diagnostic Pages
import '../../features/diagnostic/presentation/pages/deep_diagnostic_page.dart';
import '../../features/onboarding/presentation/pages/quick_diagnostic_page.dart';
import '../../features/onboarding/presentation/pages/value_prop_page.dart';
import '../../features/onboarding/presentation/pages/results_reveal_page.dart';
import '../../features/onboarding/presentation/pages/first_mission_page.dart';
import '../../features/onboarding/presentation/pages/diagnostic_intro_page.dart';
// Onboarding Steps 2-5 (LOGICA_DE_NEGOCIO.md)
import '../../features/onboarding/presentation/pages/goal_selection_page.dart';
import '../../features/onboarding/presentation/pages/level_assessment_page.dart';
import '../../features/onboarding/presentation/pages/weak_subjects_page.dart';
import '../../features/onboarding/presentation/pages/study_time_page.dart';

// Study Plan Pages
import '../../features/study_plan/presentation/pages/unit_detail_page.dart';
import '../../features/study_plan/presentation/pages/unit_quiz_page.dart';

// Video Player
import '../../features/video/presentation/pages/video_player_page.dart';

// Conquest Mode
import '../../features/dungeon/presentation/pages/dungeon_map_page.dart';
import '../../features/dungeon/presentation/pages/battle_page.dart';

// Achievements
import '../../features/achievements/presentation/pages/achievements_page.dart';

// Stats
import '../../features/stats/presentation/pages/stats_page.dart';

// Placeholder Screens for missing implementations

class ErrorPage extends StatelessWidget { final Exception? error; const ErrorPage({super.key, this.error}); @override Widget build(BuildContext context) => Scaffold(body: Center(child: Text("Error: $error"))); }


// Routes
class AppRoutes {
  static const splash = '/';
  static const onboarding = '/onboarding';
  static const login = '/login';
  static const register = '/register';
  static const home = '/home';

  // Onboarding Steps 2-5 (LOGICA_DE_NEGOCIO.md)
  static const onboardingGoal = '/onboarding/goal';
  static const onboardingLevel = '/onboarding/level';
  static const onboardingSubjects = '/onboarding/subjects';
  static const onboardingStudyTime = '/onboarding/study-time';
  
  // Diagnostic
  static const diagnostic = '/diagnostic';
  static const diagnosticQuick = '/diagnostic/quick';
  static const diagnosticDeep = '/diagnostic/deep';
  static const resultsReveal = '/diagnostic/results'; // Consistent naming
  static const firstMission = '/diagnostic/mission';

  static const practice = '/practice';
  // Helper for practice session route
  static String practiceSession(String subjectId) => '/practice/session/$subjectId';
  // Helper alias for subject specific practice (legacy support)
  static String practiceSubject(String subjectId) => practiceSession(subjectId);

  static const studyPlan = '/study-plan';
  static const unitDetail = '/study-plan/unit/:unitId';
  static const unitQuiz = '/study-plan/unit/:unitId/quiz';
  static const videoPlayer = '/video/:videoId';

  /// Helper to build video player route with optional query parameters
  ///
  /// [videoId] - YouTube video ID or URL (will be extracted)
  /// [title] - Optional video title for display
  /// [description] - Optional video description
  /// [planId] - Optional study plan ID for tracking
  /// [unitNumber] - Optional unit number for tracking
  static String videoPlayerWithParams(
    String videoId, {
    String? title,
    String? description,
    String? planId,
    int? unitNumber,
  }) {
    final params = <String, String>{};
    if (title != null) params['title'] = title;
    if (description != null) params['description'] = description;
    if (planId != null) params['planId'] = planId;
    if (unitNumber != null) params['unitNumber'] = unitNumber.toString();

    final queryString = params.isNotEmpty
        ? '?${params.entries.map((e) => '${e.key}=${Uri.encodeComponent(e.value)}').join('&')}'
        : '';
    return '/video/$videoId$queryString';
  }
  
  static const leagues = '/leagues';
  static const bossRaid = '/boss-raid';
  static const bossRaidBattle = '/boss-raid/battle/:sessionId';

  // Millionaire Mode
  static const millionaire = '/millionaire';
  
  static const dungeonMap = '/dungeon/map';
  static const dungeonBattle = '/dungeon/battle';

  static const profile = '/profile';
  static const store = '/store';
  static const settings = '/settings';
  static const achievements = '/achievements';
  static const stats = '/stats';
}

final routerProvider = Provider<GoRouter>((ref) {
  // Watch auth provider to redirect when state changes
  final authState = ref.watch(authProvider);

  return GoRouter(
    initialLocation: AppRoutes.splash,
    debugLogDiagnostics: true,
    routes: [
      // Splash / Auth check
      GoRoute(
        path: AppRoutes.splash,
        builder: (context, state) => const SplashPage(),
      ),

      // Auth
      GoRoute(
        path: AppRoutes.login,
        builder: (context, state) => const LoginPage(),
      ),
      GoRoute(
        path: AppRoutes.register,
        builder: (context, state) => const RegisterPage(),
      ),

      // Onboarding (Value Prop)
      GoRoute(
        path: AppRoutes.onboarding,
        builder: (context, state) => const ValuePropPage(),
      ),

      // Onboarding Steps 2-5 (LOGICA_DE_NEGOCIO.md)
      GoRoute(
        path: AppRoutes.onboardingGoal,
        builder: (context, state) => const GoalSelectionPage(),
      ),
      GoRoute(
        path: AppRoutes.onboardingLevel,
        builder: (context, state) => const LevelAssessmentPage(),
      ),
      GoRoute(
        path: AppRoutes.onboardingSubjects,
        builder: (context, state) => const WeakSubjectsPage(),
      ),
      GoRoute(
        path: AppRoutes.onboardingStudyTime,
        builder: (context, state) => const StudyTimePage(),
      ),

      // Main Shell (con bottom nav)
      ShellRoute(
        builder: (context, state, child) => MainShell(child: child),
        routes: [
          GoRoute(
            path: AppRoutes.home,
            builder: (context, state) => const HomePage(),
          ),
          GoRoute(
            path: AppRoutes.leagues,
            builder: (context, state) => const LeaguesPage(),
          ),
          GoRoute(
            path: AppRoutes.studyPlan,
            builder: (context, state) => const StudyPlanPage(),
          ),
          GoRoute(
            path: AppRoutes.profile,
            builder: (context, state) => const ProfilePage(),
          ),
          GoRoute(
            path: AppRoutes.store,
            builder: (context, state) => const ShopPage(),
          ),
          GoRoute(
            path: AppRoutes.settings,
            builder: (context, state) => const SettingsPage(),
          ),
        ],
      ),

      // Diagnostic flow
      GoRoute(
        path: AppRoutes.diagnostic,
        builder: (context, state) => const DiagnosticIntroPage(),
      ),
      GoRoute(
        path: AppRoutes.diagnosticQuick,
        builder: (context, state) => const QuickDiagnosticPage(),
      ),
      GoRoute(
        path: AppRoutes.diagnosticDeep,
        builder: (context, state) => const DeepDiagnosticPage(),
      ),
      GoRoute(
        path: AppRoutes.resultsReveal,
        builder: (context, state) => const ResultsRevealPage(),
      ),
      GoRoute(
        path: AppRoutes.firstMission,
        builder: (context, state) => const FirstMissionPage(),
      ),

      // Practice
      GoRoute(
        path: AppRoutes.practice,
        builder: (context, state) => const SubjectSelectionPage(), // Maps to Practice Config
      ),
      GoRoute(
        path: '/practice/session/:subjectId', // Changed from sessionId to subjectId
        name: 'practice_session',
        builder: (context, state) {
          final subjectId = state.pathParameters['subjectId'];
          return PracticeSessionPage(subjectId: subjectId);
        },
      ),

      // Study Plan
      GoRoute(
        path: AppRoutes.unitDetail,
        builder: (context, state) {
          final unitId = state.pathParameters['unitId']!;
          return UnitDetailPage(unitId: unitId);
        },
      ),
      GoRoute(
        path: AppRoutes.unitQuiz,
        builder: (context, state) {
          final unitId = state.pathParameters['unitId']!;
          return UnitQuizPage(unitId: unitId);
        },
      ),
      GoRoute(
        path: AppRoutes.videoPlayer,
        builder: (context, state) {
          final videoId = state.pathParameters['videoId']!;
          // Optional query parameters for additional video context
          final title = state.uri.queryParameters['title'];
          final description = state.uri.queryParameters['description'];
          final planId = state.uri.queryParameters['planId'];
          final unitNumber = state.uri.queryParameters['unitNumber'];

          return VideoPlayerPage(
            videoId: videoId,
            title: title,
            description: description,
            planId: planId,
            unitNumber: unitNumber != null ? int.tryParse(unitNumber) : null,
          );
        },
      ),

      // Boss Raid
      GoRoute(
        path: AppRoutes.bossRaid,
        builder: (context, state) => const BossRaidPage(),
      ),
      GoRoute(
        path: AppRoutes.bossRaidBattle,
        builder: (context, state) {
          final sessionId = state.pathParameters['sessionId']!;
          return BossRaidBattlePage(sessionId: sessionId);
        },
      ),

      // Millionaire Mode
      GoRoute(
        path: AppRoutes.millionaire,
        builder: (context, state) => const MillionairePage(),
      ),

      // Conquest Mode
      GoRoute(
        path: AppRoutes.dungeonMap,
        builder: (context, state) => const DungeonMapPage(),
      ),
      GoRoute(
        path: AppRoutes.dungeonBattle,
        builder: (context, state) => const BattlePage(),
      ),

      // Achievements
      GoRoute(
        path: AppRoutes.achievements,
        builder: (context, state) => const AchievementsPage(),
      ),

      // Stats
      GoRoute(
        path: AppRoutes.stats,
        builder: (context, state) => const StatsPage(),
      ),
    ],

    // Redirect logic - supports onboarding flow per LOGICA_DE_NEGOCIO.md
    redirect: (context, state) {
      final isLoggedIn = authState.user != null;
      final location = state.matchedLocation;

      // Routes that don't require authentication (onboarding flow)
      final publicRoutes = [
        AppRoutes.splash,
        AppRoutes.onboarding,
        AppRoutes.onboardingGoal,
        AppRoutes.onboardingLevel,
        AppRoutes.onboardingSubjects,
        AppRoutes.onboardingStudyTime,
        AppRoutes.login,
        AppRoutes.register,
        AppRoutes.diagnostic,
        AppRoutes.diagnosticQuick,
        AppRoutes.resultsReveal,
        AppRoutes.firstMission,
      ];

      final isPublicRoute = publicRoutes.any((r) => location.startsWith(r));

      // Allow public routes without authentication
      if (isPublicRoute) {
        // Authenticated users on login/register -> redirect to appropriate page
        if (isLoggedIn && (location == AppRoutes.login || location == AppRoutes.register)) {
          // Check if onboarding is complete
          final diagnosticCompleted = authState.user?.diagnosticCompleted ?? false;
          if (!diagnosticCompleted) {
            return AppRoutes.diagnosticQuick;
          }
          return AppRoutes.home;
        }
        return null;
      }

      // Protected routes require authentication
      if (!isLoggedIn) {
        return AppRoutes.login;
      }

      return null;
    },

    // Error page
    errorBuilder: (context, state) => ErrorPage(error: state.error),
  );
});
