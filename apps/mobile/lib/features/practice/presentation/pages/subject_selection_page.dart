import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/config/routes.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../../diagnostic/presentation/providers/deep_diagnostic_provider.dart';

class SubjectSelectionPage extends ConsumerWidget {
  const SubjectSelectionPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authProvider).user;
    
    // Hardcoded list of subjects for now
    final subjects = [
      {'id': 'math', 'name': 'Matemáticas'},
      {'id': 'reading', 'name': 'Lectura Crítica'},
      {'id': 'science', 'name': 'Ciencias Naturales'},
      {'id': 'social', 'name': 'Sociales y Ciudadanas'},
      {'id': 'english', 'name': 'Inglés'},
    ];

    return Scaffold(
      appBar: AppBar(title: const Text('Elige un Área')),
      body: ListView.builder(
        itemCount: subjects.length,
        itemBuilder: (context, index) {
          final subject = subjects[index];
          final subjectId = subject['id']!;

          return Card(
            margin: const EdgeInsets.all(8),
            child: ListTile(
              title: Text(subject['name']!),
              onTap: () {
                final hasCompleted = user?.completedDeepDiagnostics.contains(subjectId) ?? false;

                if (hasCompleted) {
                  context.go(AppRoutes.practiceSubject(subjectId));
                } else {
                  ref.read(deepDiagnosticProvider.notifier).startDiagnostic(subjectId);
                  context.go(Uri(path: AppRoutes.diagnosticDeep, queryParameters: {'subjectId': subjectId}).toString());
                }
              },
            ),
          );
        },
      ),
    );
  }
}
