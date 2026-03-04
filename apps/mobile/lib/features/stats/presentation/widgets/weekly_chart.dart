import 'package:flutter/material.dart';
import '../../data/models/stats_models.dart';

/// Weekly performance chart
class WeeklyChart extends StatelessWidget {
  final WeeklyPerformance data;
  final String metric; // 'xp', 'questions', 'accuracy'

  const WeeklyChart({
    super.key,
    required this.data,
    this.metric = 'xp',
  });

  @override
  Widget build(BuildContext context) {
    final maxValue = _getMaxValue();

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.03),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                _getTitle(),
                style: const TextStyle(
                  color: Colors.white70,
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1,
                ),
              ),
              Text(
                _getTotalText(),
                style: TextStyle(
                  color: _getColor(),
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          SizedBox(
            height: 120,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: data.days.map((day) {
                final value = _getValue(day);
                final height = maxValue > 0 ? (value / maxValue) * 100 : 0.0;

                return _buildBar(day, height, value);
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBar(DailyStats day, double height, double value) {
    final isToday = _isToday(day.date);
    final color = _getColor();

    return Column(
      mainAxisAlignment: MainAxisAlignment.end,
      children: [
        if (value > 0)
          Text(
            _formatValue(value),
            style: TextStyle(
              color: color.withOpacity(0.8),
              fontSize: 10,
              fontWeight: FontWeight.bold,
            ),
          ),
        const SizedBox(height: 4),
        AnimatedContainer(
          duration: const Duration(milliseconds: 300),
          width: 32,
          height: height.clamp(4, 100),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.bottomCenter,
              end: Alignment.topCenter,
              colors: [
                color.withOpacity(0.4),
                color,
              ],
            ),
            borderRadius: BorderRadius.circular(6),
            border: isToday
                ? Border.all(color: Colors.white, width: 2)
                : null,
            boxShadow: value > 0
                ? [
                    BoxShadow(
                      color: color.withOpacity(0.3),
                      blurRadius: 8,
                      offset: const Offset(0, 2),
                    ),
                  ]
                : null,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          day.dayName,
          style: TextStyle(
            color: isToday ? Colors.white : Colors.grey[600],
            fontSize: 11,
            fontWeight: isToday ? FontWeight.bold : FontWeight.normal,
          ),
        ),
      ],
    );
  }

  double _getMaxValue() {
    double max = 0;
    for (final day in data.days) {
      final value = _getValue(day);
      if (value > max) max = value;
    }
    return max > 0 ? max : 1;
  }

  double _getValue(DailyStats day) {
    switch (metric) {
      case 'xp':
        return day.xp.toDouble();
      case 'questions':
        return day.questions.toDouble();
      case 'accuracy':
        return day.accuracy * 100;
      default:
        return day.xp.toDouble();
    }
  }

  String _getTitle() {
    switch (metric) {
      case 'xp':
        return 'XP SEMANAL';
      case 'questions':
        return 'PREGUNTAS ESTA SEMANA';
      case 'accuracy':
        return 'PRECISION DIARIA';
      default:
        return 'RENDIMIENTO';
    }
  }

  String _getTotalText() {
    switch (metric) {
      case 'xp':
        return '${data.totalXp} XP';
      case 'questions':
        return '${data.totalQuestions} preguntas';
      case 'accuracy':
        return '${(data.averageAccuracy * 100).toInt()}% promedio';
      default:
        return '';
    }
  }

  String _formatValue(double value) {
    if (metric == 'accuracy') {
      return '${value.toInt()}%';
    }
    if (value >= 1000) {
      return '${(value / 1000).toStringAsFixed(1)}k';
    }
    return value.toInt().toString();
  }

  Color _getColor() {
    switch (metric) {
      case 'xp':
        return Colors.purple;
      case 'questions':
        return Colors.blue;
      case 'accuracy':
        return Colors.green;
      default:
        return Colors.blue;
    }
  }

  bool _isToday(DateTime date) {
    final now = DateTime.now();
    return date.year == now.year &&
        date.month == now.month &&
        date.day == now.day;
  }
}

/// Summary stats row
class WeeklyStatsSummary extends StatelessWidget {
  final WeeklyPerformance data;

  const WeeklyStatsSummary({
    super.key,
    required this.data,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _buildStatCard(
            icon: Icons.star,
            value: '${data.totalXp}',
            label: 'XP Ganado',
            color: Colors.purple,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _buildStatCard(
            icon: Icons.check_circle,
            value: '${data.totalQuestions}',
            label: 'Preguntas',
            color: Colors.blue,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _buildStatCard(
            icon: Icons.percent,
            value: '${(data.averageAccuracy * 100).toInt()}%',
            label: 'Precision',
            color: Colors.green,
          ),
        ),
      ],
    );
  }

  Widget _buildStatCard({
    required IconData icon,
    required String value,
    required String label,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Column(
        children: [
          Icon(icon, color: color, size: 24),
          const SizedBox(height: 8),
          Text(
            value,
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.bold,
              fontSize: 18,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            label,
            style: TextStyle(
              color: Colors.grey[500],
              fontSize: 10,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}
