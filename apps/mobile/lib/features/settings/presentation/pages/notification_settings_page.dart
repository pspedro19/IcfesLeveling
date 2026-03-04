import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/services/notification_service.dart';

/// Provider for notification settings state
final notificationSettingsProvider = StateNotifierProvider<NotificationSettingsNotifier, NotificationSettingsState>((ref) {
  final notificationService = ref.watch(notificationServiceInitProvider).valueOrNull;
  return NotificationSettingsNotifier(notificationService);
});

/// State for notification settings
class NotificationSettingsState {
  final bool allNotificationsEnabled;
  final bool streakEnabled;
  final bool dailyQuestEnabled;
  final bool leagueEnabled;
  final bool bossRaidEnabled;
  final bool achievementEnabled;
  final bool dailyGoalEnabled;
  final bool isLoading;

  const NotificationSettingsState({
    this.allNotificationsEnabled = true,
    this.streakEnabled = true,
    this.dailyQuestEnabled = true,
    this.leagueEnabled = true,
    this.bossRaidEnabled = true,
    this.achievementEnabled = true,
    this.dailyGoalEnabled = true,
    this.isLoading = false,
  });

  NotificationSettingsState copyWith({
    bool? allNotificationsEnabled,
    bool? streakEnabled,
    bool? dailyQuestEnabled,
    bool? leagueEnabled,
    bool? bossRaidEnabled,
    bool? achievementEnabled,
    bool? dailyGoalEnabled,
    bool? isLoading,
  }) {
    return NotificationSettingsState(
      allNotificationsEnabled: allNotificationsEnabled ?? this.allNotificationsEnabled,
      streakEnabled: streakEnabled ?? this.streakEnabled,
      dailyQuestEnabled: dailyQuestEnabled ?? this.dailyQuestEnabled,
      leagueEnabled: leagueEnabled ?? this.leagueEnabled,
      bossRaidEnabled: bossRaidEnabled ?? this.bossRaidEnabled,
      achievementEnabled: achievementEnabled ?? this.achievementEnabled,
      dailyGoalEnabled: dailyGoalEnabled ?? this.dailyGoalEnabled,
      isLoading: isLoading ?? this.isLoading,
    );
  }
}

/// Notifier for notification settings
class NotificationSettingsNotifier extends StateNotifier<NotificationSettingsState> {
  final NotificationService? _notificationService;

  NotificationSettingsNotifier(this._notificationService) : super(const NotificationSettingsState()) {
    _loadSettings();
  }

  void _loadSettings() {
    if (_notificationService == null) return;

    state = NotificationSettingsState(
      allNotificationsEnabled: _notificationService!.notificationsEnabled,
      streakEnabled: _notificationService!.streakNotificationsEnabled,
      dailyQuestEnabled: _notificationService!.dailyQuestNotificationsEnabled,
      leagueEnabled: _notificationService!.leagueNotificationsEnabled,
      bossRaidEnabled: _notificationService!.bossRaidNotificationsEnabled,
      achievementEnabled: _notificationService!.achievementNotificationsEnabled,
      dailyGoalEnabled: _notificationService!.dailyGoalNotificationsEnabled,
    );
  }

  Future<void> setAllNotificationsEnabled(bool enabled) async {
    if (_notificationService == null) return;
    state = state.copyWith(isLoading: true);
    await _notificationService!.setNotificationsEnabled(enabled);
    state = state.copyWith(allNotificationsEnabled: enabled, isLoading: false);
  }

  Future<void> setStreakEnabled(bool enabled) async {
    if (_notificationService == null) return;
    await _notificationService!.setStreakNotificationsEnabled(enabled);
    state = state.copyWith(streakEnabled: enabled);
  }

  Future<void> setDailyQuestEnabled(bool enabled) async {
    if (_notificationService == null) return;
    await _notificationService!.setDailyQuestNotificationsEnabled(enabled);
    state = state.copyWith(dailyQuestEnabled: enabled);
  }

  Future<void> setLeagueEnabled(bool enabled) async {
    if (_notificationService == null) return;
    await _notificationService!.setLeagueNotificationsEnabled(enabled);
    state = state.copyWith(leagueEnabled: enabled);
  }

  Future<void> setBossRaidEnabled(bool enabled) async {
    if (_notificationService == null) return;
    await _notificationService!.setBossRaidNotificationsEnabled(enabled);
    state = state.copyWith(bossRaidEnabled: enabled);
  }

  Future<void> setAchievementEnabled(bool enabled) async {
    if (_notificationService == null) return;
    await _notificationService!.setAchievementNotificationsEnabled(enabled);
    state = state.copyWith(achievementEnabled: enabled);
  }

  Future<void> setDailyGoalEnabled(bool enabled) async {
    if (_notificationService == null) return;
    await _notificationService!.setDailyGoalNotificationsEnabled(enabled);
    state = state.copyWith(dailyGoalEnabled: enabled);
  }
}

