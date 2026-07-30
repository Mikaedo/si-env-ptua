import { Component, AfterViewInit, ViewChild, ElementRef, signal, inject, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { Subscription, timer } from 'rxjs';
import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { Signalement, Alerte, Chantier } from '../../core/models';
import { LucideAngularModule, MapPin, AlertTriangle, CheckCircle, Clock, TrendingUp,
  Activity, FileText, Satellite, Filter, Wrench, BarChart2, ChevronRight, Bell } from 'lucide-angular';
import * as L from 'leaflet';
import { NgApexchartsModule, ApexOptions } from 'ng-apexcharts';
import { CustomSelect } from '../../shared/custom-select';
import { Sparkline } from '../../shared/sparkline';

@Component({
  selector: 'app-dashboard',
  imports: [CommonModule, LucideAngularModule, NgApexchartsModule, CustomSelect, Sparkline],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss'
})
export class Dashboard implements OnInit, AfterViewInit, OnDestroy {
  private api = inject(ApiService);
  private auth = inject(AuthService);
  private router = inject(Router);

  readonly MapPin = MapPin;
  readonly AlertTriangle = AlertTriangle;
  readonly CheckCircle = CheckCircle;
  readonly Clock = Clock;
  readonly Filter = Filter;
  readonly Wrench = Wrench;
  readonly BarChart2 = BarChart2;
  readonly ChevronRight = ChevronRight;
  readonly Bell = Bell;

  public statutChartOptions: Partial<ApexOptions> = {};
  public nuisanceChartOptions: Partial<ApexOptions> = {};

  @ViewChild('mapContainer') mapContainer!: ElementRef;

  signalements = signal<Signalement[]>([]);
  alertes = signal<Alerte[]>([]);
  chantiers = signal<Chantier[]>([]);
  loading = signal(true);
  filterChantier = signal('');
  filterCommune = signal('');
  filterPeriode = signal('');
  filterStatut = signal('');

  private map!: L.Map;

  private refreshSub?: Subscription;

  ngOnInit() {
    // Polling en temps réel (toutes les 10 secondes)
    this.refreshSub = timer(0, 10000).subscribe(() => this.loadData());
  }

  ngOnDestroy() {
    if (this.refreshSub) {
      this.refreshSub.unsubscribe();
    }
  }

  ngAfterViewInit() {
    setTimeout(() => this.initMap(), 100);
  }

  private loadData() {
    this.api.getSignalements().subscribe({
      next: (data) => {
        this.signalements.set(data);
        this.loading.set(false);
        this.addMarkers();
        this.initCharts();
      },
      error: () => this.loading.set(false)
    });

    this.api.getAlertes().subscribe({
      next: (data) => this.alertes.set(data),
      error: () => {}
    });

    this.api.getChantiers().subscribe({
      next: (data) => this.chantiers.set(data),
      error: () => {}
    });
  }

  private initCharts() {
    const statStats = this.statutStats;
    this.statutChartOptions = {
      series: statStats.map(s => s.count),
      chart: { type: 'donut', height: 250 },
      labels: statStats.map(s => s.label),
      colors: statStats.map(s => s.color),
      plotOptions: {
        pie: {
          donut: { size: '75%' }
        }
      },
      dataLabels: { enabled: false },
      legend: { show: false }
    };

    const nStats = this.nuisanceStats.slice(0, 5);
    this.nuisanceChartOptions = {
      series: [{ name: 'Nuisances', data: nStats.map(s => s.count) }],
      chart: { type: 'bar', height: 250, toolbar: { show: false } },
      xaxis: { categories: nStats.map(s => s.type) },
      colors: ['#F37021'],
      plotOptions: {
        bar: {
          borderRadius: 4,
          horizontal: true,
        }
      },
      dataLabels: { enabled: false }
    };
  }

  private initMap() {
    if (this.map) return;

    this.map = L.map(this.mapContainer.nativeElement, {
      center: [5.36, -4.02],
      zoom: 11.5,
      zoomControl: true,
      attributionControl: false
    });

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
      subdomains: ['a','b','c','d'],
      attribution: '© OpenStreetMap © CARTO'
    }).addTo(this.map);

    // Fallback: if tiles fail to load, try OSM standard
    setTimeout(() => {
      if (this.map) {
        this.map.invalidateSize();
      }
    }, 200);

    fetch('/assets/zones_ptua.geojson')
      .then(res => res.json())
      .then(data => {
        const projetColors: Record<string, string> = {
          '4EME_PONT': '#E8770E',
          'Y4': '#1B2A4E',
          'LATRILLE': '#7B1FA2',
          'SORTIE_EST': '#00838F',
          'SORTIE_OUEST': '#C62828',
          'ECHANGEURS_CG': '#2E7D32',
        };
        const projetLabels: Record<string, string> = {
          '4EME_PONT': '4e Pont',
          'Y4': 'Rocade Y4',
          'LATRILLE': 'Bd Latrille',
          'SORTIE_EST': 'Sortie Est',
          'SORTIE_OUEST': 'Sortie Ouest',
          'ECHANGEURS_CG': 'Echangeurs CG',
        };
        L.geoJSON(data, {
          style: (feature) => {
            const projet = feature?.properties?.projet;
            const color = projetColors[projet] || '#004F9F';
            return { color: color, weight: 2.5, fillColor: color, fillOpacity: 0.12 };
          },
          onEachFeature: (feature, layer) => {
            const projet = feature?.properties?.projet;
            const label = projetLabels[projet] || feature?.properties?.nom || 'Zone';
            const color = projetColors[projet] || '#004F9F';
            const coords = (feature?.geometry as any)?.coordinates?.[0] as number[][];
            if (coords && coords.length > 0) {
              let sumLat = 0, sumLng = 0;
              for (const c of coords) { sumLat += c[1]; sumLng += c[0]; }
              const center: L.LatLngExpression = [sumLat / coords.length, sumLng / coords.length];
              const labelIcon = L.divIcon({
                html: `<div style="font-size:11px;font-weight:700;color:${color};text-shadow:0 0 4px rgba(0,0,0,0.8),0 1px 3px rgba(0,0,0,0.9);white-space:nowrap;font-family:Inter,sans-serif;">${label}</div>`,
                className: '',
                iconSize: [100, 20],
                iconAnchor: [50, -10]
              });
              L.marker(center, { icon: labelIcon, interactive: false, keyboard: false }).addTo(this.map!);
            }
            layer.bindTooltip(label, { sticky: true, className: 'zone-tooltip' });
          }
        }).addTo(this.map!);
      })
      .catch(err => console.error("Could not load zones:", err));

    this.addMarkers();
  }

  private addMarkers() {
    if (!this.map) return;

    this.map.eachLayer((layer) => {
      if (layer instanceof L.Marker && !(layer as any).options?.interactive === false) this.map.removeLayer(layer);
    });

    const statutColors: Record<string, string> = {
      'NOUVEAU': '#F37021',
      'EN_TRAITEMENT': '#1565C0',
      'CLOTURE': '#16A34A',
      'REJETE': '#D32F2F',
      'PENDING_SYNC': '#757575',
    };

    const criticiteRadius: Record<string, number> = {
      'ELEVE': 22,
      'MODERE': 16,
      'FAIBLE': 12,
    };

    for (const s of this.filteredSignalements) {
      if (!s.geom?.coordinates) continue;
      const [lon, lat] = s.geom.coordinates;
      const color = statutColors[s.statut] ?? '#757575';
      const radius = criticiteRadius[s.criticite] ?? 14;

      const glowRadius = radius + 8;
      const icon = L.divIcon({
        html: `<div style="position:relative; width:${glowRadius * 2}px; height:${glowRadius * 2}px;">
                 <div style="position:absolute; inset:0; border-radius:50%; background:${color}; opacity:0.15; animation: ping 2.5s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>
                 <div style="position:absolute; inset:${glowRadius - radius}px; border-radius:50%;
                   background:radial-gradient(circle at 35% 30%, rgba(255,255,255,0.9) 0%, ${color} 60%, ${color}dd 100%);
                   box-shadow:0 6px 16px rgba(0,0,0,0.5), 0 0 ${radius * 0.5}px ${color}66, inset 0 -3px 6px rgba(0,0,0,0.3), inset 0 2px 4px rgba(255,255,255,0.2);
                   border:1.5px solid rgba(255,255,255,0.4);">
                 </div>
               </div>`,
        className: '',
        iconSize: [glowRadius * 2, glowRadius * 2],
        iconAnchor: [glowRadius, glowRadius]
      });

      const marker = L.marker([lat, lon], { icon }).addTo(this.map);
      const criticiteLabel = s.criticite === 'ELEVE' ? '🔴 Élevée' : s.criticite === 'MODERE' ? '🟠 Modérée' : '🟢 Faible';
      const statutLabel = s.statut === 'EN_TRAITEMENT' ? 'En cours' : s.statut === 'CLOTURE' ? 'Résolu' : s.statut === 'REJETE' ? 'Rejeté' : 'Nouveau';
      marker.bindPopup(`
        <div style="font-family:Inter,sans-serif;min-width:220px;">
          <div style="font-weight:700;font-size:14px;color:#004F9F;margin-bottom:6px;">${s.type_nuisance}</div>
          <div style="font-size:12px;color:#71717A;margin-bottom:8px;">📍 ${s.chantier?.nom ?? 'N/A'} ${s.chantier?.commune ? '· ' + s.chantier.commune : ''}</div>
          ${s.description ? `<div style="font-size:11.5px;color:#52525B;margin-bottom:8px;line-height:1.5;">${s.description}</div>` : ''}
          <div style="display:flex;gap:6px;flex-wrap:wrap;">
            <span style="padding:3px 8px;border-radius:4px;font-size:10px;font-weight:700;background:${color}22;color:${color};">${statutLabel}</span>
            <span style="padding:3px 8px;border-radius:4px;font-size:10px;font-weight:700;background:#F4F4F5;color:#52525B;">${criticiteLabel}</span>
            ${s.criticite_ia ? `<span style="padding:3px 8px;border-radius:4px;font-size:10px;font-weight:700;background:#EEF1F8;color:#004F9F;">IA: ${s.criticite_ia} (${s.confiance_ia}%)</span>` : ''}
          </div>
          <div style="margin-top:8px;font-size:10px;color:#A1A1AA;">${new Date(s.cree_le).toLocaleDateString('fr-FR', { day:'2-digit', month:'short', year:'numeric', hour:'2-digit', minute:'2-digit' })}</div>
          <a href="/signalements/${s.id}" style="display:block;margin-top:8px;padding:6px 12px;background:#004F9F;color:white;border-radius:6px;font-size:11px;font-weight:600;text-align:center;text-decoration:none;">Voir le détail →</a>
        </div>
      `);
    }
  }

  applyFilters() {
    this.addMarkers();
    this.initCharts();
  }

  get filteredSignalements(): Signalement[] {
    const now = Date.now();
    const periodDays = this.filterPeriode() ? Number(this.filterPeriode()) : 0;
    return this.signalements().filter(s => {
      if (this.filterChantier() && s.chantier_id !== Number(this.filterChantier())) return false;
      if (this.filterCommune() && s.chantier?.commune !== this.filterCommune()) return false;
      if (this.filterStatut() && s.statut !== this.filterStatut()) return false;
      if (periodDays && now - new Date(s.cree_le).getTime() > periodDays * 86400000) return false;
      return true;
    });
  }

  get communes(): string[] {
    return [...new Set(this.chantiers().map(c => c.commune).filter((commune): commune is string => !!commune))].sort();
  }

  get totalSignalements(): number {
    return this.filteredSignalements.length;
  }

  get nouveauxCount(): number {
    return this.filteredSignalements.filter(s => s.statut === 'NOUVEAU').length;
  }

  get enCoursCount(): number {
    return this.filteredSignalements.filter(s => s.statut === 'EN_TRAITEMENT').length;
  }

  get cloturesCount(): number {
    return this.filteredSignalements.filter(s => s.statut === 'CLOTURE').length;
  }

  get rejetesCount(): number {
    return this.filteredSignalements.filter(s => s.statut === 'REJETE').length;
  }

  get totalActifs(): number {
    return this.nouveauxCount + this.enCoursCount + this.cloturesCount;
  }

  get alertesCritiques(): number {
    return this.alertes().filter(a => a.niveau === 'CRITIQUE').length;
  }

  get recentSignalements(): Signalement[] {
    return [...this.filteredSignalements]
      .sort((a, b) => new Date(b.cree_le).getTime() - new Date(a.cree_le).getTime())
      .slice(0, 5);
  }

  get nuisanceStats(): { type: string; count: number; pct: number }[] {
    const counts: Record<string, number> = {};
    for (const s of this.filteredSignalements) {
      counts[s.type_nuisance] = (counts[s.type_nuisance] ?? 0) + 1;
    }
    const total = this.filteredSignalements.length || 1;
    return Object.entries(counts)
      .map(([type, count]) => ({ type, count, pct: Math.round((count / total) * 100) }))
      .sort((a, b) => b.count - a.count);
  }

  get statutStats(): { label: string; count: number; color: string }[] {
    return [
      { label: 'Nouveau', count: this.nouveauxCount, color: '#F37021' },
      { label: 'En cours', count: this.enCoursCount, color: '#1565C0' },
      { label: 'Clôturé', count: this.cloturesCount, color: '#16A34A' },
    ];
  }

  get maxStatutCount(): number {
    return Math.max(...this.statutStats.map(s => s.count), 1);
  }

  get tauxResolution(): number {
    if (this.totalActifs === 0) return 0;
    return Math.round((this.cloturesCount / this.totalActifs) * 100);
  }

  goToSignalements() {
    this.router.navigate(['/signalements']);
  }

  goToSignalement(id: number) {
    this.router.navigate(['/signalements', id]);
  }

  formatDate(date: string): string {
    return new Date(date).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' });
  }

  get currentUser() {
    return this.auth.user();
  }

  // ── Options for custom-select ──
  get chantierOptions() {
    return [
      { value: '', label: 'Tous les chantiers' },
      ...this.chantiers().map(c => ({ value: String(c.id), label: c.nom }))
    ];
  }

  get communeOptions() {
    return [
      { value: '', label: 'Toutes les communes' },
      ...this.communes.map(c => ({ value: c, label: c }))
    ];
  }

  get periodeOptions() {
    return [
      { value: '', label: 'Toute la période' },
      { value: '7', label: '7 derniers jours' },
      { value: '30', label: '30 derniers jours' },
      { value: '90', label: 'Ce trimestre' }
    ];
  }

  get statutOptions() {
    return [
      { value: '', label: 'Tous les statuts' },
      { value: 'NOUVEAU', label: 'Nouveau' },
      { value: 'EN_TRAITEMENT', label: 'En traitement' },
      { value: 'CLOTURE', label: 'Résolu' },
      { value: 'REJETE', label: 'Rejeté' }
    ];
  }

  private dailyCounts(days: number, filter?: (s: Signalement) => boolean): number[] {
    const result: number[] = [];
    const now = new Date();
    const all = this.signalements();
    for (let i = days - 1; i >= 0; i--) {
      const day = new Date(now);
      day.setDate(day.getDate() - i);
      day.setHours(0, 0, 0, 0);
      const next = new Date(day);
      next.setDate(next.getDate() + 1);
      const count = all.filter((s: Signalement) => {
        const d = new Date(s.cree_le);
        return d >= day && d < next && (!filter || filter(s));
      }).length;
      result.push(count);
    }
    return result;
  }

  get totalSparkData(): number[] {
    return this.dailyCounts(14);
  }

  get nouveauSparkData(): number[] {
    return this.dailyCounts(14, s => s.statut === 'NOUVEAU');
  }

  get enCoursSparkData(): number[] {
    return this.dailyCounts(14, s => s.statut === 'EN_TRAITEMENT');
  }

  get clotureSparkData(): number[] {
    return this.dailyCounts(14, s => s.statut === 'CLOTURE');
  }
}
