import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/onboarding_preferences_provider.dart';

/// Step 5: Study Time Commitment Page (LOGICA_DE_NEGOCIO.md)
/// User selects their daily study time: 10min / 20min / 30+ min
class StudyTimePage extends ConsumerStatefulWidget {
  const StudyTimePage({super.key});

  @override
  ConsumerState<StudyTimePage> createState() => _StudyTimePageState();
}

class _StudyTimePageState extends ConsumerState<StudyTimePage> {
  StudyTimeCommitment? _selectedTime;
  bool _isSubmitting = false;

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

              // Progress indicator (step 5 of 5)
              _buildProgressBar(5),
              const SizedBox(height: 40),

              // Title
              const Text(
                "CUANTO TIEMPO PUEDES ESTUDIAR AL DIA?",
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 24,
                  fontWeight: FontWeight.w900,
                  letterSpacing: 2,
                ),
              ).animate().fadeIn().slideX(begin: -0.2),

              const SizedBox(height: 12),

              Text(
                "La consistencia es la clave del exito. Elige un tiempo que puedas mantener.",
                style: TextStyle(
                  color: Colors.grey.shade400,
                  fontSize: 16,
                ),
              ).animate().fadeIn(delay: 200.ms),

              const SizedBox(height: 40),

              // Time options
              Expanded(
                child: Column(
                  children: StudyTimeCommitment.values.asMap().entries.map((entry) {
                    final index = entry.key;
                    final time = entry.value;
                    return _TimeOption(
                      time: time,
                      isSelected: _selectedTime == time,
                      onTap: () => _selectTime(time),
                      delay: (index * 150).ms,
                    );
                  }).toList(),
                ),
              ),

              // Streak bonus info
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      Colors.orange.withOpacity(0.15),
                      Colors.amber.withOpacity(0.05),
                    ],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.orange.withOpacity(0.3)),
                ),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: Colors.orange.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Icon(Icons.local_fire_department,
                        color: Colors.orange, size: 24),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            "BONUS DE RACHA",
                            style: TextStyle(
                              color: Colors.orange,
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 1,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            "Estudia cada dia para mantener tu racha y ganar XP extra!",
                            style: TextStyle(
                              color: Colors.grey.shade300,
                              fontSize: 13,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ).animate().fadeIn(delay: 500.ms),

              const SizedBox(height: 20),

              // Complete button
              _buildCompleteButton(),
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

  void _selectTime(StudyTimeCommitment time) {
    setState(() => _selectedTime = time);
    ref.read(onboardingPreferencesProvider.notifier).setDailyStudyTime(time);
  }

  Widget _buildCompleteButton() {
    final canComplete = _selectedTime != null && !_isSubmitting;

    return ElevatedButton(
      onPressed: canComplete ? _completeOnboarding : null,
      style: ElevatedButton.styleFrom(
        backgroundColor: canComplete ? Colors.green.shade700 : Colors.grey.shade800,
        foregroundColor: Colors.white,
        minimumSize: const Size(double.infinity, 56),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        elevation: canComplete ? 5 : 0,
        shadowColor: Colors.green.withOpacity(0.5),
      ),
      child: _isSubmitting
          ? const SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(
                color: Colors.white,
                strokeWidth: 2,
              ),
            )
          : const Text(
              "COMENZAR AVENTURA",
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, letterSpacing: 2),
            ),
    );
  }

  Future<void> _completeOnboarding() async {
    setState(() => _isSubmitting = true);

    try {
      final success = await ref
          .read(onboardingPreferencesProvider.notifier)
          .completeOnboarding();

      if (success && mounted) {
        // Navigate to diagnostic test or home
        context.go('/diagnostic');
      } else if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Error al guardar preferencias. Intenta de nuevo.'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }
}

class _TimeOption extends StatelessWidget {
  final StudyTimeCommitment time;
  final bool isSelected;
  final VoidCallback onTap;
  final Duration delay;

  const _TimeOption({
    required this.time,
    required this.isSelected,
    required this.onTap,
    required this.delay,
  });

  Color _getTimeColor() {
    switch (time) {
      case StudyTimeCommitment.tenMinutes:
        return Colors.green;
      case StudyTimeCommitment.twentyMinutes:
        return Colors.blue;
      case StudyTimeCommitment.thirtyPlusMinutes:
        return Colors.purple;
    }
  }

  IconData _getTimeIcon() {
    switch (time) {
      case StudyTimeCommitment.tenMinutes:
        return Icons.timer;
      case StudyTimeCommitment.twentyMinutes:
        return Icons.hourglass_bottom;
      case StudyTimeCommitment.thirtyPlusMinutes:
        return Icons.rocket_launch;
    }
  }

  String _getXpBonus() {
    switch (time) {
      case StudyTimeCommitment.tenMinutes:
        return "+50 XP/dia";
      case StudyTimeCommitment.twentyMinutes:
        return "+100 XP/dia";
      case StudyTimeCommitment.thirtyPlusMinutes:
        return "+200 XP/dia";
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = _getTimeColor();

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
                  _getTimeIcon(),
                  color: isSelected ? color : Colors.grey,
                  size: 28,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          time.displayName.toUpperCase(),
                          style: TextStyle(
                            color: isSelected ? color : Colors.white,
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 1,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: color.withOpacity(0.2),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            _getXpBonus(),
                            style: TextStyle(
                              color: color,
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      time.description,
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
