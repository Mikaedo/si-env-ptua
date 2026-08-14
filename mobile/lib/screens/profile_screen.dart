import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../blocs/auth/auth_bloc.dart';
import '../core/constants.dart';
import '../services/api_service.dart';
import '../models/models.dart';
import '../widgets/ptua_logo.dart';
import 'change_password_screen.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> with SingleTickerProviderStateMixin {
  Utilisateur? _user;
  bool _loading = true;
  late AnimationController _animCtrl;
  late Animation<double> _fadeAnim;

  @override
  void initState() {
    super.initState();
    _animCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 600));
    _fadeAnim = CurvedAnimation(parent: _animCtrl, curve: Curves.easeOut);
    _loadUser();
  }

  @override
  void dispose() {
    _animCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadUser() async {
    // 1) Affichage immediat depuis le cache local (SharedPreferences) : le
    //    profil apparait sans attendre le reseau, meme en mode offline.
    final cache = await ApiService().profilEnCache();
    if (cache != null && mounted) {
      setState(() { _user = cache; _loading = false; });
      _animCtrl.forward();
    }
    // 2) Rafraichissement silencieux en arriere-plan si le reseau repond.
    try {
      final u = await ApiService().me();
      if (mounted) {
        setState(() { _user = u; _loading = false; });
        if (cache == null) _animCtrl.forward();
      }
    } catch (_) {
      if (mounted && _user == null) setState(() => _loading = false);
    }
  }

  String _avatarInitials() {
    if (_user == null) return '?';
    final parts = _user!.nom.trim().split(' ');
    if (parts.length >= 2) return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
    return _user!.nom.isNotEmpty ? _user!.nom[0].toUpperCase() : '?';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kGray50,
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: kBlue))
          : CustomScrollView(
              slivers: [
                // ─── Hero Header ──────────────────────────────────────────
                SliverAppBar(
                  expandedHeight: 240,
                  pinned: true,
                  backgroundColor: kBlue,
                  elevation: 0,
                  flexibleSpace: FlexibleSpaceBar(
                    collapseMode: CollapseMode.parallax,
                    background: Container(
                      decoration: const BoxDecoration(
                        gradient: LinearGradient(
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                          colors: [kBlue, kBlueDark],
                        ),
                      ),
                      child: SafeArea(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const SizedBox(height: 8),
                            // Logo top
                            Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                const PtuaLogo(size: 20),
                                const SizedBox(width: 6),
                                Text(
                                  'Plateforme AGEROUTE',
                                  style: TextStyle(fontSize: 11, color: kWhite.withValues(alpha: 0.6), letterSpacing: 0.5),
                                ),
                              ],
                            ),
                            const SizedBox(height: 18),
                            // Avatar with initials
                            Container(
                              width: 80, height: 80,
                              decoration: BoxDecoration(
                                color: kWhite.withValues(alpha: 0.15),
                                shape: BoxShape.circle,
                                border: Border.all(color: kWhite.withValues(alpha: 0.4), width: 2.5),
                                boxShadow: [BoxShadow(color: kBlueDark.withValues(alpha: 0.4), blurRadius: 20, offset: const Offset(0, 8))],
                              ),
                              child: Center(
                                child: Text(
                                  _avatarInitials(),
                                  style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w800, color: kWhite),
                                ),
                              ),
                            ),
                            const SizedBox(height: 14),
                            Text(
                              _user?.nom ?? '—',
                              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: kWhite),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              _user != null ? (kRoleOrganizations[_user!.role] ?? 'AGEROUTE') : 'AGEROUTE',
                              style: TextStyle(fontSize: 12, color: kWhite.withValues(alpha: 0.7)),
                            ),
                            const SizedBox(height: 10),
                            if (_user != null)
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 5),
                                decoration: BoxDecoration(
                                  color: kOrange,
                                  borderRadius: BorderRadius.circular(20),
                                  boxShadow: [BoxShadow(color: kOrange.withValues(alpha: 0.3), blurRadius: 8, offset: const Offset(0, 3))],
                                ),
                                child: Text(
                                  kRoleLabels[_user!.role] ?? _user!.role,
                                  style: const TextStyle(color: kWhite, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 0.3),
                                ),
                              ),
                          ],
                        ),
                      ),
                    ),
                  ),
                  title: const Text('Mon profil', style: TextStyle(color: kWhite, fontSize: 16, fontWeight: FontWeight.w700)),
                ),

                // ─── Content ─────────────────────────────────────────────
                SliverToBoxAdapter(
                  child: FadeTransition(
                    opacity: _fadeAnim,
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(16, 20, 16, 32),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // Informations card
                          _SectionLabel(label: 'Informations personnelles'),
                          const SizedBox(height: 10),
                          _InfoCard(children: [
                            _InfoRow(
                              icon: LucideIcons.mail,
                              iconBg: kBlueLight,
                              iconColor: kBlue,
                              label: 'Email',
                              value: _user?.email ?? '—',
                            ),
                            const _CardDivider(),
                            _InfoRow(
                              icon: LucideIcons.user,
                              iconBg: kOrangeLight,
                              iconColor: kOrange,
                              label: 'Nom complet',
                              value: _user?.nom ?? '—',
                            ),
                            const _CardDivider(),
                            _InfoRow(
                              icon: LucideIcons.building2,
                              iconBg: const Color(0xFFE3F2FD),
                              iconColor: const Color(0xFF1565C0),
                              label: 'Direction',
                              value: _user != null ? (kRoleOrganizations[_user!.role] ?? 'CC-PTUA') : '—',
                            ),
                            if (_user?.telephone != null) ...[
                              const _CardDivider(),
                              _InfoRow(
                                icon: LucideIcons.phone,
                                iconBg: const Color(0xFFE8F5E9),
                                iconColor: const Color(0xFF2E7D32),
                                label: 'Téléphone',
                                value: _user!.telephone!,
                              ),
                            ],
                          ]),
                          const SizedBox(height: 22),

                          // Rôle card
                          _SectionLabel(label: 'Rôle & Responsabilité'),
                          const SizedBox(height: 10),
                          _InfoCard(children: [
                            _InfoRow(
                              icon: LucideIcons.shield,
                              iconBg: kBlueLight,
                              iconColor: kBlue,
                              label: 'Fonction',
                              value: _user != null ? (kRoleLabels[_user!.role] ?? _user!.role) : '—',
                            ),
                            const _CardDivider(),
                            _InfoRow(
                              icon: LucideIcons.briefcase,
                              iconBg: const Color(0xFFF3E5F5),
                              iconColor: const Color(0xFF6A1B9A),
                              label: 'Mission',
                              value: _user != null ? (kRoleSubtitles[_user!.role] ?? '—') : '—',
                            ),
                          ]),
                          const SizedBox(height: 22),

                          // Actions card
                          _SectionLabel(label: 'Compte'),
                          const SizedBox(height: 10),
                          _InfoCard(children: [
                            _ActionRow(
                              icon: LucideIcons.lock,
                              iconBg: kBlueLight,
                              iconColor: kBlue,
                              label: 'Changer le mot de passe',
                              subtitle: 'Sécurité du compte',
                              onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ChangePasswordScreen())),
                            ),
                            const _CardDivider(),
                            _ActionRow(
                              icon: LucideIcons.logOut,
                              iconBg: kRedLight,
                              iconColor: kRed,
                              label: 'Déconnexion',
                              subtitle: 'Quitter l\'application',
                              onTap: () => _confirmLogout(context),
                            ),
                          ]),

                          const SizedBox(height: 32),
                          Center(
                            child: Column(children: [
                              const PtuaLogo(size: 28),
                              const SizedBox(height: 6),
                              const Text(
                                'SI-ENV v1.0 · AGEROUTE · CC-PTUA',
                                style: TextStyle(fontSize: 10, color: kGray400, letterSpacing: 0.5),
                              ),
                            ]),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
    );
  }

  void _confirmLogout(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: kWhite,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (ctx) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(24, 20, 24, 16),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Container(
              width: 56, height: 56,
              decoration: BoxDecoration(color: kRedLight, borderRadius: BorderRadius.circular(18)),
              child: const Icon(LucideIcons.logOut, color: kRed, size: 26),
            ),
            const SizedBox(height: 16),
            const Text('Se déconnecter ?', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: kGray800)),
            const SizedBox(height: 8),
            const Text('Vous devrez vous reconnecter pour accéder à l\'application.', textAlign: TextAlign.center, style: TextStyle(fontSize: 13, color: kGray500, height: 1.4)),
            const SizedBox(height: 24),
            Row(children: [
              Expanded(child: OutlinedButton(
                onPressed: () => Navigator.pop(ctx),
                child: const Text('Annuler'),
              )),
              const SizedBox(width: 12),
              Expanded(child: ElevatedButton(
                style: ElevatedButton.styleFrom(backgroundColor: kRed),
                onPressed: () {
                  Navigator.pop(ctx);
                  context.read<AuthBloc>().add(LogoutRequested());
                },
                child: const Text('Déconnexion', style: TextStyle(color: kWhite)),
              )),
            ]),
          ]),
        ),
      ),
    );
  }
}

