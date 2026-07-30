import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../blocs/auth/auth_bloc.dart';
import '../core/constants.dart';
import 'forgot_password_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen>
    with SingleTickerProviderStateMixin {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscurePassword = true;
  bool _showError = false;
  late AnimationController _animCtrl;
  late Animation<double> _fadeAnim;
  late Animation<Offset> _slideAnim;

  @override
  void initState() {
    super.initState();
    _animCtrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 800));
    _fadeAnim =
        CurvedAnimation(parent: _animCtrl, curve: Curves.easeOut);
    _slideAnim = Tween<Offset>(
            begin: const Offset(0, 0.15), end: Offset.zero)
        .animate(CurvedAnimation(parent: _animCtrl, curve: Curves.easeOut));
    _animCtrl.forward();
  }

  @override
  void dispose() {
    _animCtrl.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final screenH = MediaQuery.of(context).size.height;
    return Scaffold(
      resizeToAvoidBottomInset: true,
      body: Stack(
        fit: StackFit.expand,
        children: [
          // ── Background image ────────────────────────────
          Image.asset(
            'assets/images/login_bg.png',
            fit: BoxFit.cover,
            width: double.infinity,
            height: double.infinity,
            errorBuilder: (_, __, ___) => Container(
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [Color(0xFF001A40), Color(0xFF003A70)],
                ),
              ),
            ),
          ),

          // ── Dark gradient top + bottom only ─────────────
          Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  Color(0xCC000000), // top 80% dark
                  Color(0x33000000), // middle transparent
                  Color(0x33000000),
                  Color(0xCC000000), // bottom dark
                ],
                stops: [0.0, 0.25, 0.70, 1.0],
              ),
            ),
          ),

          // ── Content ─────────────────────────────────────
          SafeArea(
            child: SingleChildScrollView(
              physics: const ClampingScrollPhysics(),
              child: SizedBox(
                height: screenH - MediaQuery.of(context).padding.top,
                child: Column(
                  children: [
                    // Top: logo + title
                    const Spacer(flex: 2),
                    FadeTransition(
                      opacity: _fadeAnim,
                      child: SlideTransition(
                        position: _slideAnim,
                        child: Column(
                          children: [
                            // Logo card (glassmorphism)
                            ClipRRect(
                              borderRadius: BorderRadius.circular(20),
                              child: BackdropFilter(
                                filter: ImageFilter.blur(sigmaX: 12, sigmaY: 12),
                                child: Container(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 28, vertical: 16),
                                  decoration: BoxDecoration(
                                    color: Colors.white.withValues(alpha: 0.05),
                                    borderRadius: BorderRadius.circular(20),
                                    border: Border.all(
                                        color: Colors.white.withValues(alpha: 0.15),
                                        width: 1.0),
                                  ),
                                  child: Image.asset(
                                    'assets/images/ptua_logo.png',
                                    height: 56,
                                    fit: BoxFit.contain,
                                    errorBuilder: (_, __, ___) => const Icon(
                                        Icons.terrain_rounded,
                                        color: Colors.white,
                                        size: 40),
                                  ),
                                ),
                              ),
                            ),
                            const SizedBox(height: 24),
                            const Text(
                              'SI-ENV',
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: 40,
                                fontWeight: FontWeight.w800,
                                letterSpacing: 2,
                                height: 1,
                              ),
                            ),
                            const SizedBox(height: 8),
                            Text(
                              'Suivi environnemental des chantiers',
                              style: TextStyle(
                                color: Colors.white.withValues(alpha: 0.85),
                                fontSize: 13,
                                fontWeight: FontWeight.w400,
                                letterSpacing: 0.3,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const Spacer(flex: 2),

                    // ── Glass form card ──────────────────────
                    FadeTransition(
                      opacity: _fadeAnim,
                      child: SlideTransition(
                        position: _slideAnim,
                        child: Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 20),
                          child: ClipRRect(
                            borderRadius: BorderRadius.circular(28),
                            child: BackdropFilter(
                              filter:
                                  ImageFilter.blur(sigmaX: 8, sigmaY: 8),
                              child: Container(
                                padding: const EdgeInsets.all(28),
                                decoration: BoxDecoration(
                                  color:
                                      Colors.white.withValues(alpha: 0.05),
                                  borderRadius: BorderRadius.circular(28),
                                  border: Border.all(
                                      color: Colors.white
                                          .withValues(alpha: 0.15),
                                      width: 1.0),
                                ),
                                child: Column(
                                  crossAxisAlignment:
                                      CrossAxisAlignment.stretch,
                                  children: [
                                    // Title
                                    const Text(
                                      'Connexion',
                                      style: TextStyle(
                                        color: Colors.white,
                                        fontSize: 22,
                                        fontWeight: FontWeight.w800,
                                      ),
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      'Accédez à votre espace de travail',
                                      style: TextStyle(
                                        color: Colors.white
                                            .withValues(alpha: 0.7),
                                        fontSize: 13,
                                      ),
                                    ),
                                    const SizedBox(height: 24),

                                    // Error banner
                                    if (_showError) ...[
                                      Container(
                                        padding: const EdgeInsets.symmetric(
                                            horizontal: 14, vertical: 10),
                                        margin: const EdgeInsets.only(
                                            bottom: 16),
                                        decoration: BoxDecoration(
                                          color: Colors.red
                                              .withValues(alpha: 0.25),
                                          borderRadius:
                                              BorderRadius.circular(12),
                                          border: Border.all(
                                              color: Colors.red
                                                  .withValues(alpha: 0.5)),
                                        ),
                                        child: Row(children: [
                                          const Icon(
                                              Icons.error_outline_rounded,
                                              color: Colors.white,
                                              size: 18),
                                          const SizedBox(width: 8),
                                          Expanded(
                                              child: Text(
                                            'Email ou mot de passe incorrect',
                                            style: TextStyle(
                                                color: Colors.white
                                                    .withValues(alpha: 0.9),
                                                fontSize: 12,
                                                fontWeight: FontWeight.w600),
                                          )),
                                        ]),
                                      ),
                                    ],

                                    // Email field
                                    _GlassField(
                                      controller: _emailController,
                                      hint: 'Adresse email',
                                      placeholder: 'nom@ageroute.ci',
                                      icon: Icons.alternate_email_rounded,
                                      keyboardType:
                                          TextInputType.emailAddress,
                                    ),
                                    const SizedBox(height: 14),

                                    // Password field
                                    _GlassField(
                                      controller: _passwordController,
                                      hint: 'Mot de passe',
                                      placeholder: 'Votre mot de passe',
                                      icon: Icons.lock_outline_rounded,
                                      obscure: _obscurePassword,
                                      onToggleObscure: () => setState(
                                          () => _obscurePassword =
                                              !_obscurePassword),
                                    ),
                                    const SizedBox(height: 28),

                                    // Login button
                                    BlocConsumer<AuthBloc, AuthState>(
                                      listener: (context, state) {
                                        if (state is AuthError) {
                                          setState(() => _showError = true);
                                        }
                                      },
                                      builder: (context, state) {
                                        if (state is AuthLoading) {
                                          return const SizedBox(
                                              height: 54,
                                              child: Center(
                                                  child:
                                                      CircularProgressIndicator(
                                                          color:
                                                              Colors.white)));
                                        }
                                        return SizedBox(
                                          height: 54,
                                          child: ElevatedButton(
                                            onPressed: () {
                                              setState(
                                                  () => _showError = false);
                                              context.read<AuthBloc>().add(
                                                    LoginRequested(
                                                      _emailController.text
                                                          .trim(),
                                                      _passwordController
                                                          .text,
                                                    ),
                                                  );
                                            },
                                            style: ElevatedButton.styleFrom(
                                              backgroundColor: kOrange,
                                              foregroundColor: Colors.white,
                                              elevation: 0,
                                              shape: RoundedRectangleBorder(
                                                borderRadius:
                                                    BorderRadius.circular(14),
                                              ),
                                            ),
                                            child: const Row(
                                              mainAxisAlignment:
                                                  MainAxisAlignment.center,
                                              children: [
                                                Text('Se connecter',
                                                    style: TextStyle(
                                                        fontSize: 16,
                                                        fontWeight:
                                                            FontWeight.w700,
                                                        letterSpacing: 0.3)),
                                                SizedBox(width: 10),
                                                Icon(
                                                    Icons.arrow_forward_rounded,
                                                    size: 20),
                                              ],
                                            ),
                                          ),
                                        );
                                      },
                                    ),

                                    const SizedBox(height: 12),
                                    Center(
                                      child: TextButton(
                                        onPressed: () => Navigator.push(
                                            context,
                                            MaterialPageRoute(
                                                builder: (_) =>
                                                    const ForgotPasswordScreen())),
                                        child: Text(
                                          'Mot de passe oublié ?',
                                          style: TextStyle(
                                              color: Colors.white
                                                  .withValues(alpha: 0.85),
                                              fontSize: 13,
                                              fontWeight: FontWeight.w500),
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),

                    // Footer
                    const SizedBox(height: 24),
                    Text(
                      'AGEROUTE  •  CC-PTUA  •  v1.0',
                      style: TextStyle(
                          fontSize: 11,
                          color: Colors.white.withValues(alpha: 0.5),
                          letterSpacing: 1.2),
                    ),
                    const SizedBox(height: 20),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Glass input field ────────────────────────────────────────
class _GlassField extends StatelessWidget {
  final TextEditingController controller;
  final String hint;
  final String placeholder;
  final IconData icon;
  final bool obscure;
  final VoidCallback? onToggleObscure;
  final TextInputType? keyboardType;

  const _GlassField({
    required this.controller,
    required this.hint,
    required this.placeholder,
    required this.icon,
    this.obscure = false,
    this.onToggleObscure,
    this.keyboardType,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(hint,
            style: TextStyle(
                color: Colors.white.withValues(alpha: 0.75),
                fontSize: 12,
                fontWeight: FontWeight.w600,
                letterSpacing: 0.3)),
        const SizedBox(height: 8),
        ClipRRect(
          borderRadius: BorderRadius.circular(14),
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 8, sigmaY: 8),
            child: TextField(
              controller: controller,
              obscureText: obscure,
              keyboardType: keyboardType,
              style: const TextStyle(color: Colors.white, fontSize: 14),
              decoration: InputDecoration(
                hintText: placeholder,
                hintStyle: TextStyle(
                    color: Colors.white.withValues(alpha: 0.45), fontSize: 13),
                prefixIcon: Icon(icon,
                    color: Colors.white.withValues(alpha: 0.65), size: 20),
                suffixIcon: onToggleObscure != null
                    ? IconButton(
                        icon: Icon(
                            obscure
                                ? Icons.visibility_off_rounded
                                : Icons.visibility_rounded,
                            color: Colors.white.withValues(alpha: 0.65),
                            size: 20),
                        onPressed: onToggleObscure,
                      )
                    : null,
                filled: true,
                fillColor: Colors.white.withValues(alpha: 0.12),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide: BorderSide(
                      color: Colors.white.withValues(alpha: 0.25), width: 1),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide: BorderSide(
                      color: Colors.white.withValues(alpha: 0.25), width: 1),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide:
                      const BorderSide(color: kOrange, width: 1.5),
                ),
                contentPadding: const EdgeInsets.symmetric(
                    vertical: 14, horizontal: 16),
              ),
            ),
          ),
        ),
      ],
    );
  }
}
