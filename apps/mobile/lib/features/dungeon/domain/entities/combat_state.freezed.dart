// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'combat_state.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

CombatState _$CombatStateFromJson(Map<String, dynamic> json) {
  return _CombatState.fromJson(json);
}

/// @nodoc
mixin _$CombatState {
  String get runId => throw _privateConstructorUsedError;
  int get currentTurn => throw _privateConstructorUsedError; // Player Stats
  int get playerHp => throw _privateConstructorUsedError;
  int get playerMaxHp => throw _privateConstructorUsedError;
  int get playerEnergy => throw _privateConstructorUsedError; // Enemy Stats
  String get enemyName => throw _privateConstructorUsedError;
  String get enemyImageUrl => throw _privateConstructorUsedError;
  int get enemyHp => throw _privateConstructorUsedError;
  int get enemyMaxHp => throw _privateConstructorUsedError; // UI State
  bool get isPlayerTurn => throw _privateConstructorUsedError;
  bool get isAnimating => throw _privateConstructorUsedError;
  String? get lastActionText => throw _privateConstructorUsedError;
  int get comboCounter => throw _privateConstructorUsedError;

  /// Serializes this CombatState to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of CombatState
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $CombatStateCopyWith<CombatState> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $CombatStateCopyWith<$Res> {
  factory $CombatStateCopyWith(
          CombatState value, $Res Function(CombatState) then) =
      _$CombatStateCopyWithImpl<$Res, CombatState>;
  @useResult
  $Res call(
      {String runId,
      int currentTurn,
      int playerHp,
      int playerMaxHp,
      int playerEnergy,
      String enemyName,
      String enemyImageUrl,
      int enemyHp,
      int enemyMaxHp,
      bool isPlayerTurn,
      bool isAnimating,
      String? lastActionText,
      int comboCounter});
}

/// @nodoc
class _$CombatStateCopyWithImpl<$Res, $Val extends CombatState>
    implements $CombatStateCopyWith<$Res> {
  _$CombatStateCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of CombatState
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? runId = null,
    Object? currentTurn = null,
    Object? playerHp = null,
    Object? playerMaxHp = null,
    Object? playerEnergy = null,
    Object? enemyName = null,
    Object? enemyImageUrl = null,
    Object? enemyHp = null,
    Object? enemyMaxHp = null,
    Object? isPlayerTurn = null,
    Object? isAnimating = null,
    Object? lastActionText = freezed,
    Object? comboCounter = null,
  }) {
    return _then(_value.copyWith(
      runId: null == runId
          ? _value.runId
          : runId // ignore: cast_nullable_to_non_nullable
              as String,
      currentTurn: null == currentTurn
          ? _value.currentTurn
          : currentTurn // ignore: cast_nullable_to_non_nullable
              as int,
      playerHp: null == playerHp
          ? _value.playerHp
          : playerHp // ignore: cast_nullable_to_non_nullable
              as int,
      playerMaxHp: null == playerMaxHp
          ? _value.playerMaxHp
          : playerMaxHp // ignore: cast_nullable_to_non_nullable
              as int,
      playerEnergy: null == playerEnergy
          ? _value.playerEnergy
          : playerEnergy // ignore: cast_nullable_to_non_nullable
              as int,
      enemyName: null == enemyName
          ? _value.enemyName
          : enemyName // ignore: cast_nullable_to_non_nullable
              as String,
      enemyImageUrl: null == enemyImageUrl
          ? _value.enemyImageUrl
          : enemyImageUrl // ignore: cast_nullable_to_non_nullable
              as String,
      enemyHp: null == enemyHp
          ? _value.enemyHp
          : enemyHp // ignore: cast_nullable_to_non_nullable
              as int,
      enemyMaxHp: null == enemyMaxHp
          ? _value.enemyMaxHp
          : enemyMaxHp // ignore: cast_nullable_to_non_nullable
              as int,
      isPlayerTurn: null == isPlayerTurn
          ? _value.isPlayerTurn
          : isPlayerTurn // ignore: cast_nullable_to_non_nullable
              as bool,
      isAnimating: null == isAnimating
          ? _value.isAnimating
          : isAnimating // ignore: cast_nullable_to_non_nullable
              as bool,
      lastActionText: freezed == lastActionText
          ? _value.lastActionText
          : lastActionText // ignore: cast_nullable_to_non_nullable
              as String?,
      comboCounter: null == comboCounter
          ? _value.comboCounter
          : comboCounter // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$CombatStateImplCopyWith<$Res>
    implements $CombatStateCopyWith<$Res> {
  factory _$$CombatStateImplCopyWith(
          _$CombatStateImpl value, $Res Function(_$CombatStateImpl) then) =
      __$$CombatStateImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String runId,
      int currentTurn,
      int playerHp,
      int playerMaxHp,
      int playerEnergy,
      String enemyName,
      String enemyImageUrl,
      int enemyHp,
      int enemyMaxHp,
      bool isPlayerTurn,
      bool isAnimating,
      String? lastActionText,
      int comboCounter});
}

/// @nodoc
class __$$CombatStateImplCopyWithImpl<$Res>
    extends _$CombatStateCopyWithImpl<$Res, _$CombatStateImpl>
    implements _$$CombatStateImplCopyWith<$Res> {
  __$$CombatStateImplCopyWithImpl(
      _$CombatStateImpl _value, $Res Function(_$CombatStateImpl) _then)
      : super(_value, _then);

  /// Create a copy of CombatState
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? runId = null,
    Object? currentTurn = null,
    Object? playerHp = null,
    Object? playerMaxHp = null,
    Object? playerEnergy = null,
    Object? enemyName = null,
    Object? enemyImageUrl = null,
    Object? enemyHp = null,
    Object? enemyMaxHp = null,
    Object? isPlayerTurn = null,
    Object? isAnimating = null,
    Object? lastActionText = freezed,
    Object? comboCounter = null,
  }) {
    return _then(_$CombatStateImpl(
      runId: null == runId
          ? _value.runId
          : runId // ignore: cast_nullable_to_non_nullable
              as String,
      currentTurn: null == currentTurn
          ? _value.currentTurn
          : currentTurn // ignore: cast_nullable_to_non_nullable
              as int,
      playerHp: null == playerHp
          ? _value.playerHp
          : playerHp // ignore: cast_nullable_to_non_nullable
              as int,
      playerMaxHp: null == playerMaxHp
          ? _value.playerMaxHp
          : playerMaxHp // ignore: cast_nullable_to_non_nullable
              as int,
      playerEnergy: null == playerEnergy
          ? _value.playerEnergy
          : playerEnergy // ignore: cast_nullable_to_non_nullable
              as int,
      enemyName: null == enemyName
          ? _value.enemyName
          : enemyName // ignore: cast_nullable_to_non_nullable
              as String,
      enemyImageUrl: null == enemyImageUrl
          ? _value.enemyImageUrl
          : enemyImageUrl // ignore: cast_nullable_to_non_nullable
              as String,
      enemyHp: null == enemyHp
          ? _value.enemyHp
          : enemyHp // ignore: cast_nullable_to_non_nullable
              as int,
      enemyMaxHp: null == enemyMaxHp
          ? _value.enemyMaxHp
          : enemyMaxHp // ignore: cast_nullable_to_non_nullable
              as int,
      isPlayerTurn: null == isPlayerTurn
          ? _value.isPlayerTurn
          : isPlayerTurn // ignore: cast_nullable_to_non_nullable
              as bool,
      isAnimating: null == isAnimating
          ? _value.isAnimating
          : isAnimating // ignore: cast_nullable_to_non_nullable
              as bool,
      lastActionText: freezed == lastActionText
          ? _value.lastActionText
          : lastActionText // ignore: cast_nullable_to_non_nullable
              as String?,
      comboCounter: null == comboCounter
          ? _value.comboCounter
          : comboCounter // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$CombatStateImpl implements _CombatState {
  const _$CombatStateImpl(
      {required this.runId,
      required this.currentTurn,
      required this.playerHp,
      required this.playerMaxHp,
      required this.playerEnergy,
      required this.enemyName,
      required this.enemyImageUrl,
      required this.enemyHp,
      required this.enemyMaxHp,
      this.isPlayerTurn = false,
      this.isAnimating = false,
      this.lastActionText,
      this.comboCounter = 0});

  factory _$CombatStateImpl.fromJson(Map<String, dynamic> json) =>
      _$$CombatStateImplFromJson(json);

  @override
  final String runId;
  @override
  final int currentTurn;
// Player Stats
  @override
  final int playerHp;
  @override
  final int playerMaxHp;
  @override
  final int playerEnergy;
// Enemy Stats
  @override
  final String enemyName;
  @override
  final String enemyImageUrl;
  @override
  final int enemyHp;
  @override
  final int enemyMaxHp;
// UI State
  @override
  @JsonKey()
  final bool isPlayerTurn;
  @override
  @JsonKey()
  final bool isAnimating;
  @override
  final String? lastActionText;
  @override
  @JsonKey()
  final int comboCounter;

  @override
  String toString() {
    return 'CombatState(runId: $runId, currentTurn: $currentTurn, playerHp: $playerHp, playerMaxHp: $playerMaxHp, playerEnergy: $playerEnergy, enemyName: $enemyName, enemyImageUrl: $enemyImageUrl, enemyHp: $enemyHp, enemyMaxHp: $enemyMaxHp, isPlayerTurn: $isPlayerTurn, isAnimating: $isAnimating, lastActionText: $lastActionText, comboCounter: $comboCounter)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$CombatStateImpl &&
            (identical(other.runId, runId) || other.runId == runId) &&
            (identical(other.currentTurn, currentTurn) ||
                other.currentTurn == currentTurn) &&
            (identical(other.playerHp, playerHp) ||
                other.playerHp == playerHp) &&
            (identical(other.playerMaxHp, playerMaxHp) ||
                other.playerMaxHp == playerMaxHp) &&
            (identical(other.playerEnergy, playerEnergy) ||
                other.playerEnergy == playerEnergy) &&
            (identical(other.enemyName, enemyName) ||
                other.enemyName == enemyName) &&
            (identical(other.enemyImageUrl, enemyImageUrl) ||
                other.enemyImageUrl == enemyImageUrl) &&
            (identical(other.enemyHp, enemyHp) || other.enemyHp == enemyHp) &&
            (identical(other.enemyMaxHp, enemyMaxHp) ||
                other.enemyMaxHp == enemyMaxHp) &&
            (identical(other.isPlayerTurn, isPlayerTurn) ||
                other.isPlayerTurn == isPlayerTurn) &&
            (identical(other.isAnimating, isAnimating) ||
                other.isAnimating == isAnimating) &&
            (identical(other.lastActionText, lastActionText) ||
                other.lastActionText == lastActionText) &&
            (identical(other.comboCounter, comboCounter) ||
                other.comboCounter == comboCounter));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      runId,
      currentTurn,
      playerHp,
      playerMaxHp,
      playerEnergy,
      enemyName,
      enemyImageUrl,
      enemyHp,
      enemyMaxHp,
      isPlayerTurn,
      isAnimating,
      lastActionText,
      comboCounter);

  /// Create a copy of CombatState
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$CombatStateImplCopyWith<_$CombatStateImpl> get copyWith =>
      __$$CombatStateImplCopyWithImpl<_$CombatStateImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$CombatStateImplToJson(
      this,
    );
  }
}

abstract class _CombatState implements CombatState {
  const factory _CombatState(
      {required final String runId,
      required final int currentTurn,
      required final int playerHp,
      required final int playerMaxHp,
      required final int playerEnergy,
      required final String enemyName,
      required final String enemyImageUrl,
      required final int enemyHp,
      required final int enemyMaxHp,
      final bool isPlayerTurn,
      final bool isAnimating,
      final String? lastActionText,
      final int comboCounter}) = _$CombatStateImpl;

  factory _CombatState.fromJson(Map<String, dynamic> json) =
      _$CombatStateImpl.fromJson;

  @override
  String get runId;
  @override
  int get currentTurn; // Player Stats
  @override
  int get playerHp;
  @override
  int get playerMaxHp;
  @override
  int get playerEnergy; // Enemy Stats
  @override
  String get enemyName;
  @override
  String get enemyImageUrl;
  @override
  int get enemyHp;
  @override
  int get enemyMaxHp; // UI State
  @override
  bool get isPlayerTurn;
  @override
  bool get isAnimating;
  @override
  String? get lastActionText;
  @override
  int get comboCounter;

  /// Create a copy of CombatState
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$CombatStateImplCopyWith<_$CombatStateImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
