/// Stats Models for ICFES Leveling
/// Data models for statistics and progress tracking

/// User progress overview
class UserProgressOverview {
  final int totalXp;
  final int level;
  final int xpForNextLevel;
  final int currentStreak;
  final int maxStreak;
  final int questionsAnswered;
  final int correctAnswers;
  final int studyDays;
  final int totalStudyMinutes;
  final DateTime? lastActivityDate;

  const UserProgressOverview({
    required this.totalXp,
    required this.level,
    required this.xpForNextLevel,
    required this.currentStreak,
    required this.maxStreak,
    required this.questionsAnswered,
    required this.correctAnswers,
    required this.studyDays,
    required this.totalStudyMinutes,
    this.lastActivityDate,
  });

  double get accuracy => questionsAnswered > 0
      ? correctAnswers / questionsAnswered
      : 0.0;

  int get accuracyPercent => (accuracy * 100).toInt();

  double get levelProgress => xpForNextLevel > 0
      ? (totalXp % (level * level * 100)) / xpForNextLevel
      : 0.0;

  factory UserProgressOverview.fromJson(Map<String, dynamic> json) {
    return UserProgressOverview(
      totalXp: json['total_xp'] ?? json['experience'] ?? 0,
      level: json['level'] ?? 1,
      xpForNextLevel: json['xp_for_next_level'] ?? 100,
      currentStreak: json['current_streak'] ?? json['streak_days'] ?? 0,
      maxStreak: json['max_streak'] ?? 0,
      questionsAnswered: json['questions_answered'] ?? 0,
      correctAnswers: json['correct_answers'] ?? 0,
      studyDays: json['study_days'] ?? 0,
      totalStudyMinutes: json['total_study_minutes'] ?? 0,
      lastActivityDate: json['last_activity_date'] != null
          ? DateTime.parse(json['last_activity_date'])
          : null,
    );
  }

  factory UserProgressOverview.empty() {
    return const UserProgressOverview(
      totalXp: 0,
      level: 1,
      xpForNextLevel: 100,
      currentStreak: 0,
      maxStreak: 0,
      questionsAnswered: 0,
      correctAnswers: 0,
      studyDays: 0,
      totalStudyMinutes: 0,
    );
  }
}

/// Subject progress data
class SubjectProgress {
  final String subjectId;
  final String subjectName;
  final String icon;
  final int color;
  final double masteryLevel; // 0.0 to 1.0
  final int questionsAnswered;
  final int correctAnswers;
  final int totalQuestions;
  final double nationalAverage;
  final String strengthLevel; // 'weak', 'average', 'strong'
  final List<TopicProgress> topics;

  const SubjectProgress({
    required this.subjectId,
    required this.subjectName,
    required this.icon,
    required this.color,
    required this.masteryLevel,
    required this.questionsAnswered,
    required this.correctAnswers,
    required this.totalQuestions,
    required this.nationalAverage,
    required this.strengthLevel,
    this.topics = const [],
  });

  double get accuracy => questionsAnswered > 0
      ? correctAnswers / questionsAnswered
      : 0.0;

  int get accuracyPercent => (accuracy * 100).toInt();

  bool get isStrength => strengthLevel == 'strong';
  bool get isWeakness => strengthLevel == 'weak';

  factory SubjectProgress.fromJson(Map<String, dynamic> json) {
    return SubjectProgress(
      subjectId: json['subject_id'] ?? '',
      subjectName: json['subject_name'] ?? '',
      icon: json['icon'] ?? 'book',
      color: json['color'] ?? 0xFF2196F3,
      masteryLevel: (json['mastery_level'] ?? 0.0).toDouble(),
      questionsAnswered: json['questions_answered'] ?? 0,
      correctAnswers: json['correct_answers'] ?? 0,
      totalQuestions: json['total_questions'] ?? 0,
      nationalAverage: (json['national_average'] ?? 0.5).toDouble(),
      strengthLevel: json['strength_level'] ?? 'average',
      topics: (json['topics'] as List?)
          ?.map((t) => TopicProgress.fromJson(t))
          .toList() ?? [],
    );
  }
}

