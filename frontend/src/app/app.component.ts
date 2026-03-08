import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    MatSidenavModule,
    MatToolbarModule,
    MatListModule,
    MatIconModule,
    MatButtonModule
  ],
  template: `
    <mat-sidenav-container class="sidenav-container">
      <mat-sidenav #sidenav mode="side" opened class="sidenav">
        <mat-toolbar class="logo-toolbar">
          <span class="logo">BuizSwarm</span>
        </mat-toolbar>
        <mat-nav-list>
          <a mat-list-item routerLink="/dashboard" routerLinkActive="active">
            <mat-icon matListItemIcon>dashboard</mat-icon>
            <span matListItemTitle>Dashboard</span>
          </a>
          <a mat-list-item routerLink="/companies" routerLinkActive="active">
            <mat-icon matListItemIcon>business</mat-icon>
            <span matListItemTitle>Companies</span>
          </a>
          <a mat-list-item routerLink="/agents" routerLinkActive="active">
            <mat-icon matListItemIcon>smart_toy</mat-icon>
            <span matListItemTitle>Agents</span>
          </a>
          <a mat-list-item routerLink="/tasks" routerLinkActive="active">
            <mat-icon matListItemIcon>assignment</mat-icon>
            <span matListItemTitle>Tasks</span>
          </a>
          <a mat-list-item routerLink="/billing" routerLinkActive="active">
            <mat-icon matListItemIcon>payments</mat-icon>
            <span matListItemTitle>Billing</span>
          </a>
          <a mat-list-item routerLink="/settings" routerLinkActive="active">
            <mat-icon matListItemIcon>settings</mat-icon>
            <span matListItemTitle>Settings</span>
          </a>
        </mat-nav-list>
      </mat-sidenav>
      
      <mat-sidenav-content>
        <mat-toolbar color="primary" class="main-toolbar">
          <button mat-icon-button (click)="sidenav.toggle()">
            <mat-icon>menu</mat-icon>
          </button>
          <span class="spacer"></span>
          <button mat-icon-button>
            <mat-icon>notifications</mat-icon>
          </button>
          <button mat-icon-button>
            <mat-icon>account_circle</mat-icon>
          </button>
        </mat-toolbar>
        
        <main class="content">
          <router-outlet></router-outlet>
        </main>
      </mat-sidenav-content>
    </mat-sidenav-container>
  `,
  styles: [`
    .sidenav-container {
      height: 100vh;
    }
    
    .sidenav {
      width: 260px;
      background: #1a1a2e;
      color: white;
    }
    
    .logo-toolbar {
      background: #16213e;
      color: white;
      justify-content: center;
    }
    
    .logo {
      font-size: 24px;
      font-weight: 700;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    
    .main-toolbar {
      background: white;
      color: #333;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .spacer {
      flex: 1;
    }
    
    .content {
      padding: 24px;
      background: #f5f7fa;
      min-height: calc(100vh - 64px);
    }
    
    mat-nav-list a {
      color: rgba(255,255,255,0.8);
    }
    
    mat-nav-list a.active {
      background: rgba(102, 126, 234, 0.2);
      color: #667eea;
    }
    
    mat-nav-list a:hover {
      background: rgba(255,255,255,0.1);
    }
  `]
})
export class AppComponent {
  title = 'BuizSwarm Dashboard';
}
