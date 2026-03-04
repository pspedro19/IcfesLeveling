import 'package:flutter/material.dart';

class TopicMasteryList extends StatelessWidget {
  final List<Map<String, dynamic>> topics;
  const TopicMasteryList({super.key, required this.topics});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: topics.map((topic) => _TopicItem(topic: topic)).toList(),
    );
  }
}

class _TopicItem extends StatelessWidget {
  final Map<String, dynamic> topic;
  const _TopicItem({required this.topic});

  @override
  Widget build(BuildContext context) {
    final double mastery = topic['mastery'] as double;
    final Color color = _getColor(mastery);

    return ListTile(
      contentPadding: EdgeInsets.zero,
      leading: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(color: color.withOpacity(0.1), shape: BoxShape.circle),
        child: Icon(topic['icon'] as IconData, color: color, size: 18),
      ),
      title: Text(topic['name'] as String, style: const TextStyle(color: Colors.white, fontSize: 14)),
      subtitle: LinearProgressIndicator(
        value: mastery,
        backgroundColor: Colors.white10,
        valueColor: AlwaysStoppedAnimation<Color>(color),
        minHeight: 2,
      ),
      trailing: Text("${(mastery * 100).toInt()}%", style: TextStyle(color: color, fontWeight: FontWeight.bold)),
    );
  }

  Color _getColor(double m) {
    if (m >= 0.8) return Colors.green;
    if (m >= 0.5) return Colors.orange;
    return Colors.red;
  }
}
