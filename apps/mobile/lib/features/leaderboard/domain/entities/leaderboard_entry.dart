class LeaderboardEntry {
  final String userId;
  final String userName;
  final int xp;
  final int position;
  final String rank;
  final bool isCurrentUser;

  LeaderboardEntry({
    required this.userId,
    required this.userName,
    required this.xp,
    required this.position,
    required this.rank,
    this.isCurrentUser = false,
  });
}
