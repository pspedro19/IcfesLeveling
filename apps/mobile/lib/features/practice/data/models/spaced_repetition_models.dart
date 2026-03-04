/// Spaced Repetition (SM-2 Algorithm) Models
/// These models represent the data structures for the spaced repetition system

/// Review result options based on SM-2 algorithm
/// - again: Complete failure, reset interval
/// - hard: Correct but with difficulty, reduce ease factor
/// - good: Correct with normal effort
/// - easy: Correct with little effort, increase ease factor
enum ReviewResult {
  again,
  hard,
  good,
  easy;

  String get apiValue {
    switch (this) {
      case ReviewResult.again:
        return 'AGAIN';
      case ReviewResult.hard:
        return 'HARD';
      case ReviewResult.good:
        return 'GOOD';
      case ReviewResult.easy:
        return 'EASY';
    }
  }

  /// Quality rating for SM-2 algorithm (0-5 scale)
  int get quality {
    switch (this) {
      case ReviewResult.again:
        return 0;
      case ReviewResult.hard:
        return 3;
      case ReviewResult.good:
        return 4;
      case ReviewResult.easy:
        return 5;
    }
  }

  static ReviewResult fromApiValue(String value) {
    switch (value.toUpperCase()) {
      case 'AGAIN':
        return ReviewResult.again;
      case 'HARD':
        return ReviewResult.hard;
      case 'GOOD':
        return ReviewResult.good;
      case 'EASY':
        return ReviewResult.easy;
      default:
        return ReviewResult.good;
    }
  }
}

/// Status of a spaced repetition item
enum SpacedItemStatus {
  newItem,
  learning,
  review,
  relearning;

  String get apiValue {
    switch (this) {
      case SpacedItemStatus.newItem:
        return 'NEW';
      case SpacedItemStatus.learning:
        return 'LEARNING';
      case SpacedItemStatus.review:
        return 'REVIEW';
      case SpacedItemStatus.relearning:
        return 'RELEARNING';
    }
  }

  static SpacedItemStatus fromApiValue(String value) {
    switch (value.toUpperCase()) {
      case 'NEW':
        return SpacedItemStatus.newItem;
      case 'LEARNING':
        return SpacedItemStatus.learning;
      case 'REVIEW':
        return SpacedItemStatus.review;
      case 'RELEARNING':
        return SpacedItemStatus.relearning;
      default:
        return SpacedItemStatus.newItem;
    }
  }
}

/// Represents a single item in the spaced repetition queue
class SpacedItem {
  final String itemId;
  final String questionId;
  final String questionText;
  final String? questionImageUrl;
  final List<SpacedItemOption> options;
  final String correctAnswer;
  final String? explanation;
  final double easeFactor;
  final int interval;
  final int repetitions;
  final DateTime dueDate;
  final SpacedItemStatus status;
  final String? subjectId;
  final String? subjectName;
  final String? topicId;
  final String? topicName;
  final DateTime? lastReviewDate;
  final int totalReviews;
  final int successfulReviews;

  SpacedItem({
    required this.itemId,
    required this.questionId,
    required this.questionText,
    this.questionImageUrl,
    required this.options,
    required this.correctAnswer,
    this.explanation,
    required this.easeFactor,
    required this.interval,
    required this.repetitions,
    required this.dueDate,
    required this.status,
    this.subjectId,
    this.subjectName,
    this.topicId,
    this.topicName,
    this.lastReviewDate,
    this.totalReviews = 0,
    this.successfulReviews = 0,
  });

  /// Success rate as a percentage (0-100)
  double get successRate =>
      totalReviews > 0 ? (successfulReviews / totalReviews) * 100 : 0;

  /// Whether this item is overdue
  bool get isOverdue => DateTime.now().isAfter(dueDate);

  /// Days until due (negative if overdue)
  int get daysUntilDue => dueDate.difference(DateTime.now()).inDays;

