import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'dart:math' as math;
import '../../../../core/config/routes.dart';
import '../../../../core/services/onboarding_service.dart';
import '../providers/quick_diagnostic_provider.dart';

class ResultsRevealPage extends ConsumerStatefulWidget {
  const ResultsRevealPage({super.key});

  @override
  ConsumerState<ResultsRevealPage> createState() => _ResultsRevealPageState();
}

class _ResultsRevealPageState extends ConsumerState<ResultsRevealPage> {
  bool _showFinalRank = false;

  @override
  void initState() {
    super.initState();
    _startSequence();
  }

  Future<void> _startSequence() async {
    await Future.delayed(4.seconds); // Wait for the "Despertar" text sequence
    if (mounted) {
      setState(() => _showFinalRank = true);
    }
  }

  Future<void> _navigateToFirstMission() async {
    // Update onboarding step to firstMission
    await ref.read(onboardingProvider.notifier).setStep(OnboardingStep.firstMission);

    // Navigate to first mission
    if (mounted) {
      context.go(AppRoutes.firstMission);
    }
  }

  @override
  Widget build(BuildContext context) {
    final diagnosticState = ref.watch(quickDiagnosticProvider);
    final results = diagnosticState.results;

    // Get mastery values from results, or use defaults if not available
    final masteryValues = results?.masteryValues ?? [0.4, 0.6, 0.3, 0.7, 0.5];
    final assignedRank = results?.assignedRank ?? 'E';

    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      body: Stack(
        children: [
          // 1. Initial Reveal Sequence
          if (!_showFinalRank)
            Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text(
                    "EL SISTEMA TE HA EVALUADO...",
                    style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold, letterSpacing: 4),
                  ).animate().fadeIn(duration: 1.seconds).fadeOut(delay: 2.seconds),

                  const SizedBox(height: 20),

                  const Text(
                    "CALCULANDO RANGO DE CAZADOR",
                    style: TextStyle(color: Colors.blue, fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 2),
                  ).animate().fadeIn(delay: 1.5.seconds).fadeOut(delay: 2.5.seconds),
                ],
              ),
            ),

          // 2. Rank Reveal (Light Flash is handled by a full screen overlay)
          if (_showFinalRank)
            _FinalResultsView(
              masteryValues: masteryValues,
              assignedRank: assignedRank,
              onContinue: () => _navigateToFirstMission(),
            ).animate().fadeIn(duration: 800.ms),

          // Flash Overlay
          Container(
            color: Colors.white,
          ).animate(target: _showFinalRank ? 1 : 0)
           .fadeIn(duration: 200.ms)
           .fadeOut(delay: 200.ms),
        ],
      ),
    );
  }
}

class _FinalResultsView extends StatelessWidget {
  final List<double> masteryValues;
  final String assignedRank;
  final VoidCallback onContinue;

  const _FinalResultsView({
    required this.masteryValues,
    required this.assignedRank,
    required this.onContinue,
  });

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Column(
        children: [
          const SizedBox(height: 40),

          const Text(
            "TUS ESTADÍSTICAS",
            style: TextStyle(color: Colors.white70, letterSpacing: 4, fontWeight: FontWeight.bold),
          ).animate().fadeIn(delay: 500.ms),

          const SizedBox(height: 10),

          const Text(
            "CAZADOR REGISTRADO",
            style: TextStyle(color: Colors.blue, fontSize: 24, fontWeight: FontWeight.w900, letterSpacing: 2),
          ).animate().fadeIn(delay: 700.ms).shimmer(delay: 1500.ms),

          Expanded(
            child: Center(
              child: _RadarChartContainer(values: masteryValues),
            ),
          ),

          // Rank Indicator
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 20),
            decoration: BoxDecoration(
              color: Colors.blue.withOpacity(0.1),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: Colors.blue.withOpacity(0.3)),
            ),
            child: Column(
              children: [
                const Text(
                  "RANGO INICIAL",
                  style: TextStyle(color: Colors.white54, fontSize: 12, letterSpacing: 2),
                ),
                const SizedBox(height: 8),
                Text(
                  assignedRank,
                  style: const TextStyle(color: Colors.white, fontSize: 72, fontWeight: FontWeight.w900, fontStyle: FontStyle.italic),
                ).animate().scale(delay: 1.seconds, duration: 1200.ms, curve: Curves.bounceOut),
              ],
            ),
          ).animate().fadeIn(delay: 1.seconds).slideY(begin: 0.1, end: 0),

          const SizedBox(height: 40),

          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 32),
            child: ElevatedButton(
              onPressed: onContinue,
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.blue.shade700,
                minimumSize: const Size(double.infinity, 56),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              child: const Text(
                "COMENZAR ENTRENAMIENTO",
                style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, letterSpacing: 2),
              ),
            ),
          ).animate().fadeIn(delay: 2.seconds),

          const SizedBox(height: 40),
        ],
      ),
    );
  }
}

