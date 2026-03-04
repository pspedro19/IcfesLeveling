import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'dart:math' as math;

/// Visual Skill Tree Widget
/// Displays topics as connected nodes with progressive unlocking and level-up animations
class VisualSkillTree extends StatefulWidget {
  final SkillTreeData treeData;
  final String? selectedSubjectId;
  final Function(SkillTreeNode)? onNodeTap;
  final Function(SkillTreeNode)? onLevelUp;

  const VisualSkillTree({
    super.key,
    required this.treeData,
    this.selectedSubjectId,
    this.onNodeTap,
    this.onLevelUp,
  });

  @override
  State<VisualSkillTree> createState() => _VisualSkillTreeState();
}

class _VisualSkillTreeState extends State<VisualSkillTree>
    with TickerProviderStateMixin {
  late TransformationController _transformController;
  String? _selectedSubject;
  SkillTreeNode? _levelUpNode;

  @override
  void initState() {
    super.initState();
    _transformController = TransformationController();
    _selectedSubject = widget.selectedSubjectId ??
        (widget.treeData.subjects.isNotEmpty ? widget.treeData.subjects.first.id : null);
  }

  @override
  void dispose() {
    _transformController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Subject selector tabs
        _buildSubjectTabs(),
        const SizedBox(height: 16),

        // Stats header
        _buildStatsHeader(),
        const SizedBox(height: 16),

        // Tree visualization
        Expanded(
          child: _buildTreeView(),
        ),

        // Legend
        _buildLegend(),
      ],
    );
  }

  Widget _buildSubjectTabs() {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: widget.treeData.subjects.map((subject) {
          final isSelected = subject.id == _selectedSubject;
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: GestureDetector(
              onTap: () => setState(() => _selectedSubject = subject.id),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: isSelected
                      ? Colors.blue.withOpacity(0.3)
                      : Colors.white.withOpacity(0.05),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: isSelected ? Colors.blue : Colors.white.withOpacity(0.1),
                  ),
                ),
                child: Text(
                  subject.name,
                  style: TextStyle(
                    color: isSelected ? Colors.blue : Colors.white60,
                    fontSize: 12,
                    fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                  ),
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildStatsHeader() {
    final selectedSubject = widget.treeData.subjects
        .where((s) => s.id == _selectedSubject)
        .firstOrNull;

    if (selectedSubject == null) return const SizedBox.shrink();

    final masteredCount = selectedSubject.nodes.where((n) => n.status == 'mastered').length;
    final strongCount = selectedSubject.nodes.where((n) => n.status == 'strong').length;
    final totalNodes = selectedSubject.nodes.length;
    final progress = (masteredCount + strongCount * 0.5) / totalNodes;

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
            icon: Icons.star,
            value: "$masteredCount",
            label: "Dominados",
            color: Colors.amber,
          ),
          _statItem(
            icon: Icons.bolt,
            value: "$strongCount",
            label: "Fuertes",
            color: Colors.green,
          ),
          _statItem(
            icon: Icons.pie_chart,
            value: "${(progress * 100).toInt()}%",
            label: "Progreso",
            color: Colors.blue,
          ),
        ],
      ),
    );
  }

  Widget _statItem({
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
          style: const TextStyle(color: Colors.white38, fontSize: 10),
        ),
      ],
    );
  }

  Widget _buildTreeView() {
    final selectedSubject = widget.treeData.subjects
        .where((s) => s.id == _selectedSubject)
        .firstOrNull;

    if (selectedSubject == null) {
      return const Center(
        child: Text(
          "Selecciona una materia",
          style: TextStyle(color: Colors.white54),
        ),
      );
    }

    return InteractiveViewer(
      transformationController: _transformController,
      minScale: 0.5,
      maxScale: 2.0,
      boundaryMargin: const EdgeInsets.all(100),
      child: CustomPaint(
        painter: _ConnectionsPainter(
          nodes: selectedSubject.nodes,
          connections: selectedSubject.connections,
        ),
        child: Stack(
          children: [
            // Render nodes by tier
            ...selectedSubject.nodes.map((node) => _buildNode(node)),
          ],
        ),
      ),
    );
  }

  Widget _buildNode(SkillTreeNode node) {
    final x = (node.position['x'] ?? 0) * 100.0 + 50;
    final y = (node.position['y'] ?? 0) * 120.0 + 50;
    final isLevelingUp = _levelUpNode?.id == node.id;

    return Positioned(
      left: x,
      top: y,
      child: GestureDetector(
        onTap: () {
          widget.onNodeTap?.call(node);
          if (node.canLevelUp) {
            _showLevelUpAnimation(node);
          } else {
            _showNodeDetails(node);
          }
        },
        child: _SkillNode(
          node: node,
          isLevelingUp: isLevelingUp,
        ),
      ),
    );
  }

  void _showLevelUpAnimation(SkillTreeNode node) {
    setState(() => _levelUpNode = node);
    Future.delayed(const Duration(seconds: 2), () {
      if (mounted) {
        setState(() => _levelUpNode = null);
        widget.onLevelUp?.call(node);
      }
    });
  }

  void _showNodeDetails(SkillTreeNode node) {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF1A1A2E),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => _NodeDetailsSheet(node: node),
    );
  }

  Widget _buildLegend() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _legendItem(Colors.grey.shade800, "Bloqueado"),
          _legendItem(Colors.red, "Debil"),
          _legendItem(Colors.orange, "Aprendiendo"),
          _legendItem(Colors.green, "Fuerte"),
          _legendItem(Colors.amber, "Maestro"),
        ],
      ),
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
            color: color,
            shape: BoxShape.circle,
          ),
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: const TextStyle(color: Colors.white54, fontSize: 10),
        ),
      ],
    );
  }
}


