import 'package:freezed_annotation/freezed_annotation.dart';

part 'combat_state.freezed.dart';
part 'combat_state.g.dart';

@freezed
class CombatState with _$CombatState {
  const factory CombatState({
    required String runId,
    required int currentTurn,
    
    // Player Stats
    required int playerHp,
    required int playerMaxHp,
    required int playerEnergy,
    
    // Enemy Stats
    required String enemyName,
    required String enemyImageUrl,
    required int enemyHp,
    required int enemyMaxHp,
    
    // UI State
    @Default(false) bool isPlayerTurn,
    @Default(false) bool isAnimating,
    String? lastActionText,
    @Default(0) int comboCounter,
  }) = _CombatState;

  factory CombatState.fromJson(Map<String, dynamic> json) => _$CombatStateFromJson(json);
}
