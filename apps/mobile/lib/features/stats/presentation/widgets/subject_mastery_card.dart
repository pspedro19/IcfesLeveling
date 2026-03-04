import 'package:flutter/material.dart';
import '../../data/models/stats_models.dart';

/// Card showing mastery progress for a single subject
class SubjectMasteryCard extends StatelessWidget {
  final SubjectProgress subject;
  final VoidCallback? onTap;

  const SubjectMasteryCard({
    super.key,
    required this.subject,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final color = Color(subject.color);
    final masteryPercent = (subject.masteryLevel * 100).toInt();

    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: color.withOpacity(0.3)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(
                    _getSubjectIcon(subject.icon),
                    color: color,
                    size: 24,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        subject.subjectName,
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 14,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 2),
                      Text(
                        '${subject.questionsAnswered} preguntas',
                        style: TextStyle(
                          color: Colors.grey[500],
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
                _buildStrengthBadge(),
              ],
            ),
            const SizedBox(height: 16),
            // Mastery progress bar
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            'Dominio',
                            style: TextStyle(
                              color: Colors.grey[500],
                              fontSize: 11,
                            ),
                          ),
                          Text(
                            '$masteryPercent%',
                            style: TextStyle(
                              color: color,
                              fontWeight: FontWeight.bold,
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Stack(
                        children: [
                          Container(
                            height: 8,
                            decoration: BoxDecoration(
                              color: Colors.grey[800],
                              borderRadius: BorderRadius.circular(4),
                            ),
                          ),
                          FractionallySizedBox(
                            widthFactor: subject.masteryLevel,
                            child: Container(
                              height: 8,
                              decoration: BoxDecoration(
                                gradient: LinearGradient(
                                  colors: [color.withOpacity(0.7), color],
                                ),
                                borderRadius: BorderRadius.circular(4),
                              ),
                            ),
                          ),
                          // National average marker
                          Positioned(
                            left: subject.nationalAverage * (MediaQuery.of(context).size.width - 100),
                            child: Container(
                              width: 2,
                              height: 8,
                              color: Colors.white54,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            // Stats row
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildStat('Precision', '${subject.accuracyPercent}%', Colors.green),
                _buildStat('vs Nacional', _getComparisonText(), _getComparisonColor()),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStrengthBadge() {
    Color badgeColor;
    String text;
    IconData icon;

    switch (subject.strengthLevel) {
      case 'strong':
        badgeColor = Colors.green;
        text = 'Fortaleza';
        icon = Icons.trending_up;
        break;
      case 'weak':
        badgeColor = Colors.red;
        text = 'Debilidad';
        icon = Icons.trending_down;
        break;
      default:
        badgeColor = Colors.orange;
        text = 'Promedio';
        icon = Icons.trending_flat;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: badgeColor.withOpacity(0.2),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: badgeColor.withOpacity(0.5)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: badgeColor, size: 12),
          const SizedBox(width: 4),
          Text(
            text,
            style: TextStyle(
              color: badgeColor,
              fontSize: 10,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStat(String label, String value, Color color) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: TextStyle(
            color: Colors.grey[600],
            fontSize: 10,
          ),
        ),
        Text(
          value,
          style: TextStyle(
            color: color,
            fontWeight: FontWeight.bold,
            fontSize: 13,
          ),
        ),
      ],
    );
  }

  String _getComparisonText() {
    final diff = subject.masteryLevel - subject.nationalAverage;
    if (diff > 0.05) {
      return '+${(diff * 100).toInt()}%';
    } else if (diff < -0.05) {
      return '${(diff * 100).toInt()}%';
    }
    return '~igual';
  }

  Color _getComparisonColor() {
    final diff = subject.masteryLevel - subject.nationalAverage;
    if (diff > 0.05) return Colors.green;
    if (diff < -0.05) return Colors.red;
    return Colors.orange;
  }

  IconData _getSubjectIcon(String icon) {
    switch (icon) {
      case 'calculate':
        return Icons.calculate;
      case 'book':
        return Icons.menu_book;
      case 'public':
        return Icons.public;
      case 'science':
        return Icons.science;
      case 'translate':
        return Icons.translate;
      default:
        return Icons.school;
    }
  }
}

/// Radar chart for subject comparison
class SubjectRadarChart extends StatelessWidget {
  final List<SubjectProgress> subjects;

  const SubjectRadarChart({
    super.key,
    required this.subjects,
  });

  @override
  Widget build(BuildContext context) {
    if (subjects.isEmpty) {
      return const SizedBox.shrink();
    }

    return Container(
      height: 250,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.03),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: CustomPaint(
        painter: _RadarChartPainter(
          subjects: subjects,
          userColor: Colors.blue,
          nationalColor: Colors.grey,
        ),
        size: Size.infinite,
      ),
    );
  }
}

class _RadarChartPainter extends CustomPainter {
  final List<SubjectProgress> subjects;
  final Color userColor;
  final Color nationalColor;

  _RadarChartPainter({
    required this.subjects,
    required this.userColor,
    required this.nationalColor,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width * 0.35;
    final n = subjects.length;

    if (n == 0) return;

    // Draw grid circles
    final gridPaint = Paint()
      ..color = Colors.white.withOpacity(0.1)
      ..style = PaintingStyle.stroke;

    for (int i = 1; i <= 4; i++) {
      canvas.drawCircle(center, radius * i / 4, gridPaint);
    }

    // Draw axis lines and labels
    final textPainter = TextPainter(
      textDirection: TextDirection.ltr,
    );

    for (int i = 0; i < n; i++) {
      final angle = -3.14159 / 2 + (2 * 3.14159 * i / n);
      final x = center.dx + radius * 1.15 * (angle == -3.14159 / 2 ? 0 : (angle > -3.14159 / 2 && angle < 3.14159 / 2 ? 1 : -1) * (1 - (angle.abs() - 3.14159 / 2).abs() / 3.14159));
      final y = center.dy + radius * 1.15 * (angle == -3.14159 / 2 ? -1 : (angle > 0 ? 1 : -1) * (1 - (angle.abs()).abs() / 3.14159));

      final endX = center.dx + radius * (angle == -3.14159 / 2 ? 0 : (angle > -3.14159 / 2 && angle < 3.14159 / 2 ? 1 : -1) * (1 - (angle.abs() - 3.14159 / 2).abs() / 3.14159).abs());
      final endY = center.dy + radius * (angle == -3.14159 / 2 ? -1 : (angle > 0 ? 1 : -1) * (1 - (angle.abs()).abs() / 3.14159).abs());

      canvas.drawLine(
        center,
        Offset(
          center.dx + radius * _cos(angle),
          center.dy + radius * _sin(angle),
        ),
        gridPaint,
      );
    }

    // Draw user data polygon
    final userPath = Path();
    final nationalPath = Path();

    for (int i = 0; i < n; i++) {
      final angle = -3.14159 / 2 + (2 * 3.14159 * i / n);
      final userR = radius * subjects[i].masteryLevel;
      final nationalR = radius * subjects[i].nationalAverage;

      final userX = center.dx + userR * _cos(angle);
      final userY = center.dy + userR * _sin(angle);
      final nationalX = center.dx + nationalR * _cos(angle);
      final nationalY = center.dy + nationalR * _sin(angle);

      if (i == 0) {
        userPath.moveTo(userX, userY);
        nationalPath.moveTo(nationalX, nationalY);
      } else {
        userPath.lineTo(userX, userY);
        nationalPath.lineTo(nationalX, nationalY);
      }
    }

    userPath.close();
    nationalPath.close();

    // Draw national average fill
    final nationalFillPaint = Paint()
      ..color = nationalColor.withOpacity(0.1)
      ..style = PaintingStyle.fill;
    canvas.drawPath(nationalPath, nationalFillPaint);

    // Draw user fill
    final userFillPaint = Paint()
      ..color = userColor.withOpacity(0.2)
      ..style = PaintingStyle.fill;
    canvas.drawPath(userPath, userFillPaint);

    // Draw national outline
    final nationalStrokePaint = Paint()
      ..color = nationalColor.withOpacity(0.5)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2;
    canvas.drawPath(nationalPath, nationalStrokePaint);

    // Draw user outline
    final userStrokePaint = Paint()
      ..color = userColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2;
    canvas.drawPath(userPath, userStrokePaint);

    // Draw points
    for (int i = 0; i < n; i++) {
      final angle = -3.14159 / 2 + (2 * 3.14159 * i / n);
      final userR = radius * subjects[i].masteryLevel;
      final userX = center.dx + userR * _cos(angle);
      final userY = center.dy + userR * _sin(angle);

      canvas.drawCircle(
        Offset(userX, userY),
        4,
        Paint()..color = userColor,
      );
    }
  }

  double _cos(double angle) => angle == -3.14159 / 2 ? 0 :
    (angle > -3.14159 / 2 && angle < 3.14159 / 2) ?
      (1 - ((angle + 3.14159 / 2) / 3.14159).abs()) :
      -(1 - ((angle - 3.14159 / 2).abs() / 3.14159));

  double _sin(double angle) => angle == -3.14159 / 2 ? -1 :
    angle == 3.14159 / 2 ? 1 :
    (angle > 0 ? 1 : -1) * (angle.abs() / 3.14159);

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
