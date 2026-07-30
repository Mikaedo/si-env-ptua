import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule, Search, Bell, User } from 'lucide-angular';

@Component({
  selector: 'app-header',
  imports: [CommonModule, LucideAngularModule],
  templateUrl: './header.html',
  styleUrl: './header.scss',
})
export class Header {
  readonly Search = Search;
  readonly Bell = Bell;
  readonly User = User;
}
