import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/config/routes.dart';
import '../../../../core/services/onboarding_service.dart';
import '../../../../core/services/notification_service.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import 'notification_settings_page.dart';

class SettingsPage extends ConsumerStatefulWidget {
  const SettingsPage({super.key});

  @override
  ConsumerState<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends ConsumerState<SettingsPage> {
  int _versionTapCount = 0;

  void _handleVersionTap() {
    _versionTapCount++;
    if (_versionTapCount >= 7) {
      _versionTapCount = 0;
      final onboardingNotifier = ref.read(onboardingProvider.notifier);
      onboardingNotifier.setDevMode(true);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Modo Desarrollador activado'),
          backgroundColor: Colors.green,
        ),
      );
    } else if (_versionTapCount >= 4) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('${7 - _versionTapCount} toques más para modo desarrollador'),
          duration: const Duration(milliseconds: 500),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);
    final onboardingState = ref.watch(onboardingProvider);
    final isDevMode = onboardingState.isDevModeEnabled;

    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      appBar: AppBar(
        title: const Text("Configuración"),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: ListView(
        children: [
          // User section
          if (authState.user != null) ...[
            _SectionHeader(title: "CUENTA"),
            ListTile(
              leading: Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: Colors.blue.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(Icons.person, color: Colors.blue.shade300),
              ),
              title: Text(
                authState.user!.name,
                style: const TextStyle(color: Colors.white),
              ),
              subtitle: Text(
                authState.user!.email,
                style: TextStyle(color: Colors.white.withOpacity(0.5)),
              ),
            ),
            const Divider(color: Colors.white10),
          ],

          // App settings
          _SectionHeader(title: "APLICACIÓN"),
          Consumer(
            builder: (context, ref, _) {
              final notificationService = ref.watch(notificationServiceInitProvider);
              final isEnabled = notificationService.valueOrNull?.notificationsEnabled ?? true;

              return ListTile(
                leading: Icon(
                  isEnabled ? Icons.notifications_active : Icons.notifications_off,
                  color: isEnabled ? Colors.blue : Colors.white.withOpacity(0.5),
                ),
                title: const Text("Notificaciones", style: TextStyle(color: Colors.white)),
                subtitle: Text(
                  isEnabled ? "Activadas" : "Desactivadas",
                  style: TextStyle(
                    color: isEnabled ? Colors.green.withOpacity(0.7) : Colors.white.withOpacity(0.5),
                    fontSize: 12,
                  ),
                ),
                trailing: const Icon(Icons.chevron_right, color: Colors.white38),
                onTap: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => const NotificationSettingsPage(),
                    ),
                  );
                },
              );
            },
          ),
          ListTile(
            leading: Icon(Icons.dark_mode_outlined, color: Colors.white.withOpacity(0.7)),
            title: const Text("Tema oscuro", style: TextStyle(color: Colors.white)),
            trailing: Switch(
              value: true,
              onChanged: (value) {
                // TODO: Implement theme toggle
              },
              activeColor: Colors.blue,
            ),
          ),
          const Divider(color: Colors.white10),

          // Developer Mode section (only visible when enabled)
          if (isDevMode) ...[
            _SectionHeader(title: "MODO DESARROLLADOR", isWarning: true),
            ListTile(
              leading: Icon(Icons.refresh, color: Colors.orange.shade300),
              title: const Text("Reiniciar Onboarding", style: TextStyle(color: Colors.white)),
              subtitle: Text(
                "Vuelve al estado de primera ejecución",
                style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 12),
              ),
              onTap: () => _showResetOnboardingDialog(),
            ),
            ListTile(
              leading: Icon(Icons.delete_forever, color: Colors.red.shade300),
              title: const Text("Reinicio Completo", style: TextStyle(color: Colors.white)),
              subtitle: Text(
                "Borra todos los datos de la app",
                style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 12),
              ),
              onTap: () => _showFullResetDialog(),
            ),
            ListTile(
              leading: Icon(Icons.bug_report, color: Colors.purple.shade300),
              title: const Text("Estado Actual", style: TextStyle(color: Colors.white)),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    "Step: ${onboardingState.currentStep.name}",
                    style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 12),
                  ),
                  Text(
                    "First Run: ${onboardingState.isFirstRun}",
                    style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 12),
                  ),
                  Text(
                    "Complete: ${onboardingState.isOnboardingComplete}",
                    style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 12),
                  ),
                  Text(
                    "Diagnostic: ${authState.user?.diagnosticCompleted ?? false}",
                    style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 12),
                  ),
                ],
              ),
              isThreeLine: true,
            ),
            ListTile(
              leading: Icon(Icons.code_off, color: Colors.grey.shade400),
              title: const Text("Desactivar Modo Dev", style: TextStyle(color: Colors.white)),
              onTap: () {
                ref.read(onboardingProvider.notifier).setDevMode(false);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Modo Desarrollador desactivado'),
                  ),
                );
              },
            ),
            const Divider(color: Colors.white10),
          ],

          // Danger zone
          _SectionHeader(title: "SESIÓN"),
          ListTile(
            leading: const Icon(Icons.logout, color: Colors.red),
            title: const Text("Cerrar Sesión", style: TextStyle(color: Colors.red)),
            onTap: () => _showLogoutDialog(),
          ),

          const SizedBox(height: 40),

          // Version info (tap 7 times to enable dev mode)
          GestureDetector(
            onTap: _handleVersionTap,
            child: Container(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  Text(
                    "ICFES LEVELING",
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.3),
                      fontWeight: FontWeight.bold,
                      letterSpacing: 2,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    "v1.0.0",
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.2),
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _showLogoutDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1A1A1A),
        title: const Text("Cerrar Sesión", style: TextStyle(color: Colors.white)),
        content: const Text(
          "¿Estás seguro de que quieres cerrar sesión?",
          style: TextStyle(color: Colors.white70),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("Cancelar"),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              ref.read(authProvider.notifier).logout();
              context.go(AppRoutes.login);
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text("Cerrar Sesión"),
          ),
        ],
      ),
    );
  }

  void _showResetOnboardingDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1A1A1A),
        title: const Text("Reiniciar Onboarding", style: TextStyle(color: Colors.white)),
        content: const Text(
          "Esto reiniciará el flujo de primera ejecución (FTUE). La app se comportará como si fuera la primera vez que la abres.\n\n¿Continuar?",
          style: TextStyle(color: Colors.white70),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("Cancelar"),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(context);
              await ref.read(onboardingProvider.notifier).resetOnboarding();
              if (mounted) {
                context.go(AppRoutes.splash);
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.orange),
            child: const Text("Reiniciar"),
          ),
        ],
      ),
    );
  }

  void _showFullResetDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1A1A1A),
        title: const Text("Reinicio Completo", style: TextStyle(color: Colors.white)),
        content: const Text(
          "ADVERTENCIA: Esto borrará TODOS los datos de la aplicación, incluyendo:\n\n• Sesión actual\n• Progreso de onboarding\n• Preferencias guardadas\n\n¿Estás seguro?",
          style: TextStyle(color: Colors.white70),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("Cancelar"),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(context);
              await ref.read(authProvider.notifier).logout();
              await ref.read(onboardingProvider.notifier).fullReset();
              if (mounted) {
                context.go(AppRoutes.splash);
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text("Borrar Todo"),
          ),
        ],
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String title;
  final bool isWarning;

  const _SectionHeader({required this.title, this.isWarning = false});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 24, 16, 8),
      child: Row(
        children: [
          if (isWarning) ...[
            Icon(Icons.warning_amber, color: Colors.orange.shade300, size: 16),
            const SizedBox(width: 8),
          ],
          Text(
            title,
            style: TextStyle(
              color: isWarning ? Colors.orange.shade300 : Colors.white.withOpacity(0.5),
              fontSize: 12,
              fontWeight: FontWeight.bold,
              letterSpacing: 1.5,
            ),
          ),
        ],
      ),
    );
  }
}
