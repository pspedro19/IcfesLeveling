// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'dungeon_gate.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

DungeonGate _$DungeonGateFromJson(Map<String, dynamic> json) {
  return _DungeonGate.fromJson(json);
}

/// @nodoc
mixin _$DungeonGate {
  String get id => throw _privateConstructorUsedError;
  String get name => throw _privateConstructorUsedError;
  String get description => throw _privateConstructorUsedError;
  String get type =>
      throw _privateConstructorUsedError; // 'normal', 'boss', 'seasonal'
  @JsonKey(name: 'difficulty_rank')
  String get difficultyRank => throw _privateConstructorUsedError;
  @JsonKey(name: 'rec_level')
  int get recommendedLevel => throw _privateConstructorUsedError;
  @JsonKey(name: 'total_rooms')
  int get totalRooms => throw _privateConstructorUsedError;
  @JsonKey(name: 'time_limit')
  int get timeLimitMinutes => throw _privateConstructorUsedError;
  bool get isLocked => throw _privateConstructorUsedError;
  double get completionPercentage => throw _privateConstructorUsedError;
  String get theme => throw _privateConstructorUsedError;

  /// Serializes this DungeonGate to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of DungeonGate
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $DungeonGateCopyWith<DungeonGate> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $DungeonGateCopyWith<$Res> {
  factory $DungeonGateCopyWith(
          DungeonGate value, $Res Function(DungeonGate) then) =
      _$DungeonGateCopyWithImpl<$Res, DungeonGate>;
  @useResult
  $Res call(
      {String id,
      String name,
      String description,
      String type,
      @JsonKey(name: 'difficulty_rank') String difficultyRank,
      @JsonKey(name: 'rec_level') int recommendedLevel,
      @JsonKey(name: 'total_rooms') int totalRooms,
      @JsonKey(name: 'time_limit') int timeLimitMinutes,
      bool isLocked,
      double completionPercentage,
      String theme});
}

/// @nodoc
class _$DungeonGateCopyWithImpl<$Res, $Val extends DungeonGate>
    implements $DungeonGateCopyWith<$Res> {
  _$DungeonGateCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of DungeonGate
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? name = null,
    Object? description = null,
    Object? type = null,
    Object? difficultyRank = null,
    Object? recommendedLevel = null,
    Object? totalRooms = null,
    Object? timeLimitMinutes = null,
    Object? isLocked = null,
    Object? completionPercentage = null,
    Object? theme = null,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      description: null == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as String,
      difficultyRank: null == difficultyRank
          ? _value.difficultyRank
          : difficultyRank // ignore: cast_nullable_to_non_nullable
              as String,
      recommendedLevel: null == recommendedLevel
          ? _value.recommendedLevel
          : recommendedLevel // ignore: cast_nullable_to_non_nullable
              as int,
      totalRooms: null == totalRooms
          ? _value.totalRooms
          : totalRooms // ignore: cast_nullable_to_non_nullable
              as int,
      timeLimitMinutes: null == timeLimitMinutes
          ? _value.timeLimitMinutes
          : timeLimitMinutes // ignore: cast_nullable_to_non_nullable
              as int,
      isLocked: null == isLocked
          ? _value.isLocked
          : isLocked // ignore: cast_nullable_to_non_nullable
              as bool,
      completionPercentage: null == completionPercentage
          ? _value.completionPercentage
          : completionPercentage // ignore: cast_nullable_to_non_nullable
              as double,
      theme: null == theme
          ? _value.theme
          : theme // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$DungeonGateImplCopyWith<$Res>
    implements $DungeonGateCopyWith<$Res> {
  factory _$$DungeonGateImplCopyWith(
          _$DungeonGateImpl value, $Res Function(_$DungeonGateImpl) then) =
      __$$DungeonGateImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String name,
      String description,
      String type,
      @JsonKey(name: 'difficulty_rank') String difficultyRank,
      @JsonKey(name: 'rec_level') int recommendedLevel,
      @JsonKey(name: 'total_rooms') int totalRooms,
      @JsonKey(name: 'time_limit') int timeLimitMinutes,
      bool isLocked,
      double completionPercentage,
      String theme});
}

