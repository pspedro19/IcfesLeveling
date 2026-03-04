class ShopItemModel {
  final String id;
  final String name;
  final String description;
  final int priceGold;
  final int? priceGems;
  final String category;
  final bool isPowerUp;
  final int? duration; // Duration in seconds for time-limited power-ups

  ShopItemModel({
    required this.id,
    required this.name,
    required this.description,
    required this.priceGold,
    this.priceGems,
    required this.category,
    this.isPowerUp = false,
    this.duration,
  });

  factory ShopItemModel.fromJson(Map<String, dynamic> json) {
    return ShopItemModel(
      id: json['id'],
      name: json['name'],
      description: json['description'],
      priceGold: json['price_gold'],
      priceGems: json['price_gems'],
      category: json['category'],
      isPowerUp: json['is_power_up'] ?? false,
      duration: json['duration'],
    );
  }
}

/// Power-up type enumeration
enum PowerUpType {
  xpBoost,
  hintToken,
  streakFreeze,
  doubleCoins,
  shield,
  timeFreezer,
}

extension PowerUpTypeExtension on PowerUpType {
  String get id {
    switch (this) {
      case PowerUpType.xpBoost:
        return 'xp_boost';
      case PowerUpType.hintToken:
        return 'hint_token';
      case PowerUpType.streakFreeze:
        return 'streak_freeze';
      case PowerUpType.doubleCoins:
        return 'double_coins';
      case PowerUpType.shield:
        return 'shield';
      case PowerUpType.timeFreezer:
        return 'time_freezer';
    }
  }

  String get displayName {
    switch (this) {
      case PowerUpType.xpBoost:
        return 'Impulso XP';
      case PowerUpType.hintToken:
        return 'Token de Pista';
      case PowerUpType.streakFreeze:
        return 'Congelar Racha';
      case PowerUpType.doubleCoins:
        return 'Monedas Dobles';
      case PowerUpType.shield:
        return 'Escudo';
      case PowerUpType.timeFreezer:
        return 'Congelador de Tiempo';
    }
  }

  static PowerUpType? fromId(String id) {
    for (final type in PowerUpType.values) {
      if (type.id == id) return type;
    }
    return null;
  }
}

/// Model for power-ups owned by the user (inventory)
class PowerUpModel {
  final String id;
  final String name;
  final String type;
  final String description;
  final int quantity;
  final int? duration; // Duration in seconds when activated
  final DateTime? expiresAt; // Only set if currently active

  PowerUpModel({
    required this.id,
    required this.name,
    required this.type,
    required this.description,
    required this.quantity,
    this.duration,
    this.expiresAt,
  });

  factory PowerUpModel.fromJson(Map<String, dynamic> json) {
    return PowerUpModel(
      id: json['id'] ?? '',
      name: json['name'] ?? '',
      type: json['type'] ?? '',
      description: json['description'] ?? '',
      quantity: json['quantity'] ?? 0,
      duration: json['duration'],
      expiresAt: json['expires_at'] != null
          ? DateTime.parse(json['expires_at'])
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'type': type,
      'description': description,
      'quantity': quantity,
      'duration': duration,
      'expires_at': expiresAt?.toIso8601String(),
    };
  }

  PowerUpModel copyWith({
    String? id,
    String? name,
    String? type,
    String? description,
    int? quantity,
    int? duration,
    DateTime? expiresAt,
  }) {
    return PowerUpModel(
      id: id ?? this.id,
      name: name ?? this.name,
      type: type ?? this.type,
      description: description ?? this.description,
      quantity: quantity ?? this.quantity,
      duration: duration ?? this.duration,
      expiresAt: expiresAt ?? this.expiresAt,
    );
  }

  bool get isActive => expiresAt != null && expiresAt!.isAfter(DateTime.now());

  Duration? get remainingTime {
    if (expiresAt == null) return null;
    final remaining = expiresAt!.difference(DateTime.now());
    return remaining.isNegative ? Duration.zero : remaining;
  }
}

/// Model for currently active power-ups
class ActivePowerUpModel {
  final String id;
  final String name;
  final String type;
  final DateTime activatedAt;
  final DateTime expiresAt;
  final double multiplier; // e.g., 2.0 for double XP
  final Map<String, dynamic>? metadata;

  ActivePowerUpModel({
    required this.id,
    required this.name,
    required this.type,
    required this.activatedAt,
    required this.expiresAt,
    this.multiplier = 1.0,
    this.metadata,
  });

  factory ActivePowerUpModel.fromJson(Map<String, dynamic> json) {
    return ActivePowerUpModel(
      id: json['id'] ?? '',
      name: json['name'] ?? '',
      type: json['type'] ?? '',
      activatedAt: DateTime.parse(json['activated_at'] ?? DateTime.now().toIso8601String()),
      expiresAt: DateTime.parse(json['expires_at'] ?? DateTime.now().toIso8601String()),
      multiplier: (json['multiplier'] ?? 1.0).toDouble(),
      metadata: json['metadata'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'type': type,
      'activated_at': activatedAt.toIso8601String(),
      'expires_at': expiresAt.toIso8601String(),
      'multiplier': multiplier,
      'metadata': metadata,
    };
  }

  bool get isExpired => DateTime.now().isAfter(expiresAt);

  Duration get remainingTime {
    final remaining = expiresAt.difference(DateTime.now());
    return remaining.isNegative ? Duration.zero : remaining;
  }

  double get progressPercent {
    final total = expiresAt.difference(activatedAt).inSeconds;
    final remaining = remainingTime.inSeconds;
    if (total <= 0) return 0;
    return remaining / total;
  }
}

/// Response model for power-ups list
class PowerUpsResponseModel {
  final List<PowerUpModel> powerUps;

  PowerUpsResponseModel({required this.powerUps});

  factory PowerUpsResponseModel.fromJson(Map<String, dynamic> json) {
    final powerUpsList = json['power_ups'] as List? ?? [];
    return PowerUpsResponseModel(
      powerUps: powerUpsList.map((p) => PowerUpModel.fromJson(p)).toList(),
    );
  }
}

/// Response model for active power-ups
class ActivePowerUpsResponseModel {
  final List<ActivePowerUpModel> activePowerUps;

  ActivePowerUpsResponseModel({required this.activePowerUps});

  factory ActivePowerUpsResponseModel.fromJson(Map<String, dynamic> json) {
    final activeList = json['active_power_ups'] as List? ??
                       json['active'] as List? ?? [];
    return ActivePowerUpsResponseModel(
      activePowerUps: activeList.map((p) => ActivePowerUpModel.fromJson(p)).toList(),
    );
  }
}

/// Response model for power-up activation
class ActivatePowerUpResponseModel {
  final bool success;
  final ActivePowerUpModel? activatedPowerUp;
  final String? message;

  ActivatePowerUpResponseModel({
    required this.success,
    this.activatedPowerUp,
    this.message,
  });

  factory ActivatePowerUpResponseModel.fromJson(Map<String, dynamic> json) {
    return ActivatePowerUpResponseModel(
      success: json['success'] ?? false,
      activatedPowerUp: json['power_up'] != null
          ? ActivePowerUpModel.fromJson(json['power_up'])
          : null,
      message: json['message'],
    );
  }
}

class ShopResponseModel {
  final List<ShopItemModel> items;

  ShopResponseModel({required this.items});

  factory ShopResponseModel.fromJson(Map<String, dynamic> json) {
    var itemsList = json['items'] as List;
    List<ShopItemModel> items = itemsList.map((i) => ShopItemModel.fromJson(i)).toList();
    return ShopResponseModel(items: items);
  }
}
