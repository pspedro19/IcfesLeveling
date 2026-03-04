import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/config/routes.dart';
import '../providers/dungeon_provider.dart';
import '../widgets/pre_battle_dialog.dart';
import '../../domain/entities/dungeon_gate.dart';
import '../../domain/entities/dungeon_node.dart';

class DungeonMapPage extends ConsumerStatefulWidget {
  const DungeonMapPage({super.key});

  @override
  ConsumerState<DungeonMapPage> createState() => _DungeonMapPageState();
}

class _DungeonMapPageState extends ConsumerState<DungeonMapPage> {
  @override
  void initState() {
    super.initState();
    // Load gates and check for current run when page initializes
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(dungeonNotifierProvider.notifier).loadGates();
      ref.read(dungeonNotifierProvider.notifier).checkCurrentRun();
    });
  }

  @override
  Widget build(BuildContext context) {
    final dungeonState = ref.watch(dungeonNotifierProvider);
    final nodes = dungeonState.nodes;
    final gate = dungeonState.currentGate;
    final isLoading = dungeonState.isLoading;
    final error = dungeonState.error;

    // Show loading state
    if (isLoading && nodes.isEmpty) {
      return Scaffold(
        backgroundColor: const Color(0xFF0F172A),
        body: const Center(
          child: CircularProgressIndicator(color: Colors.blue),
        ),
      );
    }

    // Show error state
    if (error != null && nodes.isEmpty) {
      return Scaffold(
        backgroundColor: const Color(0xFF0F172A),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, color: Colors.red, size: 48),
              const SizedBox(height: 16),
              Text(
                error,
                style: const TextStyle(color: Colors.white),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () {
                  ref.read(dungeonNotifierProvider.notifier).clearError();
                  ref.read(dungeonNotifierProvider.notifier).loadGates();
                },
                child: const Text('Reintentar'),
              ),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      backgroundColor: const Color(0xFF0F172A), // Dark blue/slate background
      body: Stack(
        children: [
          // Background Image
          Positioned.fill(
            child: Image.asset(
              'assets/images/map_${gate?.theme ?? 'default'}.png', // Use 'default' if gate or theme is null
              fit: BoxFit.cover,
              color: const Color(0xFF0F172A).withOpacity(0.5), // Lighter tint
              colorBlendMode: BlendMode.darken,
              errorBuilder: (context, error, stackTrace) {
                return Container(
                  color: const Color(0xFF0F172A),
                  child: const Center(child: Icon(Icons.map, size: 50, color: Colors.white24)),
                );
              },
            ),
          ),

          // Content
          SafeArea(
            child: Column(
              children: [
                // Header
                if (gate != null) _MapHeader(gate: gate),

                // Map Area
                Expanded(
                  child: Center(
                    child: nodes.isEmpty
                        ? const Text(
                            'No dungeon active',
                            style: TextStyle(color: Colors.white54),
                          )
                        : SizedBox(
                            width: 300,
                            height: 500,
                            child: Stack(
                              children: [
                                // Connection Lines
                                CustomPaint(
                                  size: const Size(300, 500),
                                  painter: DungeonPathPainter(nodes: nodes),
                                ),

                                // Nodes
                                ...List.generate(nodes.length, (index) {
                                  return Positioned(
                                    left: _getNodePosition(index).dx,
                                    top: _getNodePosition(index).dy,
                                    child: _DungeonNodeWidget(
                                      node: nodes[index],
                                      onTap: () {
                                        if (!nodes[index].isLocked) {
                                          showDialog(
                                            context: context,
                                            builder: (context) => PreBattleDialog(node: nodes[index]),
                                          );
                                        }
                                      },
                                    ),
                                  );
                                }),
                              ],
                            ),
                          ),
                  ),
                ),
              ],
            ),
          ),

          // Back Button
          Positioned(
            top: 50,
            left: 16,
            child: IconButton(
              icon: const Icon(Icons.arrow_back_ios, color: Colors.white),
              onPressed: () => context.pop(),
            ),
          ),

          // Loading overlay
          if (isLoading)
            Positioned.fill(
              child: Container(
                color: Colors.black54,
                child: const Center(
                  child: CircularProgressIndicator(color: Colors.blue),
                ),
              ),
            ),
        ],
      ),
    );
  }

  // Hardcoded positions for the S-shape path
  Offset _getNodePosition(int index) {
    const positions = [
      Offset(125, 420), // Start (Bottom)
      Offset(50, 320),  // Left
      Offset(200, 220), // Right
      Offset(50, 120),  // Left
      Offset(125, 20),  // Boss (Top)
    ];
    return positions[index];
  }
}