/// @nodoc
class __$$DungeonGateImplCopyWithImpl<$Res>
    extends _$DungeonGateCopyWithImpl<$Res, _$DungeonGateImpl>
    implements _$$DungeonGateImplCopyWith<$Res> {
  __$$DungeonGateImplCopyWithImpl(
      _$DungeonGateImpl _value, $Res Function(_$DungeonGateImpl) _then)
      : super(_value, _then);

  /// Create a copy of DungeonGate
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? name = null,
    Object? description = null,
    Object? type = null,
    Object? difficultyRank = null,
    Object? recommendedLevel = null,
    Object? totalRooms = null,
    Object? timeLimitMinutes = null,
    Object? isLocked = null,
    Object? completionPercentage = null,
    Object? theme = null,
  }) {
    return _then(_$DungeonGateImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      description: null == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String,
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as String,
      difficultyRank: null == difficultyRank
          ? _value.difficultyRank
          : difficultyRank // ignore: cast_nullable_to_non_nullable
              as String,
      recommendedLevel: null == recommendedLevel
          ? _value.recommendedLevel
          : recommendedLevel // ignore: cast_nullable_to_non_nullable
              as int,
      totalRooms: null == totalRooms
          ? _value.totalRooms
          : totalRooms // ignore: cast_nullable_to_non_nullable
              as int,
      timeLimitMinutes: null == timeLimitMinutes
          ? _value.timeLimitMinutes
          : timeLimitMinutes // ignore: cast_nullable_to_non_nullable
              as int,
      isLocked: null == isLocked
          ? _value.isLocked
          : isLocked // ignore: cast_nullable_to_non_nullable
              as bool,
      completionPercentage: null == completionPercentage
          ? _value.completionPercentage
          : completionPercentage // ignore: cast_nullable_to_non_nullable
              as double,
      theme: null == theme
          ? _value.theme
          : theme // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$DungeonGateImpl implements _DungeonGate {
  const _$DungeonGateImpl(
      {required this.id,
      required this.name,
      required this.description,
      required this.type,
      @JsonKey(name: 'difficulty_rank') required this.difficultyRank,
      @JsonKey(name: 'rec_level') required this.recommendedLevel,
      @JsonKey(name: 'total_rooms') required this.totalRooms,
      @JsonKey(name: 'time_limit') required this.timeLimitMinutes,
      this.isLocked = false,
      this.completionPercentage = 0,
      this.theme = 'math'});

  factory _$DungeonGateImpl.fromJson(Map<String, dynamic> json) =>
      _$$DungeonGateImplFromJson(json);

  @override
  final String id;
  @override
  final String name;
  @override
  final String description;
  @override
  final String type;
// 'normal', 'boss', 'seasonal'
  @override
  @JsonKey(name: 'difficulty_rank')
  final String difficultyRank;
  @override
  @JsonKey(name: 'rec_level')
  final int recommendedLevel;
  @override
  @JsonKey(name: 'total_rooms')
  final int totalRooms;
  @override
  @JsonKey(name: 'time_limit')
  final int timeLimitMinutes;
  @override
  @JsonKey()
  final bool isLocked;
  @override
  @JsonKey()
  final double completionPercentage;
  @override
  @JsonKey()
  final String theme;

  @override
  String toString() {
    return 'DungeonGate(id: $id, name: $name, description: $description, type: $type, difficultyRank: $difficultyRank, recommendedLevel: $recommendedLevel, totalRooms: $totalRooms, timeLimitMinutes: $timeLimitMinutes, isLocked: $isLocked, completionPercentage: $completionPercentage, theme: $theme)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$DungeonGateImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.type, type) || other.type == type) &&
            (identical(other.difficultyRank, difficultyRank) ||
                other.difficultyRank == difficultyRank) &&
            (identical(other.recommendedLevel, recommendedLevel) ||
                other.recommendedLevel == recommendedLevel) &&
            (identical(other.totalRooms, totalRooms) ||
                other.totalRooms == totalRooms) &&
            (identical(other.timeLimitMinutes, timeLimitMinutes) ||
                other.timeLimitMinutes == timeLimitMinutes) &&
            (identical(other.isLocked, isLocked) ||
                other.isLocked == isLocked) &&
            (identical(other.completionPercentage, completionPercentage) ||
                other.completionPercentage == completionPercentage) &&
            (identical(other.theme, theme) || other.theme == theme));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      id,
      name,
      description,
      type,
      difficultyRank,
      recommendedLevel,
      totalRooms,
      timeLimitMinutes,
      isLocked,
      completionPercentage,
      theme);

  /// Create a copy of DungeonGate
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$DungeonGateImplCopyWith<_$DungeonGateImpl> get copyWith =>
      __$$DungeonGateImplCopyWithImpl<_$DungeonGateImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$DungeonGateImplToJson(
      this,
    );
  }
}

abstract class _DungeonGate implements DungeonGate {
  const factory _DungeonGate(
      {required final String id,
      required final String name,
      required final String description,
      required final String type,
      @JsonKey(name: 'difficulty_rank') required final String difficultyRank,
      @JsonKey(name: 'rec_level') required final int recommendedLevel,
      @JsonKey(name: 'total_rooms') required final int totalRooms,
      @JsonKey(name: 'time_limit') required final int timeLimitMinutes,
      final bool isLocked,
      final double completionPercentage,
      final String theme}) = _$DungeonGateImpl;

  factory _DungeonGate.fromJson(Map<String, dynamic> json) =
      _$DungeonGateImpl.fromJson;

  @override
  String get id;
  @override
  String get name;
  @override
  String get description;
  @override
  String get type; // 'normal', 'boss', 'seasonal'
  @override
  @JsonKey(name: 'difficulty_rank')
  String get difficultyRank;
  @override
  @JsonKey(name: 'rec_level')
  int get recommendedLevel;
  @override
  @JsonKey(name: 'total_rooms')
  int get totalRooms;
  @override
  @JsonKey(name: 'time_limit')
  int get timeLimitMinutes;
  @override
  bool get isLocked;
  @override
  double get completionPercentage;
  @override
  String get theme;

  /// Create a copy of DungeonGate
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$DungeonGateImplCopyWith<_$DungeonGateImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
