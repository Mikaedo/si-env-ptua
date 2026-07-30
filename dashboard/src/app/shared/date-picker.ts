import { Component, signal, input, output, ElementRef, inject, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule, Calendar, ChevronLeft, ChevronRight } from 'lucide-angular';

@Component({
  selector: 'app-date-picker',
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="dp-wrapper" #wrapper>
      <button
        type="button"
        class="dp-trigger"
        (click)="toggle()"
        [class.dp-open]="open()"
      >
        <lucide-icon [img]="Calendar" size="14" style="color:#A1A1AA; flex-shrink:0;" />
        <span class="dp-value" [class.dp-placeholder]="!value()">{{ displayValue() || placeholder() }}</span>
      </button>

      @if (open()) {
        <div class="dp-dropdown">
          <div class="dp-header">
            <button type="button" class="dp-nav-btn" (click)="prevMonth()">
              <lucide-icon [img]="ChevronLeft" size="16" />
            </button>
            <span class="dp-month-label">{{ monthLabel() }}</span>
            <button type="button" class="dp-nav-btn" (click)="nextMonth()">
              <lucide-icon [img]="ChevronRight" size="16" />
            </button>
          </div>
          <div class="dp-weekdays">
            @for (d of weekdays; track d) {
              <span class="dp-weekday">{{ d }}</span>
            }
          </div>
          <div class="dp-days">
            @for (day of calendarDays(); track day.date) {
              <button
                type="button"
                class="dp-day"
                [class.dp-day-other]="!day.currentMonth"
                [class.dp-day-selected]="isSelected(day.date)"
                [class.dp-day-today]="isToday(day.date)"
                [disabled]="!day.currentMonth"
                (click)="selectDate(day.date)"
              >
                {{ day.dayNum }}
              </button>
            }
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    .dp-wrapper { position: relative; display: inline-block; width: 100%; }

    .dp-trigger {
      display: flex;
      align-items: center;
      gap: 8px;
      width: 100%;
      padding: 9px 13px;
      border: 1.5px solid #E4E4E7;
      border-radius: 9px;
      font-size: 13px;
      font-family: 'Inter', sans-serif;
      color: #18181B;
      background: #FAFAFA;
      cursor: pointer;
      outline: none;
      transition: all 0.2s;
      min-height: 38px;
    }
    .dp-trigger:hover { border-color: #D1D1D6; background: #F4F4F5; }
    .dp-trigger.dp-open {
      border-color: #004F9F;
      background: white;
      box-shadow: 0 0 0 3px rgba(0,79,159,0.08);
    }

    .dp-value {
      flex: 1;
      text-align: left;
      font-weight: 500;
    }
    .dp-placeholder { color: #A1A1AA; font-weight: 400; }

    .dp-dropdown {
      position: absolute;
      top: calc(100% + 6px);
      left: 0;
      background: white;
      border: 1px solid #E4E4E7;
      border-radius: 10px;
      box-shadow: 0 12px 40px rgba(0,0,0,0.12);
      z-index: 9999;
      padding: 14px;
      width: 280px;
      animation: dpFadeIn 0.15s ease;
    }
    @keyframes dpFadeIn {
      from { opacity: 0; transform: translateY(-4px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .dp-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 12px;
    }
    .dp-nav-btn {
      background: none;
      border: none;
      cursor: pointer;
      padding: 4px;
      border-radius: 6px;
      color: #71717A;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background 0.12s;
    }
    .dp-nav-btn:hover { background: #F4F4F5; color: #18181B; }

    .dp-month-label {
      font-size: 13px;
      font-weight: 700;
      color: #18181B;
      text-transform: capitalize;
    }

    .dp-weekdays {
      display: grid;
      grid-template-columns: repeat(7, 1fr);
      gap: 2px;
      margin-bottom: 6px;
    }
    .dp-weekday {
      text-align: center;
      font-size: 10.5px;
      font-weight: 600;
      color: #A1A1AA;
      padding: 4px 0;
    }

    .dp-days {
      display: grid;
      grid-template-columns: repeat(7, 1fr);
      gap: 2px;
    }
    .dp-day {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 0;
      height: 32px;
      border: none;
      background: transparent;
      cursor: pointer;
      font-size: 12px;
      font-family: 'Inter', sans-serif;
      color: #3F3F46;
      border-radius: 7px;
      transition: all 0.12s;
    }
    .dp-day:hover:not(:disabled) { background: #F4F4F5; }
    .dp-day-other { color: #D1D1D6; }
    .dp-day-other:disabled { cursor: default; }
    .dp-day-today {
      font-weight: 700;
      color: #004F9F;
    }
    .dp-day-selected {
      background: #004F9F !important;
      color: white !important;
      font-weight: 700;
    }
  `]
})
export class DatePicker {
  readonly Calendar = Calendar;
  readonly ChevronLeft = ChevronLeft;
  readonly ChevronRight = ChevronRight;

  value = input<string>('');
  placeholder = input<string>('Sélectionner une date');
  valueChange = output<string>();

  open = signal(false);
  viewYear = signal(new Date().getFullYear());
  viewMonth = signal(new Date().getMonth());

  weekdays = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'];

  private elementRef = inject(ElementRef);

  toggle() {
    this.open.update(v => !v);
    if (this.open() && this.value()) {
      const [y, m] = this.value().split('-');
      this.viewYear.set(+y);
      this.viewMonth.set(+m - 1);
    }
  }

  displayValue(): string {
    if (!this.value()) return '';
    const [y, m, d] = this.value().split('-');
    const date = new Date(+y, +m - 1, +d);
    return date.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' });
  }

  monthLabel(): string {
    const months = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'];
    return `${months[this.viewMonth()]} ${this.viewYear()}`;
  }

  calendarDays(): { date: string; dayNum: number; currentMonth: boolean }[] {
    const year = this.viewYear();
    const month = this.viewMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);

    // Monday = 0
    let startWeekday = firstDay.getDay() - 1;
    if (startWeekday < 0) startWeekday = 6;

    const days: { date: string; dayNum: number; currentMonth: boolean }[] = [];

    // Previous month days
    for (let i = startWeekday - 1; i >= 0; i--) {
      const d = new Date(year, month, -i);
      days.push({
        date: this.formatDate(d),
        dayNum: d.getDate(),
        currentMonth: false
      });
    }

    // Current month days
    for (let i = 1; i <= lastDay.getDate(); i++) {
      const d = new Date(year, month, i);
      days.push({
        date: this.formatDate(d),
        dayNum: i,
        currentMonth: true
      });
    }

    // Next month days to fill the grid
    const remaining = (7 - (days.length % 7)) % 7;
    for (let i = 1; i <= remaining; i++) {
      const d = new Date(year, month + 1, i);
      days.push({
        date: this.formatDate(d),
        dayNum: d.getDate(),
        currentMonth: false
      });
    }

    return days;
  }

  isSelected(date: string): boolean {
    return date === this.value();
  }

  isToday(date: string): boolean {
    return date === this.formatDate(new Date());
  }

  selectDate(date: string) {
    this.valueChange.emit(date);
    this.open.set(false);
  }

  prevMonth() {
    let m = this.viewMonth() - 1;
    let y = this.viewYear();
    if (m < 0) { m = 11; y--; }
    this.viewMonth.set(m);
    this.viewYear.set(y);
  }

  nextMonth() {
    let m = this.viewMonth() + 1;
    let y = this.viewYear();
    if (m > 11) { m = 0; y++; }
    this.viewMonth.set(m);
    this.viewYear.set(y);
  }

  private formatDate(d: Date): string {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }

  @HostListener('document:click', ['$event'])
  onOutsideClick(event: Event) {
    if (!this.elementRef.nativeElement.contains(event.target)) {
      this.open.set(false);
    }
  }
}
