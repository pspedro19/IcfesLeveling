// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'dungeon_gate.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$DungeonGateImpl _$$DungeonGateImplFromJson(Map<String, dynamic> json) =>
    _$DungeonGateImpl(
      id: json['id'] as String,
      name: json['name'] as String,
      description: json['description'] as String,
      type: json['type'] as String,
      difficultyRank: json['difficulty_rank'] as String,
      recommendedLevel: (json['rec_level'] as num).toInt(),
      totalRooms: (json['total_rooms'] as num).toInt(),
      timeLimitMinutes: (json['time_limit'] as num).toInt(),
      isLocked: json['isLocked'] as bool? ?? false,
      completionPercentage:
          (json['completionPercentage'] as num?)?.toDouble() ?? 0,
      theme: json['theme'] as String? ?? 'math',
    );

Map<String, dynamic> _$$DungeonGateImplToJson(_$DungeonGateImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'description': instance.description,
      'type': instance.type,
      'difficulty_rank': instance.difficultyRank,
      'rec_level': instance.recommendedLevel,
      'total_rooms': instance.totalRooms,
      'time_limit': instance.timeLimitMinutes,
      'isLocked': instance.isLocked,
      'completionPercentage': instance.completionPercentage,
      'theme': instance.theme,
    };
