import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/utils/app_haptics.dart';
import '../../../../shared/providers/user_stats_provider.dart';
import '../../../engagement/presentation/providers/engagement_provider.dart';
import '../../data/datasources/spaced_repetition_remote_datasource.dart';
import '../../domain/repositories/spaced_repetition_repository.dart';
import '../../data/repositories/spaced_repetition_repository_impl.dart';
import '../../data/models/spaced_repetition_models.dart';

// ============================================================================
// STATE CLASS
// ============================================================================

/// State for the spaced repetition review session
class SpacedRepetitionState {
  /// Items due for review today
  final List<SpacedItem> dueItems;

  /// Index of the current item being reviewed
  final int currentIndex;

  /// Currently selected answer option
  final String? selectedOptionId;

  /// Whether the current answer has been submitted
  final bool isAnswerSubmitted;

  /// Whether the last answer was correct
  final bool isCurrentCorrect;

  /// Result of the last review submission
  final SubmitReviewResponse? lastReviewResult;

  /// Analytics data
  final RetentionAnalytics? analytics;

  /// Daily review summary
  final DailyReviewsResponse? dailySummary;

  /// Loading state
  final bool isLoading;

  /// Submitting review state
  final bool isSubmitting;

  /// Error message
  final String? error;

  /// Session statistics
  final int reviewsCompleted;
  final int correctReviews;
  final int totalXpEarned;

  /// Whether the session is finished
  final bool isFinished;

  /// Stopwatch start time for response timing
  final DateTime? questionStartTime;

  SpacedRepetitionState({
    this.dueItems = const [],
    this.currentIndex = 0,
    this.selectedOptionId,
    this.isAnswerSubmitted = false,
    this.isCurrentCorrect = false,
    this.lastReviewResult,
    this.analytics,
    this.dailySummary,
    this.isLoading = false,
    this.isSubmitting = false,
    this.error,
    this.reviewsCompleted = 0,
    this.correctReviews = 0,
    this.totalXpEarned = 0,
    this.isFinished = false,
    this.questionStartTime,
  });

  /// Get the current item being reviewed
  SpacedItem? get currentItem =>
      currentIndex < dueItems.length ? dueItems[currentIndex] : null;

  /// Total items due for review
  int get totalDue => dueItems.length;

  /// Progress through the review session (0.0 to 1.0)
  double get progress => totalDue > 0 ? currentIndex / totalDue : 0.0;

  /// Whether there are more items to review
  bool get hasMoreItems => currentIndex < dueItems.length - 1;

  /// Whether there are items due for review
  bool get hasDueItems => dueItems.isNotEmpty;

  /// Accuracy percentage
  double get accuracy =>
      reviewsCompleted > 0 ? (correctReviews / reviewsCompleted) * 100 : 0.0;

  /// Number of new items in the queue
  int get newItemsCount =>
      dueItems.where((item) => item.status == SpacedItemStatus.newItem).length;

  /// Number of review items in the queue
  int get reviewItemsCount =>
      dueItems.where((item) => item.status != SpacedItemStatus.newItem).length;

  /// Number of overdue items
  int get overdueCount => dueItems.where((item) => item.isOverdue).length;

  SpacedRepetitionState copyWith({
    List<SpacedItem>? dueItems,
    int? currentIndex,
    String? selectedOptionId,
    bool? isAnswerSubmitted,
    bool? isCurrentCorrect,
    SubmitReviewResponse? lastReviewResult,
    RetentionAnalytics? analytics,
    DailyReviewsResponse? dailySummary,
    bool? isLoading,
    bool? isSubmitting,
    String? error,
    int? reviewsCompleted,
    int? correctReviews,
    int? totalXpEarned,
    bool? isFinished,
    DateTime? questionStartTime,
    bool clearError = false,
    bool clearSelectedOption = false,
    bool clearLastResult = false,
  }) {
    return SpacedRepetitionState(
      dueItems: dueItems ?? this.dueItems,
      currentIndex: currentIndex ?? this.currentIndex,
      selectedOptionId:
          clearSelectedOption ? null : selectedOptionId ?? this.selectedOptionId,
      isAnswerSubmitted: isAnswerSubmitted ?? this.isAnswerSubmitted,
      isCurrentCorrect: isCurrentCorrect ?? this.isCurrentCorrect,
      lastReviewResult:
          clearLastResult ? null : lastReviewResult ?? this.lastReviewResult,
      analytics: analytics ?? this.analytics,
      dailySummary: dailySummary ?? this.dailySummary,
      isLoading: isLoading ?? this.isLoading,
      isSubmitting: isSubmitting ?? this.isSubmitting,
      error: clearError ? null : error ?? this.error,
      reviewsCompleted: reviewsCompleted ?? this.reviewsCompleted,
      correctReviews: correctReviews ?? this.correctReviews,
      totalXpEarned: totalXpEarned ?? this.totalXpEarned,
      isFinished: isFinished ?? this.isFinished,
      questionStartTime: questionStartTime ?? this.questionStartTime,
    );
  }
}