/// Notification Settings Page
class NotificationSettingsPage extends ConsumerWidget {
  const NotificationSettingsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settings = ref.watch(notificationSettingsProvider);
    final notifier = ref.read(notificationSettingsProvider.notifier);

    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      appBar: AppBar(
        title: const Text("Notificaciones"),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: ListView(
        padding: const EdgeInsets.symmetric(vertical: 8),
        children: [
          // Master toggle
          _buildMasterToggle(settings, notifier),

          const SizedBox(height: 24),

          // Granular settings
          if (settings.allNotificationsEnabled) ...[
            _buildSectionHeader("RECORDATORIOS"),
            _buildNotificationTile(
              icon: Icons.local_fire_department,
              iconColor: Colors.orange,
              title: "Racha diaria",
              subtitle: "Recordatorios para mantener tu racha activa",
              value: settings.streakEnabled,
              onChanged: notifier.setStreakEnabled,
            ),
            _buildNotificationTile(
              icon: Icons.assignment,
              iconColor: Colors.blue,
              title: "Misiones diarias",
              subtitle: "Recordatorios para completar misiones",
              value: settings.dailyQuestEnabled,
              onChanged: notifier.setDailyQuestEnabled,
            ),
            _buildNotificationTile(
              icon: Icons.track_changes,
              iconColor: Colors.green,
              title: "Meta diaria de XP",
              subtitle: "Recordatorios para alcanzar tu meta",
              value: settings.dailyGoalEnabled,
              onChanged: notifier.setDailyGoalEnabled,
            ),

            const SizedBox(height: 16),
            _buildSectionHeader("EVENTOS"),
            _buildNotificationTile(
              icon: Icons.emoji_events,
              iconColor: Colors.amber,
              title: "Liga semanal",
              subtitle: "Alertas sobre el cierre de la liga",
              value: settings.leagueEnabled,
              onChanged: notifier.setLeagueEnabled,
            ),
            _buildNotificationTile(
              icon: Icons.sports_martial_arts,
              iconColor: Colors.red,
              title: "Boss Raid",
              subtitle: "Notificaciones del evento semanal",
              value: settings.bossRaidEnabled,
              onChanged: notifier.setBossRaidEnabled,
            ),

            const SizedBox(height: 16),
            _buildSectionHeader("LOGROS"),
            _buildNotificationTile(
              icon: Icons.military_tech,
              iconColor: Colors.purple,
              title: "Logros desbloqueados",
              subtitle: "Celebra cuando desbloqueas nuevos logros",
              value: settings.achievementEnabled,
              onChanged: notifier.setAchievementEnabled,
            ),
          ],

          // Info when disabled
          if (!settings.allNotificationsEnabled)
            Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                children: [
                  Icon(
                    Icons.notifications_off,
                    size: 64,
                    color: Colors.white.withOpacity(0.2),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    "Las notificaciones estan desactivadas",
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.5),
                      fontSize: 16,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    "Activa las notificaciones para recibir recordatorios importantes sobre tu progreso.",
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.3),
                      fontSize: 14,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildMasterToggle(NotificationSettingsState settings, NotificationSettingsNotifier notifier) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: settings.allNotificationsEnabled
              ? [Colors.blue.withOpacity(0.2), Colors.purple.withOpacity(0.2)]
              : [Colors.grey.withOpacity(0.1), Colors.grey.withOpacity(0.1)],
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: settings.allNotificationsEnabled
              ? Colors.blue.withOpacity(0.3)
              : Colors.white.withOpacity(0.1),
        ),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: settings.allNotificationsEnabled
                  ? Colors.blue.withOpacity(0.2)
                  : Colors.grey.withOpacity(0.2),
              shape: BoxShape.circle,
            ),
            child: Icon(
              settings.allNotificationsEnabled
                  ? Icons.notifications_active
                  : Icons.notifications_off,
              color: settings.allNotificationsEnabled ? Colors.blue : Colors.grey,
              size: 28,
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  "Todas las notificaciones",
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  settings.allNotificationsEnabled
                      ? "Recibe alertas importantes"
                      : "No recibiras ninguna notificacion",
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.5),
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
          if (settings.isLoading)
            const SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          else
            Switch(
              value: settings.allNotificationsEnabled,
              onChanged: notifier.setAllNotificationsEnabled,
              activeColor: Colors.blue,
            ),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
      child: Text(
        title,
        style: TextStyle(
          color: Colors.white.withOpacity(0.5),
          fontSize: 12,
          fontWeight: FontWeight.bold,
          letterSpacing: 1.5,
        ),
      ),
    );
  }

  Widget _buildNotificationTile({
    required IconData icon,
    required Color iconColor,
    required String title,
    required String subtitle,
    required bool value,
    required Future<void> Function(bool) onChanged,
  }) {
    return ListTile(
      leading: Container(
        width: 40,
        height: 40,
        decoration: BoxDecoration(
          color: iconColor.withOpacity(0.1),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Icon(icon, color: iconColor, size: 22),
      ),
      title: Text(
        title,
        style: const TextStyle(
          color: Colors.white,
          fontWeight: FontWeight.w500,
        ),
      ),
      subtitle: Text(
        subtitle,
        style: TextStyle(
          color: Colors.white.withOpacity(0.5),
          fontSize: 12,
        ),
      ),
      trailing: Switch(
        value: value,
        onChanged: onChanged,
        activeColor: iconColor,
      ),
    );
  }
}
