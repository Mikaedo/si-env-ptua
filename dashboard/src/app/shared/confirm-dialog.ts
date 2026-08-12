import { Component, inject, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule, AlertTriangle, CheckCircle, Info } from 'lucide-angular';
import { ConfirmService } from '../core/confirm.service';

/**
 * Rendu de la boite de confirmation pilotee par ConfirmService.
 * Place une seule fois dans le shell, comme le conteneur de notifications.
 */
@Component({
  selector: 'app-confirm-dialog',
  imports: [CommonModule, LucideAngularModule],
  template: `
    @if (confirmService.demande(); as d) {
      <div
        style="position:fixed; inset:0; z-index:10000; display:flex; align-items:center; justify-content:center; padding:20px;
               background:rgba(24,24,27,0.45); backdrop-filter:blur(3px); animation:fadeIn 0.15s ease;"
        (click)="annulerDepuisFond($event)">

        <div role="dialog" aria-modal="true"
          style="background:#fff; border-radius:16px; width:100%; max-width:440px; overflow:hidden;
                 box-shadow:0 20px 50px rgba(0,0,0,0.22); animation:popIn 0.18s cubic-bezier(0.16,1,0.3,1);
                 font-family:Inter,sans-serif;"
          (click)="$event.stopPropagation()">

          <div style="padding:26px 28px 22px;">
            <div style="display:flex; align-items:flex-start; gap:14px;">
              <div style="width:44px; height:44px; border-radius:12px; display:flex; align-items:center; justify-content:center; flex-shrink:0;"
                   [style.background]="couleurAccent(d.variant) + '15'">
                <lucide-icon [img]="iconePour(d.variant)" size="21" [style.color]="couleurAccent(d.variant)"></lucide-icon>
              </div>
              <div style="flex:1; min-width:0;">
                <h2 style="font-size:16px; font-weight:800; color:#18181B; margin:0 0 7px; letter-spacing:-0.3px; line-height:1.35;">
                  {{ d.titre }}
                </h2>
                <p style="font-size:13.5px; color:#52525B; margin:0; line-height:1.65;">{{ d.message }}</p>
              </div>
            </div>
          </div>

          <div style="display:flex; gap:10px; justify-content:flex-end; padding:16px 28px 22px; border-top:1px solid #F4F4F5;">
            <button type="button" (click)="confirmService.repondre(false)"
              style="padding:10px 18px; border-radius:9px; border:1px solid #E4E4E7; background:#fff; color:#3F3F46;
                     font-size:13px; font-weight:650; cursor:pointer; font-family:inherit; transition:background 0.15s;"
              onmouseenter="this.style.background='#FAFAFA'" onmouseleave="this.style.background='#fff'">
              {{ d.texteAnnuler ?? 'Annuler' }}
            </button>
            <button type="button" (click)="confirmService.repondre(true)" #boutonConfirmer
              style="padding:10px 20px; border-radius:9px; border:none; color:#fff;
                     font-size:13px; font-weight:700; cursor:pointer; font-family:inherit; transition:filter 0.15s;"
              [style.background]="couleurAccent(d.variant)"
              onmouseenter="this.style.filter='brightness(0.92)'" onmouseleave="this.style.filter='none'">
              {{ d.texteConfirmer ?? 'Confirmer' }}
            </button>
          </div>
        </div>
      </div>
    }
  `,
  styles: [`
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    @keyframes popIn {
      from { opacity: 0; transform: translateY(8px) scale(0.97); }
      to   { opacity: 1; transform: translateY(0) scale(1); }
    }
  `]
})
export class ConfirmDialog {
  readonly confirmService = inject(ConfirmService);

  /** Echap ferme la boite en annulant, comme un dialogue natif. */
  @HostListener('document:keydown.escape')
  surEchap() {
    if (this.confirmService.demande()) this.confirmService.repondre(false);
  }

  /** Un clic sur le fond sombre annule ; le clic sur la carte est stoppe en amont. */
  annulerDepuisFond(_event: MouseEvent) {
    this.confirmService.repondre(false);
  }

  iconePour(variant?: string): any {
    return ({ danger: AlertTriangle, success: CheckCircle, primary: Info } as Record<string, any>)[variant ?? 'primary'] ?? Info;
  }

  couleurAccent(variant?: string): string {
    return ({ danger: '#C62828', success: '#16A34A', primary: '#004F9F' } as Record<string, string>)[variant ?? 'primary'] ?? '#004F9F';
  }
}