class _MapHeader extends StatelessWidget {
  final DungeonGate gate;
  const _MapHeader({required this.gate});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.3),
        borderRadius: const BorderRadius.vertical(bottom: Radius.circular(24)),
        border: Border(bottom: BorderSide(color: Colors.white.withOpacity(0.1))),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    gate.name.toUpperCase(),
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                      letterSpacing: 1.2,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: Colors.blue.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(4),
                          border: Border.all(color: Colors.blue.withOpacity(0.5)),
                        ),
                        child: Text(
                          "RANK ${gate.difficultyRank}",
                          style: const TextStyle(color: Colors.blue, fontSize: 10, fontWeight: FontWeight.bold),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Icon(Icons.timer_outlined, color: Colors.white.withOpacity(0.5), size: 14),
                      const SizedBox(width: 4),
                      Text(
                        "${gate.timeLimitMinutes} min",
                        style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 12),
                      ),
                    ],
                  ),
                ],
              ),
              CircularProgressIndicator(
                value: gate.completionPercentage,
                backgroundColor: Colors.white10,
                color: Colors.green,
              ),
            ],
          ),
        ],
      ),
    ).animate().slideY(begin: -0.5, duration: 600.ms, curve: Curves.easeOut);
  }
}

class _DungeonNodeWidget extends StatelessWidget {
  final DungeonNode node;
  final VoidCallback onTap;

  const _DungeonNodeWidget({required this.node, required this.onTap});

  @override
  Widget build(BuildContext context) {
    Color nodeColor;
    IconData nodeIcon;
    double scale = 1.0;

    if (node.type == 'boss') {
      nodeColor = Colors.red;
      nodeIcon = Icons.whatshot;
      scale = 1.3;
    } else if (node.type == 'treasure') {
      nodeColor = Colors.amber;
      nodeIcon = Icons.inventory_2;
    } else {
      nodeColor = Colors.blue;
      nodeIcon = Icons.shield;
    }

    if (node.isLocked) {
      nodeColor = Colors.grey;
      nodeIcon = Icons.lock;
    }

    return GestureDetector(
      onTap: onTap,
      child: Column(
        children: [
          // The Circle Node
          Container(
            width: 50 * scale,
            height: 50 * scale,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: const Color(0xFF1E293B),
              border: Border.all(
                color: node.isCurrent 
                    ? Colors.white 
                    : (node.isLocked ? Colors.white12 : nodeColor),
                width: node.isCurrent ? 3 : 2,
              ),
              boxShadow: node.isCurrent || (!node.isLocked && !node.isCompleted)
                  ? [
                      BoxShadow(
                        color: nodeColor.withOpacity(0.6),
                        blurRadius: 15,
                        spreadRadius: 2,
                      )
                    ]
                  : [],
            ),
            child: Icon(
              node.isCompleted ? Icons.check : nodeIcon,
              color: node.isLocked ? Colors.white24 : Colors.white,
              size: 24 * scale,
            ),
          ).animate(target: node.isCurrent ? 1 : 0)
           .scaleXY(end: 1.1, duration: 1000.ms, curve: Curves.easeInOut)
           .then().scaleXY(end: 1.0),

          // Stars (if completed)
          if (node.isCompleted)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: List.generate(3, (i) {
                  return Icon(
                    Icons.star,
                    size: 10,
                    color: i < node.stars ? Colors.amber : Colors.grey.withOpacity(0.3),
                  );
                }),
              ),
            ),
            
          // Label for Current
          if (node.isCurrent)
             Container(
               margin: const EdgeInsets.only(top: 4),
               padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
               decoration: BoxDecoration(
                 color: Colors.red,
                 borderRadius: BorderRadius.circular(10),
               ),
               child: const Text(
                 "BATTLE!",
                 style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
               ),
             ).animate().fadeIn().slideY(begin: 0.5),
        ],
      ),
    );
  }
}

class DungeonPathPainter extends CustomPainter {
  final List<DungeonNode> nodes;
  
  DungeonPathPainter({required this.nodes});

  // Helper to match the position logic in the main widget
  Offset _getPos(int index) {
     const positions = [
      Offset(150, 445), // Start (Bottom) - Adjusted for widget center (50/2)
      Offset(75, 345),  // Left
      Offset(225, 245), // Right
      Offset(75, 145),  // Left
      Offset(150, 45),  // Boss (Top)
    ];
    return positions[index];
  }

  @override
  void paint(Canvas canvas, Size size) {
    if (nodes.isEmpty) return;

    final paintCompleted = Paint()
      ..color = Colors.blue.withOpacity(0.5)
      ..strokeWidth = 4
      ..style = PaintingStyle.stroke;
      
    final paintLocked = Paint()
      ..color = Colors.grey.withOpacity(0.2)
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    for (int i = 0; i < nodes.length - 1; i++) {
        final start = _getPos(i);
        final end = _getPos(i + 1);
        
        final isPathUnlocked = nodes[i].isCompleted;
        
        canvas.drawLine(start, end, isPathUnlocked ? paintCompleted : paintLocked);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class GridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white.withOpacity(0.05)
      ..strokeWidth = 1;

    const step = 40.0;
    
    // Vertical lines
    for (double x = 0; x < size.width; x += step) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), paint);
    }
    
    // Horizontal lines
    for (double y = 0; y < size.height; y += step) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