  factory SpacedItem.fromJson(Map<String, dynamic> json) {
    return SpacedItem(
      itemId: json['item_id'] ?? json['id'] ?? '',
      questionId: json['question_id'] ?? '',
      questionText: json['question_text'] ?? json['pregunta_texto'] ?? '',
      questionImageUrl: json['question_image_url'] ?? json['pregunta_imagen'],
      options: (json['options'] as List<dynamic>?)
              ?.map((o) => SpacedItemOption.fromJson(o))
              .toList() ??
          _buildOptionsFromJson(json),
      correctAnswer: json['correct_answer'] ?? json['respuesta_correcta'] ?? '',
      explanation: json['explanation'] ?? json['explicacion_texto'],
      easeFactor: (json['ease_factor'] ?? 2.5).toDouble(),
      interval: json['interval'] ?? 0,
      repetitions: json['repetitions'] ?? 0,
      dueDate: json['due_date'] != null
          ? DateTime.parse(json['due_date'])
          : DateTime.now(),
      status: SpacedItemStatus.fromApiValue(json['status'] ?? 'NEW'),
      subjectId: json['subject_id'],
      subjectName: json['subject_name'],
      topicId: json['topic_id'],
      topicName: json['topic_name'],
      lastReviewDate: json['last_review_date'] != null
          ? DateTime.parse(json['last_review_date'])
          : null,
      totalReviews: json['total_reviews'] ?? 0,
      successfulReviews: json['successful_reviews'] ?? 0,
    );
  }

  static List<SpacedItemOption> _buildOptionsFromJson(Map<String, dynamic> json) {
    final options = <SpacedItemOption>[];
    if (json['opcion_a_texto'] != null || json['opcion_a_imagen'] != null) {
      options.add(SpacedItemOption(
        id: 'A',
        text: json['opcion_a_texto'] ?? '',
        imageUrl: json['opcion_a_imagen'],
      ));
    }
    if (json['opcion_b_texto'] != null || json['opcion_b_imagen'] != null) {
      options.add(SpacedItemOption(
        id: 'B',
        text: json['opcion_b_texto'] ?? '',
        imageUrl: json['opcion_b_imagen'],
      ));
    }
    if (json['opcion_c_texto'] != null || json['opcion_c_imagen'] != null) {
      options.add(SpacedItemOption(
        id: 'C',
        text: json['opcion_c_texto'] ?? '',
        imageUrl: json['opcion_c_imagen'],
      ));
    }
    if (json['opcion_d_texto'] != null || json['opcion_d_imagen'] != null) {
      options.add(SpacedItemOption(
        id: 'D',
        text: json['opcion_d_texto'] ?? '',
        imageUrl: json['opcion_d_imagen'],
      ));
    }
    return options;
  }

  Map<String, dynamic> toJson() {
    return {
      'item_id': itemId,
      'question_id': questionId,
      'question_text': questionText,
      'question_image_url': questionImageUrl,
      'options': options.map((o) => o.toJson()).toList(),
      'correct_answer': correctAnswer,
      'explanation': explanation,
      'ease_factor': easeFactor,
      'interval': interval,
      'repetitions': repetitions,
      'due_date': dueDate.toIso8601String(),
      'status': status.apiValue,
      'subject_id': subjectId,
      'subject_name': subjectName,
      'topic_id': topicId,
      'topic_name': topicName,
      'last_review_date': lastReviewDate?.toIso8601String(),
      'total_reviews': totalReviews,
      'successful_reviews': successfulReviews,
    };
  }

