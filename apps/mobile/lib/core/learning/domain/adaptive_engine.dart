import 'dart:math';

enum Subject { math, lit, science, social, english }

class AdaptiveEngine {
  /// Calculates weights for subjects based on current mastery levels.
  /// Lower mastery level results in a higher weight (priority).
  Map<Subject, double> calculateWeights(Map<Subject, double> masteryLevels) {
    if (masteryLevels.isEmpty) {
      return { for (var s in Subject.values) s : 1.0 / Subject.values.length };
    }

    // Inverse weight: we want to focus more on lower scores.
    // We use a simple formula: weight = (1.0 - mastery) + epsilon
    // Then normalize to sum to 1.0.
    final rawWeights = masteryLevels.map((subject, mastery) {
      return MapEntry(subject, max(0.1, 1.0 - mastery));
    });

    final totalRaw = rawWeights.values.reduce((a, b) => a + b);
    
    return rawWeights.map((subject, weight) {
      return MapEntry(subject, weight / totalRaw);
    });
  }

  /// Determines the "Next Focus" subject based on weights.
  Subject selectNextSubject(Map<Subject, double> masteryLevels) {
    final weights = calculateWeights(masteryLevels);
    final random = Random().nextDouble();
    double cumulative = 0.0;

    for (final entry in weights.entries) {
      cumulative += entry.value;
      if (random <= cumulative) return entry.key;
    }

    return Subject.math; // Fallback
  }

  /// Adjusts question difficulty (0.0 to 1.0) based on user rank and success rate.
  double calculateTargetDifficulty(int userRankLevel, double recentSuccessRate) {
    // Rank E (0) -> difficulty 0.2
    // Rank S (5) -> difficulty 0.9
    double baseDiff = 0.2 + (userRankLevel * 0.14);
    
    // Adjust based on performance: if succeeding too much, push harder.
    if (recentSuccessRate > 0.8) baseDiff += 0.1;
    if (recentSuccessRate < 0.4) baseDiff -= 0.1;

    return baseDiff.clamp(0.1, 1.0);
  }
}
