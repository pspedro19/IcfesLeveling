class User {
  final String id;
  final String email;
  final String name;
  final int level;
  final int xp;
  final String rank;
  final int hearts;
  final int currentStreak;

  // Onboarding state
  final bool onboardingCompleted;
  final bool diagnosticCompleted;
  final bool firstMissionCompleted;
  final List<String> completedDeepDiagnostics;

  // Projected score from diagnostic
  final int? projectedIcfesScore;

  // Timestamps
  final DateTime? lastActivityAt;
  final DateTime? createdAt;

  User({
    required this.id,
    required this.email,
    required this.name,
    required this.level,
    required this.xp,
    required this.rank,
    required this.hearts,
    required this.currentStreak,
    this.onboardingCompleted = false,
    this.diagnosticCompleted = false,
    this.firstMissionCompleted = false,
    this.completedDeepDiagnostics = const [],
    this.projectedIcfesScore,
    this.lastActivityAt,
    this.createdAt,
  });

  /// Copy with updated fields
  User copyWith({
    String? id,
    String? email,
    String? name,
    int? level,
    int? xp,
    String? rank,
    int? hearts,
    int? currentStreak,
    bool? onboardingCompleted,
    bool? diagnosticCompleted,
    bool? firstMissionCompleted,
    List<String>? completedDeepDiagnostics,
    int? projectedIcfesScore,
    DateTime? lastActivityAt,
    DateTime? createdAt,
  }) {
    return User(
      id: id ?? this.id,
      email: email ?? this.email,
      name: name ?? this.name,
      level: level ?? this.level,
      xp: xp ?? this.xp,
      rank: rank ?? this.rank,
      hearts: hearts ?? this.hearts,
      currentStreak: currentStreak ?? this.currentStreak,
      onboardingCompleted: onboardingCompleted ?? this.onboardingCompleted,
      diagnosticCompleted: diagnosticCompleted ?? this.diagnosticCompleted,
      firstMissionCompleted: firstMissionCompleted ?? this.firstMissionCompleted,
      completedDeepDiagnostics: completedDeepDiagnostics ?? this.completedDeepDiagnostics,
      projectedIcfesScore: projectedIcfesScore ?? this.projectedIcfesScore,
      lastActivityAt: lastActivityAt ?? this.lastActivityAt,
      createdAt: createdAt ?? this.createdAt,
    );
  }
}
