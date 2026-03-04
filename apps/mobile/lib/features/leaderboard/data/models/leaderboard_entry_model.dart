import '../../domain/entities/leaderboard_entry.dart';

class LeaderboardEntryModel extends LeaderboardEntry {
  LeaderboardEntryModel({
    required super.userId,
    required super.userName,
    required super.xp,
    required super.position,
    required super.rank,
    super.isCurrentUser,
  });

  factory LeaderboardEntryModel.fromJson(Map<String, dynamic> json, {String? currentUserId}) {
    return LeaderboardEntryModel(
      userId: json['user_id'] ?? json['id'],
      userName: json['display_name'] ?? json['username'] ?? json['name'] ?? 'Usuario',
      xp: json['xp'] ?? 0,
      position: json['position'] ?? 0,
      rank: json['rank'] ?? 'E',
      isCurrentUser: (json['user_id'] ?? json['id']) == currentUserId,
    );
  }
}
