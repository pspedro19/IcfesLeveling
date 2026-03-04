import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/deep_diagnostic_provider.dart';
import 'skill_tree_page.dart';

class DeepDiagnosticPage extends ConsumerWidget {
  const DeepDiagnosticPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(deepDiagnosticProvider);
    final notifier = ref.read(deepDiagnosticProvider.notifier);

    // After submitting, if we have results, go to the skill tree page
    if (state.results != null) {
      return const SkillTreePage();
    }
    
    // During the test
    return Scaffold(
      appBar: AppBar(
        title: Text(state.session?.subjectName ?? 'Diagnóstico Profundo'),
      ),
      body: Builder(
        builder: (context) {
          if (state.isLoading && state.session == null) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state.error != null) {
            return Center(child: Text('Error: ${state.error}'));
          }
          if (state.session == null) {
            // Check for subjectId in query parameters
            final state = GoRouterState.of(context);
            final subjectId = state.uri.queryParameters['subjectId'];

            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text('Inicia el diagnóstico para empezar.'),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () {
                       if (subjectId != null) {
                         notifier.startDiagnostic(subjectId);
                       } else {
                         // Fallback or go back
                         context.pop();
                       }
                    },
                    child: Text(subjectId != null ? 'Iniciar Diagnóstico' : 'Volver'),
                  ),
                ],
              ),
            );
          }

          final questions = state.session!.questions;
          
          return PageView.builder(
            itemCount: questions.length + 1, // +1 for the final submit page
            itemBuilder: (context, index) {
              if (index == questions.length) {
                return Center(
                  child: ElevatedButton(
                    onPressed: () => notifier.submitDiagnostic(),
                    child: const Text('Finalizar y ver resultados'),
                  ),
                );
              }

              final question = questions[index];
              return Card(
                margin: const EdgeInsets.all(16),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Pregunta ${index + 1} de ${questions.length}', style: Theme.of(context).textTheme.titleMedium),
                      const SizedBox(height: 16),
                      Text(question.text, style: Theme.of(context).textTheme.bodyLarge),
                      const SizedBox(height: 24),
                      ...question.options.map((option) {
                        final isSelected = state.answers[question.id] == option.id;
                        return RadioListTile<String>(
                          title: Text(option.text),
                          value: option.id,
                          groupValue: state.answers[question.id],
                          onChanged: (value) {
                            if (value != null) {
                              notifier.answerQuestion(question.id, value);
                            }
                          },
                          activeColor: isSelected ? Colors.blue : null,
                        );
                      }),
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
