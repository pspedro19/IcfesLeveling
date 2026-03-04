import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hive/hive.dart';
import 'offline_queue_provider.dart';
import '../services/offline_action_queue.dart';
import '../api/node_progress_api_service.dart';
import '../network/api_client.dart';

/// Estado del progreso de un nodo
class NodeProgress {
  final String nodeId;
  final String kingdomId;
  final double masteryPercent;
  final int starsEarned;
  final int timesCompleted;
  final double bestAccuracy;
  final bool isUnlocked;
  final DateTime? unlockedAt;

  const NodeProgress({
    required this.nodeId,
    required this.kingdomId,
    this.masteryPercent = 0.0,
    this.starsEarned = 0,
    this.timesCompleted = 0,
    this.bestAccuracy = 0.0,
    this.isUnlocked = false,
    this.unlockedAt,
  });

  NodeProgress copyWith({
    String? nodeId,
    String? kingdomId,
    double? masteryPercent,
    int? starsEarned,
    int? timesCompleted,
    double? bestAccuracy,
    bool? isUnlocked,
    DateTime? unlockedAt,
  }) {
    return NodeProgress(
      nodeId: nodeId ?? this.nodeId,
      kingdomId: kingdomId ?? this.kingdomId,
      masteryPercent: masteryPercent ?? this.masteryPercent,
      starsEarned: starsEarned ?? this.starsEarned,
      timesCompleted: timesCompleted ?? this.timesCompleted,
      bestAccuracy: bestAccuracy ?? this.bestAccuracy,
      isUnlocked: isUnlocked ?? this.isUnlocked,
      unlockedAt: unlockedAt ?? this.unlockedAt,
    );
  }

  Map<String, dynamic> toJson() => {
        'node_id': nodeId,
        'kingdom_id': kingdomId,
        'mastery_percent': masteryPercent,
        'stars_earned': starsEarned,
        'times_completed': timesCompleted,
        'best_accuracy': bestAccuracy,
        'is_unlocked': isUnlocked,
        'unlocked_at': unlockedAt?.toIso8601String(),
      };

  factory NodeProgress.fromJson(Map<String, dynamic> json) {
    return NodeProgress(
      nodeId: json['node_id'] ?? '',
      kingdomId: json['kingdom_id'] ?? '',
      masteryPercent: (json['mastery_percent'] ?? 0.0).toDouble(),
      starsEarned: json['stars_earned'] ?? 0,
      timesCompleted: json['times_completed'] ?? 0,
      bestAccuracy: (json['best_accuracy'] ?? 0.0).toDouble(),
      isUnlocked: json['is_unlocked'] ?? false,
      unlockedAt: json['unlocked_at'] != null
          ? DateTime.parse(json['unlocked_at'])
          : null,
    );
  }
}

/// Estado del progreso de un reino
class KingdomProgress {
  final String kingdomId;
  final bool diagnosticCompleted;
  final double overallMastery;
  final String rank;
  final bool bossDefeated;
  final int totalStars;
  final List<NodeProgress> nodes;

  const KingdomProgress({
    required this.kingdomId,
    this.diagnosticCompleted = false,
    this.overallMastery = 0.0,
    this.rank = 'E',
    this.bossDefeated = false,
    this.totalStars = 0,
    this.nodes = const [],
  });

  KingdomProgress copyWith({
    String? kingdomId,
    bool? diagnosticCompleted,
    double? overallMastery,
    String? rank,
    bool? bossDefeated,
    int? totalStars,
    List<NodeProgress>? nodes,
  }) {
    return KingdomProgress(
      kingdomId: kingdomId ?? this.kingdomId,
      diagnosticCompleted: diagnosticCompleted ?? this.diagnosticCompleted,
      overallMastery: overallMastery ?? this.overallMastery,
      rank: rank ?? this.rank,
      bossDefeated: bossDefeated ?? this.bossDefeated,
      totalStars: totalStars ?? this.totalStars,
      nodes: nodes ?? this.nodes,
    );
  }

