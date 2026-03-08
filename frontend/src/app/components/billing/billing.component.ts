import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-billing',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatTableModule, MatButtonModule, MatIconModule],
  template: `
    <div class="billing-page">
      <h1>Billing</h1>
      
      <div class="billing-stats">
        <mat-card class="stat-card">
          <mat-card-content>
            <div class="stat-label">Total Revenue</div>
            <div class="stat-value">$0.00</div>
          </mat-card-content>
        </mat-card>
        
        <mat-card class="stat-card">
          <mat-card-content>
            <div class="stat-label">Platform Fees</div>
            <div class="stat-value">$0.00</div>
          </mat-card-content>
        </mat-card>
        
        <mat-card class="stat-card">
          <mat-card-content>
            <div class="stat-label">Net Revenue</div>
            <div class="stat-value">$0.00</div>
          </mat-card-content>
        </mat-card>
      </div>
      
      <mat-card>
        <mat-card-header>
          <mat-card-title>Transactions</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <p>No transactions yet</p>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [`
    .billing-page {
      max-width: 1200px;
      margin: 0 auto;
    }
    
    h1 {
      margin-bottom: 24px;
    }
    
    .billing-stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }
    
    .stat-card {
      mat-card-content {
        text-align: center;
        padding: 20px;
      }
      
      .stat-label {
        font-size: 14px;
        color: #666;
        margin-bottom: 8px;
      }
      
      .stat-value {
        font-size: 28px;
        font-weight: 700;
        color: #1a1a2e;
      }
    }
  `]
})
export class BillingComponent {}
