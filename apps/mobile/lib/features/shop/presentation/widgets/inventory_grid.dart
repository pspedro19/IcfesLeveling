import 'package:flutter/material.dart';

class InventoryGrid extends StatelessWidget {
  final List<Map<String, dynamic>> items;
  const InventoryGrid({super.key, required this.items});

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) {
      return Container(
        height: 120,
        width: double.infinity,
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.02),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: Colors.white.withOpacity(0.05)),
        ),
        child: const Center(
          child: Text("Inventario vacío", style: TextStyle(color: Colors.white24)),
        ),
      );
    }

    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 4,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
      ),
      itemCount: items.length,
      itemBuilder: (context, index) {
        final item = items[index];
        return _InventorySlot(
          icon: item['icon'] as IconData,
          color: item['color'] as Color,
          count: item['count'] as int,
        );
      },
    );
  }
}

class _InventorySlot extends StatelessWidget {
  final IconData icon;
  final Color color;
  final int count;

  const _InventorySlot({required this.icon, required this.color, required this.count});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.03),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: Stack(
        alignment: Alignment.center,
        children: [
          Icon(icon, color: color, size: 24),
          Positioned(
            bottom: 4,
            right: 4,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
              decoration: BoxDecoration(
                color: Colors.black,
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                "x$count",
                style: const TextStyle(color: Colors.white, fontSize: 8, fontWeight: FontWeight.bold),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
