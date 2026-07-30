import { Component, signal, input, output, ElementRef, inject, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule, ChevronDown, Search, Check } from 'lucide-angular';

interface SelectOption {
  value: string;
  label: string;
}

@Component({
  selector: 'app-custom-select',
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="cs-wrapper" #wrapper>
      <button
        type="button"
        class="cs-trigger"
        (click)="toggle()"
        [class.cs-open]="open()"
        [style.width]="width()"
      >
        <span class="cs-value" [class.cs-placeholder]="!selectedLabel">{{ selectedLabel || placeholder() }}</span>
        <lucide-icon [img]="ChevronDown" size="14" class="cs-chevron" [class.cs-chevron-open]="open()" />
      </button>

      @if (open()) {
        <div class="cs-dropdown">
          @if (searchable()) {
            <div class="cs-search">
              <lucide-icon [img]="Search" size="13" style="color:#A1A1AA; flex-shrink:0;" />
              <input
                type="text"
                class="cs-search-input"
                placeholder="Rechercher..."
                [value]="searchTerm()"
                (input)="searchTerm.set($any($event.target).value)"
                (click)="$event.stopPropagation()"
              />
            </div>
          }
          <div class="cs-options">
            @for (opt of filteredOptions; track opt.value) {
              <button
                type="button"
                class="cs-option"
                [class.cs-selected]="opt.value === value()"
                (click)="select(opt)"
              >
                <span>{{ opt.label }}</span>
                @if (opt.value === value()) {
                  <lucide-icon [img]="Check" size="14" style="color:#004F9F;" />
                }
              </button>
            } @empty {
              <div class="cs-empty">Aucun résultat</div>
            }
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    .cs-wrapper { position: relative; display: inline-block; }

    .cs-trigger {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
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
    .cs-trigger:hover { border-color: #D1D1D6; background: #F4F4F5; }
    .cs-trigger.cs-open {
      border-color: #004F9F;
      background: white;
      box-shadow: 0 0 0 3px rgba(0,79,159,0.08);
    }

    .cs-value {
      flex: 1;
      text-align: left;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      font-weight: 500;
    }
    .cs-placeholder { color: #A1A1AA; font-weight: 400; }

    .cs-chevron {
      color: #A1A1AA;
      flex-shrink: 0;
      transition: transform 0.2s;
    }
    .cs-chevron-open { transform: rotate(180deg); }

    .cs-dropdown {
      position: absolute;
      top: calc(100% + 6px);
      left: 0;
      right: 0;
      min-width: 100%;
      background: white;
      border: 1px solid #E4E4E7;
      border-radius: 10px;
      box-shadow: 0 12px 40px rgba(0,0,0,0.12);
      z-index: 9999;
      overflow: hidden;
      animation: csFadeIn 0.15s ease;
    }
    @keyframes csFadeIn {
      from { opacity: 0; transform: translateY(-4px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .cs-search {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 12px;
      border-bottom: 1px solid #F4F4F5;
    }
    .cs-search-input {
      flex: 1;
      border: none;
      outline: none;
      font-size: 12.5px;
      font-family: 'Inter', sans-serif;
      color: #18181B;
      background: transparent;
    }
    .cs-search-input::placeholder { color: #A1A1AA; }

    .cs-options {
      max-height: 240px;
      overflow-y: auto;
      padding: 4px;
    }

    .cs-option {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      width: 100%;
      padding: 9px 12px;
      border: none;
      background: transparent;
      cursor: pointer;
      font-size: 12.5px;
      font-family: 'Inter', sans-serif;
      color: #3F3F46;
      border-radius: 7px;
      transition: background 0.12s;
      text-align: left;
    }
    .cs-option:hover { background: #F4F4F5; }
    .cs-option.cs-selected { background: #EEF1F8; color: #004F9F; font-weight: 600; }

    .cs-empty {
      padding: 20px;
      text-align: center;
      font-size: 12px;
      color: #A1A1AA;
    }
  `]
})
export class CustomSelect {
  readonly ChevronDown = ChevronDown;
  readonly Search = Search;
  readonly Check = Check;

  options = input.required<SelectOption[]>();
  value = input<string>('');
  placeholder = input<string>('Sélectionner...');
  searchable = input<boolean>(true);
  width = input<string>('100%');

  valueChange = output<string>();

  open = signal(false);
  searchTerm = signal('');

  private elementRef = inject(ElementRef);

  get selectedLabel(): string {
    const opt = this.options().find(o => o.value === this.value());
    return opt?.label ?? '';
  }

  get filteredOptions(): SelectOption[] {
    const term = this.searchTerm().toLowerCase();
    if (!term) return this.options();
    return this.options().filter(o => o.label.toLowerCase().includes(term));
  }

  toggle() {
    this.open.update(v => !v);
    if (!this.open()) this.searchTerm.set('');
  }

  select(opt: SelectOption) {
    this.valueChange.emit(opt.value);
    this.open.set(false);
    this.searchTerm.set('');
  }

  @HostListener('document:click', ['$event'])
  onOutsideClick(event: Event) {
    if (!this.elementRef.nativeElement.contains(event.target)) {
      this.open.set(false);
      this.searchTerm.set('');
    }
  }
}