  SpacedItem copyWith({
    String? itemId,
    String? questionId,
    String? questionText,
    String? questionImageUrl,
    List<SpacedItemOption>? options,
    String? correctAnswer,
    String? explanation,
    double? easeFactor,
    int? interval,
    int? repetitions,
    DateTime? dueDate,
    SpacedItemStatus? status,
    String? subjectId,
    String? subjectName,
    String? topicId,
    String? topicName,
    DateTime? lastReviewDate,
    int? totalReviews,
    int? successfulReviews,
  }) {
    return SpacedItem(
      itemId: itemId ?? this.itemId,
      questionId: questionId ?? this.questionId,
      questionText: questionText ?? this.questionText,
      questionImageUrl: questionImageUrl ?? this.questionImageUrl,
      options: options ?? this.options,
      correctAnswer: correctAnswer ?? this.correctAnswer,
      explanation: explanation ?? this.explanation,
      easeFactor: easeFactor ?? this.easeFactor,
      interval: interval ?? this.interval,
      repetitions: repetitions ?? this.repetitions,
      dueDate: dueDate ?? this.dueDate,
      status: status ?? this.status,
      subjectId: subjectId ?? this.subjectId,
      subjectName: subjectName ?? this.subjectName,
      topicId: topicId ?? this.topicId,
      topicName: topicName ?? this.topicName,
      lastReviewDate: lastReviewDate ?? this.lastReviewDate,
      totalReviews: totalReviews ?? this.totalReviews,
      successfulReviews: successfulReviews ?? this.successfulReviews,
    );
  }
}

/// Option for a spaced repetition question
class SpacedItemOption {
  final String id;
  final String text;
  final String? imageUrl;

  SpacedItemOption({
    required this.id,
    required this.text,
    this.imageUrl,
  });

  factory SpacedItemOption.fromJson(Map<String, dynamic> json) {
    return SpacedItemOption(
      id: json['id'] ?? '',
      text: json['text'] ?? '',
      imageUrl: json['image_url'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'text': text,
      'image_url': imageUrl,
    };
  }
}

/// Response from the daily reviews endpoint
class DailyReviewsResponse {
  final DateTime date;
  final int totalDue;
  final int newItems;
  final int reviewItems;
  final int overdue;
  final List<SpacedItem> items;
  final int estimatedTimeMinutes;

  DailyReviewsResponse({
    required this.date,
    required this.totalDue,
    required this.newItems,
    required this.reviewItems,
    this.overdue = 0,
    required this.items,
    this.estimatedTimeMinutes = 0,
  });

  bool get hasDueItems => totalDue > 0;

  factory DailyReviewsResponse.fromJson(Map<String, dynamic> json) {
    final data = json['data'] ?? json;
    return DailyReviewsResponse(
      date: data['date'] != null
          ? DateTime.parse(data['date'])
          : DateTime.now(),
      totalDue: data['total_due'] ?? 0,
      newItems: data['new_items'] ?? 0,
      reviewItems: data['review_items'] ?? 0,
      overdue: data['overdue'] ?? 0,
      items: (data['items'] as List<dynamic>?)
              ?.map((item) => SpacedItem.fromJson(item))
              .toList() ??
          [],
      estimatedTimeMinutes: data['estimated_time_minutes'] ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'date': date.toIso8601String(),
      'total_due': totalDue,
      'new_items': newItems,
      'review_items': reviewItems,
      'overdue': overdue,
      'items': items.map((item) => item.toJson()).toList(),
      'estimated_time_minutes': estimatedTimeMinutes,
    };
  }
}

/// Response from submitting a review
class SubmitReviewResponse {
  final String itemId;
  final bool success;
  final double newEaseFactor;
  final int newInterval;
  final DateTime nextDueDate;
  final SpacedItemStatus newStatus;
  final int xpEarned;
  final String? message;

  SubmitReviewResponse({
    required this.itemId,
    required this.success,
    required this.newEaseFactor,
    required this.newInterval,
    required this.nextDueDate,
    required this.newStatus,
    this.xpEarned = 0,
    this.message,
  });

