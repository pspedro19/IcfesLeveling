import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

/// Activity Heatmap Widget - GitHub-style contribution calendar
/// Shows daily activity levels over the past year
class ActivityHeatmap extends ConsumerWidget {
  final Map<String, HeatmapDay> heatmapData;
  final HeatmapStats? stats;
  final int weeks;
  final Function(String date, HeatmapDay data)? onDayTap;

  const ActivityHeatmap({
    super.key,
    required this.heatmapData,
    this.stats,
    this.weeks = 52,
    this.onDayTap,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
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
          // Header with stats
          _buildHeader(context),
          const SizedBox(height: 16),

          // Month labels
          _buildMonthLabels(),
          const SizedBox(height: 8),

          // Heatmap grid
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            reverse: true, // Show most recent on right
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Day labels (Mon, Wed, Fri)
                _buildDayLabels(),
                const SizedBox(width: 8),
                // Heatmap weeks
                _buildHeatmapGrid(context),
              ],
            ),
          ),

          const SizedBox(height: 16),

          // Legend
          _buildLegend(),

          // Stats row
          if (stats != null) ...[
            const SizedBox(height: 16),
            _buildStatsRow(context),
          ],
        ],
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        const Text(
          "ACTIVIDAD",
          style: TextStyle(
            color: Colors.white60,
            fontSize: 12,
            fontWeight: FontWeight.bold,
            letterSpacing: 2,
          ),
        ),
        if (stats != null)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: Colors.green.withOpacity(0.2),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.local_fire_department, color: Colors.orange, size: 14),
                const SizedBox(width: 4),
                Text(
                  "${stats!.currentStreak} dias",
                  style: const TextStyle(
                    color: Colors.orange,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }

  Widget _buildMonthLabels() {
    final now = DateTime.now();
    final months = <String>[];

    for (int i = 11; i >= 0; i--) {
      final month = DateTime(now.year, now.month - i, 1);
      months.add(DateFormat('MMM', 'es').format(month).substring(0, 3));
    }

    return Padding(
      padding: const EdgeInsets.only(left: 28),
      child: Row(
        children: months.map((m) => SizedBox(
          width: (weeks / 12 * 14).toDouble(),
          child: Text(
            m.toUpperCase(),
            style: const TextStyle(
              color: Colors.white38,
              fontSize: 9,
            ),
          ),
        )).toList(),
      ),
    );
  }

  Widget _buildDayLabels() {
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        const SizedBox(height: 0),
        _dayLabel(""),
        _dayLabel("Lun"),
        _dayLabel(""),
        _dayLabel("Mie"),
        _dayLabel(""),
        _dayLabel("Vie"),
        _dayLabel(""),
      ],
    );
  }

  Widget _dayLabel(String text) {
    return SizedBox(
      height: 14,
      child: Text(
        text,
        style: const TextStyle(
          color: Colors.white38,
          fontSize: 9,
        ),
      ),
    );
  }

  Widget _buildHeatmapGrid(BuildContext context) {
    final now = DateTime.now();
    final startDate = now.subtract(Duration(days: weeks * 7));

    // Build weeks
    List<Widget> weekColumns = [];
    DateTime currentDate = startDate;

    // Align to start of week (Monday)
    while (currentDate.weekday != DateTime.monday) {
      currentDate = currentDate.add(const Duration(days: 1));
    }

    while (currentDate.isBefore(now) || currentDate.isAtSameMomentAs(now)) {
      List<Widget> daySquares = [];

      for (int day = 0; day < 7; day++) {
        if (currentDate.isAfter(now)) {
          daySquares.add(_buildEmptyCell());
        } else {
          final dateStr = DateFormat('yyyy-MM-dd').format(currentDate);
          final dayData = heatmapData[dateStr];
          daySquares.add(_buildDayCell(context, dateStr, dayData));
        }
        currentDate = currentDate.add(const Duration(days: 1));
      }

      weekColumns.add(Column(
        mainAxisSize: MainAxisSize.min,
        children: daySquares,
      ));
    }

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: weekColumns,
    );
  }

  Widget _buildDayCell(BuildContext context, String dateStr, HeatmapDay? data) {
    final level = data?.level ?? 0;
    final color = _getLevelColor(level);

    return GestureDetector(
      onTap: () {
        if (onDayTap != null && data != null) {
          onDayTap!(dateStr, data);
        } else {
          _showDayDetails(context, dateStr, data);
        }
      },
      child: Container(
        width: 12,
        height: 12,
        margin: const EdgeInsets.all(1),
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(2),
          border: level > 0
              ? Border.all(color: color.withOpacity(0.8), width: 0.5)
              : null,
        ),
      ),
    );
  }

  Widget _buildEmptyCell() {
    return Container(
      width: 12,
      height: 12,
      margin: const EdgeInsets.all(1),
    );
  }

  Color _getLevelColor(int level) {
    switch (level) {
      case 0:
        return Colors.white.withOpacity(0.05);
      case 1:
        return const Color(0xFF0E4429);
      case 2:
        return const Color(0xFF006D32);
      case 3:
        return const Color(0xFF26A641);
      case 4:
        return const Color(0xFF39D353);
      default:
        return Colors.white.withOpacity(0.05);
    }
  }

  void _showDayDetails(BuildContext context, String dateStr, HeatmapDay? data) {
    final date = DateTime.parse(dateStr);
    final formattedDate = DateFormat('EEEE, d MMMM', 'es').format(date);

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1A1A2E),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Text(
          formattedDate,
          style: const TextStyle(color: Colors.white, fontSize: 16),
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (data != null && data.count > 0) ...[
              Text(
                "${data.count} actividades",
                style: const TextStyle(color: Colors.green, fontSize: 24, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              if (data.breakdown != null) ...[
                ...data.breakdown!.entries.map((e) => Padding(
                  padding: const EdgeInsets.symmetric(vertical: 2),
                  child: Row(
                    children: [
                      Icon(_getActivityIcon(e.key), color: Colors.white54, size: 16),
                      const SizedBox(width: 8),
                      Text(
                        "${_getActivityName(e.key)}: ${e.value}",
                        style: const TextStyle(color: Colors.white70, fontSize: 14),
                      ),
                    ],
                  ),
                )),
              ],
            ] else
              const Text(
                "Sin actividad",
                style: TextStyle(color: Colors.white54, fontSize: 16),
              ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("Cerrar"),
          ),
        ],
      ),
    );
  }

  IconData _getActivityIcon(String type) {
    switch (type) {
      case 'answer':
        return Icons.check_circle;
      case 'diagnostic':
        return Icons.assessment;
      case 'video':
        return Icons.play_circle;
      default:
        return Icons.circle;
    }
  }

  String _getActivityName(String type) {
    switch (type) {
      case 'answer':
        return 'Respuestas';
      case 'diagnostic':
        return 'Diagnosticos';
      case 'video':
        return 'Videos';
      default:
        return type;
    }
  }

  Widget _buildLegend() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.end,
      children: [
        const Text(
          "Menos",
          style: TextStyle(color: Colors.white38, fontSize: 10),
        ),
        const SizedBox(width: 4),
        for (int i = 0; i <= 4; i++)
          Container(
            width: 10,
            height: 10,
            margin: const EdgeInsets.symmetric(horizontal: 1),
            decoration: BoxDecoration(
              color: _getLevelColor(i),
              borderRadius: BorderRadius.circular(2),
            ),
          ),
        const SizedBox(width: 4),
        const Text(
          "Mas",
          style: TextStyle(color: Colors.white38, fontSize: 10),
        ),
      ],
    );
  }

  Widget _buildStatsRow(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceAround,
      children: [
        _buildStatItem(
          icon: Icons.calendar_today,
          value: "${stats!.activeDays}",
          label: "Dias activos",
          color: Colors.green,
        ),
        _buildStatItem(
          icon: Icons.local_fire_department,
          value: "${stats!.maxStreak}",
          label: "Mejor racha",
          color: Colors.orange,
        ),
        _buildStatItem(
          icon: Icons.speed,
          value: "${stats!.avgDailyActivities.toStringAsFixed(1)}",
          label: "Promedio/dia",
          color: Colors.blue,
        ),
      ],
    );
  }

  Widget _buildStatItem({
    required IconData icon,
    required String value,
    required String label,
    required Color color,
  }) {
    return Column(
      children: [
        Icon(icon, color: color, size: 20),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            color: color,
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          style: const TextStyle(
            color: Colors.white38,
            fontSize: 10,
          ),
        ),
      ],
    );
  }
}


