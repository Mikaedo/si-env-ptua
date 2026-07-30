import 'package:flutter/material.dart';
import '../../core/constants.dart';

class AppButton extends StatelessWidget {
  final String text;
  final VoidCallback onPressed;
  final bool isLoading;
  final bool isSecondary;
  final IconData? icon;

  const AppButton({
    super.key,
    required this.text,
    required this.onPressed,
    this.isLoading = false,
    this.isSecondary = false,
    this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      height: 56,
      decoration: BoxDecoration(
        color: isSecondary ? kWhite : kBlue,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          if (!isSecondary)
            BoxShadow(
              color: kBlue.withOpacity(0.25),
              blurRadius: 16,
              offset: const Offset(0, 8),
            ),
          if (isSecondary)
            BoxShadow(
              color: kGray200,
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
        ],
        border: isSecondary ? Border.all(color: kGray200) : null,
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: isLoading ? null : onPressed,
          child: Center(
            child: isLoading
                ? SizedBox(
                    height: 24,
                    width: 24,
                    child: CircularProgressIndicator(
                      color: isSecondary ? kBlue : kWhite,
                      strokeWidth: 2.5,
                    ),
                  )
                : Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      if (icon != null) ...[
                        Icon(
                          icon,
                          color: isSecondary ? kGray800 : kWhite,
                          size: 20,
                        ),
                        const SizedBox(width: 8),
                      ],
                      Text(
                        text,
                        style: TextStyle(
                          color: isSecondary ? kGray800 : kWhite,
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
          ),
        ),
      ),
    );
  }
}
