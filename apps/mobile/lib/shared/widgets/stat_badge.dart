import 'package:flutter/material.dart';

/// A small, visually distinct badge widget used to display a numerical or
/// textual statistic alongside an icon.
///
/// [icon] The icon to display on the left side of the badge.
/// [iconColor] The color of the icon.
/// [label] The main text or numerical value to display.
/// [semanticLabel] A semantic description for accessibility purposes.
/// [textColor] Optional color for the label text. If null, uses theme's default.
class StatBadge extends StatelessWidget {
  final IconData icon;
  final Color iconColor;
  final String label;
  final String semanticLabel;
  final Color? textColor;

  const StatBadge({
    super.key,
    required this.icon,
    required this.iconColor,
    required this.label,
    required this.semanticLabel,
    this.textColor,
  });

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: semanticLabel,
      value: label,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          color: Colors.white10,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon, 
              color: iconColor, 
              size: 20,
              semanticLabel: '', // Already covered by Semantics wrapper
            ),
            const SizedBox(width: 6),
            Text(
              label,
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: textColor,
                  ),
            ),
          ],
        ),
      ),
    );
  }
}
