import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/network/api_client.dart';

class UserStats {
  final int questionsAnswered;
  final int correctAnswers;
  final int weeklyXp;
  final int streakDays;

  const UserStats({
    required this.questionsAnswered,
    required this.correctAnswers,
    required this.weeklyXp,
    required this.streakDays,
  });

  factory UserStats.empty() {
    return const UserStats(
      questionsAnswered: 0,
      correctAnswers: 0,
      weeklyXp: 0,
      streakDays: 0,
    );
  }

  double get accuracy {
    if (questionsAnswered == 0) return 0.0;
    return correctAnswers / questionsAnswered;
  }

  int get accuracyPercent => (accuracy * 100).toInt();
}

class UserStatsNotifier extends StateNotifier<AsyncValue<UserStats>> {
  final ApiClient _apiClient;

  UserStatsNotifier(this._apiClient) : super(const AsyncValue.loading()) {
    fetchStats();
  }

  Future<void> fetchStats() async {
    try {
      final response = await _apiClient.get('/users/cached/profile/me');
      if (response.statusCode == 200 && response.data != null) {
        final data = response.data;
        state = AsyncValue.data(UserStats(
          questionsAnswered: data['questions_answered'] ?? 0,
          correctAnswers: data['correct_answers'] ?? 0,
          weeklyXp: data['experience'] ?? 0, // Use experience as proxy
          streakDays: data['streak_days'] ?? 0,
        ));
      }
    } catch (e) {
      if (state.value == null) {
        state = AsyncValue.error(e, StackTrace.current);
      }
    }
  }

  void updateAfterAnswer(bool isCorrect) {
    state.whenData((stats) {
      state = AsyncValue.data(UserStats(
        questionsAnswered: stats.questionsAnswered + 1,
        correctAnswers: stats.correctAnswers + (isCorrect ? 1 : 0),
        weeklyXp: stats.weeklyXp,
        streakDays: stats.streakDays,
      ));
    });
  }
}

final userStatsProvider = StateNotifierProvider<UserStatsNotifier, AsyncValue<UserStats>>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return UserStatsNotifier(apiClient);
});
