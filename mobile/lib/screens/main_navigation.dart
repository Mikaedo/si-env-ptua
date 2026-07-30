import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../core/constants.dart';
import '../services/api_service.dart';
import 'map_screen.dart';
import 'signalements_list_screen.dart';
import 'stats_screen.dart';
import 'profile_screen.dart';

class MainNavigation extends StatefulWidget {
  const MainNavigation({super.key});

  @override
  State<MainNavigation> createState() => _MainNavigationState();
}

class _MainNavigationState extends State<MainNavigation> {
  late final bool _isRespEnv;
  late final bool _isExpert;
  late final bool _canSaisie;
  int _currentIndex = 1;

  @override
  void initState() {
    super.initState();
    _isRespEnv = ApiService().role == 'RESP_ENV';
    _isExpert = ApiService().role == 'EXPERT_HSE';
    _canSaisie = _isRespEnv || _isExpert;
  }

  final _screens = [
    const MapScreen(),
    const SignalementsListScreen(),
    const StatsScreen(),
    const ProfileScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kGray50,
      body: _screens[_currentIndex],
      floatingActionButton: _canSaisie
          ? FloatingActionButton(
              onPressed: () => Navigator.pushNamed(context, '/nouveau-signalement'),
              backgroundColor: kOrange,
              elevation: 8,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              child: const Icon(LucideIcons.plus, color: kWhite, size: 28),
            )
          : null,
      floatingActionButtonLocation: FloatingActionButtonLocation.centerDocked,
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: kWhite,
          boxShadow: const [
            BoxShadow(
              color: kShadowLgColor,
              blurRadius: 24,
              offset: Offset(0, -8),
            ),
          ],
          borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
        ),
        child: SafeArea(
          child: Container(
            height: 72,
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildNavItem(0, LucideIcons.map, 'Carte'),
                _buildNavItem(1, LucideIcons.list, 'Mes signaux'),
                if (_canSaisie) const SizedBox(width: 48), // Space for FAB
                _buildNavItem(2, LucideIcons.barChart2, 'Stats'),
                _buildNavItem(3, LucideIcons.user, 'Profil'),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildNavItem(int index, IconData icon, String label) {
    final isActive = _currentIndex == index;
    return GestureDetector(
      onTap: () => setState(() => _currentIndex = index),
      behavior: HitTestBehavior.opaque,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: isActive ? kBlue.withOpacity(0.1) : Colors.transparent,
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              size: 24,
              color: isActive ? kBlue : kGray400,
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(
                fontSize: 10,
                fontWeight: isActive ? FontWeight.w700 : FontWeight.w500,
                color: isActive ? kBlue : kGray400,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

