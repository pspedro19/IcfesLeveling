import 'package:flutter/material.dart';
import 'dart:async';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/config/animation_config.dart';
import '../../features/engagement/presentation/providers/engagement_provider.dart';

/// Displays the user's current heart/mana count, along with visual indicators
/// for full/empty hearts, and a timer for the next heart regeneration.
/// It also shows an "unlimited" icon for premium users.
///
/// This widget observes the [engagementProvider] for its state.
class HeartsDisplay extends ConsumerWidget {
  const HeartsDisplay({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final engagement = ref.watch(engagementProvider);
    final hearts = engagement.hearts;
    final maxHearts = engagement.maxHearts;
    final isPremium = engagement.isPremium;
    final nextHeartAt = engagement.nextHeartAt;

    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            color: Colors.white.withOpacity(0.05),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: Colors.white.withOpacity(0.1)),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (isPremium)
                const Icon(Icons.all_inclusive, color: Colors.blue, size: 20)
              else
                ...List.generate(maxHearts, (index) {
                  final isFull = index < hearts;
                  return Icon(
                    isFull ? Icons.favorite : Icons.favorite_border,
                    color: isFull ? Colors.red : Colors.grey.shade600,
                    size: 18,
                  ).animate(
                     target: hearts <= 2 && isFull ? 1 : 0,
                     onPlay: AnimationConfig.infiniteAnimationsEnabled
                         ? (controller) => controller.repeat(reverse: true)
                         : null,
                   )
                   .scale(
                     begin: const Offset(1, 1),
                     end: const Offset(1.2, 1.2),
                     duration: 800.ms,
                     curve: Curves.easeInOut,
                   );
                }),
              const SizedBox(width: 8),
              Text(
                isPremium ? "INF." : "$hearts",
                style: TextStyle(
                  color: isPremium ? Colors.blue : (hearts <= 1 ? Colors.red : Colors.white),
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                ),
              ),
            ],
          ),
        ),
        if (!isPremium && hearts < maxHearts && nextHeartAt != null)
          Padding(
            padding: const EdgeInsets.only(top: 4, right: 8),
            child: _RegenTimer(nextHeartAt: nextHeartAt),
          ),
      ],
    );
  }
}

/// A private StatefulWidget that displays a countdown timer until the next heart
/// is regenerated. It updates every second.
///
/// [nextHeartAt] The DateTime when the next heart is expected to be available.
class _RegenTimer extends StatefulWidget {
  final DateTime nextHeartAt;
  const _RegenTimer({required this.nextHeartAt});

  @override
  State<_RegenTimer> createState() => _RegenTimerState();
}

class _RegenTimerState extends State<_RegenTimer> {
  late Timer _timer;
  String _timeStr = "";

  @override
  void initState() {
    super.initState();
    _startTimer();
  }

  void _startTimer() {
    _updateTime();
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      _updateTime();
    });
  }

  void _updateTime() {
    if (!mounted) return;
    final diff = widget.nextHeartAt.difference(DateTime.now());
    if (diff.isNegative) {
      setState(() => _timeStr = "00:00");
      return;
    }
    final hours = diff.inHours;
    final minutes = diff.inMinutes.remainder(60);
    final seconds = diff.inSeconds.remainder(60);
    setState(() {
      _timeStr = "${hours > 0 ? '$hours:' : ''}${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}";
    });
  }

  @override
  void dispose() {
    _timer.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Text(
      _timeStr,
      style: TextStyle(color: Colors.grey.shade500, fontSize: 10, fontWeight: FontWeight.normal),
    );
  }
}
