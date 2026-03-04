// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'combat_state.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$CombatStateImpl _$$CombatStateImplFromJson(Map<String, dynamic> json) =>
    _$CombatStateImpl(
      runId: json['runId'] as String,
      currentTurn: (json['currentTurn'] as num).toInt(),
      playerHp: (json['playerHp'] as num).toInt(),
      playerMaxHp: (json['playerMaxHp'] as num).toInt(),
      playerEnergy: (json['playerEnergy'] as num).toInt(),
      enemyName: json['enemyName'] as String,
      enemyImageUrl: json['enemyImageUrl'] as String,
      enemyHp: (json['enemyHp'] as num).toInt(),
      enemyMaxHp: (json['enemyMaxHp'] as num).toInt(),
      isPlayerTurn: json['isPlayerTurn'] as bool? ?? false,
      isAnimating: json['isAnimating'] as bool? ?? false,
      lastActionText: json['lastActionText'] as String?,
      comboCounter: (json['comboCounter'] as num?)?.toInt() ?? 0,
    );

Map<String, dynamic> _$$CombatStateImplToJson(_$CombatStateImpl instance) =>
    <String, dynamic>{
      'runId': instance.runId,
      'currentTurn': instance.currentTurn,
      'playerHp': instance.playerHp,
      'playerMaxHp': instance.playerMaxHp,
      'playerEnergy': instance.playerEnergy,
      'enemyName': instance.enemyName,
      'enemyImageUrl': instance.enemyImageUrl,
      'enemyHp': instance.enemyHp,
      'enemyMaxHp': instance.enemyMaxHp,
      'isPlayerTurn': instance.isPlayerTurn,
      'isAnimating': instance.isAnimating,
      'lastActionText': instance.lastActionText,
      'comboCounter': instance.comboCounter,
    };
