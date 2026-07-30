import 'package:flutter/material.dart';
import '../widgets/ptua_logo.dart';
import '../core/constants.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _alertesUrgentes = true;
  bool _vibrer = true;
  bool _son = false;
  bool _gpsAuto = true;
  bool _hautePrecision = true;
  bool _offlineMode = true;
  bool _syncAuto = true;
  bool _wifiOnly = false;
  bool _darkMode = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        titleSpacing: 0,
        title: Row(children: [
          Container(margin: const EdgeInsets.only(right: 12), child: const PtuaLogo(size: 40)),
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('Parametres', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontSize: 17)),
            Text('Preferences de l\'application', style: const TextStyle(fontSize: 11, color: kGray600)),
          ]),
        ]),
      ),
      body: SafeArea(
        child: ListView(padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16), children: [
          _Section(title: 'Donnees', children: [
            _SwitchTile(icon: Icons.cloud_off, title: 'Mode hors-ligne', subtitle: 'Enregistrer localement sans reseau', value: _offlineMode, onChanged: (v) => setState(() => _offlineMode = v)),
            _SwitchTile(icon: Icons.sync, title: 'Synchronisation auto', subtitle: 'Envoyer des que connexion disponible', value: _syncAuto, onChanged: (v) => setState(() => _syncAuto = v)),
            _SwitchTile(icon: Icons.wifi, title: 'Wifi uniquement', subtitle: 'Ne pas utiliser les donnees mobiles', value: _wifiOnly, onChanged: (v) => setState(() => _wifiOnly = v)),
            ListTile(leading: Container(width: 36, height: 36, decoration: BoxDecoration(color: kGray100, borderRadius: BorderRadius.circular(10)), child: const Icon(Icons.cleaning_services, color: kGray800, size: 18)),
              title: const Text('Vider le cache', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
              subtitle: const Text('Supprimer les donnees locales', style: TextStyle(fontSize: 11, color: kGray600)),
              trailing: const Icon(Icons.chevron_right, color: kGray400, size: 20),
              onTap: () {}),
          ]),
          const SizedBox(height: 12),
          _Section(title: 'Localisation', children: [
            _SwitchTile(icon: Icons.gps_fixed, title: 'GPS automatique', subtitle: 'Capturer les coordonnees a la saisie', value: _gpsAuto, onChanged: (v) => setState(() => _gpsAuto = v)),
            _SwitchTile(icon: Icons.my_location, title: 'Haute precision', subtitle: 'Utiliser GPS + reseau', value: _hautePrecision, onChanged: (v) => setState(() => _hautePrecision = v)),
          ]),
          const SizedBox(height: 12),
          _Section(title: 'Notifications', children: [
            _SwitchTile(icon: Icons.notifications, title: 'Alertes urgentes', subtitle: 'Notifier pour criticite elevee', value: _alertesUrgentes, onChanged: (v) => setState(() => _alertesUrgentes = v)),
            _SwitchTile(icon: Icons.vibration, title: 'Vibrer', subtitle: 'Vibration lors des alertes', value: _vibrer, onChanged: (v) => setState(() => _vibrer = v)),
            _SwitchTile(icon: Icons.volume_up, title: 'Son', subtitle: 'Son de notification', value: _son, onChanged: (v) => setState(() => _son = v)),
          ]),
          const SizedBox(height: 12),
          _Section(title: 'Apparence', children: [
            _SwitchTile(icon: Icons.dark_mode, title: 'Theme sombre', subtitle: 'Activer le mode sombre', value: _darkMode, onChanged: (v) => setState(() => _darkMode = v)),
          ]),
          const SizedBox(height: 12),
          _Section(title: 'A propos', children: [
            ListTile(leading: Container(width: 36, height: 36, decoration: BoxDecoration(color: kBlueLight, borderRadius: BorderRadius.circular(10)), child: const Icon(Icons.info, color: kBlue, size: 18)),
              title: const Text('SI-ENV v1.0.0', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
              subtitle: const Text('Suivi Environnemental PTUA', style: TextStyle(fontSize: 11, color: kGray600))),
            ListTile(leading: Container(width: 36, height: 36, decoration: BoxDecoration(color: kGray100, borderRadius: BorderRadius.circular(10)), child: const Icon(Icons.build, color: kGray800, size: 18)),
              title: const Text('Build', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
              subtitle: const Text('2026.07.22', style: TextStyle(fontSize: 11, color: kGray600)),
              trailing: const Icon(Icons.chevron_right, color: kGray400, size: 20)),
            ListTile(leading: Container(width: 36, height: 36, decoration: BoxDecoration(color: kBlueLight, borderRadius: BorderRadius.circular(10)), child: const Icon(Icons.dns, color: kBlue, size: 18)),
              title: const Text('Serveur', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
              subtitle: const Text('api.si-env.ageroute.ci', style: TextStyle(fontSize: 11, color: kGray600)),
              trailing: const Icon(Icons.chevron_right, color: kGray400, size: 20)),
            ListTile(leading: Container(width: 36, height: 36, decoration: BoxDecoration(color: kOrangeLight, borderRadius: BorderRadius.circular(10)), child: const Icon(Icons.update, color: kOrange, size: 18)),
              title: const Text('Mises a jour', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
              subtitle: const Text('Verifier les mises a jour', style: TextStyle(fontSize: 11, color: kGray600)),
              trailing: const Icon(Icons.chevron_right, color: kGray400, size: 20)),
          ]),
        ]),
      ),
    );
  }
}

class _Section extends StatelessWidget {
  final String title;
  final List<Widget> children;
  const _Section({required this.title, required this.children});

  @override
  Widget build(BuildContext context) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Padding(padding: const EdgeInsets.only(left: 4, bottom: 6),
        child: Text(title, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: kGray600))),
      Container(decoration: BoxDecoration(color: kWhite, borderRadius: BorderRadius.circular(16), border: Border.all(color: kGray200, width: 1)),
        child: Column(children: children)),
    ]);
  }
}

class _SwitchTile extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final bool value;
  final ValueChanged<bool> onChanged;
  const _SwitchTile({required this.icon, required this.title, required this.subtitle, required this.value, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return SwitchListTile(
      secondary: Container(width: 36, height: 36, decoration: BoxDecoration(color: kGray100, borderRadius: BorderRadius.circular(10)), child: Icon(icon, color: kGray800, size: 18)),
      title: Text(title, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
      subtitle: Text(subtitle, style: const TextStyle(fontSize: 11, color: kGray600)),
      value: value, onChanged: onChanged, activeTrackColor: kBlueLight, activeThumbColor: kBlue);
  }
}