  factory SubmitReviewResponse.fromJson(Map<String, dynamic> json) {
    final data = json['data'] ?? json;
    return SubmitReviewResponse(
      itemId: data['item_id'] ?? '',
      success: data['success'] ?? true,
      newEaseFactor: (data['new_ease_factor'] ?? data['ease_factor'] ?? 2.5).toDouble(),
      newInterval: data['new_interval'] ?? data['interval'] ?? 1,
      nextDueDate: data['next_due_date'] != null
          ? DateTime.parse(data['next_due_date'])
          : DateTime.now().add(const Duration(days: 1)),
      newStatus: SpacedItemStatus.fromApiValue(data['new_status'] ?? data['status'] ?? 'REVIEW'),
      xpEarned: data['xp_earned'] ?? 0,
      message: data['message'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'item_id': itemId,
      'success': success,
      'new_ease_factor': newEaseFactor,
      'new_interval': newInterval,
      'next_due_date': nextDueDate.toIso8601String(),
      'new_status': newStatus.apiValue,
      'xp_earned': xpEarned,
      'message': message,
    };
  }
}

/// Analytics data for retention and learning progress
class RetentionAnalytics {
  final int totalItems;
  final int matureItems;
  final int learningItems;
  final int newItems;
  final double averageEaseFactor;
  final double retentionRate;
  final int reviewsToday;
  final int reviewsThisWeek;
  final int totalReviewsAllTime;
  final List<DailyReviewStats> dailyStats;
  final Map<String, SubjectRetention> subjectRetention;
  final int currentStreak;
  final int longestStreak;
  final DateTime? lastReviewDate;

  RetentionAnalytics({
    required this.totalItems,
    required this.matureItems,
    required this.learningItems,
    required this.newItems,
    required this.averageEaseFactor,
    required this.retentionRate,
    required this.reviewsToday,
    required this.reviewsThisWeek,
    required this.totalReviewsAllTime,
    this.dailyStats = const [],
    this.subjectRetention = const {},
    this.currentStreak = 0,
    this.longestStreak = 0,
    this.lastReviewDate,
  });

  /// Items that have graduated to long-term memory (interval > 21 days)
  int get graduatedItems => matureItems;

  factory RetentionAnalytics.fromJson(Map<String, dynamic> json) {
    final data = json['data'] ?? json;
    return RetentionAnalytics(
      totalItems: data['total_items'] ?? 0,
      matureItems: data['mature_items'] ?? 0,
      learningItems: data['learning_items'] ?? 0,
      newItems: data['new_items'] ?? 0,
      averageEaseFactor: (data['average_ease_factor'] ?? 2.5).toDouble(),
      retentionRate: (data['retention_rate'] ?? 0.0).toDouble(),
      reviewsToday: data['reviews_today'] ?? 0,
      reviewsThisWeek: data['reviews_this_week'] ?? 0,
      totalReviewsAllTime: data['total_reviews_all_time'] ?? 0,
      dailyStats: (data['daily_stats'] as List<dynamic>?)
              ?.map((s) => DailyReviewStats.fromJson(s))
              .toList() ??
          [],
      subjectRetention: (data['subject_retention'] as Map<String, dynamic>?)
              ?.map((key, value) =>
                  MapEntry(key, SubjectRetention.fromJson(value))) ??
          {},
      currentStreak: data['current_streak'] ?? 0,
      longestStreak: data['longest_streak'] ?? 0,
      lastReviewDate: data['last_review_date'] != null
          ? DateTime.parse(data['last_review_date'])
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'total_items': totalItems,
      'mature_items': matureItems,
      'learning_items': learningItems,
      'new_items': newItems,
      'average_ease_factor': averageEaseFactor,
      'retention_rate': retentionRate,
      'reviews_today': reviewsToday,
      'reviews_this_week': reviewsThisWeek,
      'total_reviews_all_time': totalReviewsAllTime,
      'daily_stats': dailyStats.map((s) => s.toJson()).toList(),
      'subject_retention':
          subjectRetention.map((key, value) => MapEntry(key, value.toJson())),
      'current_streak': currentStreak,
      'longest_streak': longestStreak,
      'last_review_date': lastReviewDate?.toIso8601String(),
    };
  }

