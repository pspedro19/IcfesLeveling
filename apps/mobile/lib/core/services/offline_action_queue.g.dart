// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'offline_action_queue.dart';

// **************************************************************************
// TypeAdapterGenerator
// **************************************************************************

class PendingActionAdapter extends TypeAdapter<PendingAction> {
  @override
  final int typeId = 10;

  @override
  PendingAction read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{
      for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read(),
    };
    return PendingAction(
      id: fields[0] as String,
      type: fields[1] as GameActionType,
      payload: (fields[2] as Map).cast<String, dynamic>(),
      timestamp: fields[3] as DateTime,
      retryCount: fields[4] as int,
    );
  }

  @override
  void write(BinaryWriter writer, PendingAction obj) {
    writer
      ..writeByte(5)
      ..writeByte(0)
      ..write(obj.id)
      ..writeByte(1)
      ..write(obj.type)
      ..writeByte(2)
      ..write(obj.payload)
      ..writeByte(3)
      ..write(obj.timestamp)
      ..writeByte(4)
      ..write(obj.retryCount);
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is PendingActionAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}

class GameActionTypeAdapter extends TypeAdapter<GameActionType> {
  @override
  final int typeId = 11;

  @override
  GameActionType read(BinaryReader reader) {
    switch (reader.readByte()) {
      case 0:
        return GameActionType.answerSubmission;
      case 1:
        return GameActionType.battleComplete;
      case 2:
        return GameActionType.xpGain;
      case 3:
        return GameActionType.goldTransaction;
      case 4:
        return GameActionType.streakUpdate;
      case 5:
        return GameActionType.achievementUnlock;
      case 6:
        return GameActionType.heartUse;
      case 7:
        return GameActionType.nodeComplete;
      case 8:
        return GameActionType.nodeUnlock;
      case 9:
        return GameActionType.purchaseItem;
      default:
        return GameActionType.answerSubmission;
    }
  }

  @override
  void write(BinaryWriter writer, GameActionType obj) {
    switch (obj) {
      case GameActionType.answerSubmission:
        writer.writeByte(0);
        break;
      case GameActionType.battleComplete:
        writer.writeByte(1);
        break;
      case GameActionType.xpGain:
        writer.writeByte(2);
        break;
      case GameActionType.goldTransaction:
        writer.writeByte(3);
        break;
      case GameActionType.streakUpdate:
        writer.writeByte(4);
        break;
      case GameActionType.achievementUnlock:
        writer.writeByte(5);
        break;
      case GameActionType.heartUse:
        writer.writeByte(6);
        break;
      case GameActionType.nodeComplete:
        writer.writeByte(7);
        break;
      case GameActionType.nodeUnlock:
        writer.writeByte(8);
        break;
      case GameActionType.purchaseItem:
        writer.writeByte(9);
        break;
    }
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is GameActionTypeAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}
