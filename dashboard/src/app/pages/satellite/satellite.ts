import {
  Component, signal, inject, OnInit, AfterViewInit,
  ViewChild, ElementRef, OnDestroy, computed
} from '@angular/core';
import { CommonModule, DecimalPipe, DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { AuthService } from '../../core/auth.service';
import {
  LucideAngularModule,
  Satellite as SatelliteIcon, Wind, Droplets, Leaf, CloudRain,
  TrendingUp, TrendingDown, Minus, AlertTriangle,
  CheckCircle, RefreshCw, Info, BarChart2, Map, Calendar, Layers, Activity,
  SlidersHorizontal, Building2, BellRing, Plus, Trash2, MapPin, Ruler
} from 'lucide-angular';
import * as L from 'leaflet';

import { environment } from '../../../environments/environment';
import {
  SEUILS, couleurIndice, etatIndice, jaugeIndice,
} from '../../core/seuils-satellite';
import {
  ATTRIBUTION_CARTE, FOND_PLAN, FOND_SATELLITE, ZOOM_MAX,
} from '../../core/fonds-carte';
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

/** Chantier du référentiel, tel que le paramètre le spécialiste. */
interface ChantierRef {
  id: number;
  nom: string;
  commune: string | null;
  geom?: { type: string; coordinates: [number, number] } | null;
  rayon_influence_m?: number | null;
}

/** Seuil de déclenchement d'alerte sur un indicateur satellitaire. */
interface SeuilRef {
  id: number;
  nom: string;
  indicateur: string;
  seuil: number;
  niveau: string;
  actif: boolean;
  chantier_id?: number | null;
}

// ─── Composant ───────────────────────────────────────────
@Component({
  selector: 'app-satellite',
  imports: [CommonModule, FormsModule, LucideAngularModule],
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
  readonly SlidersHorizontal = SlidersHorizontal; readonly Building2 = Building2;
  readonly BellRing = BellRing; readonly Plus = Plus; readonly Trash2 = Trash2;
  readonly MapPin = MapPin; readonly Ruler = Ruler;

  // State
  indices = signal<IndicePoint[]>([]);
  resume = signal<ResumeSatellite | null>(null);
  serie = signal<SerieTemporelle | null>(null);
  selectedType = signal<'NO2' | 'NDVI' | 'NDWI' | 'RISQUE_PLUIE'>('NO2');
  selectedChantier = signal<number>(1);
  activeTab = signal<'carte' | 'serie' | 'indices' | 'parametrage'>('indices');

  // ── Paramétrage, réuni ici plutôt que dans l'espace d'administration ──
  // Le référentiel des chantiers et les seuils de déclenchement conditionnent
  // directement ce qu'affichent les trois autres onglets. Les tenir dans un
  // écran séparé obligeait le spécialiste à naviguer entre deux pages pour
  // comprendre l'effet d'une valeur qu'il venait de modifier.
  chantiers = signal<ChantierRef[]>([]);
  seuils = signal<SeuilRef[]>([]);
  erreurParam = signal('');
  succesParam = signal('');

  nvChantierNom = signal('');
  nvChantierCommune = signal('');
  nvChantierLat = signal('');
  nvChantierLon = signal('');
  nvChantierRayon = signal('1500');

  nvSeuilNom = signal('');
  nvSeuilIndicateur = signal('NO2');
  nvSeuilValeur = signal('');
  nvSeuilNiveau = signal('WARNING');
  nvSeuilChantier = signal('');
  loading = signal(true);
  loadingSerie = signal(false);
  lastRefresh = signal(new Date());
  mapLayerSat = signal(false);
  private satLayer!: L.TileLayer;
  /** Fond de plan cartographique, alterné avec la vue satellite. */
  private planLayer!: L.TileLayer;

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

  ngOnInit() {
    // Le référentiel alimente aussi bien le sélecteur de série temporelle que
    // l'onglet de paramétrage : il est chargé d'emblée et non à l'ouverture
    // d'un onglet particulier.
    this.chargerParametrage();
    this.loadAll();
  }

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

  /**
   * Chantiers proposés dans le sélecteur de série temporelle.
   *
   * Cette liste était elle aussi figée dans le code, avec six entrées dont les
   * identifiants supposaient une numérotation immuable. Elle dérive désormais
   * du référentiel chargé depuis la base : un chantier ajouté apparaît dans le
   * sélecteur, un chantier retiré en disparaît.
   */
  get chantiersList(): { id: number; nom: string }[] {
    return this.chantiers().map(c => ({
      id: c.id,
      nom: c.commune ? `${c.nom} · ${c.commune}` : c.nom,
    }));
  }

  ngAfterViewInit() { setTimeout(() => this.initMap(), 200); }

  private initMap() {
    if (!this.mapContainer?.nativeElement || this.map) return;
    this.map = L.map(this.mapContainer.nativeElement, {
      center: [5.35, -4.02], zoom: 11,
      zoomControl: true, attributionControl: false
    });
    // Les deux fonds viennent de core/fonds-carte.ts, comme la carte
    // des signalements : le plan tirait ses tuiles d'OpenStreetMap, qui
    // ne sert plus les sites tiers et renvoyait une image vide.
    this.planLayer = L.tileLayer(FOND_PLAN, {
      maxZoom: ZOOM_MAX, attribution: ATTRIBUTION_CARTE
    }).addTo(this.map);
    this.satLayer = L.tileLayer(FOND_SATELLITE, {
      maxZoom: ZOOM_MAX, attribution: ATTRIBUTION_CARTE
    });
    this.ajouterZonesPtua();
    this.addSatOverlays();
  }

  /**
   * Trace les six chantiers du programme sur la carte.
   *
   * La carte satellitaire n'affichait que des cercles d'indices, sans le
   * moindre repere : on voyait des valeurs sans savoir a quel ouvrage
   * elles se rapportaient. Les traces du PTUA donnent ce contexte.
   */
  private ajouterZonesPtua() {
    if (!this.map) return;
    const couleurs: Record<string, string> = {
      '4EME_PONT': '#E8770E', 'Y4': '#1B2A4E', 'LATRILLE': '#7B1FA2',
      'SORTIE_EST': '#00838F', 'SORTIE_OUEST': '#C62828',
      'ECHANGEURS_CG': '#2E7D32',
    };
    fetch('/assets/zones_ptua.geojson')
      .then(r => r.json())
      .then(data => {
        L.geoJSON(data, {
          style: (f) => ({
            color: couleurs[f?.properties?.projet] || '#004F9F',
            weight: 4, opacity: 0.85,
          }),
          onEachFeature: (f, couche) => {
            const p = f?.properties || {};
            couche.bindTooltip(
              `${p.nom}${p.longueur_km ? ` · ${p.longueur_km} km` : ''}`,
              { sticky: true });
          },
        }).addTo(this.map);
      })
      .catch(() => { /* la carte reste exploitable sans les traces */ });
  }

  toggleMapLayer() {
    const useSat = !this.mapLayerSat();
    this.mapLayerSat.set(useSat);
    if (useSat) {
      this.map.removeLayer(this.planLayer);
      this.satLayer.addTo(this.map);
    } else {
      this.map.removeLayer(this.satLayer);
      this.planLayer.addTo(this.map);
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
      const no2Color = couleurIndice(c.no2, SEUILS.no2);
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
            <span style="font-size:12px;font-weight:700;color:${couleurIndice(c.ndvi, SEUILS.ndvi)}">${c.ndvi.toFixed(3)}</span>
          </div>
          <div style="display:flex;justify-content:space-between">
            <span style="font-size:11px;color:#A1A1AA">Risque pluie</span>
            <span style="font-size:12px;font-weight:700;color:${couleurIndice(c.risque, SEUILS.pluie)}">${c.risque}/10</span>
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

  // ── Les seuils, tels que le tableau 5.6 du memoire les fixe ──
  //
  // Ils vivent dans core/seuils-satellite.ts, non ici : ils etaient
  // recopies a treize endroits entre cette classe et son gabarit, et
  // deux avaient deja diverge du memoire. Les exposer ainsi laisse le
  // gabarit s'y referer sans les redire.
  readonly seuilsIndices = SEUILS;
  readonly couleurDe = couleurIndice;
  readonly etatDe = etatIndice;

  private valeur(indice: 'no2' | 'ndvi' | 'ndwi' | 'pluie'): number {
    const r = this.resume();
    if (!r) return 0;
    if (indice === 'no2') return r.no2_moyen ?? 0;
    if (indice === 'ndvi') return r.ndvi_moyen ?? 0;
    if (indice === 'ndwi') return r.ndwi_moyen ?? 0;
    return r.risque_pluie_max ?? 0;
  }

  /** L'etat d'un indice : BON, VIGILANCE ou CRITIQUE. */
  etat(indice: 'no2' | 'ndvi' | 'ndwi' | 'pluie') {
    return etatIndice(this.valeur(indice), SEUILS[indice]);
  }

  /** La couleur d'un indice, pour sa jauge et son chiffre. */
  couleur(indice: 'no2' | 'ndvi' | 'ndwi' | 'pluie'): string {
    return couleurIndice(this.valeur(indice), SEUILS[indice]);
  }

  /** Le remplissage de la jauge d'un indice, en pourcentage. */
  jauge(indice: 'no2' | 'ndvi' | 'ndwi' | 'pluie'): number {
    return jaugeIndice(this.valeur(indice), SEUILS[indice]);
  }

  /**
   * La position d'un repere de seuil sur la jauge, en pourcentage.
   *
   * Les traits etaient poses a des pourcentages en dur, qui ne
   * correspondaient a aucun seuil : le NDVI marquait 50 % et 67 %
   * quand ses seuils tombent a 33 % et 67 % de son echelle. Le repere
   * se calcule donc, et suit le seuil si celui-ci change.
   */
  repere(indice: 'no2' | 'ndvi' | 'ndwi' | 'pluie',
         lequel: 'vigilance' | 'critique'): number {
    return jaugeIndice(SEUILS[indice][lequel], SEUILS[indice]);
  }

  // ── Gauge percentage for KPI cards ──
  no2GaugePct(): number { return this.jauge('no2'); }
  ndviGaugePct(): number { return this.jauge('ndvi'); }
  ndwiGaugePct(): number { return this.jauge('ndwi'); }
  pluieGaugePct(): number { return this.jauge('pluie'); }

  // ── Interpretation text ──
  //
  // Le NO2 ne dit pas « conforme aux normes » quand il est bas : le
  // memoire est explicite, ce sont des seuils de vigilance pour
  // hierarchiser les visites de terrain, non des seuils de conformite,
  // Sentinel-5P mesurant une colonne tropospherique quand les valeurs
  // sanitaires portent sur une concentration respiree.
  no2Interpretation(): string {
    const etat = this.etat('no2');
    if (etat === 'CRITIQUE') {
      return `Concentration élevée. Visite de terrain à programmer en priorité.`;
    }
    if (etat === 'VIGILANCE') {
      return `Concentration modérée. Surveillance renforcée recommandée.`;
    }
    return `Concentration faible sur la période. Pas de priorité de visite.`;
  }
  ndviInterpretation(): string {
    const etat = this.etat('ndvi');
    if (etat === 'CRITIQUE') {
      return 'Couvert quasi nul, proche du sol nu. Plan de reboisement à étudier.';
    }
    if (etat === 'VIGILANCE') {
      return 'Végétation stressée. Suivi phytosanitaire conseillé.';
    }
    return 'Couvert végétal établi.';
  }
  ndwiInterpretation(): string {
    const etat = this.etat('ndwi');
    if (etat === 'CRITIQUE') {
      return `Indice négatif : stress hydrique marqué du couvert végétal.`;
    }
    if (etat === 'VIGILANCE') {
      return `Humidité modérée. Surveillance des points d'eau.`;
    }
    return `Teneur en eau du couvert satisfaisante.`;
  }
  pluieInterpretation(): string {
    const etat = this.etat('pluie');
    if (etat === 'CRITIQUE') {
      return `Risque élevé de flaques persistantes. Contrôle du drainage à prévoir.`;
    }
    if (etat === 'VIGILANCE') {
      return `Risque modéré. Surveillance pendant la saison des pluies.`;
    }
    return `Risque faible sur la période.`;
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

  setTab(tab: 'carte' | 'serie' | 'indices' | 'parametrage') {
    this.activeTab.set(tab);
    if (tab === 'carte') {
      setTimeout(() => {
        if (!this.map) this.initMap();
        else this.map.invalidateSize();
      }, 100);
    }
    if (tab === 'parametrage') this.chargerParametrage();
  }

  // ══════════════════════════════════════════════════════════════════
  //  Paramétrage du dispositif de surveillance
  // ══════════════════════════════════════════════════════════════════

  private get entetes() {
    return { Authorization: `Bearer ${this.auth.token}` };
  }

  /** Signale brièvement une opération réussie, puis efface le message. */
  private annoncer(message: string) {
    this.erreurParam.set('');
    this.succesParam.set(message);
    setTimeout(() => this.succesParam.set(''), 3200);
  }

  chargerParametrage() {
    this.http.get<ChantierRef[]>(`${API}/chantiers`, { headers: this.entetes }).subscribe({
      next: d => {
        this.chantiers.set(d);
        // La sélection par défaut visait l'identifiant 1, qui pouvait
        // désigner un chantier supprimé. On se cale sur le premier réellement
        // présent, sauf si l'utilisateur a déjà fait son choix.
        if (d.length && !d.some(c => c.id === this.selectedChantier())) {
          this.selectedChantier.set(d[0].id);
        }
      },
      error: () => this.erreurParam.set('Le référentiel des chantiers n\'a pas pu être chargé.'),
    });
    this.http.get<SeuilRef[]>(`${API}/admin/seuils`, { headers: this.entetes }).subscribe({
      next: d => this.seuils.set(d),
      error: () => this.erreurParam.set('Les seuils de surveillance n\'ont pas pu être chargés.'),
    });
  }

  creerChantier() {
    const nom = this.nvChantierNom().trim();
    if (!nom) {
      this.erreurParam.set('Le nom du chantier est obligatoire.');
      return;
    }
    const lat = parseFloat(this.nvChantierLat());
    const lon = parseFloat(this.nvChantierLon());
    if (isNaN(lat) || isNaN(lon)) {
      // Sans coordonnées, aucun indice satellitaire ne peut être extrait et
      // aucun riverain ne peut être rattaché : autant le dire tout de suite.
      this.erreurParam.set('Les coordonnées sont nécessaires pour suivre le chantier par satellite.');
      return;
    }

    const corps = {
      nom,
      commune: this.nvChantierCommune().trim() || null,
      latitude: lat,
      longitude: lon,
      rayon_influence_m: parseInt(this.nvChantierRayon(), 10) || 1500,
    };

    this.http.post<ChantierRef>(`${API}/chantiers`, corps, { headers: this.entetes }).subscribe({
      next: () => {
        this.nvChantierNom.set(''); this.nvChantierCommune.set('');
        this.nvChantierLat.set(''); this.nvChantierLon.set('');
        this.nvChantierRayon.set('1500');
        this.chargerParametrage();
        this.annoncer('Chantier ajouté au périmètre de surveillance.');
        // Les indices portent sur le référentiel : ils doivent suivre.
        this.loadAll();
      },
      error: e => this.erreurParam.set(e?.error?.detail ?? 'La création du chantier a échoué.'),
    });
  }

  supprimerChantier(chantier: ChantierRef) {
    if (!confirm(`Retirer « ${chantier.nom} » du périmètre de surveillance ?`)) return;
    this.http.delete(`${API}/chantiers/${chantier.id}`, { headers: this.entetes }).subscribe({
      next: () => {
        this.chargerParametrage();
        this.annoncer('Chantier retiré du périmètre.');
        this.loadAll();
      },
      error: e => this.erreurParam.set(
        e?.error?.detail ?? 'Ce chantier ne peut pas être retiré.'
      ),
    });
  }

  creerSeuil() {
    const nom = this.nvSeuilNom().trim();
    const valeur = parseFloat(this.nvSeuilValeur());
    if (!nom || isNaN(valeur)) {
      this.erreurParam.set('Un intitulé et une valeur de seuil sont nécessaires.');
      return;
    }

    const portee = this.nvSeuilChantier();
    const corps = {
      nom,
      indicateur: this.nvSeuilIndicateur(),
      seuil: valeur,
      niveau: this.nvSeuilNiveau(),
      actif: true,
      // Portée vide : le seuil vaut pour l'ensemble des chantiers.
      chantier_id: portee ? parseInt(portee, 10) : null,
    };

    this.http.post<SeuilRef>(`${API}/admin/seuils`, corps, { headers: this.entetes }).subscribe({
      next: () => {
        this.nvSeuilNom.set(''); this.nvSeuilValeur.set(''); this.nvSeuilChantier.set('');
        this.chargerParametrage();
        this.annoncer('Seuil de déclenchement enregistré.');
      },
      error: e => this.erreurParam.set(e?.error?.detail ?? 'La création du seuil a échoué.'),
    });
  }

  supprimerSeuil(seuil: SeuilRef) {
    if (!confirm(`Supprimer le seuil « ${seuil.nom} » ?`)) return;
    this.http.delete(`${API}/admin/seuils/${seuil.id}`, { headers: this.entetes }).subscribe({
      next: () => { this.chargerParametrage(); this.annoncer('Seuil supprimé.'); },
      error: e => this.erreurParam.set(e?.error?.detail ?? 'La suppression a échoué.'),
    });
  }

  /** Coordonnées lisibles d'un chantier, ou mention explicite d'absence. */
  coordonneesLisibles(chantier: ChantierRef): string {
    const c = chantier.geom?.coordinates;
    if (!c) return 'Non positionné';
    return `${c[1].toFixed(4)}, ${c[0].toFixed(4)}`;
  }

  /** Rayon d'influence exprimé dans l'unité la plus lisible. */
  rayonLisible(chantier: ChantierRef): string {
    const r = chantier.rayon_influence_m ?? 1500;
    return r >= 1000 ? `${(r / 1000).toFixed(r % 1000 === 0 ? 0 : 1)} km` : `${r} m`;
  }

  /** Chantier visé par un seuil, ou mention de portée générale. */
  porteeSeuil(seuil: SeuilRef): string {
    if (!seuil.chantier_id) return 'Tous les chantiers';
    return this.chantiers().find(c => c.id === seuil.chantier_id)?.nom ?? 'Chantier retiré';
  }
}
