import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/onboarding_preferences_provider.dart';

/// Step 2: Goal Selection Page (LOGICA_DE_NEGOCIO.md)
/// User selects their study goal and optionally an exam date
class GoalSelectionPage extends ConsumerStatefulWidget {
  const GoalSelectionPage({super.key});

  @override
  ConsumerState<GoalSelectionPage> createState() => _GoalSelectionPageState();
}

class _GoalSelectionPageState extends ConsumerState<GoalSelectionPage> {
  StudyGoal? _selectedGoal;
  DateTime? _examDate;
  bool _showDatePicker = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Progress indicator
              _buildProgressBar(2),
              const SizedBox(height: 40),

              // Title
              const Text(
                "CUAL ES TU OBJETIVO?",
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 28,
                  fontWeight: FontWeight.w900,
                  letterSpacing: 2,
                ),
              ).animate().fadeIn().slideX(begin: -0.2),

              const SizedBox(height: 12),

              Text(
                "Esto nos ayudara a personalizar tu experiencia de entrenamiento.",
                style: TextStyle(
                  color: Colors.grey.shade400,
                  fontSize: 16,
                ),
              ).animate().fadeIn(delay: 200.ms),

              const SizedBox(height: 40),

              // Goal options
              Expanded(
                child: ListView(
                  children: [
                    ...StudyGoal.values.asMap().entries.map((entry) {
                      final index = entry.key;
                      final goal = entry.value;
                      return _GoalOption(
                        goal: goal,
                        isSelected: _selectedGoal == goal,
                        onTap: () => _selectGoal(goal),
                        delay: (index * 150).ms,
                      );
                    }),

                    // Exam date picker (only for specific goals)
                    if (_showDatePicker) ...[
                      const SizedBox(height: 24),
                      _buildDatePicker(),
                    ],
                  ],
                ),
              ),

              // Continue button
              _buildContinueButton(),
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

  void _selectGoal(StudyGoal goal) {
    setState(() {
      _selectedGoal = goal;
      _showDatePicker = goal == StudyGoal.aprobarExamen;
    });
    ref.read(onboardingPreferencesProvider.notifier).setGoal(goal);
  }

  Widget _buildDatePicker() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.blue.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.blue.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            "FECHA DEL EXAMEN",
            style: TextStyle(
              color: Colors.blue,
              fontSize: 12,
              fontWeight: FontWeight.bold,
              letterSpacing: 1,
            ),
          ),
          const SizedBox(height: 12),
          GestureDetector(
            onTap: () async {
              final date = await showDatePicker(
                context: context,
                initialDate: DateTime.now().add(const Duration(days: 30)),
                firstDate: DateTime.now(),
                lastDate: DateTime.now().add(const Duration(days: 365)),
                builder: (context, child) {
                  return Theme(
                    data: ThemeData.dark().copyWith(
                      colorScheme: const ColorScheme.dark(
                        primary: Colors.blue,
                        surface: Color(0xFF1A1A1A),
                      ),
                    ),
                    child: child!,
                  );
                },
              );
              if (date != null) {
                setState(() => _examDate = date);
                ref.read(onboardingPreferencesProvider.notifier)
                    .setGoal(_selectedGoal!, examDate: date);
              }
            },
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: Colors.grey.shade900,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.grey.shade700),
              ),
              child: Row(
                children: [
                  const Icon(Icons.calendar_today, color: Colors.blue, size: 20),
                  const SizedBox(width: 12),
                  Text(
                    _examDate != null
                        ? "${_examDate!.day}/${_examDate!.month}/${_examDate!.year}"
                        : "Seleccionar fecha",
                    style: TextStyle(
                      color: _examDate != null ? Colors.white : Colors.grey,
                      fontSize: 16,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    ).animate().fadeIn().slideY(begin: 0.2);
  }

  Widget _buildContinueButton() {
    final canContinue = _selectedGoal != null;

    return Padding(
      padding: const EdgeInsets.only(top: 20),
      child: ElevatedButton(
        onPressed: canContinue ? () => context.push('/onboarding/level') : null,
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
      ),
    );
  }
}

class _GoalOption extends StatelessWidget {
  final StudyGoal goal;
  final bool isSelected;
  final VoidCallback onTap;
  final Duration delay;

  const _GoalOption({
    required this.goal,
    required this.isSelected,
    required this.onTap,
    required this.delay,
  });

  IconData _getIcon() {
    switch (goal) {
      case StudyGoal.mejorarIcfes:
        return Icons.trending_up;
      case StudyGoal.aprobarExamen:
        return Icons.school;
      case StudyGoal.practicar:
        return Icons.fitness_center;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: GestureDetector(
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: isSelected ? Colors.blue.withOpacity(0.15) : Colors.grey.shade900,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: isSelected ? Colors.blue : Colors.grey.shade800,
              width: isSelected ? 2 : 1,
            ),
            boxShadow: isSelected
                ? [BoxShadow(color: Colors.blue.withOpacity(0.2), blurRadius: 10)]
                : null,
          ),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: isSelected ? Colors.blue.withOpacity(0.2) : Colors.grey.shade800,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  _getIcon(),
                  color: isSelected ? Colors.blue : Colors.grey,
                  size: 28,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Text(
                  goal.displayName,
                  style: TextStyle(
                    color: isSelected ? Colors.white : Colors.grey.shade300,
                    fontSize: 16,
                    fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                  ),
                ),
              ),
              if (isSelected)
                const Icon(Icons.check_circle, color: Colors.blue, size: 24),
            ],
          ),
        ),
      ),
    ).animate().fadeIn(delay: delay).slideX(begin: 0.1);
  }
}
