import 'package:freezed_annotation/freezed_annotation.dart';

part 'dungeon_gate.freezed.dart';
part 'dungeon_gate.g.dart';

@freezed
class DungeonGate with _$DungeonGate {
  const factory DungeonGate({
    required String id,
    required String name,
    required String description,
    required String type, // 'normal', 'boss', 'seasonal'
    @JsonKey(name: 'difficulty_rank') required String difficultyRank,
    @JsonKey(name: 'rec_level') required int recommendedLevel,
    @JsonKey(name: 'total_rooms') required int totalRooms,
    @JsonKey(name: 'time_limit') required int timeLimitMinutes,
    @Default(false) bool isLocked,
    @Default(0) double completionPercentage,
    @Default('math') String theme, // 'math', 'reading', 'science', 'social', 'english'
  }) = _DungeonGate;

  factory DungeonGate.fromJson(Map<String, dynamic> json) => _$DungeonGateFromJson(json);
}
