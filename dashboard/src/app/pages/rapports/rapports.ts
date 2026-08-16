import { Component, signal, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { ToastService } from '../../core/toast.service';
import { Chantier, TransmissionRapport } from '../../core/models';
import { LucideAngularModule, FileText, Download, Calendar, Building2, Info, CheckCircle, MapPin, AlertCircle, Send, History, Mail, XCircle } from 'lucide-angular';
import { DatePicker } from '../../shared/date-picker';

@Component({
  selector: 'app-rapports',
  imports: [CommonModule, LucideAngularModule, DatePicker],
  templateUrl: './rapports.html',
  styleUrl: './rapports.scss'
})
export class Rapports implements OnInit {
  private api = inject(ApiService);
  private auth = inject(AuthService);
  private toast = inject(ToastService);

  readonly History = History;
  readonly Mail = Mail;
  readonly XCircle = XCircle;

  // ── Transmission formelle ────────────────────────────────────────────
  // Le téléchargement sert à consulter, la transmission engage l'AGEROUTE
  // devant son régulateur et son bailleur. Les destinataires eux-mêmes n'y
  // ont pas accès : la remise qu'ils reçoivent ne peut pas être produite par
  // eux, sinon la trace n'attesterait plus rien.
  transmissions = signal<TransmissionRapport[]>([]);
  transmission = signal(false);
  emailPersonnalise = signal('');
  afficherHistorique = signal(false);

  get peutTransmettre(): boolean {
    return this.auth.hasRole('SPEC_ENV', 'ADMIN');
  }

  readonly FileText = FileText;
  readonly Download = Download;
  readonly Calendar = Calendar;
  readonly Building2 = Building2;
  readonly Info = Info;
  readonly CheckCircle = CheckCircle;
  readonly MapPin = MapPin;
  readonly AlertCircle = AlertCircle;
  readonly Send = Send;

  chantiers = signal<Chantier[]>([]);
  selectedChantiers = signal<number[]>([]);
  dateDebut = signal('');
  dateFin = signal('');
  generating = signal(false);
  error = signal('');

  entreprises = [
    { value: 'ANDE', label: 'ANDE · Agence Nationale de l\'Environnement' },
    { value: 'BAD', label: 'BAD · Banque Africaine de Développement' },
    { value: 'AGEROUTE', label: 'AGEROUTE · Agence de Gestion des Routes' },
    { value: 'CC-PTUA', label: 'CC-PTUA · Cellule de Coordination du Projet' },
    { value: 'BEIE', label: 'BEIE · Bureau d\'Études d\'Impact Environnemental' },
    { value: 'CSCEC', label: 'CSCEC · China State Construction Engineering' },
    { value: 'SOGEA-SATOM', label: 'SOGEA-SATOM · Entreprise de Travaux' },
    { value: 'COLAS', label: 'COLAS · Entreprise de Travaux' },
  ];
  selectedEntreprise = signal('ANDE');

  // Etat de chargement du referentiel. Sans lui, un echec de l'appel laissait
  // la liste vide et affichait « Aucun chantier disponible », message qui
  // designe une base vide alors que le probleme venait de la requete. La
  // distinction compte : dans un cas il n'y a rien a selectionner, dans
  // l'autre la selection est momentanement inaccessible.
  chargementChantiers = signal(true);
  erreurChantiers = signal('');

  ngOnInit() {
    this.chargerChantiers();
    this.chargerTransmissions();

    const today = new Date();
    const threeMonthsAgo = new Date(today.getFullYear(), today.getMonth() - 3, today.getDate());
    this.dateFin.set(today.toISOString().split('T')[0]);
    this.dateDebut.set(threeMonthsAgo.toISOString().split('T')[0]);
  }

  chargerChantiers() {
    this.chargementChantiers.set(true);
    this.erreurChantiers.set('');
    this.api.getChantiers().subscribe({
      next: (data) => {
        this.chantiers.set(data);
        this.chargementChantiers.set(false);
      },
      error: () => {
        this.chargementChantiers.set(false);
        this.erreurChantiers.set(
          'Le référentiel des chantiers n\'a pas pu être chargé. Vérifiez votre connexion, puis réessayez.'
        );
      }
    });
  }

  toggleChantier(id: number) {
    this.selectedChantiers.update(list =>
      list.includes(id) ? list.filter(c => c !== id) : [...list, id]
    );
  }

  generate() {
    if (this.selectedChantiers().length === 0) {
      this.error.set('Sélectionnez au moins un chantier');
      return;
    }
    if (!this.dateDebut() || !this.dateFin()) {
      this.error.set('Sélectionnez une période');
      return;
    }

    this.generating.set(true);
    this.error.set('');

    this.api.generateRapport(this.selectedChantiers(), this.dateDebut(), this.dateFin(), this.selectedEntreprise()).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `rapport_suivi_environnemental_${this.dateDebut()}_${this.dateFin()}.pdf`;
        a.click();
        window.URL.revokeObjectURL(url);
        this.generating.set(false);
        this.toast.success('Rapport de suivi généré avec succès');
      },
      error: () => {
        this.error.set('Erreur lors de la génération du rapport');
        this.generating.set(false);
        this.toast.error('Échec de la génération du rapport');
      }
    });
  }

  transmettre() {
    if (this.selectedChantiers().length === 0) {
      this.error.set('Sélectionnez au moins un chantier');
      return;
    }
    if (!this.dateDebut() || !this.dateFin()) {
      this.error.set('Sélectionnez une période');
      return;
    }

    const organisme = this.selectedEntreprise();
    const adresse = this.emailPersonnalise().trim();
    const cible = adresse || `l'adresse institutionnelle de ${organisme}`;
    if (!confirm(
      `Adresser le rapport à ${cible} ?\n\n` +
      `Cette remise sera enregistrée à votre nom dans l'historique des transmissions.`
    )) return;

    this.transmission.set(true);
    this.error.set('');

    this.api.transmettreRapport(
      this.selectedChantiers(), this.dateDebut(), this.dateFin(), organisme, adresse
    ).subscribe({
      next: (t) => {
        this.transmission.set(false);
        this.emailPersonnalise.set('');
        this.toast.success(`Rapport transmis à ${t.destinataire_email}`);
        this.chargerTransmissions();
        this.afficherHistorique.set(true);
      },
      error: (e) => {
        this.transmission.set(false);
        const motif = e?.error?.detail ?? 'La transmission a échoué.';
        this.error.set(motif);
        this.toast.error('Échec de la transmission');
        // L'historique est rechargé malgré l'échec : la tentative y figure,
        // et il vaut mieux que l'utilisateur la voie plutôt qu'il la croie
        // perdue et la relance en double.
        this.chargerTransmissions();
      }
    });
  }

  chargerTransmissions() {
    this.api.getTransmissions().subscribe({
      next: (d) => this.transmissions.set(d),
      error: () => {}
    });
  }

  basculerHistorique() {
    const ouvert = !this.afficherHistorique();
    this.afficherHistorique.set(ouvert);
    if (ouvert) this.chargerTransmissions();
  }

  /** Date et heure d'une remise, au format lisible en Côte d'Ivoire. */
  dateTransmission(t: TransmissionRapport): string {
    const d = new Date(t.transmis_le);
    return d.toLocaleDateString('fr-FR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  }

  poidsLisible(t: TransmissionRapport): string {
    const o = t.taille_octets ?? 0;
    return o >= 1024 * 1024
      ? `${(o / (1024 * 1024)).toFixed(1)} Mo`
      : `${Math.max(1, Math.round(o / 1024))} ko`;
  }
}
