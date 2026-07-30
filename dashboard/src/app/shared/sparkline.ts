import { Component, input, computed } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-sparkline',
  imports: [CommonModule],
  template: `
    <svg [attr.width]="width()" [attr.height]="height()" viewBox="0 0 100 30" preserveAspectRatio="none">
      <defs>
        <linearGradient [attr.id]="gradId" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" [attr.stop-color]="color()" stop-opacity="0.25" />
          <stop offset="100%" [attr.stop-color]="color()" stop-opacity="0" />
        </linearGradient>
      </defs>
      @if (areaPath()) {
        <path [attr.d]="areaPath()" [attr.fill]="'url(#' + gradId + ')'" stroke="none" />
      }
      @if (linePath()) {
        <path [attr.d]="linePath()" fill="none" [attr.stroke]="color()" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
      }
      @if (lastDot(); as dot) {
        <circle [attr.cx]="dot.x" [attr.cy]="dot.y" r="1.8" [attr.fill]="color()" />
      }
    </svg>
  `,
  styles: [`
    :host { display: inline-block; }
  `]
})
export class Sparkline {
  data = input<number[]>([]);
  color = input<string>('#004F9F');
  width = input<number>(120);
  height = input<number>(30);

  private static counter = 0;
  gradId = `spark-${++Sparkline.counter}`;

  linePath = computed(() => {
    const d = this.data();
    if (d.length < 2) return '';
    const max = Math.max(...d, 1);
    const min = Math.min(...d, 0);
    const range = max - min || 1;
    const step = 100 / (d.length - 1);
    return d.map((v, i) => {
      const x = i * step;
      const y = 28 - ((v - min) / range) * 26;
      return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(' ');
  });

  areaPath = computed(() => {
    const d = this.data();
    if (d.length < 2) return '';
    const line = this.linePath();
    const step = 100 / (d.length - 1);
    return `${line} L100,30 L0,30 Z`;
  });

  lastDot = computed(() => {
    const d = this.data();
    if (d.length < 2) return null;
    const max = Math.max(...d, 1);
    const min = Math.min(...d, 0);
    const range = max - min || 1;
    const x = 100;
    const y = 28 - ((d[d.length - 1] - min) / range) * 26;
    return { x, y };
  });
}
