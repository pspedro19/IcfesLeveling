import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/onboarding_preferences_provider.dart';

/// Step 3: Level Assessment Page (LOGICA_DE_NEGOCIO.md)
/// User self-assesses their current level: Basico / Intermedio / Avanzado
class LevelAssessmentPage extends ConsumerStatefulWidget {
  const LevelAssessmentPage({super.key});

  @override
  ConsumerState<LevelAssessmentPage> createState() => _LevelAssessmentPageState();
}

class _LevelAssessmentPageState extends ConsumerState<LevelAssessmentPage> {
  StudentLevel? _selectedLevel;

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
              // Back button
              IconButton(
                onPressed: () => context.pop(),
                icon: const Icon(Icons.arrow_back, color: Colors.white),
              ),

              // Progress indicator
              _buildProgressBar(3),
              const SizedBox(height: 40),

              // Title
              const Text(
                "CUAL ES TU NIVEL ACTUAL?",
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 26,
                  fontWeight: FontWeight.w900,
                  letterSpacing: 2,
                ),
              ).animate().fadeIn().slideX(begin: -0.2),

              const SizedBox(height: 12),

              Text(
                "Se honesto - esto nos ayuda a encontrar el punto de partida perfecto para ti.",
                style: TextStyle(
                  color: Colors.grey.shade400,
                  fontSize: 16,
                ),
              ).animate().fadeIn(delay: 200.ms),

              const SizedBox(height: 40),

              // Level options
              Expanded(
                child: Column(
                  children: StudentLevel.values.asMap().entries.map((entry) {
                    final index = entry.key;
                    final level = entry.value;
                    return _LevelOption(
                      level: level,
                      isSelected: _selectedLevel == level,
                      onTap: () => _selectLevel(level),
                      delay: (index * 150).ms,
                    );
                  }).toList(),
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

  void _selectLevel(StudentLevel level) {
    setState(() => _selectedLevel = level);
    ref.read(onboardingPreferencesProvider.notifier).setCurrentLevel(level);
  }

  Widget _buildContinueButton() {
    final canContinue = _selectedLevel != null;

    return Padding(
      padding: const EdgeInsets.only(top: 20),
      child: ElevatedButton(
        onPressed: canContinue ? () => context.push('/onboarding/subjects') : null,
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

class _LevelOption extends StatelessWidget {
  final StudentLevel level;
  final bool isSelected;
  final VoidCallback onTap;
  final Duration delay;

  const _LevelOption({
    required this.level,
    required this.isSelected,
    required this.onTap,
    required this.delay,
  });

  Color _getLevelColor() {
    switch (level) {
      case StudentLevel.basico:
        return Colors.green;
      case StudentLevel.intermedio:
        return Colors.orange;
      case StudentLevel.avanzado:
        return Colors.purple;
    }
  }

  IconData _getLevelIcon() {
    switch (level) {
      case StudentLevel.basico:
        return Icons.looks_one;
      case StudentLevel.intermedio:
        return Icons.looks_two;
      case StudentLevel.avanzado:
        return Icons.looks_3;
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = _getLevelColor();

    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: GestureDetector(
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            gradient: isSelected
                ? LinearGradient(
                    colors: [color.withOpacity(0.2), color.withOpacity(0.05)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  )
                : null,
            color: isSelected ? null : Colors.grey.shade900,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: isSelected ? color : Colors.grey.shade800,
              width: isSelected ? 2 : 1,
            ),
            boxShadow: isSelected
                ? [BoxShadow(color: color.withOpacity(0.3), blurRadius: 15)]
                : null,
          ),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: isSelected ? color.withOpacity(0.2) : Colors.grey.shade800,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  _getLevelIcon(),
                  color: isSelected ? color : Colors.grey,
                  size: 28,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      level.displayName.toUpperCase(),
                      style: TextStyle(
                        color: isSelected ? color : Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 1,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      level.description,
                      style: TextStyle(
                        color: Colors.grey.shade400,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
              if (isSelected)
                Icon(Icons.check_circle, color: color, size: 24),
            ],
          ),
        ),
      ),
    ).animate().fadeIn(delay: delay).slideX(begin: 0.1);
  }
}
