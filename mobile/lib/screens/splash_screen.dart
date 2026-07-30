import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../blocs/auth/auth_bloc.dart';
import '../core/constants.dart';
import 'login_screen.dart';
import 'first_login_screen.dart';
import 'main_navigation.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen>
    with TickerProviderStateMixin {
  // ── Controllers ──────────────────────────────
  late final AnimationController _bgController;
  late final AnimationController _logoController;
  late final AnimationController _orbitController;
  late final AnimationController _pulseController;
  late final AnimationController _textController;

  // ── Animations ───────────────────────────────
  late final Animation<double> _logoScale;
  late final Animation<double> _logoFade;
  late final Animation<double> _textFade;
  late final Animation<Offset> _textSlide;
  late final Animation<double> _bgGradient;

  bool _navigated = false;

  @override
  void initState() {
    super.initState();

    // Background gradient shift
    _bgController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 6),
    )..repeat(reverse: true);

    _bgGradient = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _bgController, curve: Curves.easeInOut),
    );

    // Logo appear
    _logoController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    )..forward();

    _logoScale = Tween<double>(begin: 0.4, end: 1.0).animate(
      CurvedAnimation(parent: _logoController, curve: Curves.elasticOut),
    );
    _logoFade = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(
          parent: _logoController,
          curve: const Interval(0, 0.6, curve: Curves.easeIn)),
    );

    // Orbit ring spin (continuous)
    _orbitController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1800),
    )..repeat();

    // Pulse
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat(reverse: true);

    // Text slide up
    _textController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 700),
    );

    _textFade = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _textController, curve: Curves.easeOut),
    );
    _textSlide = Tween<Offset>(
      begin: const Offset(0, 0.4),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _textController, curve: Curves.easeOut));

    Future.delayed(const Duration(milliseconds: 700), () {
      if (mounted) _textController.forward();
    });
  }

  @override
  void dispose() {
    _bgController.dispose();
    _logoController.dispose();
    _orbitController.dispose();
    _pulseController.dispose();
    _textController.dispose();
    super.dispose();
  }

  void _navigate(BuildContext context, AuthState state) {
    if (_navigated) return;
    _navigated = true;
    Future.delayed(const Duration(milliseconds: 2600), () {
      if (!mounted) return;
      final nav = Navigator.of(context);
      if (state is AuthAuthenticated) {
        if (state.premiereConnexion) {
          nav.pushReplacement(_fadeRoute(const FirstLoginScreen()));
        } else {
          nav.pushReplacement(_fadeRoute(const MainNavigation()));
        }
      } else {
        nav.pushReplacement(_fadeRoute(const LoginScreen()));
      }
    });
  }

  PageRoute _fadeRoute(Widget page) => PageRouteBuilder(
        pageBuilder: (_, __, ___) => page,
        transitionDuration: const Duration(milliseconds: 500),
        transitionsBuilder: (_, anim, __, child) =>
            FadeTransition(opacity: anim, child: child),
      );

  @override
  Widget build(BuildContext context) {
    return BlocListener<AuthBloc, AuthState>(
      listener: (context, state) => _navigate(context, state),
      child: AnimatedBuilder(
        animation: _bgGradient,
        builder: (context, child) {
          // Animated dark gradient background
          final t = _bgGradient.value;
          return Scaffold(
            backgroundColor: Colors.black,
            body: SizedBox.expand(
              child: Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      Color.lerp(
                        const Color(0xFF001A40),
                        const Color(0xFF003A70),
                        t,
                      )!,
                      Color.lerp(
                        const Color(0xFF003A70),
                        const Color(0xFF0A0F1E),
                        t,
                      )!,
                      Color.lerp(
                        const Color(0xFF0A0F1E),
                        const Color(0xFF001A40),
                        t,
                      )!,
                    ],
                  ),
                ),
                child: child,
              ),
            ),
          );
        },
        child: Stack(
          children: [
            // ── Decorative background circles ──────────
            Positioned(
              top: -120,
              right: -80,
              child: _DecoBubble(size: 380, color: kBlue.withValues(alpha: 0.08)),
            ),
            Positioned(
              bottom: -100,
              left: -60,
              child: _DecoBubble(size: 300, color: kOrange.withValues(alpha: 0.06)),
            ),
            Positioned(
              top: 200,
              left: -100,
              child: _DecoBubble(size: 240, color: const Color(0xFF004F9F).withValues(alpha: 0.07)),
            ),

            // ── Main content ────────────────────────────
            SafeArea(
              child: SizedBox(
                width: double.infinity,
                child: Column(
                  children: [
                    const Spacer(flex: 2),

                  // ── Logo + Orbit ──────────────────────
                  AnimatedBuilder(
                    animation: Listenable.merge(
                        [_logoScale, _logoFade, _orbitController, _pulseController]),
                    builder: (context, _) {
                      return FadeTransition(
                        opacity: _logoFade,
                        child: ScaleTransition(
                          scale: _logoScale,
                          child: SizedBox(
                            width: 200,
                            height: 200,
                            child: Stack(
                              alignment: Alignment.center,
                              children: [
                                // Outer pulsing ring
                                Transform.scale(
                                  scale: 1.0 + _pulseController.value * 0.06,
                                  child: Container(
                                    width: 180,
                                    height: 180,
                                    decoration: BoxDecoration(
                                      shape: BoxShape.circle,
                                      border: Border.all(
                                        color: kOrange.withValues(alpha: 0.15 + _pulseController.value * 0.1),
                                        width: 1.5,
                                      ),
                                    ),
                                  ),
                                ),

                                // Spinning orbit ring
                                Transform.rotate(
                                  angle: _orbitController.value * 2 * math.pi,
                                  child: CustomPaint(
                                    size: const Size(162, 162),
                                    painter: _OrbitPainter(),
                                  ),
                                ),

                                // Counter-rotating inner ring (slower)
                                Transform.rotate(
                                  angle: -_orbitController.value * 2 * math.pi * 0.6,
                                  child: CustomPaint(
                                    size: const Size(130, 130),
                                    painter: _OrbitPainter(
                                      color: kOrange.withValues(alpha: 0.4),
                                      strokeWidth: 1.5,
                                      dashCount: 12,
                                    ),
                                  ),
                                ),

                                // Logo circle
                                Container(
                                  width: 110,
                                  height: 110,
                                  decoration: BoxDecoration(
                                    shape: BoxShape.circle,
                                    color: Colors.white,
                                    boxShadow: [
                                      BoxShadow(
                                        color: kBlue.withValues(alpha: 0.3),
                                        blurRadius: 30,
                                        spreadRadius: 4,
                                      ),
                                      BoxShadow(
                                        color: kOrange.withValues(alpha: 0.15),
                                        blurRadius: 20,
                                        spreadRadius: 0,
                                      ),
                                    ],
                                  ),
                                  child: ClipOval(
                                    child: Padding(
                                      padding: const EdgeInsets.all(14),
                                      child: Image.asset(
                                        'assets/images/logo.png',
                                        fit: BoxFit.contain,
                                        errorBuilder: (_, __, ___) => const Icon(
                                          Icons.terrain,
                                          size: 48,
                                          color: Color(0xFF004F9F),
                                        ),
                                      ),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      );
                    },
                  ),

                  const SizedBox(height: 40),

                  // ── Texts ────────────────────────────
                  FadeTransition(
                    opacity: _textFade,
                    child: SlideTransition(
                      position: _textSlide,
                      child: Column(
                        children: [
                          const Text(
                            'SI-ENV',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 36,
                              fontWeight: FontWeight.w800,
                              letterSpacing: 2,
                              height: 1.1,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'Plateforme AGEROUTE',
                            style: TextStyle(
                              color: Colors.white.withValues(alpha: 0.7),
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                              letterSpacing: 1.5,
                            ),
                          ),
                          const SizedBox(height: 24),
                          // Orange separator line
                          Container(
                            width: 40,
                            height: 4,
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(2),
                              gradient: const LinearGradient(colors: [
                                Color(0xFFF37021),
                                Color(0xFFFFB347),
                              ]),
                            ),
                          ),
                          const SizedBox(height: 24),
                          Text(
                            'Suivi environnemental des chantiers',
                            style: TextStyle(
                              color: Colors.white.withValues(alpha: 0.8),
                              fontSize: 14,
                              fontWeight: FontWeight.w500,
                              letterSpacing: 0.2,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),

                  const Spacer(flex: 3),

                  // ── Footer ───────────────────────────
                  FadeTransition(
                    opacity: _textFade,
                    child: Padding(
                      padding: const EdgeInsets.only(bottom: 40),
                      child: Column(
                        children: [
                          // Dot loader
                          _DotLoader(controller: _orbitController),
                          const SizedBox(height: 14),
                          Text(
                            'Initialisation du système...',
                            style: TextStyle(
                              color: Colors.white.withValues(alpha: 0.35),
                              fontSize: 11.5,
                              letterSpacing: 0.5,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
             ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────
// Widgets helpers
// ─────────────────────────────────────────────────────────

class _DecoBubble extends StatelessWidget {
  final double size;
  final Color color;
  const _DecoBubble({required this.size, required this.color});

  @override
  Widget build(BuildContext context) => Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: color,
        ),
      );
}

// Orbit ring with dashes
class _OrbitPainter extends CustomPainter {
  final Color color;
  final double strokeWidth;
  final int dashCount;

  const _OrbitPainter({
    this.color = const Color(0x66004F9F),
    this.strokeWidth = 2,
    this.dashCount = 8,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..strokeWidth = strokeWidth
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2;
    const dashAngle = math.pi / 24; // dash length in radians
    final gapAngle = (2 * math.pi / dashCount) - dashAngle;
    double angle = 0;

    for (int i = 0; i < dashCount; i++) {
      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius),
        angle,
        dashAngle,
        false,
        paint,
      );
      angle += dashAngle + gapAngle;
    }
  }

  @override
  bool shouldRepaint(_OrbitPainter old) => false;
}

// Animated 3 dots loader
class _DotLoader extends StatelessWidget {
  final AnimationController controller;
  const _DotLoader({required this.controller});

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: controller,
      builder: (_, __) {
        return Row(
          mainAxisSize: MainAxisSize.min,
          children: List.generate(3, (i) {
            final phase = (controller.value - i * 0.15).clamp(0.0, 1.0);
            final brightness = (math.sin(phase * math.pi)).clamp(0.0, 1.0);
            return Container(
              margin: const EdgeInsets.symmetric(horizontal: 4),
              width: 6,
              height: 6,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: Colors.white.withOpacity(0.2 + brightness * 0.8),
              ),
            );
          }),
        );
      },
    );
  }
}
