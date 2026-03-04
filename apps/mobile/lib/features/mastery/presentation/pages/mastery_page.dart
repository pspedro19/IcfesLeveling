import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../widgets/subject_radar_chart.dart';
import '../widgets/topic_mastery_list.dart';

class MasteryPage extends ConsumerWidget {
  const MasteryPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Text(
          "MAESTRÍA",
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, letterSpacing: 2),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            // Radar Chart Section
            const _RadarChartSection().animate().fadeIn().scale(),
            
            const SizedBox(height: 32),
            
            // Top Weaknesses / Topics
            const Align(
              alignment: Alignment.centerLeft,
              child: Text(
                "TEMAS CLAVE",
                style: TextStyle(color: Colors.white60, fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 2),
              ),
            ),
            const SizedBox(height: 16),
            const TopicMasteryList(topics: [
              {"name": "Álgebra Lineal", "mastery": 0.35, "icon": Icons.functions},
              {"name": "Comprensión Lectora", "mastery": 0.85, "icon": Icons.menu_book},
              {"name": "Termodinámica", "mastery": 0.42, "icon": Icons.science},
            ]),
            
            const SizedBox(height: 32),
            
            // Subject Progress Cards
            const _SubjectProgressList(),
          ],
        ),
      ),
    );
  }
}

class _RadarChartSection extends StatelessWidget {
  const _RadarChartSection();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.02),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.blue.withOpacity(0.2)),
      ),
      child: Column(
        children: [
          const Text(
            "TU PERFIL DE PODER",
            style: TextStyle(color: Colors.blue, fontWeight: FontWeight.bold, letterSpacing: 2, fontSize: 12),
          ),
          const SizedBox(height: 24),
          const SizedBox(
            height: 250,
            child: SubjectRadarChart(
              values: [0.45, 0.62, 0.38, 0.55, 0.70],
              labels: ["MAT", "LIT", "CIEN", "SOC", "ING"],
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            "Cazador de Rango E",
            style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w900, fontStyle: FontStyle.italic),
          ),
        ],
      ),
    );
  }
}

class _SubjectProgressList extends StatelessWidget {
  const _SubjectProgressList();

  @override
  Widget build(BuildContext context) {
    final subjects = [
      {"name": "Matemáticas", "mastery": 0.45, "color": Colors.blue},
      {"name": "Lectura Crítica", "mastery": 0.62, "color": Colors.green},
      {"name": "Ciencias Naturales", "mastery": 0.38, "color": Colors.orange},
      {"name": "Sociales y Ciudadanas", "mastery": 0.55, "color": Colors.purple},
      {"name": "Inglés", "mastery": 0.70, "color": Colors.pink},
    ];

    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: subjects.length,
      itemBuilder: (context, index) {
        final subject = subjects[index];
        return _SubjectCard(
          name: subject["name"] as String,
          mastery: subject["mastery"] as double,
          color: subject["color"] as Color,
        ).animate().fadeIn(delay: (index * 100).ms).slideX(begin: 0.1, end: 0);
      },
    );
  }
}

class _SubjectCard extends StatelessWidget {
  final String name;
  final double mastery;
  final Color color;

  const _SubjectCard({required this.name, required this.mastery, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.03),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.05)),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                name,
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
              ),
              Text(
                "${(mastery * 100).toInt()}%",
                style: TextStyle(color: color, fontWeight: FontWeight.w900, fontSize: 16),
              ),
            ],
          ),
          const SizedBox(height: 12),
          ClipRRect(
            borderRadius: BorderRadius.circular(10),
            child: LinearProgressIndicator(
              value: mastery,
              minHeight: 8,
              backgroundColor: Colors.white.withOpacity(0.05),
              valueColor: AlwaysStoppedAnimation<Color>(color),
            ),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text("Temas Dominados: 12/45", style: TextStyle(color: Colors.white38, fontSize: 10)),
              const Icon(Icons.chevron_right, color: Colors.white24, size: 16),
            ],
          ),
        ],
      ),
    );
  }
}
