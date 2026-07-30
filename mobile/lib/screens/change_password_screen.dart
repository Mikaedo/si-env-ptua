import 'package:flutter/material.dart';
import '../widgets/ptua_logo.dart';
import '../core/constants.dart';
import '../services/api_service.dart';

class ChangePasswordScreen extends StatefulWidget {
  const ChangePasswordScreen({super.key});

  @override
  State<ChangePasswordScreen> createState() => _ChangePasswordScreenState();
}

class _ChangePasswordScreenState extends State<ChangePasswordScreen> {
  final _oldController = TextEditingController();
  final _newController = TextEditingController();
  final _confirmController = TextEditingController();
  bool _obscure1 = true;
  bool _obscure2 = true;
  bool _obscure3 = true;
  bool _loading = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        titleSpacing: 0,
        title: Row(children: [
          Container(margin: const EdgeInsets.only(right: 12), child: const PtuaLogo(size: 40)),
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Changer mot de passe', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontSize: 17)),
            Text('Modifier votre mot de passe', style: const TextStyle(fontSize: 11, color: kGray600)),
          ]),
        ]),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Container(padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(color: kBlueLight, borderRadius: BorderRadius.circular(16)),
              child: const Text('Saisissez votre mot de passe actuel puis choisissez un nouveau.',
                textAlign: TextAlign.center, style: TextStyle(fontSize: 12, color: kGray600, height: 1.5))),
            const SizedBox(height: 20),
            _InputLabel(label: 'Mot de passe actuel'),
            TextField(controller: _oldController, obscureText: _obscure1,
              decoration: InputDecoration(
                suffixIcon: IconButton(icon: Icon(_obscure1 ? Icons.visibility_off_rounded : Icons.visibility_rounded, color: kGray400, size: 20),
                  onPressed: () => setState(() => _obscure1 = !_obscure1)))),
            const SizedBox(height: 14),
            _InputLabel(label: 'Nouveau mot de passe'),
            TextField(controller: _newController, obscureText: _obscure2,
              decoration: InputDecoration(hintText: 'Min. 8 caracteres',
                suffixIcon: IconButton(icon: Icon(_obscure2 ? Icons.visibility_off_rounded : Icons.visibility_rounded, color: kGray400, size: 20),
                  onPressed: () => setState(() => _obscure2 = !_obscure2)))),
            const Padding(padding: EdgeInsets.only(top: 6, left: 4),
              child: Text('8 caractères min. • 1 majuscule • 1 chiffre • 1 caractère spécial',
                style: TextStyle(fontSize: 10, color: kGray400, height: 1.6))),
            const SizedBox(height: 14),
            _InputLabel(label: 'Confirmer le mot de passe'),
            TextField(controller: _confirmController, obscureText: _obscure3,
              decoration: InputDecoration(
                suffixIcon: IconButton(icon: Icon(_obscure3 ? Icons.visibility_off_rounded : Icons.visibility_rounded, color: kGray400, size: 20),
                  onPressed: () => setState(() => _obscure3 = !_obscure3)))),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () async {
                if (_newController.text != _confirmController.text) {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Les mots de passe ne correspondent pas'), backgroundColor: kRed));
                  return;
                }
                setState(() => _loading = true);
                try {
                  await ApiService().changePassword(_oldController.text, _newController.text);
                  setState(() => _loading = false);
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Mot de passe modifie'), backgroundColor: kBlue));
                    Navigator.pop(context);
                  }
                } catch (e) {
                  setState(() => _loading = false);
                  if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString().replaceFirst('Exception: ', '')), backgroundColor: kRed));
                }
              },
              child: _loading ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: kWhite))
                : const Row(mainAxisAlignment: MainAxisAlignment.center, children: [Icon(Icons.check_rounded, size: 18), SizedBox(width: 8), Text('Changer mon mot de passe')]),
            ),
          ]),
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
