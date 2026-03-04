// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'dungeon_node.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

DungeonNode _$DungeonNodeFromJson(Map<String, dynamic> json) {
  return _DungeonNode.fromJson(json);
}

/// @nodoc
mixin _$DungeonNode {
  String get id => throw _privateConstructorUsedError;
  @JsonKey(name: 'room_number')
  int get roomNumber => throw _privateConstructorUsedError;
  String get type =>
      throw _privateConstructorUsedError; // 'monster', 'boss', 'treasure', 'rest'
  @JsonKey(name: 'is_completed')
  bool get isCompleted => throw _privateConstructorUsedError;
  @JsonKey(name: 'is_current')
  bool get isCurrent => throw _privateConstructorUsedError;
  @JsonKey(name: 'is_locked')
  bool get isLocked => throw _privateConstructorUsedError;
  int get stars => throw _privateConstructorUsedError;

  /// Serializes this DungeonNode to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of DungeonNode
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $DungeonNodeCopyWith<DungeonNode> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $DungeonNodeCopyWith<$Res> {
  factory $DungeonNodeCopyWith(
          DungeonNode value, $Res Function(DungeonNode) then) =
      _$DungeonNodeCopyWithImpl<$Res, DungeonNode>;
  @useResult
  $Res call(
      {String id,
      @JsonKey(name: 'room_number') int roomNumber,
      String type,
      @JsonKey(name: 'is_completed') bool isCompleted,
      @JsonKey(name: 'is_current') bool isCurrent,
      @JsonKey(name: 'is_locked') bool isLocked,
      int stars});
}

/// @nodoc
class _$DungeonNodeCopyWithImpl<$Res, $Val extends DungeonNode>
    implements $DungeonNodeCopyWith<$Res> {
  _$DungeonNodeCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of DungeonNode
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? roomNumber = null,
    Object? type = null,
    Object? isCompleted = null,
    Object? isCurrent = null,
    Object? isLocked = null,
    Object? stars = null,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      roomNumber: null == roomNumber
          ? _value.roomNumber
          : roomNumber // ignore: cast_nullable_to_non_nullable
              as int,
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as String,
      isCompleted: null == isCompleted
          ? _value.isCompleted
          : isCompleted // ignore: cast_nullable_to_non_nullable
              as bool,
      isCurrent: null == isCurrent
          ? _value.isCurrent
          : isCurrent // ignore: cast_nullable_to_non_nullable
              as bool,
      isLocked: null == isLocked
          ? _value.isLocked
          : isLocked // ignore: cast_nullable_to_non_nullable
              as bool,
      stars: null == stars
          ? _value.stars
          : stars // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$DungeonNodeImplCopyWith<$Res>
    implements $DungeonNodeCopyWith<$Res> {
  factory _$$DungeonNodeImplCopyWith(
          _$DungeonNodeImpl value, $Res Function(_$DungeonNodeImpl) then) =
      __$$DungeonNodeImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      @JsonKey(name: 'room_number') int roomNumber,
      String type,
      @JsonKey(name: 'is_completed') bool isCompleted,
      @JsonKey(name: 'is_current') bool isCurrent,
      @JsonKey(name: 'is_locked') bool isLocked,
      int stars});
}

