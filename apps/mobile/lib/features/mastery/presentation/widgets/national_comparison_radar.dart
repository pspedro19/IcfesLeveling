import 'package:flutter/material.dart';
import 'dart:math' as math;

/// Enhanced Radar Chart with National Comparison
/// Shows user mastery vs national average with percentile ranking
class NationalComparisonRadar extends StatefulWidget {
  final List<SubjectComparison> subjects;
  final OverallComparison? overall;
  final bool showNationalAverage;
  final Color userColor;
  final Color nationalColor;

  const NationalComparisonRadar({
    super.key,
    required this.subjects,
    this.overall,
    this.showNationalAverage = true,
    this.userColor = Colors.blue,
    this.nationalColor = Colors.orange,
  });

  @override
  State<NationalComparisonRadar> createState() => _NationalComparisonRadarState();
}

class _NationalComparisonRadarState extends State<NationalComparisonRadar>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    );
    _animation = CurvedAnimation(parent: _controller, curve: Curves.easeOutCubic);
    _controller.forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.02),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.blue.withOpacity(0.2)),
      ),
      child: Column(
        children: [
          // Header
          _buildHeader(),
          const SizedBox(height: 16),

          // Radar Chart
          AspectRatio(
            aspectRatio: 1.1,
            child: AnimatedBuilder(
              animation: _animation,
              builder: (context, child) {
                return CustomPaint(
                  size: Size.infinite,
                  painter: _ComparisonRadarPainter(
                    subjects: widget.subjects,
                    progress: _animation.value,
                    showNational: widget.showNationalAverage,
                    userColor: widget.userColor,
                    nationalColor: widget.nationalColor,
                  ),
                );
              },
            ),
          ),

          const SizedBox(height: 16),

          // Legend
          _buildLegend(),

          // Overall stats
          if (widget.overall != null) ...[
            const SizedBox(height: 16),
            _buildOverallStats(),
          ],

          // Subject breakdown
          const SizedBox(height: 16),
          _buildSubjectBreakdown(),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              "TU PERFIL VS NACIONAL",
              style: TextStyle(
                color: Colors.white60,
                fontSize: 10,
                fontWeight: FontWeight.bold,
                letterSpacing: 2,
              ),
            ),
            if (widget.overall != null)
              Text(
                "Percentil ${widget.overall!.overallPercentile}",
                style: const TextStyle(
                  color: Colors.blue,
                  fontSize: 20,
                  fontWeight: FontWeight.w900,
                ),
              ),
          ],
        ),
        if (widget.overall != null)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: _getDifferenceColor(widget.overall!.difference).withOpacity(0.2),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  widget.overall!.difference >= 0
                      ? Icons.arrow_upward
                      : Icons.arrow_downward,
                  color: _getDifferenceColor(widget.overall!.difference),
                  size: 16,
                ),
                const SizedBox(width: 4),
                Text(
                  "${widget.overall!.difference >= 0 ? '+' : ''}${widget.overall!.difference.toStringAsFixed(1)}%",
                  style: TextStyle(
                    color: _getDifferenceColor(widget.overall!.difference),
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }

  Color _getDifferenceColor(double diff) {
    if (diff > 5) return Colors.green;
    if (diff < -5) return Colors.red;
    return Colors.orange;
  }

  Widget _buildLegend() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        _legendItem(widget.userColor, "Tu nivel"),
        const SizedBox(width: 24),
        if (widget.showNationalAverage)
          _legendItem(widget.nationalColor, "Promedio Nacional"),
      ],
    );
  }

  Widget _legendItem(Color color, String label) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(
            color: color.withOpacity(0.5),
            borderRadius: BorderRadius.circular(3),
            border: Border.all(color: color, width: 2),
          ),
        ),
        const SizedBox(width: 6),
        Text(
          label,
          style: const TextStyle(color: Colors.white70, fontSize: 12),
        ),
      ],
    );
  }

  Widget _buildOverallStats() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.03),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _statItem(
            "Tu Promedio",
            "${widget.overall!.userAverage.toStringAsFixed(1)}%",
            widget.userColor,
          ),
          Container(
            width: 1,
            height: 40,
            color: Colors.white.withOpacity(0.1),
          ),
          _statItem(
            "Promedio Nacional",
            "${widget.overall!.nationalAverage.toStringAsFixed(1)}%",
            widget.nationalColor,
          ),
        ],
      ),
    );
  }

  Widget _statItem(String label, String value, Color color) {
    return Column(
      children: [
        Text(
          value,
          style: TextStyle(
            color: color,
            fontSize: 24,
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          style: const TextStyle(
            color: Colors.white38,
            fontSize: 11,
          ),
        ),
      ],
    );
  }

  Widget _buildSubjectBreakdown() {
    return Column(
      children: widget.subjects.map((subject) => _subjectRow(subject)).toList(),
    );
  }

  Widget _subjectRow(SubjectComparison subject) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          // Subject name
          SizedBox(
            width: 80,
            child: Text(
              subject.subjectName,
              style: const TextStyle(color: Colors.white70, fontSize: 12),
              overflow: TextOverflow.ellipsis,
            ),
          ),

          // Progress bar
          Expanded(
            child: Stack(
              children: [
                // Background
                Container(
                  height: 8,
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.05),
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),

                // National average marker
                if (widget.showNationalAverage)
                  Positioned(
                    left: (subject.nationalAverage / 100) *
                        (MediaQuery.of(context).size.width - 200),
                    child: Container(
                      width: 2,
                      height: 8,
                      decoration: BoxDecoration(
                        color: widget.nationalColor,
                        borderRadius: BorderRadius.circular(1),
                      ),
                    ),
                  ),

                // User progress
                FractionallySizedBox(
                  widthFactor: subject.userMastery / 100,
                  child: Container(
                    height: 8,
                    decoration: BoxDecoration(
                      color: widget.userColor.withOpacity(0.7),
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ),
                ),
              ],
            ),
          ),

          // Percentile badge
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: _getPercentileColor(subject.percentile).withOpacity(0.2),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              "P${subject.percentile}",
              style: TextStyle(
                color: _getPercentileColor(subject.percentile),
                fontSize: 10,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Color _getPercentileColor(int percentile) {
    if (percentile >= 80) return Colors.green;
    if (percentile >= 60) return Colors.blue;
    if (percentile >= 40) return Colors.orange;
    return Colors.red;
  }
}


/// Custom painter for the radar chart with comparison
class _ComparisonRadarPainter extends CustomPainter {
  final List<SubjectComparison> subjects;
  final double progress;
  final bool showNational;
  final Color userColor;
  final Color nationalColor;

  _ComparisonRadarPainter({
    required this.subjects,
    required this.progress,
    required this.showNational,
    required this.userColor,
    required this.nationalColor,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width * 0.38;
    final count = subjects.length;

    if (count == 0) return;

    // Draw background grid
    _drawGrid(canvas, center, radius, count);

    // Draw national average polygon
    if (showNational) {
      _drawPolygon(
        canvas,
        center,
        radius,
        subjects.map((s) => s.nationalAverage / 100).toList(),
        nationalColor,
        filled: true,
        strokeWidth: 2,
      );
    }

    // Draw user polygon (on top)
    _drawPolygon(
      canvas,
      center,
      radius,
      subjects.map((s) => s.userMastery / 100 * progress).toList(),
      userColor,
      filled: true,
      strokeWidth: 3,
    );

    // Draw labels
    _drawLabels(canvas, center, radius, subjects);
  }

  void _drawGrid(Canvas canvas, Offset center, double radius, int count) {
    final gridPaint = Paint()
      ..color = Colors.white.withOpacity(0.08)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;

    // Draw concentric circles
    for (int i = 1; i <= 5; i++) {
      canvas.drawCircle(center, radius * (i / 5), gridPaint);
    }

    // Draw radial lines
    for (int i = 0; i < count; i++) {
      final angle = (i * (360 / count) - 90) * math.pi / 180;
      final endPoint = Offset(
        center.dx + radius * math.cos(angle),
        center.dy + radius * math.sin(angle),
      );
      canvas.drawLine(center, endPoint, gridPaint);
    }
  }

  void _drawPolygon(
    Canvas canvas,
    Offset center,
    double radius,
    List<double> values,
    Color color, {
    bool filled = false,
    double strokeWidth = 2,
  }) {
    if (values.isEmpty) return;

    final count = values.length;
    final path = Path();

    for (int i = 0; i < count; i++) {
      final val = values[i].clamp(0.0, 1.0);
      final angle = (i * (360 / count) - 90) * math.pi / 180;
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

    // Fill
    if (filled) {
      canvas.drawPath(
        path,
        Paint()
          ..color = color.withOpacity(0.2)
          ..style = PaintingStyle.fill,
      );
    }

    // Stroke
    canvas.drawPath(
      path,
      Paint()
        ..color = color
        ..style = PaintingStyle.stroke
        ..strokeWidth = strokeWidth,
    );

    // Draw points
    final pointPaint = Paint()
      ..color = color
      ..style = PaintingStyle.fill;

    for (int i = 0; i < count; i++) {
      final val = values[i].clamp(0.0, 1.0);
      final angle = (i * (360 / count) - 90) * math.pi / 180;
      final point = Offset(
        center.dx + radius * val * math.cos(angle),
        center.dy + radius * val * math.sin(angle),
      );
      canvas.drawCircle(point, 4, pointPaint);
    }
  }

  void _drawLabels(
    Canvas canvas,
    Offset center,
    double radius,
    List<SubjectComparison> subjects,
  ) {
    final count = subjects.length;
    final labelRadius = radius + 20;

    for (int i = 0; i < count; i++) {
      final angle = (i * (360 / count) - 90) * math.pi / 180;
      final labelPos = Offset(
        center.dx + labelRadius * math.cos(angle),
        center.dy + labelRadius * math.sin(angle),
      );

      // Get abbreviated name
      final name = _abbreviateName(subjects[i].subjectName);

      final textPainter = TextPainter(
        text: TextSpan(
          text: name,
          style: const TextStyle(
            color: Colors.white70,
            fontSize: 10,
            fontWeight: FontWeight.bold,
          ),
        ),
        textDirection: TextDirection.ltr,
      );
      textPainter.layout();

      // Center the text
      final textOffset = Offset(
        labelPos.dx - textPainter.width / 2,
        labelPos.dy - textPainter.height / 2,
      );
      textPainter.paint(canvas, textOffset);
    }
  }

  String _abbreviateName(String name) {
    final abbreviations = {
      'Matematicas': 'MAT',
      'Lectura Critica': 'LEC',
      'Ciencias Naturales': 'CIEN',
      'Sociales y Ciudadanas': 'SOC',
      'Ingles': 'ING',
    };

    return abbreviations[name] ??
        (name.length > 4 ? name.substring(0, 4).toUpperCase() : name.toUpperCase());
  }

  @override
  bool shouldRepaint(covariant _ComparisonRadarPainter oldDelegate) {
    return oldDelegate.progress != progress ||
        oldDelegate.subjects != subjects ||
        oldDelegate.showNational != showNational;
  }
}


/// Data class for subject comparison
class SubjectComparison {
  final String subjectId;
  final String subjectName;
  final double userMastery;
  final double nationalAverage;
  final double difference;
  final int percentile;
  final int totalUsersCompared;
  final String status; // 'above', 'below', 'equal'

  const SubjectComparison({
    required this.subjectId,
    required this.subjectName,
    required this.userMastery,
    required this.nationalAverage,
    required this.difference,
    required this.percentile,
    required this.totalUsersCompared,
    required this.status,
  });

  factory SubjectComparison.fromJson(Map<String, dynamic> json) {
    return SubjectComparison(
      subjectId: json['subject_id'] ?? '',
      subjectName: json['subject_name'] ?? '',
      userMastery: (json['user_mastery'] ?? 50).toDouble(),
      nationalAverage: (json['national_average'] ?? 50).toDouble(),
      difference: (json['difference'] ?? 0).toDouble(),
      percentile: json['percentile'] ?? 50,
      totalUsersCompared: json['total_users_compared'] ?? 0,
      status: json['status'] ?? 'equal',
    );
  }
}


/// Data class for overall comparison
class OverallComparison {
  final double userAverage;
  final double nationalAverage;
  final double difference;
  final int overallPercentile;

  const OverallComparison({
    required this.userAverage,
    required this.nationalAverage,
    required this.difference,
    required this.overallPercentile,
  });

  factory OverallComparison.fromJson(Map<String, dynamic> json) {
    return OverallComparison(
      userAverage: (json['user_average'] ?? 50).toDouble(),
      nationalAverage: (json['national_average'] ?? 50).toDouble(),
      difference: (json['difference'] ?? 0).toDouble(),
      overallPercentile: json['overall_percentile'] ?? 50,
    );
  }
}
