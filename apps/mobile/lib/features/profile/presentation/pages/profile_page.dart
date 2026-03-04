import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/config/routes.dart';
import '../../../auth/presentation/providers/auth_provider.dart';

class ProfilePage extends ConsumerWidget {
  const ProfilePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authProvider).user;

    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      appBar: AppBar(
        title: const Text("Perfil de Cazador"),
        backgroundColor: Colors.transparent,
      ),
      body: user == null
          ? const Center(child: Text("No user found"))
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                const Center(
                  child: CircleAvatar(
                    radius: 50,
                    backgroundColor: Colors.blueAccent,
                    child: Icon(Icons.person, size: 50, color: Colors.white),
                  ),
                ),
                const SizedBox(height: 16),
                Center(
                  child: Text(
                    user.name,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                Center(
                  child: Text(
                    user.email,
                    style: const TextStyle(
                      color: Colors.grey,
                      fontSize: 16,
                    ),
                  ),
                ),
                const SizedBox(height: 32),
                const Divider(color: Colors.white24),
                ListTile(
                  leading: const Icon(Icons.shield, color: Colors.blue),
                  title: const Text("Clase", style: TextStyle(color: Colors.white)),
                  subtitle: const Text("Cazador Rango E", style: TextStyle(color: Colors.grey)),
                  trailing: const Icon(Icons.chevron_right, color: Colors.grey),
                  onTap: () {},
                ),
                ListTile(
                  leading: const Icon(Icons.bar_chart, color: Colors.cyan),
                  title: const Text("Estadisticas y Progreso", style: TextStyle(color: Colors.white)),
                  subtitle: const Text("Ve tu progreso y debilidades", style: TextStyle(color: Colors.grey)),
                  trailing: const Icon(Icons.chevron_right, color: Colors.grey),
                  onTap: () => context.push(AppRoutes.stats),
                ),
                ListTile(
                  leading: const Icon(Icons.emoji_events, color: Colors.amber),
                  title: const Text("Logros", style: TextStyle(color: Colors.white)),
                  subtitle: const Text("Ve tus logros y medallas", style: TextStyle(color: Colors.grey)),
                  trailing: const Icon(Icons.chevron_right, color: Colors.grey),
                  onTap: () => context.push(AppRoutes.achievements),
                ),
                ListTile(
                  leading: const Icon(Icons.settings, color: Colors.grey),
                  title: const Text("Configuracion", style: TextStyle(color: Colors.white)),
                  trailing: const Icon(Icons.chevron_right, color: Colors.grey),
                  onTap: () => context.push(AppRoutes.settings),
                ),
                const SizedBox(height: 24),
                const Divider(color: Colors.white24),
                ListTile(
                  leading: const Icon(Icons.logout, color: Colors.redAccent),
                  title: const Text("Cerrar Sesión", style: TextStyle(color: Colors.redAccent)),
                  onTap: () => _showLogoutDialog(context, ref),
                ),
              ],
            ),
    );
  }

  void _showLogoutDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1A1A1A),
        title: const Text("Cerrar Sesión", style: TextStyle(color: Colors.white)),
        content: const Text(
          "¿Estás seguro de que quieres salir?",
          style: TextStyle(color: Colors.grey),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text("Cancelar"),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(ctx);
              ref.read(authProvider.notifier).logout();
              context.go(AppRoutes.login);
            },
            child: const Text("Salir", style: TextStyle(color: Colors.redAccent)),
          ),
        ],
      ),
    );
  }
}