  factory KingdomProgress.fromJson(Map<String, dynamic> json) {
    return KingdomProgress(
      kingdomId: json['kingdom_id'] ?? '',
      diagnosticCompleted: json['diagnostic_completed'] ?? false,
      overallMastery: (json['overall_mastery'] ?? 0.0).toDouble(),
      rank: json['rank'] ?? 'E',
      bossDefeated: json['boss_defeated'] ?? false,
      totalStars: json['total_stars'] ?? 0,
      nodes: (json['nodes'] as List<dynamic>?)
              ?.map((e) => NodeProgress.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }
}

/// Estado global de progreso
class ProgressState {
  final Map<String, KingdomProgress> kingdoms;
  final int totalStars;
  final bool isLoading;
  final String? error;

  const ProgressState({
    this.kingdoms = const {},
    this.totalStars = 0,
    this.isLoading = false,
    this.error,
  });

  ProgressState copyWith({
    Map<String, KingdomProgress>? kingdoms,
    int? totalStars,
    bool? isLoading,
    String? error,
  }) {
    return ProgressState(
      kingdoms: kingdoms ?? this.kingdoms,
      totalStars: totalStars ?? this.totalStars,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

/// Notifier para el progreso de nodos con soporte offline
class NodeProgressNotifier extends StateNotifier<ProgressState> {
  final Ref _ref;
  final NodeProgressApiService _apiService;
  final OfflineActionQueue _offlineQueue;
  late Box _localCache;

  NodeProgressNotifier(this._ref, this._apiService, this._offlineQueue)
      : super(const ProgressState(isLoading: true)) {
    _initialize();
  }

  Future<void> _initialize() async {
    _localCache = await Hive.openBox('node_progress_cache');
    await _loadFromCache();
    await fetchAllProgress();
  }

  /// Carga datos del cache local
  Future<void> _loadFromCache() async {
    final cached = _localCache.get('kingdoms');
    if (cached != null) {
      final kingdoms = <String, KingdomProgress>{};
      for (final entry in (cached as Map).entries) {
        kingdoms[entry.key] = KingdomProgress.fromJson(
          Map<String, dynamic>.from(entry.value),
        );
      }
      state = state.copyWith(kingdoms: kingdoms, isLoading: false);
    }
  }

  /// Guarda en cache local
  Future<void> _saveToCache() async {
    final data = <String, Map<String, dynamic>>{};
    for (final entry in state.kingdoms.entries) {
      data[entry.key] = {
        'kingdom_id': entry.value.kingdomId,
        'diagnostic_completed': entry.value.diagnosticCompleted,
        'overall_mastery': entry.value.overallMastery,
        'rank': entry.value.rank,
        'boss_defeated': entry.value.bossDefeated,
        'total_stars': entry.value.totalStars,
        'nodes': entry.value.nodes.map((n) => n.toJson()).toList(),
      };
    }
    await _localCache.put('kingdoms', data);
  }

  /// Obtiene progreso de todos los reinos
  Future<void> fetchAllProgress() async {
    try {
      state = state.copyWith(isLoading: true, error: null);
      final response = await _apiService.getAllProgress();

      final data = response['data'] ?? response;
      final kingdomsData = data['kingdoms'] as Map<String, dynamic>?;

      if (kingdomsData != null) {
        final kingdoms = <String, KingdomProgress>{};
        for (final entry in kingdomsData.entries) {
          kingdoms[entry.key] = KingdomProgress.fromJson(
            Map<String, dynamic>.from(entry.value),
          );
        }
        state = state.copyWith(
          kingdoms: kingdoms,
          totalStars: data['total_stars'] ?? 0,
          isLoading: false,
        );
        await _saveToCache();
      }
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: 'Error cargando progreso: $e',
      );
    }
  }

  /// Completa un nodo y actualiza el progreso
  Future<void> completeNode({
    required String nodeId,
    required String kingdomId,
    required double accuracy,
    List<String> questionsAnswered = const [],
  }) async {
    // Calcular estrellas localmente
    int stars = 0;
    if (accuracy >= 0.95) {
      stars = 3;
    } else if (accuracy >= 0.80) {
      stars = 2;
    } else if (accuracy >= 0.60) {
      stars = 1;
    }

    // Actualizar estado local optimisticamente
    final kingdom = state.kingdoms[kingdomId];
    if (kingdom != null) {
      final updatedNodes = kingdom.nodes.map((node) {
        if (node.nodeId == nodeId) {
          return node.copyWith(
            masteryPercent: accuracy * 100,
            starsEarned: stars > node.starsEarned ? stars : node.starsEarned,
            timesCompleted: node.timesCompleted + 1,
            bestAccuracy:
                accuracy > node.bestAccuracy ? accuracy : node.bestAccuracy,
          );
        }
        return node;
      }).toList();

      final updatedKingdoms = Map<String, KingdomProgress>.from(state.kingdoms);
      updatedKingdoms[kingdomId] = kingdom.copyWith(nodes: updatedNodes);
      state = state.copyWith(kingdoms: updatedKingdoms);
      await _saveToCache();
    }

    // Encolar para sincronizacion con backend
    await _offlineQueue.enqueueNodeComplete(
      nodeId: nodeId,
      kingdomId: kingdomId,
      accuracy: accuracy,
      questionsAnswered: questionsAnswered,
    );
  }

  /// Desbloquea un nodo
  Future<void> unlockNode({
    required String nodeId,
    required String kingdomId,
  }) async {
    // Actualizar estado local optimisticamente
    final kingdom = state.kingdoms[kingdomId];
    if (kingdom != null) {
      final updatedNodes = kingdom.nodes.map((node) {
        if (node.nodeId == nodeId) {
          return node.copyWith(
            isUnlocked: true,
            unlockedAt: DateTime.now(),
          );
        }
        return node;
      }).toList();

      final updatedKingdoms = Map<String, KingdomProgress>.from(state.kingdoms);
      updatedKingdoms[kingdomId] = kingdom.copyWith(nodes: updatedNodes);
      state = state.copyWith(kingdoms: updatedKingdoms);
      await _saveToCache();
    }

    // Encolar para sincronizacion
    await _offlineQueue.enqueueNodeUnlock(
      nodeId: nodeId,
      kingdomId: kingdomId,
    );
  }

  /// Obtiene progreso de un reino especifico
  KingdomProgress? getKingdomProgress(String kingdomId) {
    return state.kingdoms[kingdomId];
  }

  /// Obtiene progreso de un nodo especifico
  NodeProgress? getNodeProgress(String kingdomId, String nodeId) {
    return state.kingdoms[kingdomId]?.nodes.firstWhere(
      (n) => n.nodeId == nodeId,
      orElse: () => NodeProgress(nodeId: nodeId, kingdomId: kingdomId),
    );
  }
}

/// Provider para el servicio de API
final nodeProgressApiServiceProvider = Provider<NodeProgressApiService>((ref) {
  final dio = ref.watch(apiClientProvider).dio;
  return NodeProgressApiService(dio);
});

/// Provider principal de progreso de nodos
final nodeProgressProvider =
    StateNotifierProvider<NodeProgressNotifier, ProgressState>((ref) {
  final apiService = ref.watch(nodeProgressApiServiceProvider);
  final offlineQueue = ref.watch(offlineQueueProvider);
  return NodeProgressNotifier(ref, apiService, offlineQueue);
});

/// Provider para obtener progreso de un reino especifico
final kingdomProgressProvider =
    Provider.family<KingdomProgress?, String>((ref, kingdomId) {
  return ref.watch(nodeProgressProvider).kingdoms[kingdomId];
});

/// Provider para obtener progreso de un nodo especifico
final singleNodeProgressProvider =
    Provider.family<NodeProgress?, ({String kingdomId, String nodeId})>(
        (ref, params) {
  final kingdom = ref.watch(nodeProgressProvider).kingdoms[params.kingdomId];
  return kingdom?.nodes.firstWhere(
    (n) => n.nodeId == params.nodeId,
    orElse: () =>
        NodeProgress(nodeId: params.nodeId, kingdomId: params.kingdomId),
  );
});