  static RetentionAnalytics empty() {
    return RetentionAnalytics(
      totalItems: 0,
      matureItems: 0,
      learningItems: 0,
      newItems: 0,
      averageEaseFactor: 2.5,
      retentionRate: 0.0,
      reviewsToday: 0,
      reviewsThisWeek: 0,
      totalReviewsAllTime: 0,
    );
  }
}

/// Daily review statistics for analytics charts
class DailyReviewStats {
  final DateTime date;
  final int reviewed;
  final int correct;
  final int incorrect;
  final double retentionRate;
  final int averageTimeMs;

  DailyReviewStats({
    required this.date,
    required this.reviewed,
    required this.correct,
    required this.incorrect,
    required this.retentionRate,
    this.averageTimeMs = 0,
  });

  factory DailyReviewStats.fromJson(Map<String, dynamic> json) {
    return DailyReviewStats(
      date: DateTime.parse(json['date']),
      reviewed: json['reviewed'] ?? 0,
      correct: json['correct'] ?? 0,
      incorrect: json['incorrect'] ?? 0,
      retentionRate: (json['retention_rate'] ?? 0.0).toDouble(),
      averageTimeMs: json['average_time_ms'] ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'date': date.toIso8601String(),
      'reviewed': reviewed,
      'correct': correct,
      'incorrect': incorrect,
      'retention_rate': retentionRate,
      'average_time_ms': averageTimeMs,
    };
  }
}

/// Per-subject retention data
class SubjectRetention {
  final String subjectId;
  final String subjectName;
  final int totalItems;
  final int matureItems;
  final double retentionRate;
  final double averageEaseFactor;

  SubjectRetention({
    required this.subjectId,
    required this.subjectName,
    required this.totalItems,
    required this.matureItems,
    required this.retentionRate,
    required this.averageEaseFactor,
  });

  factory SubjectRetention.fromJson(Map<String, dynamic> json) {
    return SubjectRetention(
      subjectId: json['subject_id'] ?? '',
      subjectName: json['subject_name'] ?? '',
      totalItems: json['total_items'] ?? 0,
      matureItems: json['mature_items'] ?? 0,
      retentionRate: (json['retention_rate'] ?? 0.0).toDouble(),
      averageEaseFactor: (json['average_ease_factor'] ?? 2.5).toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'subject_id': subjectId,
      'subject_name': subjectName,
      'total_items': totalItems,
      'mature_items': matureItems,
      'retention_rate': retentionRate,
      'average_ease_factor': averageEaseFactor,
    };
  }
}

/// Request to create a new spaced repetition schedule from a study plan
class CreateScheduleRequest {
  final String planId;
  final int newCardsPerDay;
  final int maxReviewsPerDay;

  CreateScheduleRequest({
    required this.planId,
    this.newCardsPerDay = 20,
    this.maxReviewsPerDay = 100,
  });

  Map<String, dynamic> toJson() {
    return {
      'plan_id': planId,
      'new_cards_per_day': newCardsPerDay,
      'max_reviews_per_day': maxReviewsPerDay,
    };
  }
}

/// Response from creating a schedule
class CreateScheduleResponse {
  final String scheduleId;
  final int itemsCreated;
  final DateTime firstReviewDate;
  final String message;

  CreateScheduleResponse({
    required this.scheduleId,
    required this.itemsCreated,
    required this.firstReviewDate,
    required this.message,
  });

  factory CreateScheduleResponse.fromJson(Map<String, dynamic> json) {
    final data = json['data'] ?? json;
    return CreateScheduleResponse(
      scheduleId: data['schedule_id'] ?? '',
      itemsCreated: data['items_created'] ?? 0,
      firstReviewDate: data['first_review_date'] != null
          ? DateTime.parse(data['first_review_date'])
          : DateTime.now(),
      message: data['message'] ?? 'Schedule created successfully',
    );
  }
}