/// Individual skill node widget
class _SkillNode extends StatelessWidget {
  final SkillTreeNode node;
  final bool isLevelingUp;

  const _SkillNode({
    required this.node,
    this.isLevelingUp = false,
  });

  @override
  Widget build(BuildContext context) {
    final color = _getStatusColor(node.status);
    final size = 60.0;

    Widget nodeWidget = Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: color.withOpacity(0.2),
        border: Border.all(color: color, width: 3),
        boxShadow: [
          if (node.isUnlocked)
            BoxShadow(
              color: color.withOpacity(0.4),
              blurRadius: 10,
              spreadRadius: 2,
            ),
        ],
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Icon based on status
          Icon(
            _getStatusIcon(node.status),
            color: color,
            size: 20,
          ),
          const SizedBox(height: 2),
          // Mastery percentage
          Text(
            "${(node.masteryScore * 100).toInt()}%",
            style: TextStyle(
              color: color,
              fontSize: 10,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );

    // Add level-up animation
    if (isLevelingUp) {
      nodeWidget = nodeWidget
          .animate(onPlay: (c) => c.repeat())
          .scale(duration: 200.ms, begin: const Offset(1, 1), end: const Offset(1.2, 1.2))
          .then()
          .scale(duration: 200.ms, begin: const Offset(1.2, 1.2), end: const Offset(1, 1))
          .shimmer(duration: 500.ms, color: Colors.amber);
    }

    // Add can-level-up indicator
    if (node.canLevelUp && !isLevelingUp) {
      nodeWidget = Stack(
        clipBehavior: Clip.none,
        children: [
          nodeWidget,
          Positioned(
            right: -5,
            top: -5,
            child: Container(
              padding: const EdgeInsets.all(4),
              decoration: const BoxDecoration(
                color: Colors.amber,
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.arrow_upward,
                color: Colors.black,
                size: 12,
              ),
            ).animate(onPlay: (c) => c.repeat())
                .scale(duration: 500.ms, begin: const Offset(0.8, 0.8), end: const Offset(1.1, 1.1))
                .then()
                .scale(duration: 500.ms, begin: const Offset(1.1, 1.1), end: const Offset(0.8, 0.8)),
          ),
        ],
      );
    }

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        nodeWidget,
        const SizedBox(height: 4),
        SizedBox(
          width: 70,
          child: Text(
            node.name,
            style: TextStyle(
              color: node.isUnlocked ? Colors.white70 : Colors.white30,
              fontSize: 9,
            ),
            textAlign: TextAlign.center,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }

  Color _getStatusColor(String status) {
    switch (status) {
      case 'mastered':
        return Colors.amber;
      case 'strong':
        return Colors.green;
      case 'learning':
        return Colors.orange;
      case 'weak':
        return Colors.red;
      case 'locked':
      default:
        return Colors.grey.shade700;
    }
  }

  IconData _getStatusIcon(String status) {
    switch (status) {
      case 'mastered':
        return Icons.star;
      case 'strong':
        return Icons.bolt;
      case 'learning':
        return Icons.trending_up;
      case 'weak':
        return Icons.warning;
      case 'locked':
      default:
        return Icons.lock;
    }
  }
}


/// Custom painter for drawing connections between nodes
class _ConnectionsPainter extends CustomPainter {
  final List<SkillTreeNode> nodes;
  final List<SkillTreeConnection> connections;

  _ConnectionsPainter({
    required this.nodes,
    required this.connections,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final nodeMap = {for (var n in nodes) n.id: n};

    for (final conn in connections) {
      final fromNode = nodeMap[conn.fromId];
      final toNode = nodeMap[conn.toId];

      if (fromNode != null && toNode != null) {
        final fromX = (fromNode.position['x'] ?? 0) * 100.0 + 50 + 30;
        final fromY = (fromNode.position['y'] ?? 0) * 120.0 + 50 + 30;
        final toX = (toNode.position['x'] ?? 0) * 100.0 + 50 + 30;
        final toY = (toNode.position['y'] ?? 0) * 120.0 + 50 + 30;

        final isActive = fromNode.isUnlocked && toNode.isUnlocked;

        final paint = Paint()
          ..color = isActive
              ? Colors.blue.withOpacity(0.5)
              : Colors.white.withOpacity(0.1)
          ..strokeWidth = isActive ? 3 : 1
          ..style = PaintingStyle.stroke;

        // Draw curved line
        final path = Path();
        path.moveTo(fromX, fromY);
        path.quadraticBezierTo(
          (fromX + toX) / 2,
          fromY,
          toX,
          toY,
        );

        canvas.drawPath(path, paint);
      }
    }
  }

  @override
  bool shouldRepaint(covariant _ConnectionsPainter oldDelegate) => true;
}


/// Bottom sheet for node details
class _NodeDetailsSheet extends StatelessWidget {
  final SkillTreeNode node;

  const _NodeDetailsSheet({required this.node});

  @override
  Widget build(BuildContext context) {
    final color = _getStatusColor(node.status);

    return Container(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.2),
                  shape: BoxShape.circle,
                ),
                child: Icon(_getStatusIcon(node.status), color: color, size: 24),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      node.name,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      _getStatusLabel(node.status),
                      style: TextStyle(color: color, fontSize: 14),
                    ),
                  ],
                ),
              ),
              Text(
                "${(node.masteryScore * 100).toInt()}%",
                style: TextStyle(
                  color: color,
                  fontSize: 32,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),

          const SizedBox(height: 24),

          // Progress bar
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: LinearProgressIndicator(
              value: node.masteryScore,
              minHeight: 12,
              backgroundColor: Colors.white.withOpacity(0.1),
              valueColor: AlwaysStoppedAnimation(color),
            ),
          ),

