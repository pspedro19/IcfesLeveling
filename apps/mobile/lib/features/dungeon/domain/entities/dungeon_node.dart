import 'package:freezed_annotation/freezed_annotation.dart';

part 'dungeon_node.freezed.dart';
part 'dungeon_node.g.dart';

@freezed
class DungeonNode with _$DungeonNode {
  const factory DungeonNode({
    required String id,
    @JsonKey(name: 'room_number') required int roomNumber,
    required String type, // 'monster', 'boss', 'treasure', 'rest'
    @JsonKey(name: 'is_completed') @Default(false) bool isCompleted,
    @JsonKey(name: 'is_current') @Default(false) bool isCurrent,
    @JsonKey(name: 'is_locked') @Default(true) bool isLocked,
    @Default(0) int stars, // 1-3 stars
  }) = _DungeonNode;

  factory DungeonNode.fromJson(Map<String, dynamic> json) => _$DungeonNodeFromJson(json);
}
