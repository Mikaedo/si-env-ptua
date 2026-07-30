import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule, CheckCircle, XCircle, Info, AlertTriangle, X } from 'lucide-angular';
import { ToastService, Toast } from '../core/toast.service';

@Component({
  selector: 'app-toast-container',
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div style="position:fixed; top:20px; right:20px; z-index:9999; display:flex; flex-direction:column; gap:10px; pointer-events:none;">
      @for (t of toastService.toasts(); track t.id) {
        <div style="pointer-events:auto; display:flex; align-items:center; gap:12px; padding:14px 18px; border-radius:12px; min-width:300px; max-width:420px;
          box-shadow:0 8px 24px rgba(0,0,0,0.12); animation:slideInUp 0.3s ease forwards; font-family:Inter,sans-serif;"
          [style.background]="bgColor(t.type)"
          [style.border]="'1px solid ' + borderColor(t.type)">
          <lucide-icon [img]="iconFor(t.type)" size="18" [style.color]="iconColor(t.type)"></lucide-icon>
          <span style="font-size:13px; font-weight:600; color:#18181B; flex:1; line-height:1.4;">{{ t.message }}</span>
          <button (click)="toastService.dismiss(t.id)" style="background:none; border:none; cursor:pointer; padding:2px; color:#A1A1AA; display:flex; align-items:center;">
            <lucide-icon [img]="X" size="14"></lucide-icon>
          </button>
        </div>
      }
    </div>
  `,
  styles: [`
    @keyframes slideInUp {
      from { opacity: 0; transform: translateX(20px); }
      to { opacity: 1; transform: translateX(0); }
    }
  `]
})
export class ToastContainer {
  readonly toastService = inject(ToastService);
  readonly CheckCircle = CheckCircle;
  readonly XCircle = XCircle;
  readonly Info = Info;
  readonly AlertTriangle = AlertTriangle;
  readonly X = X;

  iconFor(type: string): any {
    return { success: CheckCircle, error: XCircle, info: Info, warning: AlertTriangle }[type] ?? Info;
  }

  bgColor(type: string): string {
    return ({ success: '#F0FDF4', error: '#FFEBEE', info: '#EFF6FF', warning: '#FEF3E8' } as Record<string, string>)[type] ?? '#F4F4F5';
  }

  borderColor(type: string): string {
    return ({ success: 'rgba(22,163,74,0.2)', error: 'rgba(198,40,40,0.2)', info: 'rgba(21,101,192,0.2)', warning: 'rgba(243,112,33,0.2)' } as Record<string, string>)[type] ?? '#E4E4E7';
  }

  iconColor(type: string): string {
    return ({ success: '#16A34A', error: '#C62828', info: '#1565C0', warning: '#F37021' } as Record<string, string>)[type] ?? '#71717A';
  }
}