          const SizedBox(height: 16),

          // Stats
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _statItem("Preguntas vistas", "${node.questionsSeen}"),
              _statItem("Tier", "${node.tier}"),
            ],
          ),

          const SizedBox(height: 24),

          // Action button
          if (node.isUnlocked)
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () {
                  Navigator.pop(context);
                  // Navigate to practice
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: color,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: const Text(
                  "PRACTICAR",
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _statItem(String label, String value) {
    return Column(
      children: [
        Text(
          value,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          style: const TextStyle(color: Colors.white54, fontSize: 12),
        ),
      ],
    );
  }

  Color _getStatusColor(String status) {
    switch (status) {
      case 'mastered': return Colors.amber;
      case 'strong': return Colors.green;
      case 'learning': return Colors.orange;
      case 'weak': return Colors.red;
      default: return Colors.grey;
    }
  }

  IconData _getStatusIcon(String status) {
    switch (status) {
      case 'mastered': return Icons.star;
      case 'strong': return Icons.bolt;
      case 'learning': return Icons.trending_up;
      case 'weak': return Icons.warning;
      default: return Icons.lock;
    }
  }

  String _getStatusLabel(String status) {
    switch (status) {
      case 'mastered': return 'Dominado';
      case 'strong': return 'Fuerte';
      case 'learning': return 'Aprendiendo';
      case 'weak': return 'Debil';
      default: return 'Bloqueado';
    }
  }
}


// ============================================
// DATA CLASSES
// ============================================

class SkillTreeData {
  final List<SkillTreeSubject> subjects;
  final List<SubjectStats> subjectStats;
  final int totalNodes;
  final int totalMastered;

  const SkillTreeData({
    required this.subjects,
    required this.subjectStats,
    required this.totalNodes,
    required this.totalMastered,
  });

  factory SkillTreeData.fromJson(Map<String, dynamic> json) {
    return SkillTreeData(
      subjects: (json['subjects'] as List? ?? [])
          .map((s) => SkillTreeSubject.fromJson(s))
          .toList(),
      subjectStats: (json['subject_stats'] as List? ?? [])
          .map((s) => SubjectStats.fromJson(s))
          .toList(),
      totalNodes: json['total_nodes'] ?? 0,
      totalMastered: json['total_mastered'] ?? 0,
    );
  }
}

class SkillTreeSubject {
  final String id;
  final String name;
  final List<SkillTreeNode> nodes;
  final List<SkillTreeConnection> connections;

  const SkillTreeSubject({
    required this.id,
    required this.name,
    required this.nodes,
    required this.connections,
  });

  factory SkillTreeSubject.fromJson(Map<String, dynamic> json) {
    return SkillTreeSubject(
      id: json['id'] ?? '',
      name: json['name'] ?? '',
      nodes: (json['nodes'] as List? ?? [])
          .map((n) => SkillTreeNode.fromJson(n))
          .toList(),
      connections: (json['connections'] as List? ?? [])
          .map((c) => SkillTreeConnection.fromJson(c))
          .toList(),
    );
  }
}

class SkillTreeNode {
  final String id;
  final String name;
  final String subjectId;
  final double masteryScore;
  final int questionsSeen;
  final List<String> prerequisites;
  final Map<String, int> position;
  final int tier;
  final String status;
  final bool isUnlocked;
  final bool canLevelUp;

  const SkillTreeNode({
    required this.id,
    required this.name,
    required this.subjectId,
    required this.masteryScore,
    required this.questionsSeen,
    required this.prerequisites,
    required this.position,
    required this.tier,
    required this.status,
    required this.isUnlocked,
    required this.canLevelUp,
  });

  factory SkillTreeNode.fromJson(Map<String, dynamic> json) {
    return SkillTreeNode(
      id: json['id'] ?? '',
      name: json['name'] ?? '',
      subjectId: json['subject_id'] ?? '',
      masteryScore: (json['mastery_score'] ?? 0).toDouble(),
      questionsSeen: json['questions_seen'] ?? 0,
      prerequisites: List<String>.from(json['prerequisites'] ?? []),
      position: Map<String, int>.from(json['position'] ?? {'x': 0, 'y': 0}),
      tier: json['tier'] ?? 1,
      status: json['status'] ?? 'locked',
      isUnlocked: json['is_unlocked'] ?? false,
      canLevelUp: json['can_level_up'] ?? false,
    );
  }
}

class SkillTreeConnection {
  final String fromId;
  final String toId;
  final String type;

  const SkillTreeConnection({
    required this.fromId,
    required this.toId,
    required this.type,
  });

  factory SkillTreeConnection.fromJson(Map<String, dynamic> json) {
    return SkillTreeConnection(
      fromId: json['from'] ?? '',
      toId: json['to'] ?? '',
      type: json['type'] ?? 'prerequisite',
    );
  }
}

class SubjectStats {
  final String subjectId;
  final String subjectName;
  final int totalNodes;
  final int masteredNodes;
  final int strongNodes;
  final double averageMastery;
  final double completionPercentage;

  const SubjectStats({
    required this.subjectId,
    required this.subjectName,
    required this.totalNodes,
    required this.masteredNodes,
    required this.strongNodes,
    required this.averageMastery,
    required this.completionPercentage,
  });

  factory SubjectStats.fromJson(Map<String, dynamic> json) {
    return SubjectStats(
      subjectId: json['subject_id'] ?? '',
      subjectName: json['subject_name'] ?? '',
      totalNodes: json['total_nodes'] ?? 0,
      masteredNodes: json['mastered_nodes'] ?? 0,
      strongNodes: json['strong_nodes'] ?? 0,
      averageMastery: (json['average_mastery'] ?? 0).toDouble(),
      completionPercentage: (json['completion_percentage'] ?? 0).toDouble(),
    );
  }
}