/// @nodoc
class __$$DungeonNodeImplCopyWithImpl<$Res>
    extends _$DungeonNodeCopyWithImpl<$Res, _$DungeonNodeImpl>
    implements _$$DungeonNodeImplCopyWith<$Res> {
  __$$DungeonNodeImplCopyWithImpl(
      _$DungeonNodeImpl _value, $Res Function(_$DungeonNodeImpl) _then)
      : super(_value, _then);

  /// Create a copy of DungeonNode
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? roomNumber = null,
    Object? type = null,
    Object? isCompleted = null,
    Object? isCurrent = null,
    Object? isLocked = null,
    Object? stars = null,
  }) {
    return _then(_$DungeonNodeImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      roomNumber: null == roomNumber
          ? _value.roomNumber
          : roomNumber // ignore: cast_nullable_to_non_nullable
              as int,
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as String,
      isCompleted: null == isCompleted
          ? _value.isCompleted
          : isCompleted // ignore: cast_nullable_to_non_nullable
              as bool,
      isCurrent: null == isCurrent
          ? _value.isCurrent
          : isCurrent // ignore: cast_nullable_to_non_nullable
              as bool,
      isLocked: null == isLocked
          ? _value.isLocked
          : isLocked // ignore: cast_nullable_to_non_nullable
              as bool,
      stars: null == stars
          ? _value.stars
          : stars // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$DungeonNodeImpl implements _DungeonNode {
  const _$DungeonNodeImpl(
      {required this.id,
      @JsonKey(name: 'room_number') required this.roomNumber,
      required this.type,
      @JsonKey(name: 'is_completed') this.isCompleted = false,
      @JsonKey(name: 'is_current') this.isCurrent = false,
      @JsonKey(name: 'is_locked') this.isLocked = true,
      this.stars = 0});

  factory _$DungeonNodeImpl.fromJson(Map<String, dynamic> json) =>
      _$$DungeonNodeImplFromJson(json);

  @override
  final String id;
  @override
  @JsonKey(name: 'room_number')
  final int roomNumber;
  @override
  final String type;
// 'monster', 'boss', 'treasure', 'rest'
  @override
  @JsonKey(name: 'is_completed')
  final bool isCompleted;
  @override
  @JsonKey(name: 'is_current')
  final bool isCurrent;
  @override
  @JsonKey(name: 'is_locked')
  final bool isLocked;
  @override
  @JsonKey()
  final int stars;

  @override
  String toString() {
    return 'DungeonNode(id: $id, roomNumber: $roomNumber, type: $type, isCompleted: $isCompleted, isCurrent: $isCurrent, isLocked: $isLocked, stars: $stars)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$DungeonNodeImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.roomNumber, roomNumber) ||
                other.roomNumber == roomNumber) &&
            (identical(other.type, type) || other.type == type) &&
            (identical(other.isCompleted, isCompleted) ||
                other.isCompleted == isCompleted) &&
            (identical(other.isCurrent, isCurrent) ||
                other.isCurrent == isCurrent) &&
            (identical(other.isLocked, isLocked) ||
                other.isLocked == isLocked) &&
            (identical(other.stars, stars) || other.stars == stars));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, id, roomNumber, type,
      isCompleted, isCurrent, isLocked, stars);

  /// Create a copy of DungeonNode
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$DungeonNodeImplCopyWith<_$DungeonNodeImpl> get copyWith =>
      __$$DungeonNodeImplCopyWithImpl<_$DungeonNodeImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$DungeonNodeImplToJson(
      this,
    );
  }
}

abstract class _DungeonNode implements DungeonNode {
  const factory _DungeonNode(
      {required final String id,
      @JsonKey(name: 'room_number') required final int roomNumber,
      required final String type,
      @JsonKey(name: 'is_completed') final bool isCompleted,
      @JsonKey(name: 'is_current') final bool isCurrent,
      @JsonKey(name: 'is_locked') final bool isLocked,
      final int stars}) = _$DungeonNodeImpl;

  factory _DungeonNode.fromJson(Map<String, dynamic> json) =
      _$DungeonNodeImpl.fromJson;

  @override
  String get id;
  @override
  @JsonKey(name: 'room_number')
  int get roomNumber;
  @override
  String get type; // 'monster', 'boss', 'treasure', 'rest'
  @override
  @JsonKey(name: 'is_completed')
  bool get isCompleted;
  @override
  @JsonKey(name: 'is_current')
  bool get isCurrent;
  @override
  @JsonKey(name: 'is_locked')
  bool get isLocked;
  @override
  int get stars;

  /// Create a copy of DungeonNode
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$DungeonNodeImplCopyWith<_$DungeonNodeImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
