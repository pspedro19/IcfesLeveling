// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'dungeon_node.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$DungeonNodeImpl _$$DungeonNodeImplFromJson(Map<String, dynamic> json) =>
    _$DungeonNodeImpl(
      id: json['id'] as String,
      roomNumber: (json['room_number'] as num).toInt(),
      type: json['type'] as String,
      isCompleted: json['is_completed'] as bool? ?? false,
      isCurrent: json['is_current'] as bool? ?? false,
      isLocked: json['is_locked'] as bool? ?? true,
      stars: (json['stars'] as num?)?.toInt() ?? 0,
    );

Map<String, dynamic> _$$DungeonNodeImplToJson(_$DungeonNodeImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'room_number': instance.roomNumber,
      'type': instance.type,
      'is_completed': instance.isCompleted,
      'is_current': instance.isCurrent,
      'is_locked': instance.isLocked,
      'stars': instance.stars,
    };
