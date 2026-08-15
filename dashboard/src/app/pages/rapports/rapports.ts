import { Component, signal, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/api.service';
import { ToastService } from '../../core/toast.service';
import { Chantier } from '../../core/models';
import { LucideAngularModule, FileText, Download, Calendar, Building2, Info, CheckCircle, MapPin, AlertCircle, Send } from 'lucide-angular';
import { DatePicker } from '../../shared/date-picker';

@Component({
  selector: 'app-rapports',
  imports: [CommonModule, LucideAngularModule, DatePicker],
  templateUrl: './rapports.html',
  styleUrl: './rapports.scss'
})
export class Rapports implements OnInit {
  private api = inject(ApiService);
  private toast = inject(ToastService);

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
        a.download = `rapport_pges_${this.dateDebut()}_${this.dateFin()}.pdf`;
        a.click();
        window.URL.revokeObjectURL(url);
        this.generating.set(false);
        this.toast.success('Rapport PGES généré avec succès');
      },
      error: () => {
        this.error.set('Erreur lors de la génération du rapport');
        this.generating.set(false);
        this.toast.error('Échec de la génération du rapport');
      }
    });
  }
}
