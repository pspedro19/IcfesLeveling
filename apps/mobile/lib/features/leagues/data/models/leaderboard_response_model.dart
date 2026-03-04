class LeagueUserModel {
  final String userId;
  final String name;
  final String? avatarUrl;
  final int xp;
  final int rank;
  final String zone;
  final bool isMe;

  LeagueUserModel({
    required this.userId,
    required this.name,
    this.avatarUrl,
    required this.xp,
    required this.rank,
    required this.zone,
    required this.isMe,
  });

  factory LeagueUserModel.fromJson(Map<String, dynamic> json) {
    return LeagueUserModel(
      userId: json['user_id'],
      name: json['name'],
      avatarUrl: json['avatar_url'],
      xp: json['xp'],
      rank: json['rank'],
      zone: json['zone'],
      isMe: json['is_me'],
    );
  }
}

class LeaderboardResponseModel {
  final List<LeagueUserModel> leaderboard;
  final int myRank;
  final int myXp;
  final String myZone;
  final int totalParticipants;

  LeaderboardResponseModel({
    required this.leaderboard,
    required this.myRank,
    required this.myXp,
    required this.myZone,
    required this.totalParticipants,
  });

  factory LeaderboardResponseModel.fromJson(Map<String, dynamic> json) {
    var leaderboardList = json['leaderboard'] as List;
    List<LeagueUserModel> leaderboard = leaderboardList.map((i) => LeagueUserModel.fromJson(i)).toList();

    return LeaderboardResponseModel(
      leaderboard: leaderboard,
      myRank: json['my_rank'],
      myXp: json['my_xp'],
      myZone: json['my_zone'],
      totalParticipants: json['total_participants'],
    );
  }
}
