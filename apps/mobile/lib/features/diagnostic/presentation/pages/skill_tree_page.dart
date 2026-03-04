import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/deep_diagnostic_provider.dart';

class SkillTreePage extends ConsumerWidget {
  const SkillTreePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(deepDiagnosticProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Resultados del Diagnóstico'),
        automaticallyImplyLeading: false, // No back button
      ),
      body: Builder(
        builder: (context) {
          if (state.results == null) {
            return const Center(child: Text('No hay resultados disponibles.'));
          }

          final results = state.results!;
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text('¡Diagnóstico completado!', style: Theme.of(context).textTheme.headlineMedium),
                  const SizedBox(height: 16),
                  Text('Respuestas correctas: ${results.correct} de ${results.total}'),
                  const SizedBox(height: 24),
                  Text('Tu árbol de habilidades:', style: Theme.of(context).textTheme.titleLarge),
                  Expanded(
                    child: ListView(
                      children: results.skillTree.map((topic) => Card(
                        child: ListTile(
                          title: Text(topic.topicName),
                          subtitle: Text('Maestría: ${(topic.masteryScore * 100).toStringAsFixed(0)}%'),
                          trailing: Text(topic.status, style: TextStyle(color: _getColorForStatus(topic.status), fontWeight: FontWeight.bold)),
                        ),
                      )).toList(),
                    ),
                  ),
                  const SizedBox(height: 32),
                  ElevatedButton(
                    onPressed: () {
                      Navigator.of(context).popUntil((route) => route.isFirst);
                    },
                    child: const Text('Continuar'),
                  )
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Color _getColorForStatus(String status) {
    switch (status) {
      case 'weak':
        return Colors.red;
      case 'learning':
        return Colors.orange;
      case 'strong':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }
}
