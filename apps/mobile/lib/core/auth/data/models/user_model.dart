import '../../domain/entities/user.dart';

class UserModel extends User {
  UserModel({
    required super.id,
    required super.email,
    required super.name,
    required super.level,
    required super.xp,
    required super.rank,
    required super.hearts,
    required super.currentStreak,
    required super.completedDeepDiagnostics,
  });

  /// Factory constructor that handles field mapping between backend and Flutter.
  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id']?.toString() ?? '',
      email: json['email'] ?? '',
      name: json['name'] ?? json['display_name'] ?? json['username'] ?? '',
      level: json['level'] ?? 1,
      xp: json['xp'] ?? json['experience'] ?? 0,
      rank: json['rank'] ?? 'Novato',
      hearts: json['hearts'] ?? json['hp'] ?? 5,
      currentStreak: json['current_streak'] ?? json['streak_days'] ?? 0,
      completedDeepDiagnostics: List<String>.from(json['completed_deep_diagnostics'] ?? []),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'name': name,
      'level': level,
      'xp': xp,
      'rank': rank,
      'hearts': hearts,
      'current_streak': currentStreak,
      'completed_deep_diagnostics': completedDeepDiagnostics,
    };
  }
}
