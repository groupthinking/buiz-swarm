import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatSlideToggleModule,
    MatButtonModule
  ],
  template: `
    <div class="settings-page">
      <h1>Settings</h1>
      
      <mat-card>
        <mat-card-header>
          <mat-card-title>General Settings</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <div class="settings-form">
            <mat-form-field appearance="outline">
              <mat-label>Theme</mat-label>
              <input matInput value="Light" disabled>
            </mat-form-field>
            
            <mat-form-field appearance="outline">
              <mat-label>Language</mat-label>
              <input matInput value="English" disabled>
            </mat-form-field>
            
            <div class="toggle-setting">
              <span>Email Notifications</span>
              <mat-slide-toggle checked></mat-slide-toggle>
            </div>
            
            <div class="toggle-setting">
              <span>Push Notifications</span>
              <mat-slide-toggle checked></mat-slide-toggle>
            </div>
          </div>
        </mat-card-content>
      </mat-card>
      
      <mat-card class="mt-3">
        <mat-card-header>
          <mat-card-title>API Keys</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <p>Manage your API keys here</p>
          <button mat-raised-button color="primary">Generate New API Key</button>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [`
    .settings-page {
      max-width: 800px;
      margin: 0 auto;
    }
    
    h1 {
      margin-bottom: 24px;
    }
    
    .settings-form {
      display: flex;
      flex-direction: column;
      gap: 16px;
      
      mat-form-field {
        width: 100%;
      }
    }
    
    .toggle-setting {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 0;
    }
    
    .mt-3 {
      margin-top: 24px;
    }
  `]
})
export class SettingsComponent {}
