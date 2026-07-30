import 'package:flutter/material.dart';
import '../widgets/ptua_logo.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../blocs/auth/auth_bloc.dart';
import '../core/constants.dart';

class FirstLoginScreen extends StatefulWidget {
  const FirstLoginScreen({super.key});

  @override
  State<FirstLoginScreen> createState() => _FirstLoginScreenState();
}

class _FirstLoginScreenState extends State<FirstLoginScreen> {
  final _nomController = TextEditingController();
  final _telController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmController = TextEditingController();
  bool _obscure1 = true;
  bool _obscure2 = true;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        titleSpacing: 0,
        title: Row(children: [
          Container(margin: const EdgeInsets.only(right: 12), child: const PtuaLogo(size: 40)),
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Bienvenue', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontSize: 17)),
            Text('Complétez votre profil', style: const TextStyle(fontSize: 11, color: kGray600)),
          ]),
        ]),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(color: kBlueLight, borderRadius: BorderRadius.circular(16)),
                child: Column(children: [
                  Container(
                    width: 56, height: 56,
                    decoration: BoxDecoration(borderRadius: BorderRadius.circular(16), gradient: const LinearGradient(colors: [kBlue, kBlueDark])),
                    child: const Icon(Icons.person_add, color: kWhite, size: 28),
                  ),
                  const SizedBox(height: 14),
                  Text(
                    'Votre compte a été créé par l''administrateur. Pour votre première connexion, complétez votre profil et choisissez votre mot de passe.',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ]),
              ),
              const SizedBox(height: 20),
              _InputLabel(label: 'Nom complet'),
              TextField(
                controller: _nomController,
                textCapitalization: TextCapitalization.words,
                decoration: const InputDecoration(
                  hintText: 'Ex : Jean Kouassi',
                  prefixIcon: Icon(Icons.person_outline, color: kGray400, size: 20),
                ),
              ),
              const SizedBox(height: 14),
              _InputLabel(label: 'Téléphone'),
              TextField(
                controller: _telController,
                keyboardType: TextInputType.phone,
                decoration: const InputDecoration(
                  hintText: 'Ex : +225 07 00 00 00',
                  prefixIcon: Icon(Icons.phone_outlined, color: kGray400, size: 20),
                ),
              ),
              const SizedBox(height: 14),
              _InputLabel(label: 'Nouveau mot de passe'),
              TextField(
                controller: _passwordController,
                obscureText: _obscure1,
                decoration: InputDecoration(
                  hintText: 'Min. 8 caractères',
                  suffixIcon: IconButton(
                    icon: Icon(_obscure1 ? Icons.visibility_off : Icons.visibility, color: kGray400, size: 20),
                    onPressed: () => setState(() => _obscure1 = !_obscure1),
                  ),
                ),
              ),
              const Padding(
                padding: EdgeInsets.only(top: 6, left: 4),
                child: Text('8 caractères min. • 1 majuscule • 1 chiffre • 1 caractère spécial',
                  style: TextStyle(fontSize: 10, color: kGray400, height: 1.6)),
              ),
              const SizedBox(height: 14),
              _InputLabel(label: 'Confirmer le mot de passe'),
              TextField(
                controller: _confirmController,
                obscureText: _obscure2,
                decoration: InputDecoration(
                  suffixIcon: IconButton(
                    icon: Icon(_obscure2 ? Icons.visibility_off : Icons.visibility, color: kGray400, size: 20),
                    onPressed: () => setState(() => _obscure2 = !_obscure2),
                  ),
                ),
              ),
              const SizedBox(height: 20),
              BlocConsumer<AuthBloc, AuthState>(
                listener: (context, state) {
                  if (state is AuthError) {
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(state.message), backgroundColor: kRed));
                  }
                },
                builder: (context, state) {
                  if (state is AuthLoading) return const Center(child: CircularProgressIndicator(color: kBlue));
                  return ElevatedButton(
                    onPressed: () {
                      if (_nomController.text.trim().isEmpty) {
                        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Veuillez saisir votre nom complet'), backgroundColor: kRed));
                        return;
                      }
                      if (_passwordController.text != _confirmController.text) {
                        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Les mots de passe ne correspondent pas'), backgroundColor: kRed));
                        return;
                      }
                      context.read<AuthBloc>().add(FirstLoginRequested(
                        _nomController.text.trim(),
                        _telController.text.trim(),
                        _passwordController.text,
                      ));
                    },
                    child: const Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                      Icon(Icons.check, size: 18), SizedBox(width: 8), Text('Définir mon mot de passe'),
                    ]),
                  );
                },
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _InputLabel extends StatelessWidget {
  final String label;
  const _InputLabel({required this.label});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: kGray600)),
    );
  }
}