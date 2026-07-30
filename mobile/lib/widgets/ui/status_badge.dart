import 'package:flutter/material.dart';
import '../../core/constants.dart';

class StatusBadge extends StatelessWidget {
  final String status; // or criticite
  final bool isCriticite;

  const StatusBadge({
    super.key,
    required this.status,
    this.isCriticite = false,
  });

  @override
  Widget build(BuildContext context) {
    Color color;
    String label;

    if (isCriticite) {
      color = kCriticiteColors[status] ?? kGray600;
      label = kCriticiteLabels[status] ?? status;
    } else {
      color = kStatutColors[status] ?? kGray600;
      label = kStatutLabels[status] ?? status;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withOpacity(0.2)),
      ),
      child: Text(
        label.toUpperCase(),
        style: TextStyle(
          color: color,
          fontSize: 10,
          fontWeight: FontWeight.w800,
          letterSpacing: 0.5,
        ),
      ),
    );
  }
}
