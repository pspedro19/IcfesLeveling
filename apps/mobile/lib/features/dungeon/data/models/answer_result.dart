/// Resultado de una respuesta enviada al servidor
class AnswerResult {
  final bool isCorrect;
  final String correctAnswerId;
  final String? explanation;  // CRITICO: siempre incluir
  final String? videoUrl;     // Opcional: video explicativo
  final int damageDealt;
  final int damageTaken;
  final int enemyCurrentHp;
  final int playerCurrentHp;
  final int currentCombo;
  final int xpEarned;
  final int goldEarned;
  final bool enemyDefeated;
  final bool playerDefeated;

  AnswerResult({
    required this.isCorrect,
    required this.correctAnswerId,
    this.explanation,
    this.videoUrl,
    required this.damageDealt,
    required this.damageTaken,
    required this.enemyCurrentHp,
    required this.playerCurrentHp,
    required this.currentCombo,
    required this.xpEarned,
    this.goldEarned = 0,
    required this.enemyDefeated,
    required this.playerDefeated,
  });

  factory AnswerResult.fromJson(Map<String, dynamic> json) {
    return AnswerResult(
      isCorrect: json['correct'] ?? false,
      correctAnswerId: json['correct_answer_id'] ?? '',
      explanation: json['explanation'],
      videoUrl: json['video_url'],
      damageDealt: json['damage_dealt'] ?? 0,
      damageTaken: json['damage_taken'] ?? 0,
      enemyCurrentHp: json['enemy_current_hp'] ?? 0,
      playerCurrentHp: json['player_current_hp'] ?? 0,
      currentCombo: json['current_combo'] ?? 0,
      xpEarned: json['xp_earned'] ?? 0,
      goldEarned: json['gold_earned'] ?? 0,
      enemyDefeated: json['enemy_defeated'] ?? false,
      playerDefeated: json['player_defeated'] ?? false,
    );
  }
}
