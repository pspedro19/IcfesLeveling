import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/config/routes.dart';
import '../../../../core/services/onboarding_service.dart';
import '../providers/quick_diagnostic_provider.dart';
import '../../../practice/domain/entities/question.dart';

class QuickDiagnosticPage extends ConsumerWidget {
  const QuickDiagnosticPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(quickDiagnosticProvider);
    final notifier = ref.read(quickDiagnosticProvider.notifier);

    ref.listen<QuickDiagnosticState>(quickDiagnosticProvider, (previous, next) {
      if (next.isFinished && previous?.isFinished != true) {
        // Update onboarding step before navigating
        ref.read(onboardingProvider.notifier).setStep(OnboardingStep.results);
        context.go(AppRoutes.resultsReveal);
      }
    });

    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.close, color: Colors.white),
          onPressed: () => context.pop(),
        ),
        title: Column(
          children: [
            const Text(
              "CALIBRACIÓN DEL SISTEMA",
              style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 2),
            ),
            const SizedBox(height: 8),
            if (state.questions.isNotEmpty)
              ClipRRect(
                borderRadius: BorderRadius.circular(10),
                child: LinearProgressIndicator(
                  value: (state.currentIndex + 1) / state.questions.length,
                  backgroundColor: Colors.white.withOpacity(0.05),
                  valueColor: const AlwaysStoppedAnimation<Color>(Colors.blue),
                  minHeight: 6,
                ),
              ),
          ],
        ),
        centerTitle: true,
      ),
      body: _buildBody(context, state, notifier),
    );
  }

  Widget _buildBody(BuildContext context, QuickDiagnosticState state, QuickDiagnosticNotifier notifier) {
    if (state.isLoading && state.questions.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }

    if (state.error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('Error: ${state.error}', style: const TextStyle(color: Colors.red)),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => notifier.startDiagnostic(),
              child: const Text('Reintentar'),
            ),
          ],
        ),
      );
    }
    
    final Question? question = state.currentQuestion;
    if (question == null) {
      return const Center(child: Text("No hay preguntas disponibles.", style: TextStyle(color: Colors.white)));
    }

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const SizedBox(height: 40),
          Text(
            "PREGUNTA ${state.currentIndex + 1} DE ${state.questions.length}",
            style: TextStyle(color: Colors.blue.shade400, fontWeight: FontWeight.bold, letterSpacing: 1),
          ).animate().fadeIn(),
          const SizedBox(height: 24),
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.03),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.white.withOpacity(0.05)),
            ),
            child: Text(
              question.text,
              style: const TextStyle(color: Colors.white, fontSize: 20, height: 1.6, fontWeight: FontWeight.w500),
            ),
          ).animate(key: ValueKey(state.currentIndex))
           .fadeIn(duration: 400.ms)
           .slideX(begin: 0.1, end: 0),
          const SizedBox(height: 40),
          Expanded(
            child: ListView.builder(
              itemCount: question.options.length,
              itemBuilder: (context, index) {
                final option = question.options[index];
                return _OptionButton(
                  label: "${option.id}. ${option.text}",
                  onPressed: () => notifier.answerQuestion(question.id, option.id),
                );
              },
            ),
          ),
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 20),
            child: Text(
              "Responde con sinceridad. No hay feedback inmediato en esta fase.",
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.white24, fontSize: 12),
            ),
          ),
        ],
      ),
    );
  }
}

class _OptionButton extends StatelessWidget {
  final String label;
  final VoidCallback onPressed;

  const _OptionButton({required this.label, required this.onPressed});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          decoration: BoxDecoration(
            border: Border.all(color: Colors.white.withOpacity(0.1)),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  label,
                  style: const TextStyle(color: Colors.white, fontSize: 16),
                ),
              ),
              Icon(Icons.chevron_right, color: Colors.white.withOpacity(0.3)),
            ],
          ),
        ),
      ),
    ).animate().fadeIn(delay: 100.ms);
  }
}