// ─── UI helpers ──────────────────────────────────────────────────────────────

class _SectionLabel extends StatelessWidget {
  final String label;
  const _SectionLabel({required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(children: [
      Container(width: 3, height: 16, decoration: BoxDecoration(color: kOrange, borderRadius: BorderRadius.circular(4))),
      const SizedBox(width: 8),
      Text(label, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: kGray800)),
    ]);
  }
}

class _InfoCard extends StatelessWidget {
  final List<Widget> children;
  const _InfoCard({required this.children});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: kWhite,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: kGray200, width: 1),
        boxShadow: const [BoxShadow(color: kShadowColor, blurRadius: 10, offset: Offset(0, 2))],
      ),
      child: Column(children: children),
    );
  }
}

class _CardDivider extends StatelessWidget {
  const _CardDivider();

  @override
  Widget build(BuildContext context) {
    return const Divider(height: 1, indent: 64, color: Color(0xFFF1F5F9));
  }
}

class _InfoRow extends StatelessWidget {
  final IconData icon;
  final Color iconBg;
  final Color iconColor;
  final String label;
  final String value;
  const _InfoRow({required this.icon, required this.iconBg, required this.iconColor, required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(children: [
        Container(
          width: 40, height: 40,
          decoration: BoxDecoration(color: iconBg, borderRadius: BorderRadius.circular(12)),
          child: Icon(icon, color: iconColor, size: 20),
        ),
        const SizedBox(width: 14),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(label, style: const TextStyle(fontSize: 11, color: kGray500, fontWeight: FontWeight.w500)),
          const SizedBox(height: 2),
          Text(value, style: const TextStyle(fontSize: 14, color: kGray800, fontWeight: FontWeight.w600)),
        ])),
      ]),
    );
  }
}

class _ActionRow extends StatelessWidget {
  final IconData icon;
  final Color iconBg;
  final Color iconColor;
  final String label;
  final String subtitle;
  final VoidCallback onTap;
  const _ActionRow({required this.icon, required this.iconBg, required this.iconColor, required this.label, required this.subtitle, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(20),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Row(children: [
          Container(
            width: 40, height: 40,
            decoration: BoxDecoration(color: iconBg, borderRadius: BorderRadius.circular(12)),
            child: Icon(icon, color: iconColor, size: 20),
          ),
          const SizedBox(width: 14),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(label, style: const TextStyle(fontSize: 14, color: kGray800, fontWeight: FontWeight.w600)),
            Text(subtitle, style: const TextStyle(fontSize: 11, color: kGray500)),
          ])),
          const Icon(LucideIcons.chevronRight, color: kGray400, size: 18),
        ]),
      ),
    );
  }
}
