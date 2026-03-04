import 'package:flutter/material.dart';
import 'dart:math' as math;

class SubjectRadarChart extends StatefulWidget {
  final List<double> values;
  final List<String> labels;
  final Color color;

  const SubjectRadarChart({
    super.key,
    required this.values,
    required this.labels,
    this.color = Colors.blue,
  });

  @override
  State<SubjectRadarChart> createState() => _SubjectRadarChartState();
}

class _SubjectRadarChartState extends State<SubjectRadarChart> with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(vsync: this, duration: const Duration(seconds: 1))..forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AspectRatio(
      aspectRatio: 1,
      child: Stack(
        alignment: Alignment.center,
        children: [
          CustomPaint(
            size: Size.infinite,
            painter: _RadarBackgroundPainter(vCount: widget.values.length),
          ),
          AnimatedBuilder(
            animation: _controller,
            builder: (context, child) {
              return CustomPaint(
                size: Size.infinite,
                painter: _RadarPolygonPainter(
                  values: widget.values,
                  progress: _controller.value,
                  color: widget.color,
                ),
              );
            },
          ),
          ..._buildLabels(),
        ],
      ),
    );
  }

  List<Widget> _buildLabels() {
    final widgets = <Widget>[];
    final count = widget.values.length;
    const double radiusFactor = 0.45;

    return List.generate(count, (i) {
      final angle = (i * (360 / count) - 90) * math.pi / 180;
      return LayoutBuilder(
        builder: (context, constraints) {
          final radius = constraints.maxWidth * radiusFactor;
          return Transform.translate(
            offset: Offset(radius * math.cos(angle), radius * math.sin(angle)),
            child: Text(
              widget.labels[i],
              style: const TextStyle(color: Colors.white70, fontSize: 10, fontWeight: FontWeight.bold),
            ),
          );
        },
      );
    });
  }
}

class _RadarBackgroundPainter extends CustomPainter {
  final int vCount;
  _RadarBackgroundPainter({required this.vCount});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white.withOpacity(0.05)
      ..style = PaintingStyle.stroke;

    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width * 0.4;

    for (var i = 1; i <= 5; i++) {
      canvas.drawCircle(center, radius * (i / 5), paint);
    }

    for (var i = 0; i < vCount; i++) {
      final angle = (i * (360 / vCount) - 90) * math.pi / 180;
      canvas.drawLine(center, Offset(center.dx + radius * math.cos(angle), center.dy + radius * math.sin(angle)), paint);
    }
  }

  @override
  bool shouldRepaint(CustomPainter old) => false;
}

class _RadarPolygonPainter extends CustomPainter {
  final List<double> values;
  final double progress;
  final Color color;

  _RadarPolygonPainter({required this.values, required this.progress, required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width * 0.4;
    final path = Path();
    final count = values.length;

    for (var i = 0; i < count; i++) {
      final val = values[i] * progress;
      final angle = (i * (360 / count) - 90) * math.pi / 180;
      final point = Offset(center.dx + radius * val * math.cos(angle), center.dy + radius * val * math.sin(angle));
      if (i == 0) path.moveTo(point.dx, point.dy); else path.lineTo(point.dx, point.dy);
    }
    path.close();

    canvas.drawPath(path, Paint()..color = color.withOpacity(0.3)..style = PaintingStyle.fill);
    canvas.drawPath(path, Paint()..color = color..style = PaintingStyle.stroke..strokeWidth = 2);
  }

  @override
  bool shouldRepaint(CustomPainter old) => true;
}
