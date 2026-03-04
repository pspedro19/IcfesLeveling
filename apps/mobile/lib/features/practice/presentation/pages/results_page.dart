import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/practice_provider.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/config/routes.dart';
import '../../../../core/constants/app_strings.dart';

import 'dart:async';
import '../../../../core/utils/app_haptics.dart';
import '../../../../shared/widgets/pressable_scale.dart';

class ResultsPage extends ConsumerStatefulWidget {
  const ResultsPage({super.key});

  @override
  ConsumerState<ResultsPage> createState() => _ResultsPageState();
}

class _ResultsPageState extends ConsumerState<ResultsPage> {
  int _animatedXp = 0;
  bool _showStats = false;
  Timer? _xpTimer;

  @override
  void initState() {
    super.initState();
    _startCelebration();
  }

  @override
  void dispose() {
    _xpTimer?.cancel();
    super.dispose();
  }

  void _startCelebration() async {
    // Stage 1: Fanfare Haptics immediately
    AppHaptics.celebration();

    // Stage 2: Delay for visual build-up
    await Future.delayed(const Duration(milliseconds: 500));
    if (mounted) {
      setState(() => _showStats = true);
      _animateXp();
    }
  }

  void _animateXp() {
    final targetXp = ref.read(practiceProvider).totalXp;
    if (targetXp == 0) return;

    final duration = const Duration(seconds: 1);
    final steps = 20;
    final increment = targetXp / steps;
    int currentStep = 0;

    _xpTimer = Timer.periodic(Duration(milliseconds: duration.inMilliseconds ~/ steps), (timer) {
      if (!mounted || currentStep >= steps) {
        timer.cancel();
        setState(() => _animatedXp = targetXp);
        return;
      }
      currentStep++;
      setState(() => _animatedXp = (increment * currentStep).toInt());
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(practiceProvider);

    return Scaffold(
      body: Stack(
        children: [
          // Background "Confetti" Placeholder
          if (_showStats)
            const Positioned.fill(
              child: IgnorePointer(
                child: Center(
                  child: Text('🎊', style: TextStyle(fontSize: 100)),
                ),
              ),
            ),

          Center(
            child: Padding(
              padding: const EdgeInsets.all(32),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text(
                    AppStrings.sessionFinished,
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 48),
                  
                  if (_showStats) ...[
                    _buildStatRow(context, AppStrings.correctAnswers, '${state.correctAnswers}/${state.questions.length}'),
                    const Divider(),
                    _buildStatRow(context, AppStrings.xpGained, '+$_animatedXp', color: Colors.orangeAccent),
                    if (state.totalBonusXp > 0) ...[
                      Padding(
                        padding: const EdgeInsets.only(left: 16),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.end,
                          children: [
                            Text(
                              'Incluye +${state.totalBonusXp} XP de combo',
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.orange.withOpacity(0.8),
                                fontStyle: FontStyle.italic,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                    const Divider(),
                    _buildStatRow(context, AppStrings.maxCombo, '${state.maxCombo}', color: Colors.deepOrange),
                    const Divider(),
                    _buildStatRow(context, AppStrings.precision, '${state.accuracy}%'),

                    const SizedBox(height: 64),
                    PressableScale(
                      onTap: () => context.go(AppRoutes.home),
                      child: Container(
                        height: 60,
                        width: double.infinity,
                        alignment: Alignment.center,
                        decoration: BoxDecoration(
                          color: Colors.blue,
                          borderRadius: BorderRadius.circular(16),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.blue.withOpacity(0.3),
                              blurRadius: 10,
                              offset: const Offset(0, 4),
                            )
                          ],
                        ),
                        child: Text(
                          AppStrings.finish,
                          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatRow(BuildContext context, String label, String value, {Color? color}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 18, color: Colors.white70)),
          Text(value, style: TextStyle(
            fontSize: 24, 
            fontWeight: FontWeight.bold,
            color: color ?? Colors.white,
          )),
        ],
      ),
    );
  }
}
