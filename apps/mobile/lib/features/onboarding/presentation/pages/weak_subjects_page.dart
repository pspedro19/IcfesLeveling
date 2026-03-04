import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/onboarding_preferences_provider.dart';

/// Step 4: Weak Subjects Selection Page (LOGICA_DE_NEGOCIO.md)
/// User selects 1-3 subjects they want to improve
class WeakSubjectsPage extends ConsumerWidget {
  const WeakSubjectsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final preferences = ref.watch(onboardingPreferencesProvider);
    final selectedSubjects = preferences.weakSubjects;

    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Back button
              IconButton(
                onPressed: () => context.pop(),
                icon: const Icon(Icons.arrow_back, color: Colors.white),
              ),

              // Progress indicator
              _buildProgressBar(4),
              const SizedBox(height: 40),

              // Title
              const Text(
                "EN QUE MATERIAS QUIERES MEJORAR?",
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 24,
                  fontWeight: FontWeight.w900,
                  letterSpacing: 2,
                ),
              ).animate().fadeIn().slideX(begin: -0.2),

              const SizedBox(height: 12),

              Row(
                children: [
                  Text(
                    "Selecciona de 1 a 3 materias",
                    style: TextStyle(
                      color: Colors.grey.shade400,
                      fontSize: 16,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: selectedSubjects.length >= 1 && selectedSubjects.length <= 3
                          ? Colors.green.withOpacity(0.2)
                          : Colors.red.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      "${selectedSubjects.length}/3",
                      style: TextStyle(
                        color: selectedSubjects.length >= 1 && selectedSubjects.length <= 3
                            ? Colors.green
                            : Colors.red,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ).animate().fadeIn(delay: 200.ms),

              const SizedBox(height: 30),

              // Subject chips
              Expanded(
                child: Wrap(
                  spacing: 12,
                  runSpacing: 12,
                  children: IcfesSubject.all.asMap().entries.map((entry) {
                    final index = entry.key;
                    final subject = entry.value;
                    final isSelected = selectedSubjects.contains(subject.id);
                    final color = _parseColor(subject.color);

                    return _SubjectChip(
                      subject: subject,
                      isSelected: isSelected,
                      color: color,
                      delay: (index * 100).ms,
                      onTap: () {
                        ref.read(onboardingPreferencesProvider.notifier)
                            .toggleWeakSubject(subject.id);
                      },
                    );
                  }).toList(),
                ),
              ),

              // Hint text
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.blue.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.blue.withOpacity(0.3)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.lightbulb_outline, color: Colors.blue, size: 20),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        "Te daremos mas practica en estas materias para que mejores rapidamente.",
                        style: TextStyle(
                          color: Colors.grey.shade300,
                          fontSize: 13,
                        ),
                      ),
                    ),
                  ],
                ),
              ).animate().fadeIn(delay: 500.ms),

              const SizedBox(height: 20),

              // Continue button
              _buildContinueButton(context, selectedSubjects),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildProgressBar(int step) {
    return Row(
      children: List.generate(5, (index) {
        final isActive = index < step;
        final isCurrent = index == step - 1;
        return Expanded(
          child: Container(
            height: 4,
            margin: const EdgeInsets.symmetric(horizontal: 2),
            decoration: BoxDecoration(
              color: isActive ? Colors.blue : Colors.grey.shade800,
              borderRadius: BorderRadius.circular(2),
              boxShadow: isCurrent
                  ? [BoxShadow(color: Colors.blue.withOpacity(0.5), blurRadius: 4)]
                  : null,
            ),
          ),
        );
      }),
    );
  }

  Color _parseColor(String hexColor) {
    final hex = hexColor.replaceAll('#', '');
    return Color(int.parse('FF$hex', radix: 16));
  }

  Widget _buildContinueButton(BuildContext context, List<String> selectedSubjects) {
    final canContinue = selectedSubjects.isNotEmpty && selectedSubjects.length <= 3;

    return ElevatedButton(
      onPressed: canContinue ? () => context.push('/onboarding/study-time') : null,
      style: ElevatedButton.styleFrom(
        backgroundColor: canContinue ? Colors.blue.shade700 : Colors.grey.shade800,
        foregroundColor: Colors.white,
        minimumSize: const Size(double.infinity, 56),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        elevation: canContinue ? 5 : 0,
        shadowColor: Colors.blue.withOpacity(0.5),
      ),
      child: const Text(
        "CONTINUAR",
        style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, letterSpacing: 2),
      ),
    );
  }
}

class _SubjectChip extends StatelessWidget {
  final IcfesSubject subject;
  final bool isSelected;
  final Color color;
  final Duration delay;
  final VoidCallback onTap;

  const _SubjectChip({
    required this.subject,
    required this.isSelected,
    required this.color,
    required this.delay,
    required this.onTap,
  });

  IconData _getIcon() {
    switch (subject.icon) {
      case 'calculate':
        return Icons.calculate;
      case 'menu_book':
        return Icons.menu_book;
      case 'science':
        return Icons.science;
      case 'public':
        return Icons.public;
      case 'language':
        return Icons.language;
      default:
        return Icons.book;
    }
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        decoration: BoxDecoration(
          gradient: isSelected
              ? LinearGradient(
                  colors: [color.withOpacity(0.3), color.withOpacity(0.1)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                )
              : null,
          color: isSelected ? null : Colors.grey.shade900,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isSelected ? color : Colors.grey.shade700,
            width: isSelected ? 2 : 1,
          ),
          boxShadow: isSelected
              ? [BoxShadow(color: color.withOpacity(0.3), blurRadius: 10)]
              : null,
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              _getIcon(),
              color: isSelected ? color : Colors.grey,
              size: 24,
            ),
            const SizedBox(width: 12),
            Text(
              subject.name,
              style: TextStyle(
                color: isSelected ? Colors.white : Colors.grey.shade300,
                fontSize: 15,
                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
              ),
            ),
            if (isSelected) ...[
              const SizedBox(width: 8),
              Icon(Icons.check, color: color, size: 18),
            ],
          ],
        ),
      ),
    ).animate().fadeIn(delay: delay).scale(begin: const Offset(0.9, 0.9));
  }
}