class _RadarChartContainer extends StatelessWidget {
  final List<double> values;

  const _RadarChartContainer({required this.values});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Stack(
        alignment: Alignment.center,
        children: [
          CustomPaint(
            size: const Size(300, 300),
            painter: _RadarBackgroundPainter(),
          ),
          _AnimatedRadarPolygon(values: values).animate().fadeIn(delay: 1200.ms).scale(delay: 1200.ms, duration: 800.ms),

          // Area Labels
          ..._buildLabels(),
        ],
      ),
    );
  }

  List<Widget> _buildLabels() {
    final areas = ["MAT", "LEC", "CIEN", "SOC", "ING"];
    final widgets = <Widget>[];
    const double radius = 140;

    for (var i = 0; i < 5; i++) {
      final angle = (i * 72 - 90) * math.pi / 180;
      widgets.add(
        Transform.translate(
          offset: Offset(radius * math.cos(angle), radius * math.sin(angle)),
          child: Text(
            areas[i],
            style: const TextStyle(color: Colors.white70, fontSize: 10, fontWeight: FontWeight.bold),
          ),
        ),
      );
    }
    return widgets;
  }
}

class _RadarBackgroundPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white.withOpacity(0.1)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;

    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2;

    // Circles
    for (var i = 1; i <= 5; i++) {
      canvas.drawCircle(center, radius * (i / 5), paint);
    }

    // Lines
    for (var i = 0; i < 5; i++) {
      final angle = (i * 72 - 90) * math.pi / 180;
      canvas.drawLine(
        center,
        Offset(center.dx + radius * math.cos(angle), center.dy + radius * math.sin(angle)),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _AnimatedRadarPolygon extends StatefulWidget {
  final List<double> values;

  const _AnimatedRadarPolygon({required this.values});

  @override
  State<_AnimatedRadarPolygon> createState() => _AnimatedRadarPolygonState();
}

class _AnimatedRadarPolygonState extends State<_AnimatedRadarPolygon> with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(vsync: this, duration: 2.seconds)..forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return CustomPaint(
          size: const Size(300, 300),
          painter: _RadarPolygonPainter(values: widget.values, progress: _controller.value),
        );
      },
    );
  }
}

class _RadarPolygonPainter extends CustomPainter {
  final List<double> values;
  final double progress;

  _RadarPolygonPainter({required this.values, required this.progress});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.blue.withOpacity(0.4)
      ..style = PaintingStyle.fill;

    final borderPaint = Paint()
      ..color = Colors.blue
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2;

    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2;
    final path = Path();

    for (var i = 0; i < 5; i++) {
      final val = values[i] * progress;
      final angle = (i * 72 - 90) * math.pi / 180;
      final point = Offset(
        center.dx + radius * val * math.cos(angle),
        center.dy + radius * val * math.sin(angle),
      );
      if (i == 0) {
        path.moveTo(point.dx, point.dy);
      } else {
        path.lineTo(point.dx, point.dy);
      }
    }
    path.close();

    canvas.drawPath(path, paint);
    canvas.drawPath(path, borderPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
