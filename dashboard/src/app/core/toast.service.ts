import { Injectable, signal } from '@angular/core';

export interface Toast {
  id: number;
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
}

@Injectable({ providedIn: 'root' })
export class ToastService {
  readonly toasts = signal<Toast[]>([]);
  private counter = 0;

  show(message: string, type: Toast['type'] = 'info', duration = 3500) {
    const id = ++this.counter;
    this.toasts.update(list => [...list, { id, type, message }]);
    setTimeout(() => this.dismiss(id), duration);
  }

  success(message: string) { this.show(message, 'success'); }
  error(message: string) { this.show(message, 'error', 5000); }
  info(message: string) { this.show(message, 'info'); }
  warning(message: string) { this.show(message, 'warning'); }

  dismiss(id: number) {
    this.toasts.update(list => list.filter(t => t.id !== id));
  }
}
