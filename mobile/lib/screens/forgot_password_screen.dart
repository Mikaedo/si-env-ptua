import 'dart:ui';
import 'package:flutter/material.dart';
import '../core/constants.dart';
import '../services/api_service.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen>
    with SingleTickerProviderStateMixin {
  int _step = 0;
  final _emailController = TextEditingController();
  final _codeController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmController = TextEditingController();
  bool _obscurePassword = true;
  bool _obscureConfirm = true;
  bool _loading = false;
  String _errorMsg = '';
  bool _showError = false;
  late AnimationController _animCtrl;
  late Animation<double> _fadeAnim;
  late Animation<Offset> _slideAnim;

  @override
  void initState() {
    super.initState();
    _animCtrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 700));
    _fadeAnim = CurvedAnimation(parent: _animCtrl, curve: Curves.easeOut);
    _slideAnim = Tween<Offset>(
            begin: const Offset(0, 0.15), end: Offset.zero)
        .animate(CurvedAnimation(parent: _animCtrl, curve: Curves.easeOut));
    _animCtrl.forward();
  }

  @override
  void dispose() {
    _animCtrl.dispose();
    _emailController.dispose();
    _codeController.dispose();
    _passwordController.dispose();
    _confirmController.dispose();
    super.dispose();
  }

  void _goToStep(int step) {
    setState(() {
      _step = step;
      _showError = false;
      _errorMsg = '';
    });
    _animCtrl.reset();
    _animCtrl.forward();
  }

  @override
  Widget build(BuildContext context) {
    final screenH = MediaQuery.of(context).size.height;
    return Scaffold(
      resizeToAvoidBottomInset: true,
      body: Stack(
        fit: StackFit.expand,
        children: [
          // Background image (same as login)
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

          // Dark gradient overlay
          Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  Color(0xCC000000),
                  Color(0x33000000),
                  Color(0x33000000),
                  Color(0xCC000000),
                ],
                stops: [0.0, 0.25, 0.70, 1.0],
              ),
            ),
          ),

          // Content
          SafeArea(
            child: SingleChildScrollView(
              physics: const ClampingScrollPhysics(),
              child: SizedBox(
                height: screenH - MediaQuery.of(context).padding.top,
                child: Column(
                  children: [
                    // Top bar with back button
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                      child: Row(
                        children: [
                          IconButton(
                            icon: const Icon(Icons.arrow_back_rounded, color: Colors.white, size: 24),
                            onPressed: () => Navigator.pop(context),
                          ),
                        ],
                      ),
                    ),
                    const Spacer(flex: 1),

                    // Logo + title
                    FadeTransition(
                      opacity: _fadeAnim,
                      child: SlideTransition(
                        position: _slideAnim,
                        child: Column(
                          children: [
                            ClipRRect(
                              borderRadius: BorderRadius.circular(20),
                              child: BackdropFilter(
                                filter: ImageFilter.blur(sigmaX: 12, sigmaY: 12),
                                child: Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 16),
                                  decoration: BoxDecoration(
                                    color: Colors.white.withValues(alpha: 0.05),
                                    borderRadius: BorderRadius.circular(20),
                                    border: Border.all(color: Colors.white.withValues(alpha: 0.15), width: 1.0),
                                  ),
                                  child: Image.asset(
                                    'assets/images/ptua_logo.png',
                                    height: 48,
                                    fit: BoxFit.contain,
                                    errorBuilder: (_, __, ___) => const Icon(Icons.terrain_rounded, color: Colors.white, size: 32),
                                  ),
                                ),
                              ),
                            ),
                            const SizedBox(height: 20),
                            Text(
                              _stepTitle(),
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 28,
                                fontWeight: FontWeight.w800,
                                letterSpacing: 1,
                                height: 1,
                              ),
                            ),
                            const SizedBox(height: 8),
                            Text(
                              _stepSubtitle(),
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                color: Colors.white.withValues(alpha: 0.7),
                                fontSize: 13,
                                fontWeight: FontWeight.w400,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const Spacer(flex: 2),

                    // Glass form card
                    FadeTransition(
                      opacity: _fadeAnim,
                      child: SlideTransition(
                        position: _slideAnim,
                        child: Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 20),
                          child: ClipRRect(
                            borderRadius: BorderRadius.circular(28),
                            child: BackdropFilter(
                              filter: ImageFilter.blur(sigmaX: 8, sigmaY: 8),
                              child: Container(
                                padding: const EdgeInsets.all(28),
                                decoration: BoxDecoration(
                                  color: Colors.white.withValues(alpha: 0.05),
                                  borderRadius: BorderRadius.circular(28),
                                  border: Border.all(color: Colors.white.withValues(alpha: 0.15), width: 1.0),
                                ),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.stretch,
                                  children: [
                                    // Step indicator
                                    Row(
                                      children: List.generate(3, (i) {
                                        final active = i <= _step;
                                        return Expanded(
                                          child: Container(
                                            margin: EdgeInsets.only(right: i < 2 ? 6 : 0),
                                            height: 3,
                                            decoration: BoxDecoration(
                                              color: active ? kOrange : Colors.white.withValues(alpha: 0.15),
                                              borderRadius: BorderRadius.circular(2),
                                            ),
                                          ),
                                        );
                                      }),
                                    ),
                                    const SizedBox(height: 24),

                                    // Error banner
                                    if (_showError && _errorMsg.isNotEmpty) ...[
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                                        margin: const EdgeInsets.only(bottom: 16),
                                        decoration: BoxDecoration(
                                          color: Colors.red.withValues(alpha: 0.25),
                                          borderRadius: BorderRadius.circular(12),
                                          border: Border.all(color: Colors.red.withValues(alpha: 0.5)),
                                        ),
                                        child: Row(children: [
                                          const Icon(Icons.error_outline_rounded, color: Colors.white, size: 18),
                                          const SizedBox(width: 8),
                                          Expanded(child: Text(_errorMsg, style: TextStyle(color: Colors.white.withValues(alpha: 0.9), fontSize: 12, fontWeight: FontWeight.w600))),
                                        ]),
                                      ),
                                    ],

                                    // Step 0: Email
                                    if (_step == 0) ...[
                                      _GlassField(
                                        controller: _emailController,
                                        hint: 'Adresse email',
                                        placeholder: 'nom@ageroute.ci',
                                        icon: Icons.alternate_email_rounded,
                                        keyboardType: TextInputType.emailAddress,
                                      ),
                                      const SizedBox(height: 24),
                                      _buildActionButton(
                                        label: 'Envoyer le code',
                                        icon: Icons.arrow_forward_rounded,
                                        onPressed: () async {
                                          if (_emailController.text.trim().isEmpty) {
                                            setState(() { _showError = true; _errorMsg = 'Veuillez saisir votre email'; });
                                            return;
                                          }
                                          setState(() { _loading = true; _showError = false; });
                                          try {
                                            await ApiService().forgotPassword(_emailController.text.trim());
                                            setState(() => _loading = false);
                                            _goToStep(1);
                                          } catch (e) {
                                            setState(() { _loading = false; _showError = true; _errorMsg = e.toString().replaceFirst('Exception: ', ''); });
                                          }
                                        },
                                      ),
                                    ],

                                    // Step 1: Code
                                    if (_step == 1) ...[
                                      _GlassField(
                                        controller: _codeController,
                                        hint: 'Code de vérification',
                                        placeholder: '000000',
                                        icon: Icons.password_rounded,
                                        keyboardType: TextInputType.number,
                                      ),
                                      const SizedBox(height: 24),
                                      _buildActionButton(
                                        label: 'Vérifier le code',
                                        icon: Icons.arrow_forward_rounded,
                                        onPressed: () async {
                                          if (_codeController.text.trim().length < 4) {
                                            setState(() { _showError = true; _errorMsg = 'Code invalide'; });
                                            return;
                                          }
                                          setState(() { _loading = true; _showError = false; });
                                          try {
                                            await ApiService().verifyCode(_emailController.text.trim(), _codeController.text.trim());
                                            setState(() => _loading = false);
                                            _goToStep(2);
                                          } catch (e) {
                                            setState(() { _loading = false; _showError = true; _errorMsg = 'Code incorrect ou expiré'; });
                                          }
                                        },
                                      ),
                                    ],

                                    // Step 2: New password
                                    if (_step == 2) ...[
                                      _GlassField(
                                        controller: _passwordController,
                                        hint: 'Nouveau mot de passe',
                                        placeholder: 'Min. 8 caractères',
                                        icon: Icons.lock_outline_rounded,
                                        obscure: _obscurePassword,
                                        onToggleObscure: () => setState(() => _obscurePassword = !_obscurePassword),
                                      ),
                                      const SizedBox(height: 14),
                                      _GlassField(
                                        controller: _confirmController,
                                        hint: 'Confirmer le mot de passe',
                                        placeholder: 'Répéter le mot de passe',
                                        icon: Icons.lock_outline_rounded,
                                        obscure: _obscureConfirm,
                                        onToggleObscure: () => setState(() => _obscureConfirm = !_obscureConfirm),
                                      ),
                                      const SizedBox(height: 24),
                                      _buildActionButton(
                                        label: 'Réinitialiser',
                                        icon: Icons.check_rounded,
                                        onPressed: () async {
                                          if (_passwordController.text.length < 8) {
                                            setState(() { _showError = true; _errorMsg = 'Le mot de passe doit contenir au moins 8 caractères'; });
                                            return;
                                          }
                                          if (_passwordController.text != _confirmController.text) {
                                            setState(() { _showError = true; _errorMsg = 'Les mots de passe ne correspondent pas'; });
                                            return;
                                          }
                                          setState(() { _loading = true; _showError = false; });
                                          try {
                                            await ApiService().resetPassword(_emailController.text.trim(), _codeController.text.trim(), _passwordController.text);
                                            setState(() => _loading = false);
                                            if (mounted) {
                                              ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                                                content: Text('Mot de passe réinitialisé avec succès'),
                                                backgroundColor: kBlue,
                                                behavior: SnackBarBehavior.floating,
                                              ));
                                              Navigator.pop(context);
                                            }
                                          } catch (e) {
                                            setState(() { _loading = false; _showError = true; _errorMsg = 'Erreur lors de la réinitialisation'; });
                                          }
                                        },
                                      ),
                                    ],
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
                      style: TextStyle(fontSize: 11, color: Colors.white.withValues(alpha: 0.5), letterSpacing: 1.2),
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

  String _stepTitle() {
    switch (_step) {
      case 0: return 'Récupération';
      case 1: return 'Vérification';
      case 2: return 'Nouveau mot de passe';
      default: return '';
    }
  }

  String _stepSubtitle() {
    switch (_step) {
      case 0: return 'Saisissez votre adresse email professionnel';
      case 1: return 'Un code à 6 chiffres a été envoyé à votre email';
      case 2: return 'Choisissez un nouveau mot de passe sécurisé';
      default: return '';
    }
  }

  Widget _buildActionButton({required String label, required IconData icon, required VoidCallback onPressed}) {
    return SizedBox(
      height: 54,
      child: ElevatedButton(
        onPressed: _loading ? null : onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: kOrange,
          foregroundColor: Colors.white,
          elevation: 0,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        ),
        child: _loading
            ? const SizedBox(height: 22, width: 22, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2.5))
            : Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(label, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, letterSpacing: 0.3)),
                  const SizedBox(width: 10),
                  Icon(icon, size: 20),
                ],
              ),
      ),
    );
  }
}

// ── Glass input field (same as login) ───────────────────────────
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
        Text(hint, style: TextStyle(color: Colors.white.withValues(alpha: 0.75), fontSize: 12, fontWeight: FontWeight.w600, letterSpacing: 0.3)),
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
                hintStyle: TextStyle(color: Colors.white.withValues(alpha: 0.45), fontSize: 13),
                prefixIcon: Icon(icon, color: Colors.white.withValues(alpha: 0.65), size: 20),
                suffixIcon: onToggleObscure != null
                    ? IconButton(
                        icon: Icon(obscure ? Icons.visibility_off_rounded : Icons.visibility_rounded,
                            color: Colors.white.withValues(alpha: 0.65), size: 20),
                        onPressed: onToggleObscure,
                      )
                    : null,
                filled: true,
                fillColor: Colors.white.withValues(alpha: 0.12),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.25), width: 1),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.25), width: 1),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide: const BorderSide(color: kOrange, width: 1.5),
                ),
                contentPadding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
              ),
            ),
          ),
        ),
      ],
    );
  }
}