/// Topic progress within a subject
class TopicProgress {
  final String topicId;
  final String topicName;
  final double masteryLevel;
  final int questionsAnswered;
  final int correctAnswers;
  final bool isCompleted;

  const TopicProgress({
    required this.topicId,
    required this.topicName,
    required this.masteryLevel,
    required this.questionsAnswered,
    required this.correctAnswers,
    required this.isCompleted,
  });

  double get accuracy => questionsAnswered > 0
      ? correctAnswers / questionsAnswered
      : 0.0;

  factory TopicProgress.fromJson(Map<String, dynamic> json) {
    return TopicProgress(
      topicId: json['topic_id'] ?? '',
      topicName: json['topic_name'] ?? '',
      masteryLevel: (json['mastery_level'] ?? 0.0).toDouble(),
      questionsAnswered: json['questions_answered'] ?? 0,
      correctAnswers: json['correct_answers'] ?? 0,
      isCompleted: json['is_completed'] ?? false,
    );
  }
}

/// Study plan progress
class StudyPlanProgress {
  final String planId;
  final String planName;
  final int totalUnits;
  final int completedUnits;
  final int totalVideos;
  final int watchedVideos;
  final int totalQuizzes;
  final int passedQuizzes;
  final double overallProgress; // 0.0 to 1.0
  final DateTime? startDate;
  final DateTime? estimatedCompletionDate;
  final List<UnitProgress> units;

  const StudyPlanProgress({
    required this.planId,
    required this.planName,
    required this.totalUnits,
    required this.completedUnits,
    required this.totalVideos,
    required this.watchedVideos,
    required this.totalQuizzes,
    required this.passedQuizzes,
    required this.overallProgress,
    this.startDate,
    this.estimatedCompletionDate,
    this.units = const [],
  });

  bool get isCompleted => completedUnits >= totalUnits;

  int get progressPercent => (overallProgress * 100).toInt();

  factory StudyPlanProgress.fromJson(Map<String, dynamic> json) {
    return StudyPlanProgress(
      planId: json['plan_id'] ?? '',
      planName: json['plan_name'] ?? 'Plan de Estudio',
      totalUnits: json['total_units'] ?? 0,
      completedUnits: json['completed_units'] ?? 0,
      totalVideos: json['total_videos'] ?? 0,
      watchedVideos: json['watched_videos'] ?? 0,
      totalQuizzes: json['total_quizzes'] ?? 0,
      passedQuizzes: json['passed_quizzes'] ?? 0,
      overallProgress: (json['overall_progress'] ?? 0.0).toDouble(),
      startDate: json['start_date'] != null
          ? DateTime.parse(json['start_date'])
          : null,
      estimatedCompletionDate: json['estimated_completion_date'] != null
          ? DateTime.parse(json['estimated_completion_date'])
          : null,
      units: (json['units'] as List?)
          ?.map((u) => UnitProgress.fromJson(u))
          .toList() ?? [],
    );
  }

  factory StudyPlanProgress.empty() {
    return const StudyPlanProgress(
      planId: '',
      planName: 'Sin plan activo',
      totalUnits: 0,
      completedUnits: 0,
      totalVideos: 0,
      watchedVideos: 0,
      totalQuizzes: 0,
      passedQuizzes: 0,
      overallProgress: 0.0,
    );
  }
}

/// Individual unit progress
class UnitProgress {
  final String unitId;
  final String unitName;
  final int unitNumber;
  final bool isCompleted;
  final bool isLocked;
  final double progress;
  final int videosWatched;
  final int totalVideos;
  final bool quizPassed;
  final int? quizScore;

  const UnitProgress({
    required this.unitId,
    required this.unitName,
    required this.unitNumber,
    required this.isCompleted,
    required this.isLocked,
    required this.progress,
    required this.videosWatched,
    required this.totalVideos,
    required this.quizPassed,
    this.quizScore,
  });

