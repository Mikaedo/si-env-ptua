import {
  Component, signal, inject, OnInit, AfterViewInit,
  ViewChild, ElementRef, OnDestroy, computed
} from '@angular/core';
import { CommonModule, DecimalPipe, DatePipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { AuthService } from '../../core/auth.service';
import {
  LucideAngularModule,
  Satellite as SatelliteIcon, Wind, Droplets, Leaf, CloudRain,
  TrendingUp, TrendingDown, Minus, AlertTriangle,
  CheckCircle, RefreshCw, Info, BarChart2, Map, Calendar, Layers, Activity
} from 'lucide-angular';
import * as L from 'leaflet';

import { environment } from '../../../environments/environment';
const API = environment.apiUrl;

// ─── Types ───────────────────────────────────────────────
interface IndicePoint {
  id: number;
  type_indice: string;
  valeur: number;
  unite: string;
  date_calcule: string;
  chantier?: { id: number; nom: string; commune: string };
  statut: string;
  tendance: string;
  source: string;
}

interface PointSerie {
  mois: string;
  valeur: number;
  phase: 'AVANT' | 'TRAVAUX' | 'APRES';
}

interface SerieTemporelle {
  type_indice: string;
  unite: string;
  description: string;
  chantier: string;
  points: PointSerie[];
}

interface ResumeSatellite {
  no2_moyen: number;
  ndwi_moyen: number;
  ndvi_moyen: number;
  risque_pluie_max: number;
  nb_alertes_qualite: number;
  derniere_mise_a_jour: string;
  couverture_nuageuse_pct: number;
}

// ─── Composant ───────────────────────────────────────────
@Component({
  selector: 'app-satellite',
  imports: [CommonModule, LucideAngularModule],
  templateUrl: './satellite.html',
  styleUrl: './satellite.scss'
})
export class Satellite implements OnInit, AfterViewInit, OnDestroy {
  private http = inject(HttpClient);
  private auth = inject(AuthService);

  // Icônes
  readonly SatelliteIcon = SatelliteIcon;
  readonly Wind = Wind; readonly Droplets = Droplets; readonly Leaf = Leaf;
  readonly CloudRain = CloudRain; readonly TrendingUp = TrendingUp;
  readonly TrendingDown = TrendingDown; readonly Minus = Minus;
  readonly AlertTriangle = AlertTriangle; readonly CheckCircle = CheckCircle;
  readonly RefreshCw = RefreshCw; readonly Info = Info;
  readonly BarChart2 = BarChart2; readonly Map = Map; readonly Calendar = Calendar;
  readonly Layers = Layers; readonly Activity = Activity;

  // State
  indices = signal<IndicePoint[]>([]);
  resume = signal<ResumeSatellite | null>(null);
  serie = signal<SerieTemporelle | null>(null);
  selectedType = signal<'NO2' | 'NDVI' | 'NDWI' | 'RISQUE_PLUIE'>('NO2');
  selectedChantier = signal<number>(1);
  activeTab = signal<'carte' | 'serie' | 'indices'>('indices');
  loading = signal(true);
  loadingSerie = signal(false);
  lastRefresh = signal(new Date());
  mapLayerSat = signal(false);
  private satLayer!: L.TileLayer;
  private darkLayer!: L.TileLayer;

  @ViewChild('mapSat') mapContainer!: ElementRef;
  private map!: L.Map;

  // ── Computed : regroupement par type ──
  get no2List()     { return this.indices().filter(i => i.type_indice === 'NO2'); }
  get ndviList()    { return this.indices().filter(i => i.type_indice === 'NDVI'); }
  get ndwiList()    { return this.indices().filter(i => i.type_indice === 'NDWI'); }
  get risqueList()  { return this.indices().filter(i => i.type_indice === 'RISQUE_PLUIE'); }

  // ── Bar chart pour la série sélectionnée ──
  get seriePoints(): PointSerie[] { return this.serie()?.points ?? []; }

  get serieMax(): number {
    const vals = this.seriePoints.map(p => p.valeur);
    return vals.length ? Math.max(...vals) : 1;
  }

  ngOnInit() { this.loadAll(); }

  loadAll() {
    this.loading.set(true);
    const headers = { Authorization: `Bearer ${this.auth.token}` };

    this.http.get<IndicePoint[]>(`${API}/satellite/indices`, { headers }).subscribe({
      next: d => { this.indices.set(d); this.loading.set(false); this.lastRefresh.set(new Date()); },
      error: () => this.loading.set(false)
    });

    this.http.get<ResumeSatellite>(`${API}/satellite/resume`, { headers }).subscribe({
      next: d => this.resume.set(d),
      error: () => {}
    });

    this.loadSerie('NO2');
  }

  loadSerie(type: 'NO2' | 'NDVI' | 'NDWI' | 'RISQUE_PLUIE', chantierId?: number) {
    this.selectedType.set(type);
    if (chantierId !== undefined) this.selectedChantier.set(chantierId);
    this.loadingSerie.set(true);
    const headers = { Authorization: `Bearer ${this.auth.token}` };
    const cid = chantierId !== undefined ? chantierId : this.selectedChantier();
    this.http.get<SerieTemporelle>(`${API}/satellite/serie/${type}?chantier_id=${cid}`, { headers }).subscribe({
      next: d => { this.serie.set(d); this.loadingSerie.set(false); },
      error: () => this.loadingSerie.set(false)
    });
  }

  chantiersList = [
    { id: 1, nom: 'Rocade Y4 — Yopougon' },
    { id: 2, nom: '4e Pont — Plateau/Adjamé' },
    { id: 3, nom: 'Bd Latrille — Cocody' },
    { id: 4, nom: 'Sortie Est — Bingerville' },
    { id: 5, nom: 'Sortie Ouest — Songon' },
    { id: 6, nom: 'Échangeurs CG — Plateau' },
  ];

  ngAfterViewInit() { setTimeout(() => this.initMap(), 200); }

  private initMap() {
    if (!this.mapContainer?.nativeElement || this.map) return;
    this.map = L.map(this.mapContainer.nativeElement, {
      center: [5.35, -4.02], zoom: 11,
      zoomControl: true, attributionControl: false
    });
    this.darkLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_matter_no_labels/{z}/{x}/{y}{r}.png', {
      maxZoom: 19, subdomains: ['a','b','c','d']
    }).addTo(this.map);
    this.satLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19
    });
    this.addSatOverlays();
  }

  toggleMapLayer() {
    const useSat = !this.mapLayerSat();
    this.mapLayerSat.set(useSat);
    if (useSat) {
      this.map.removeLayer(this.darkLayer);
      this.satLayer.addTo(this.map);
    } else {
      this.map.removeLayer(this.satLayer);
      this.darkLayer.addTo(this.map);
    }
  }

  private CHANTIERS_GEO = [
    { nom: 'Rocade Y4',        commune: 'Yopougon',        lat: 5.372, lng: -4.048, no2: 43.8, ndvi: -0.005, risque: 3.3 },
    { nom: '4e Pont',          commune: 'Plateau/Adjamé',  lat: 5.356, lng: -4.009, no2: 46.8, ndvi: -0.006, risque: 2.4 },
    { nom: 'Bd Latrille',      commune: 'Cocody',          lat: 5.348, lng: -3.974, no2: 47.3, ndvi: 0.026, risque: 2.3 },
    { nom: 'Sortie Est',       commune: 'Bingerville',     lat: 5.338, lng: -3.881, no2: 24.6, ndvi: 0.022, risque: 2.2 },
    { nom: 'Sortie Ouest',     commune: 'Yopougon/Songon', lat: 5.341, lng: -4.103, no2: 21.9, ndvi: 0.001, risque: 2.5 },
    { nom: 'Échangeurs CG',    commune: 'Plateau',         lat: 5.319, lng: -4.016, no2: 50.1, ndvi: -0.012, risque: 2.5 },
  ];

  private addSatOverlays() {
    for (const c of this.CHANTIERS_GEO) {
      // Cercle NO2 : rouge si > seuil
      const no2Color = c.no2 > 50 ? '#C62828' : c.no2 > 30 ? '#F37021' : '#16A34A';
      const radius = 800 + c.no2 * 20;

      L.circle([c.lat, c.lng], {
        radius,
        color: no2Color, fillColor: no2Color,
        fillOpacity: 0.18, weight: 1.5
      }).addTo(this.map).bindPopup(`
        <div style="font-family:Inter,sans-serif;min-width:200px">
          <div style="font-weight:800;font-size:14px;color:#18181B;margin-bottom:8px">📍 ${c.nom}</div>
          <div style="font-size:12px;color:#71717A;margin-bottom:6px">${c.commune}</div>
          <hr style="border:none;border-top:1px solid #F4F4F5;margin:8px 0"/>
          <div style="display:flex;justify-content:space-between;margin-bottom:4px">
            <span style="font-size:11px;color:#A1A1AA">NO₂ (Sentinel-5P)</span>
            <span style="font-size:12px;font-weight:700;color:${no2Color}">${c.no2.toFixed(1)} µmol/m²</span>
          </div>
          <div style="display:flex;justify-content:space-between;margin-bottom:4px">
            <span style="font-size:11px;color:#A1A1AA">NDVI (Sentinel-2)</span>
            <span style="font-size:12px;font-weight:700;color:#16A34A">${c.ndvi.toFixed(3)}</span>
          </div>
          <div style="display:flex;justify-content:space-between">
            <span style="font-size:11px;color:#A1A1AA">Risque pluie</span>
            <span style="font-size:12px;font-weight:700;color:#F37021">${c.risque}/10</span>
          </div>
        </div>
      `);

      // Pin chantier
      const icon = L.divIcon({
        html: `<div style="width:10px;height:10px;border-radius:50%;background:${no2Color};border:2px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.4)"></div>`,
        iconSize: [10, 10], iconAnchor: [5, 5], className: ''
      });
      L.marker([c.lat, c.lng], { icon }).addTo(this.map)
        .bindTooltip(`<b>${c.nom}</b>`, { permanent: false, direction: 'top', className: 'sat-tooltip' });
    }
  }

  ngOnDestroy() { if (this.map) this.map.remove(); }

  // ── Gauge percentage for KPI cards ──
  no2GaugePct(): number {
    const v = this.resume()?.no2_moyen ?? 0;
    return Math.min(100, (v / 80) * 100);
  }
  ndviGaugePct(): number {
    const v = this.resume()?.ndvi_moyen ?? 0;
    return Math.min(100, (v / 0.6) * 100);
  }
  ndwiGaugePct(): number {
    const v = this.resume()?.ndwi_moyen ?? 0;
    return Math.min(100, (v / 0.5) * 100);
  }
  pluieGaugePct(): number {
    const v = this.resume()?.risque_pluie_max ?? 0;
    return Math.min(100, (v / 10) * 100);
  }

  // ── Interpretation text ──
  no2Interpretation(): string {
    const v = this.resume()?.no2_moyen ?? 0;
    if (v > 50) return `Pollution critique. Mesures d'atténuation requises immédiatement.`;
    if (v > 30) return `Pollution modérée. Surveillance renforcée recommandée.`;
    return `Qualité de l'air conforme aux normes.`;
  }
  ndviInterpretation(): string {
    const v = this.resume()?.ndvi_moyen ?? 0;
    if (v < 0.30) return 'Dégradation végétale sévère. Plan de reboisement nécessaire.';
    if (v < 0.40) return 'Végétation stressée. Suivi phytosanitaire conseillé.';
    return 'Couvert végétal sain et préservé.';
  }
  ndwiInterpretation(): string {
    const v = this.resume()?.ndwi_moyen ?? 0;
    if (v < 0.20) return `Stress hydrique critique. Risque pour les écosystèmes.`;
    if (v < 0.30) return `Humidité modérée. Surveillance des points d'eau.`;
    return `Ressources en eau suffisantes.`;
  }
  pluieInterpretation(): string {
    const v = this.resume()?.risque_pluie_max ?? 0;
    if (v > 7) return `Risque d'érosion élevé. Ouvrages de protection nécessaires.`;
    if (v > 5) return `Risque modéré. Surveillance pendant la saison des pluies.`;
    return `Risque d'érosion faible et maîtrisé.`;
  }

  // ── Helpers UI ──
  statutColor(statut: string): string {
    if (statut === 'BON')     return '#16A34A';
    if (statut === 'MODÉRÉ')  return '#F37021';
    return '#C62828';
  }

  statutBg(statut: string): string {
    if (statut === 'BON')     return '#F0FDF4';
    if (statut === 'MODÉRÉ')  return '#FEF3E8';
    return '#FFEBEE';
  }

  phaseColor(phase: string): string {
    if (phase === 'AVANT')   return '#1565C0';
    if (phase === 'TRAVAUX') return '#F37021';
    return '#16A34A';
  }

  barWidth(valeur: number): string {
    return Math.min(100, (valeur / this.serieMax) * 100).toFixed(1) + '%';
  }

  formatMois(mois: string): string {
    const [y, m] = mois.split('-');
    const months = ['Jan','Fév','Mar','Avr','Mai','Jun','Jul','Aoû','Sep','Oct','Nov','Déc'];
    return `${months[+m - 1]} ${y.slice(2)}`;
  }

  typeLabel(t: string): string {
    return { NO2:'NO₂', NDVI:'NDVI', NDWI:'NDWI', RISQUE_PLUIE:'Risque Pluie' }[t] ?? t;
  }

  typeUnite(t: string): string {
    return { NO2:'µmol/m²', NDVI:'indice', NDWI:'indice', RISQUE_PLUIE:'/10' }[t] ?? '';
  }

  setTab(tab: 'carte' | 'serie' | 'indices') {
    this.activeTab.set(tab);
    if (tab === 'carte') {
      setTimeout(() => {
        if (!this.map) this.initMap();
        else this.map.invalidateSize();
      }, 100);
    }
  }
}
