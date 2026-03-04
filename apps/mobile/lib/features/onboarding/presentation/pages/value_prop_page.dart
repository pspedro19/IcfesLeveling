import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/config/routes.dart';
import '../../../../core/services/onboarding_service.dart';

class ValuePropPage extends ConsumerStatefulWidget {
  const ValuePropPage({super.key});

  @override
  ConsumerState<ValuePropPage> createState() => _ValuePropPageState();
}

class _ValuePropPageState extends ConsumerState<ValuePropPage> {
  final PageController _pageController = PageController();
  int _currentPage = 0;

  final List<ValuePropData> _slides = [
    ValuePropData(
      title: "Sube tu Rango ICFES",
      description: "Entrena como un cazador y escala desde el Rango-E hasta convertirte en un Maestro Rango-S.",
      icon: Icons.trending_up,
      color: Colors.blue,
      animationType: ValuePropAnimationType.rank,
    ),
    ValuePropData(
      title: "Compite en Ligas Semanales",
      description: "Demuestra quién es el mejor en grupos de 30 cazadores. ¡Sube de liga cada semana!",
      icon: Icons.emoji_events,
      color: Colors.amber,
      animationType: ValuePropAnimationType.league,
    ),
    ValuePropData(
      title: "Domina cada Tema",
      description: "El Sistema rastrea tu progreso en tiempo real. Identifica tus debilidades y conquístalas.",
      icon: Icons.radar,
      color: Colors.purple,
      animationType: ValuePropAnimationType.mastery,
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      body: SafeArea(
        child: Column(
          children: [
            // Skip Button
            Align(
              alignment: Alignment.topRight,
              child: TextButton(
                onPressed: () => _finishValueProp(),
                child: Text(
                  "SALTAR",
                  style: TextStyle(color: Colors.grey.shade500, letterSpacing: 2),
                ),
              ),
            ),
            
            Expanded(
              child: PageView.builder(
                controller: _pageController,
                onPageChanged: (index) => setState(() => _currentPage = index),
                itemCount: _slides.length,
                itemBuilder: (context, index) {
                  return _ValuePropSlide(data: _slides[index]);
                },
              ),
            ),
            
            // Indicators
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(
                _slides.length,
                (index) => AnimatedContainer(
                  duration: 300.ms,
                  margin: const EdgeInsets.symmetric(horizontal: 4),
                  width: _currentPage == index ? 24 : 8,
                  height: 8,
                  decoration: BoxDecoration(
                    color: _currentPage == index ? Colors.blue : Colors.grey.shade800,
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),
              ),
            ),
            
            const SizedBox(height: 40),
            
            // Action Button
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
              child: ElevatedButton(
                onPressed: () {
                  if (_currentPage < _slides.length - 1) {
                    _pageController.nextPage(
                      duration: 500.ms,
                      curve: Curves.easeInOut,
                    );
                  } else {
                    _finishValueProp();
                  }
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue.shade700,
                  foregroundColor: Colors.white,
                  minimumSize: const Size(double.infinity, 56),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  elevation: 5,
                  shadowColor: Colors.blue.withOpacity(0.5),
                ),
                child: Text(
                  _currentPage == _slides.length - 1 ? "COMENZAR" : "SIGUIENTE",
                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, letterSpacing: 2),
                ),
              ).animate(target: _currentPage == _slides.length - 1 ? 1 : 0)
               .shimmer(duration: 2.seconds, color: Colors.white.withOpacity(0.3)),
            ),
            
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }

  /// Mark value prop as seen and navigate to login
  Future<void> _finishValueProp() async {
    // Update onboarding state
    await ref.read(onboardingProvider.notifier).markValuePropSeen();

    // Navigate to login/signup
    if (mounted) {
      context.go(AppRoutes.login);
    }
  }
}

enum ValuePropAnimationType { rank, league, mastery }

class ValuePropData {
  final String title;
  final String description;
  final IconData icon;
  final Color color;
  final ValuePropAnimationType animationType;

  ValuePropData({
    required this.title,
    required this.description,
    required this.icon,
    required this.color,
    required this.animationType,
  });
}

class _ValuePropSlide extends StatelessWidget {
  final ValuePropData data;

  const _ValuePropSlide({required this.data});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 40),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Animation Area
          SizedBox(
            height: 280,
            child: _buildAnimation(),
          ),
          
          const SizedBox(height: 40),
          
          Text(
            data.title.toUpperCase(),
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 24,
              fontWeight: FontWeight.w900,
              letterSpacing: 2,
            ),
          ).animate().fadeIn(duration: 600.ms).moveY(begin: 20, end: 0),
          
          const SizedBox(height: 20),
          
          Text(
            data.description,
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Colors.grey.shade400,
              fontSize: 16,
              height: 1.5,
            ),
          ).animate().fadeIn(delay: 200.ms, duration: 600.ms),
        ],
      ),
    );
  }

  Widget _buildAnimation() {
    switch (data.animationType) {
      case ValuePropAnimationType.rank:
        return _RankAnimation(color: data.color);
      case ValuePropAnimationType.league:
        return _LeagueAnimation(color: data.color);
      case ValuePropAnimationType.mastery:
        return _MasteryAnimation(color: data.color);
    }
  }
}

