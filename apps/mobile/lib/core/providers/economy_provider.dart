import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'offline_queue_provider.dart';
import '../services/offline_action_queue.dart';

/// Estado de la economia del usuario
class UserEconomy {
  final int gold;
  final int totalXp;
  final int level;
  final String rank;

  const UserEconomy({
    this.gold = 100,
    this.totalXp = 0,
    this.level = 1,
    this.rank = 'E',
  });

  UserEconomy copyWith({
    int? gold,
    int? totalXp,
    int? level,
    String? rank,
  }) {
    return UserEconomy(
      gold: gold ?? this.gold,
      totalXp: totalXp ?? this.totalXp,
      level: level ?? this.level,
      rank: rank ?? this.rank,
    );
  }
}

/// Notifier para la economia
class EconomyNotifier extends StateNotifier<UserEconomy> {
  final Ref _ref;
  OfflineActionQueue? _offlineQueue;

  EconomyNotifier(this._ref) : super(const UserEconomy()) {
    _offlineQueue = _ref.read(offlineQueueProvider);
  }

  void addGold(int amount, {String source = 'unknown'}) {
    state = state.copyWith(gold: state.gold + amount);
    // Encolar para sincronizacion
    _offlineQueue?.enqueue(GameActionType.goldTransaction, {
      'amount': amount,
      'source': source,
      'type': 'earn',
    });
  }

  void spendGold(int amount, {String itemId = 'unknown'}) {
    if (state.gold >= amount) {
      state = state.copyWith(gold: state.gold - amount);
      // Encolar compra para sincronizacion
      _offlineQueue?.enqueuePurchase(
        itemId: itemId,
        quantity: 1,
        currency: 'gold',
      );
    }
  }

  void addXp(int amount) {
    final newXp = state.totalXp + amount;
    final newLevel = _calculateLevel(newXp);
    final newRank = _calculateRank(newLevel);

    state = state.copyWith(
      totalXp: newXp,
      level: newLevel,
      rank: newRank,
    );
  }

  int _calculateLevel(int xp) {
    int level = 1;
    int xpForNext = 100;
    int remaining = xp;

    while (remaining >= xpForNext) {
      remaining -= xpForNext;
      level++;
      xpForNext = (100 * (level * 1.5)).toInt();
    }

    return level;
  }

  String _calculateRank(int level) {
    if (level >= 50) return 'S';
    if (level >= 40) return 'A';
    if (level >= 30) return 'B';
    if (level >= 20) return 'C';
    if (level >= 10) return 'D';
    return 'E';
  }

  void setFromServer(UserEconomy economy) {
    state = economy;
  }
}

/// Provider de economia
final economyProvider = StateNotifierProvider<EconomyNotifier, UserEconomy>((ref) {
  return EconomyNotifier(ref);
});

/// Provider de oro
final goldProvider = Provider<int>((ref) {
  return ref.watch(economyProvider).gold;
});

/// Provider de nivel
final levelProvider = Provider<int>((ref) {
  return ref.watch(economyProvider).level;
});

/// Provider de rango
final rankProvider = Provider<String>((ref) {
  return ref.watch(economyProvider).rank;
});
