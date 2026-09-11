import { Component, Input, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '../core/auth.service';
import { LucideAngularModule, Scale, Landmark, Eye } from 'lucide-angular';

/**
 * Le bandeau qui nomme l'organisme de controle et ce qu'il vient
 * chercher sur l'ecran courant.
 *
 * Sans lui, l'agence de tutelle et le bailleur consultent les memes
 * ecrans avec les memes titres, et rien ne dit ce qui les distingue :
 * un jury qui compare les deux sessions conclut qu'elles sont
 * identiques. Elles ne le sont pas, et le tableau 3.2 du memoire le
 * precise.
 *
 * L'ANDE verifie la conformite reglementaire : elle lit les indices au
 * regard des textes, et les constats au regard du Plan de Gestion.
 * La BAD controle le respect de ses sauvegardes operationnelles, volet
 * social compris : d'ou son acces aux doleances de riverains, que
 * l'agence n'a pas.
 *
 * Le bandeau ne s'affiche que pour ces deux profils. Pour les autres,
 * il ne rend rien.
 */
@Component({
  selector: 'app-bandeau-mandat',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    @if (organisme(); as o) {
      <div class="bandeau" [class.bandeau--bailleur]="o.sigle === 'BAD'">
        <div class="bandeau__sigle">
          <lucide-icon [img]="o.icone" size="22"></lucide-icon>
        </div>
        <div class="bandeau__texte">
          <div class="bandeau__nom">{{ o.nom }}</div>
          <div class="bandeau__mission">{{ propos || o.mandat }}</div>
        </div>
        <div class="bandeau__acces">
          <lucide-icon [img]="Eye" size="13"></lucide-icon>
          Consultation
        </div>
      </div>
    }
  `,
  styles: [`
    :host { display: block; }
    .bandeau {
      display: flex; align-items: center; gap: 14px;
      padding: 15px 20px; border-radius: 12px; margin-bottom: 18px;
      background: linear-gradient(135deg, #002B55, #004F9F);
      box-shadow: 0 4px 16px rgba(0, 43, 85, 0.18);
    }
    /* Le bailleur porte une teinte distincte : deux institutions
       differentes ne doivent pas se confondre a l'ecran. */
    .bandeau--bailleur {
      background: linear-gradient(135deg, #7A3B00, #C4660A);
      box-shadow: 0 4px 16px rgba(122, 59, 0, 0.20);
    }
    .bandeau__sigle {
      width: 42px; height: 42px; border-radius: 11px; flex-shrink: 0;
      background: rgba(255, 255, 255, 0.15); color: white;
      display: flex; align-items: center; justify-content: center;
    }
    .bandeau__texte { flex: 1; min-width: 0; }
    .bandeau__nom {
      font-size: 14.5px; font-weight: 800; color: white;
      letter-spacing: -0.2px; line-height: 1.3;
    }
    .bandeau__mission {
      font-size: 12px; color: rgba(255, 255, 255, 0.80);
      margin-top: 3px; font-weight: 500; line-height: 1.5;
    }
    .bandeau__acces {
      display: inline-flex; align-items: center; gap: 5px; flex-shrink: 0;
      padding: 6px 12px; border-radius: 18px;
      background: rgba(255, 255, 255, 0.16);
      font-size: 11px; font-weight: 700; color: white;
      letter-spacing: 0.3px; text-transform: uppercase;
    }
    @media (max-width: 560px) {
      .bandeau { flex-wrap: wrap; }
      .bandeau__acces { margin-left: 56px; }
    }
  `],
})
export class BandeauMandat {
  private auth = inject(AuthService);

  /** Ce que l'organisme vient chercher sur cet ecran precis.
   *
   * Laisse vide, le bandeau affiche le mandat general. Renseigne, il
   * dit ce que l'ecran courant lui apporte : les deux organismes ne
   * lisent pas une meme alerte pour la meme raison.
   */
  @Input() propos = '';

  readonly Eye = Eye;

  organisme = computed(() => {
    const role = this.auth.user()?.role;
    if (role === 'ANDE') {
      return {
        sigle: 'ANDE',
        nom: "Agence Nationale de l'Environnement",
        mandat: 'Vérification de la conformité réglementaire des chantiers',
        icone: Scale,
      };
    }
    if (role === 'BAD') {
      return {
        sigle: 'BAD',
        nom: 'Banque Africaine de Développement',
        mandat: 'Contrôle des sauvegardes opérationnelles, '
              + 'volet social compris',
        icone: Landmark,
      };
    }
    return null;
  });
}
