import 'package:flutter/material.dart';

class PtuaLogo extends StatelessWidget {
  final double size;
  final bool withText;

  const PtuaLogo({super.key, this.size = 40, this.withText = false});

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(size * 0.2),
      child: Image.asset(
        'assets/images/ptua_logo.png',
        width: size,
        height: size,
        fit: BoxFit.cover,
        errorBuilder: (context, error, child) => Container(
          width: size,
          height: size,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(size * 0.2),
            color: const Color(0xFF1B2A4E),
          ),
          child: Icon(Icons.eco, color: Colors.white, size: size * 0.5),
        ),
      ),
    );
  }
}