  factory UnitProgress.fromJson(Map<String, dynamic> json) {
    return UnitProgress(
      unitId: json['unit_id'] ?? '',
      unitName: json['unit_name'] ?? '',
      unitNumber: json['unit_number'] ?? 0,
      isCompleted: json['is_completed'] ?? false,
      isLocked: json['is_locked'] ?? true,
      progress: (json['progress'] ?? 0.0).toDouble(),
      videosWatched: json['videos_watched'] ?? 0,
      totalVideos: json['total_videos'] ?? 0,
      quizPassed: json['quiz_passed'] ?? false,
      quizScore: json['quiz_score'],
    );
  }
}

/// Recent activity item
class RecentActivity {
  final String id;
  final String type; // 'practice', 'video', 'quiz', 'diagnostic', 'achievement'
  final String title;
  final String? subtitle;
  final int xpEarned;
  final DateTime timestamp;
  final Map<String, dynamic>? metadata;

  const RecentActivity({
    required this.id,
    required this.type,
    required this.title,
    this.subtitle,
    required this.xpEarned,
    required this.timestamp,
    this.metadata,
  });

  factory RecentActivity.fromJson(Map<String, dynamic> json) {
    return RecentActivity(
      id: json['id'] ?? '',
      type: json['type'] ?? 'practice',
      title: json['title'] ?? '',
      subtitle: json['subtitle'],
      xpEarned: json['xp_earned'] ?? 0,
      timestamp: DateTime.parse(json['timestamp'] ?? DateTime.now().toIso8601String()),
      metadata: json['metadata'],
    );
  }
}

/// Weekly performance data
class WeeklyPerformance {
  final List<DailyStats> days;
  final int totalXp;
  final int totalQuestions;
  final double averageAccuracy;
  final int studyMinutes;

  const WeeklyPerformance({
    required this.days,
    required this.totalXp,
    required this.totalQuestions,
    required this.averageAccuracy,
    required this.studyMinutes,
  });

  factory WeeklyPerformance.fromJson(Map<String, dynamic> json) {
    return WeeklyPerformance(
      days: (json['days'] as List?)
          ?.map((d) => DailyStats.fromJson(d))
          .toList() ?? [],
      totalXp: json['total_xp'] ?? 0,
      totalQuestions: json['total_questions'] ?? 0,
      averageAccuracy: (json['average_accuracy'] ?? 0.0).toDouble(),
      studyMinutes: json['study_minutes'] ?? 0,
    );
  }

  factory WeeklyPerformance.empty() {
    return WeeklyPerformance(
      days: List.generate(7, (i) => DailyStats.empty(
        DateTime.now().subtract(Duration(days: 6 - i)),
      )),
      totalXp: 0,
      totalQuestions: 0,
      averageAccuracy: 0.0,
      studyMinutes: 0,
    );
  }
}

/// Daily stats for charts
class DailyStats {
  final DateTime date;
  final int xp;
  final int questions;
  final int correct;
  final int studyMinutes;

  const DailyStats({
    required this.date,
    required this.xp,
    required this.questions,
    required this.correct,
    required this.studyMinutes,
  });

  double get accuracy => questions > 0 ? correct / questions : 0.0;

  String get dayName {
    const days = ['Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom'];
    return days[date.weekday - 1];
  }

  factory DailyStats.fromJson(Map<String, dynamic> json) {
    return DailyStats(
      date: DateTime.parse(json['date']),
      xp: json['xp'] ?? 0,
      questions: json['questions'] ?? 0,
      correct: json['correct'] ?? 0,
      studyMinutes: json['study_minutes'] ?? 0,
    );
  }

  factory DailyStats.empty(DateTime date) {
    return DailyStats(
      date: date,
      xp: 0,
      questions: 0,
      correct: 0,
      studyMinutes: 0,
    );
  }
}
