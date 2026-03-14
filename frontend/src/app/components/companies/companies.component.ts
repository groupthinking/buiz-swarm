import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';
import { MatChipsModule } from '@angular/material/chips';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-companies',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatTableModule,
    MatChipsModule
  ],
  template: `
    <div class="companies-page">
      <div class="header">
        <h1>Companies</h1>
        <button mat-raised-button color="primary" routerLink="/companies/new">
          <mat-icon>add</mat-icon>
          New Company
        </button>
      </div>
      
      <mat-card>
        <mat-card-content>
          <table mat-table [dataSource]="companies" class="companies-table">
            <ng-container matColumnDef="name">
              <th mat-header-cell *matHeaderCellDef>Name</th>
              <td mat-cell *matCellDef="let company">
                <strong>{{company.name}}</strong>
                <div class="company-slug">{{company.slug}}</div>
              </td>
            </ng-container>
            
            <ng-container matColumnDef="status">
              <th mat-header-cell *matHeaderCellDef>Status</th>
              <td mat-cell *matCellDef="let company">
                <mat-chip [class]="company.status">
                  {{company.status}}
                </mat-chip>
              </td>
            </ng-container>
            
            <ng-container matColumnDef="revenue">
              <th mat-header-cell *matHeaderCellDef>Revenue</th>
              <td mat-cell *matCellDef="let company">
                \${{company.total_revenue_processed?.toFixed(2) || '0.00'}}
              </td>
            </ng-container>
            
            <ng-container matColumnDef="cycles">
              <th mat-header-cell *matHeaderCellDef>Daily Cycles</th>
              <td mat-cell *matCellDef="let company">
                {{company.daily_cycle_count}}
              </td>
            </ng-container>
            
            <ng-container matColumnDef="actions">
              <th mat-header-cell *matHeaderCellDef>Actions</th>
              <td mat-cell *matCellDef="let company">
                <button mat-icon-button [routerLink]="['/companies', company.id]">
                  <mat-icon>visibility</mat-icon>
                </button>
                <button mat-icon-button color="warn" (click)="deleteCompany(company.id)">
                  <mat-icon>delete</mat-icon>
                </button>
              </td>
            </ng-container>
            
            <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
            <tr mat-row *matRowDef="let row; columns: displayedColumns;"></tr>
          </table>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [`
    .companies-page {
      max-width: 1200px;
      margin: 0 auto;
    }
    
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      
      h1 {
        margin: 0;
      }
    }
    
    .companies-table {
      width: 100%;
    }
    
    .company-slug {
      font-size: 12px;
      color: #666;
    }
    
    mat-chip {
      &.active {
        background: #e8f5e9;
        color: #2e7d32;
      }
      
      &.paused {
        background: #fff3e0;
        color: #ef6c00;
      }
      
      &.onboarding {
        background: #e3f2fd;
        color: #1565c0;
      }
    }
  `]
})
export class CompaniesComponent implements OnInit {
  companies: any[] = [];
  displayedColumns = ['name', 'status', 'revenue', 'cycles', 'actions'];

  constructor(private apiService: ApiService) {}

  ngOnInit() {
    this.loadCompanies();
  }

  async loadCompanies() {
    try {
      const response = await this.apiService.getCompanies();
      this.companies = response.companies || [];
    } catch (error) {
      console.error('Failed to load companies:', error);
    }
  }


  async deleteCompany(id: string) {
    if (confirm('Are you sure you want to delete this company?')) {
      try {
        await this.apiService.deleteCompany(id);
        this.loadCompanies();
      } catch (error) {
        console.error('Failed to delete company:', error);
      }
    }
  }
}
