import 'package:flutter/material.dart';

// AGEROUTE colors: bleu nuit + orange fonce
const Color kBlue = Color(0xFF004F9F); // Primary AGEROUTE Blue
const Color kBlueDark = Color(0xFF003063);
const Color kBlueLight = Color(0xFFE6EFFF);
const Color kOrange = Color(0xFFF37021); // Accent AGEROUTE Orange
const Color kOrangeLight = Color(0xFFFEF0E8);
const Color kRed = Color(0xFFD32F2F);
const Color kRedLight = Color(0xFFFFEBEE);
const Color kGreen = Color(0xFF2E7D32);
const Color kGreenLight = Color(0xFFE8F5E9);
const Color kGray50 = Color(0xFFF8F9FA); // Very light background
const Color kGray100 = Color(0xFFF1F5F9); // Light surface/input
const Color kGray200 = Color(0xFFE2E8F0);
const Color kGray400 = Color(0xFF94A3B8);
const Color kGray600 = Color(0xFF475569);
const Color kGray800 = Color(0xFF1E293B);
const Color kGray900 = Color(0xFF0F172A);
const Color kGray500 = Color(0xFF64748B); // Dark text
const Color kWhite = Color(0xFFFFFFFF);
const Color kBlack = Color(0xFF0F172A);

const Color kShadowColor = Color(0x0A000000);
const Color kShadowLgColor = Color(0x0C000000);

const String kApiBaseUrl = 'http://127.0.0.1:8000';

const List<String> kChantiers = [
  '4eme Pont',
  'Pont de Bassam · Lot 1',
  'Bd Latrille · Lot 3',
  'Rocade Marcory · Lot 2',
];

const List<String> kNuisanceTypes = [
  'Déchets de chantier',
  'Eaux stagnantes',
  'Poussières',
  'Bruit',
  'Dégradation végétation',
];

const List<String> kCriticites = ['FAIBLE', 'MODERE', 'ELEVE'];

const Map<String, String> kCriticiteLabels = {
  'FAIBLE': 'Faible',
  'MODERE': 'Modéré',
  'ELEVE': 'Élevé',
};

const Map<String, Color> kCriticiteColors = {
  'FAIBLE': Color(0xFF2E7D32),
  'MODERE': kOrange,
  'ELEVE': kRed,
};

const Map<String, String> kStatutLabels = {
  'NOUVEAU': 'Nouveau',
  'EN_TRAITEMENT': 'En cours',
  'CLOTURE': 'Traité',
  'REJETE': 'Rejeté',
  'PENDING_SYNC': 'Synchronisation',
};

const Map<String, Color> kStatutColors = {
  'NOUVEAU': kOrange,
  'EN_TRAITEMENT': Color(0xFF1565C0),
  'CLOTURE': Color(0xFF2E7D32),
  'REJETE': kRed,
  'PENDING_SYNC': Color(0xFF757575),
};

const Map<String, String> kRoleLabels = {
  'RESP_ENV': 'Resp. Environnement',
  'EXPERT_HSE': 'Expert HSE',
  'SPEC_ENV': 'Spéc. Env.',
  'SPEC_PAR': 'Spéc. P.A.R',
  'ADMIN': 'Administrateur',
};

const Map<String, String> kRoleOrganizations = {
  'RESP_ENV': 'Entreprise de travaux',
  'EXPERT_HSE': 'Bureau de Contrôle',
  'SPEC_ENV': 'CC-PTUA • Unité Sauvegardes',
  'SPEC_PAR': 'CC-PTUA • Suivi P.A.R',
  'ADMIN': 'AGEROUTE • Administration',
};

const Map<String, String> kRoleSubtitles = {
  'RESP_ENV': 'Autocontrôle environnemental',
  'EXPERT_HSE': 'Contrôle externe quotidien',
  'SPEC_ENV': 'Suivi environnemental',
  'SPEC_PAR': 'Mécanisme de Gestion des Plaintes',
  'ADMIN': 'Administration système',
};