// ============================================================================
// DATA LAYER PROVIDERS
// ============================================================================

final spacedRepetitionRemoteDataSourceProvider = Provider.autoDispose((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return SpacedRepetitionRemoteDataSource(apiClient);
});

final spacedRepetitionRepositoryProvider =
    Provider.autoDispose<SpacedRepetitionRepository>((ref) {
  final remote = ref.watch(spacedRepetitionRemoteDataSourceProvider);
  return SpacedRepetitionRepositoryImpl(remote);
});

// ============================================================================
// NOTIFIER
// ============================================================================

class SpacedRepetitionNotifier extends StateNotifier<SpacedRepetitionState> {
  final SpacedRepetitionRepository _repository;
  final EngagementNotifier _engagementNotifier;
  final UserStatsNotifier _userStatsNotifier;

  SpacedRepetitionNotifier(
    this._repository,
    this._engagementNotifier,
    this._userStatsNotifier,
  ) : super(SpacedRepetitionState());

  /// Load daily reviews for today (or specified date)
  Future<void> loadDailyReviews({DateTime? date}) async {
    state = state.copyWith(isLoading: true, clearError: true);

    try {
      final response = await _repository.getDailyReviews(date: date);
      state = state.copyWith(
        isLoading: false,
        dueItems: response.items,
        dailySummary: response,
        currentIndex: 0,
        reviewsCompleted: 0,
        correctReviews: 0,
        totalXpEarned: 0,
        isFinished: false,
        questionStartTime: DateTime.now(),
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  /// Load retention analytics
  Future<void> loadAnalytics({int daysBack = 30}) async {
    try {
      final analytics = await _repository.getAnalytics(daysBack: daysBack);
      state = state.copyWith(analytics: analytics);
    } catch (e) {
      // Analytics failure shouldn't block the UI
      print('Failed to load analytics: $e');
    }
  }

  /// Select an answer option
  void selectOption(String optionId) {
    if (state.isAnswerSubmitted || state.isSubmitting) return;
    AppHaptics.light();
    state = state.copyWith(selectedOptionId: optionId);
  }

  /// Submit the current review
  /// The ReviewResult is determined based on correctness and response time
  Future<void> submitReview() async {
    final currentItem = state.currentItem;
    if (currentItem == null ||
        state.selectedOptionId == null ||
        state.isAnswerSubmitted ||
        state.isSubmitting) {
      return;
    }

    state = state.copyWith(isSubmitting: true, clearError: true);

    // Calculate response time
    final responseTimeMs = state.questionStartTime != null
        ? DateTime.now().difference(state.questionStartTime!).inMilliseconds
        : 0;

    // Determine if answer is correct
    final isCorrect = state.selectedOptionId == currentItem.correctAnswer;

    // Determine review result based on correctness and response time
    final reviewResult = _determineReviewResult(
      isCorrect: isCorrect,
      responseTimeMs: responseTimeMs,
    );

    try {
      final response = await _repository.submitReview(
        itemId: currentItem.itemId,
        result: reviewResult,
        responseTimeMs: responseTimeMs,
        selectedAnswer: state.selectedOptionId,
      );

      // Provide haptic feedback
      if (isCorrect) {
        AppHaptics.success();
      } else {
        AppHaptics.error();
      }

      // Update engagement XP if earned
      if (response.xpEarned > 0) {
        _engagementNotifier.addXp(response.xpEarned);
      }

      // Update user stats for accuracy tracking
      _userStatsNotifier.updateAfterAnswer(isCorrect);

      state = state.copyWith(
        isSubmitting: false,
        isAnswerSubmitted: true,
        isCurrentCorrect: isCorrect,
        lastReviewResult: response,
        reviewsCompleted: state.reviewsCompleted + 1,
        correctReviews:
            isCorrect ? state.correctReviews + 1 : state.correctReviews,
        totalXpEarned: state.totalXpEarned + response.xpEarned,
      );
    } catch (e) {
      state = state.copyWith(isSubmitting: false, error: e.toString());
    }
  }

  /// Submit a review with an explicit result (for external use)
  Future<void> submitReviewWithResult({
    required String itemId,
    required ReviewResult result,
    required int responseTimeMs,
    String? selectedAnswer,
  }) async {
    try {
      await _repository.submitReview(
        itemId: itemId,
        result: result,
        responseTimeMs: responseTimeMs,
        selectedAnswer: selectedAnswer,
      );
    } catch (e) {
      // Fire and forget - don't block on errors
      print('Failed to submit spaced repetition review: $e');
    }
  }

  /// Move to the next item
  void nextItem() {
    if (!state.isAnswerSubmitted) return;

    if (state.hasMoreItems) {
      state = state.copyWith(
        currentIndex: state.currentIndex + 1,
        isAnswerSubmitted: false,
        isCurrentCorrect: false,
        clearSelectedOption: true,
        clearLastResult: true,
        questionStartTime: DateTime.now(),
      );
    } else {
      // No more items, finish the session
      state = state.copyWith(isFinished: true);
      // Refresh analytics after completing reviews
      loadAnalytics();
    }
  }

  /// Create a spaced repetition schedule from a study plan
  Future<void> createSchedule({
    required String planId,
    int newCardsPerDay = 20,
    int maxReviewsPerDay = 100,
  }) async {
    state = state.copyWith(isLoading: true, clearError: true);

    try {
      await _repository.createSchedule(
        planId: planId,
        newCardsPerDay: newCardsPerDay,
        maxReviewsPerDay: maxReviewsPerDay,
      );

      // Reload daily reviews after creating schedule
      await loadDailyReviews();
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  /// Add a question to the spaced repetition queue
  /// Called when user answers incorrectly to ensure review
  Future<void> addItemForReview({
    required String questionId,
    String? subjectId,
    String? topicId,
  }) async {
    try {
      await _repository.addItem(
        questionId: questionId,
        subjectId: subjectId,
        topicId: topicId,
      );
    } catch (e) {
      // Don't fail silently but also don't block the user
      print('Failed to add item for review: $e');
    }
  }

  /// Reset the review session
  void resetSession() {
    state = SpacedRepetitionState(
      analytics: state.analytics, // Keep analytics
    );
  }

  /// Determine the review result based on answer correctness and response time
  ///
  /// SM-2 quality ratings:
  /// - AGAIN (0): Complete failure, couldn't recall
  /// - HARD (3): Correct with significant difficulty
  /// - GOOD (4): Correct with some hesitation
  /// - EASY (5): Perfect recall with no hesitation
  ReviewResult _determineReviewResult({
    required bool isCorrect,
    required int responseTimeMs,
  }) {
    if (!isCorrect) {
      return ReviewResult.again;
    }

    // Response time thresholds (in milliseconds)
    const fastThreshold = 5000; // 5 seconds
    const slowThreshold = 15000; // 15 seconds

    if (responseTimeMs < fastThreshold) {
      return ReviewResult.easy;
    } else if (responseTimeMs > slowThreshold) {
      return ReviewResult.hard;
    } else {
      return ReviewResult.good;
    }
  }
}

// ============================================================================
// MAIN PROVIDER
// ============================================================================

final spacedRepetitionProvider =
    StateNotifierProvider.autoDispose<SpacedRepetitionNotifier, SpacedRepetitionState>(
        (ref) {
  final repo = ref.watch(spacedRepetitionRepositoryProvider);
  final engagement = ref.read(engagementProvider.notifier);
  final userStats = ref.read(userStatsProvider.notifier);
  return SpacedRepetitionNotifier(repo, engagement, userStats);
});

// ============================================================================
// CONVENIENCE PROVIDERS
// ============================================================================

/// Provider for just the daily reviews count (for badges/notifications)
final dailyReviewsCountProvider = FutureProvider.autoDispose<int>((ref) async {
  final repo = ref.watch(spacedRepetitionRepositoryProvider);
  try {
    final response = await repo.getDailyReviews();
    return response.totalDue;
  } catch (e) {
    return 0;
  }
});

/// Provider for retention analytics
final retentionAnalyticsProvider =
    FutureProvider.autoDispose<RetentionAnalytics>((ref) async {
  final repo = ref.watch(spacedRepetitionRepositoryProvider);
  return await repo.getAnalytics(daysBack: 30);
});

/// Provider to check if there are due reviews (for home page indicator)
final hasDueReviewsProvider = FutureProvider.autoDispose<bool>((ref) async {
  final count = await ref.watch(dailyReviewsCountProvider.future);
  return count > 0;
});