class _RankAnimation extends StatelessWidget {
  final Color color;
  const _RankAnimation({required this.color});

  @override
  Widget build(BuildContext context) {
    return Stack(
      alignment: Alignment.center,
      children: [
        // Background circles
        ...List.generate(3, (index) => Container(
          width: 150.0 + (index * 40),
          height: 150.0 + (index * 40),
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            border: Border.all(color: color.withOpacity(0.1 - (index * 0.03))),
          ),
        ).animate(onPlay: (c) => c.repeat()).scale(begin: const Offset(1, 1), end: const Offset(1.1, 1.1), duration: (1000 + index * 500).ms, curve: Curves.easeInOut)),

        // Central Rank Hexagon
        Container(
          width: 120,
          height: 120,
          decoration: BoxDecoration(
            color: color.withOpacity(0.1),
            border: Border.all(color: color, width: 3),
            shape: BoxShape.circle, // Simplified for now, can use CustomPainter for Hexagon
            boxShadow: [
              BoxShadow(color: color.withOpacity(0.5), blurRadius: 20, spreadRadius: 5),
            ],
          ),
          child: const Center(
            child: Text(
              "E",
              style: TextStyle(color: Colors.white, fontSize: 60, fontWeight: FontWeight.w900, fontStyle: FontStyle.italic),
            ),
          ),
        ).animate(onPlay: (c) => c.repeat(reverse: true))
         .shimmer(duration: 2.seconds, color: Colors.white70)
         .scale(begin: const Offset(1, 1), end: const Offset(1.05, 1.05), duration: 1.seconds),
         
        // Floating particles or elements
        ...List.generate(5, (index) => Positioned(
          left: 40.0 + (index * 30),
          top: 20.0 + (index * 20),
          child: Icon(Icons.star, color: color.withOpacity(0.5), size: 16),
        ).animate(onPlay: (c) => c.repeat()).moveY(begin: 0, end: -30, duration: (1000 + index * 200).ms).fadeOut()),
      ],
    );
  }
}

class _LeagueAnimation extends StatelessWidget {
  final Color color;
  const _LeagueAnimation({required this.color});

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(4, (index) {
        final isMe = index == 1;
        return Container(
          margin: const EdgeInsets.symmetric(vertical: 4),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          decoration: BoxDecoration(
            color: isMe ? color.withOpacity(0.2) : Colors.white.withOpacity(0.05),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: isMe ? color : Colors.transparent),
          ),
          child: Row(
            children: [
              Text("#${index + 1}", style: TextStyle(color: isMe ? color : Colors.grey)),
              const SizedBox(width: 12),
              CircleAvatar(radius: 12, backgroundColor: Colors.grey.shade800),
              const SizedBox(width: 12),
              Expanded(child: Container(height: 8, color: Colors.grey.shade800)),
              const SizedBox(width: 20),
              Text("${(4 - index) * 100} XP", style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
            ],
          ),
        ).animate()
         .fadeIn(delay: (index * 150).ms)
         .slideX(begin: 0.2, end: 0);
      }),
    );
  }
}

class _MasteryAnimation extends StatelessWidget {
  final Color color;
  const _MasteryAnimation({required this.color});

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      size: const Size(200, 200),
      painter: RadarPainter(color: color),
    ).animate(onPlay: (c) => c.repeat())
     .shimmer(duration: 3.seconds, color: Colors.white24);
  }
}

class RadarPainter extends CustomPainter {
  final Color color;
  RadarPainter({required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2;
    final paint = Paint()
      ..color = color.withOpacity(0.3)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;

    // Draw background circles
    for (var i = 1; i <= 4; i++) {
      canvas.drawCircle(center, radius * (i / 4), paint);
    }

    // Draw lines
    for (var i = 0; i < 5; i++) {
      final angle = (i * 360 / 5) * 3.14159 / 180;
      canvas.drawLine(
        center,
        Offset(center.dx + radius * 0.8 * (i % 2 == 0 ? 0.9 : 1.1) * (i / 5), center.dy + radius * 0.8), // Placeholder
        paint,
      );
    }
    
    // Draw polygon for "Mastery"
    final polyPaint = Paint()
      ..color = color.withOpacity(0.5)
      ..style = PaintingStyle.fill;
    
    final path = Path();
    path.moveTo(center.dx, center.dy - radius * 0.8);
    path.lineTo(center.dx + radius * 0.7, center.dy - radius * 0.2);
    path.lineTo(center.dx + radius * 0.4, center.dy + radius * 0.7);
    path.lineTo(center.dx - radius * 0.5, center.dy + radius * 0.6);
    path.lineTo(center.dx - radius * 0.8, center.dy - radius * 0.3);
    path.close();
    
    canvas.drawPath(path, polyPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