/// Data class for a single day in the heatmap
class HeatmapDay {
  final int count;
  final int level;
  final Map<String, int>? breakdown;

  const HeatmapDay({
    required this.count,
    required this.level,
    this.breakdown,
  });

  factory HeatmapDay.fromJson(Map<String, dynamic> json) {
    return HeatmapDay(
      count: json['count'] ?? 0,
      level: json['level'] ?? 0,
      breakdown: json['breakdown'] != null
          ? Map<String, int>.from(json['breakdown'])
          : null,
    );
  }
}


/// Statistics for the heatmap
class HeatmapStats {
  final int totalActivities;
  final int activeDays;
  final int totalDays;
  final double activityRate;
  final int maxStreak;
  final int currentStreak;
  final double avgDailyActivities;

  const HeatmapStats({
    required this.totalActivities,
    required this.activeDays,
    required this.totalDays,
    required this.activityRate,
    required this.maxStreak,
    required this.currentStreak,
    required this.avgDailyActivities,
  });

  factory HeatmapStats.fromJson(Map<String, dynamic> json) {
    return HeatmapStats(
      totalActivities: json['total_activities'] ?? 0,
      activeDays: json['active_days'] ?? 0,
      totalDays: json['total_days'] ?? 365,
      activityRate: (json['activity_rate'] ?? 0).toDouble(),
      maxStreak: json['max_streak'] ?? 0,
      currentStreak: json['current_streak'] ?? 0,
      avgDailyActivities: (json['avg_daily_activities'] ?? 0).toDouble(),
    );
  }
}
