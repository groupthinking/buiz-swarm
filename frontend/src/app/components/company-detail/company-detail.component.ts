import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTabsModule } from '@angular/material/tabs';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-company-detail',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatTabsModule,
    MatProgressBarModule
  ],
  template: `
    <div class="company-detail" *ngIf="company">
      <div class="header">
        <div>
          <h1>{{company.company.name}}</h1>
          <span class="status-badge" [class]="company.company.status">
            {{company.company.status}}
          </span>
        </div>
        <div class="actions">
          <button mat-raised-button color="primary" (click)="triggerDailyCycle()">
            <mat-icon>play_arrow</mat-icon>
            Run Daily Cycle
          </button>
          <button mat-raised-button (click)="provisionInfrastructure()">
            <mat-icon>cloud</mat-icon>
            Provision Infrastructure
          </button>
        </div>
      </div>
      
      <mat-tab-group>
        <mat-tab label="Overview">
          <div class="tab-content">
            <div class="metrics-grid">
              <mat-card class="metric-card">
                <mat-card-content>
                  <div class="metric-label">Total Revenue</div>
                  <div class="metric-value">
                    \${{company.metrics?.total_revenue?.toFixed(2) || '0.00'}}
                  </div>
                </mat-card-content>
              </mat-card>
              
              <mat-card class="metric-card">
                <mat-card-content>
                  <div class="metric-label">Daily Cycles</div>
                  <div class="metric-value">{{company.company.daily_cycle_count}}</div>
                </mat-card-content>
              </mat-card>
              
              <mat-card class="metric-card">
                <mat-card-content>
                  <div class="metric-label">Active Agents</div>
                  <div class="metric-value">{{company.swarm?.agent_count || 0}}</div>
                </mat-card-content>
              </mat-card>
              
              <mat-card class="metric-card">
                <mat-card-content>
                  <div class="metric-label">Pending Tasks</div>
                  <div class="metric-value">{{company.swarm?.pending_tasks || 0}}</div>
                </mat-card-content>
              </mat-card>
            </div>
            
            <mat-card class="agents-card">
              <mat-card-header>
                <mat-card-title>Agents</mat-card-title>
              </mat-card-header>
              <mat-card-content>
                <div class="agents-list">
                  <div *ngFor="let agent of company.agents" class="agent-item">
                    <div class="agent-info">
                      <mat-icon>smart_toy</mat-icon>
                      <span class="agent-type">{{agent.type}}</span>
                    </div>
                    <span class="agent-status" [class]="agent.status">
                      {{agent.status}}
                    </span>
                  </div>
                </div>
              </mat-card-content>
            </mat-card>
          </div>
        </mat-tab>
        
        <mat-tab label="Infrastructure">
          <div class="tab-content">
            <mat-card>
              <mat-card-content>
                <div class="infrastructure-list">
                  <div class="infra-item">
                    <span class="infra-name">Web Server</span>
                    <span class="infra-status" [class]="company.infrastructure?.web_server?.status">
                      {{company.infrastructure?.web_server?.status}}
                    </span>
                  </div>
                  <div class="infra-item">
                    <span class="infra-name">Database</span>
                    <span class="infra-status" [class]="company.infrastructure?.database?.status">
                      {{company.infrastructure?.database?.status}}
                    </span>
                  </div>
                  <div class="infra-item">
                    <span class="infra-name">Email</span>
                    <span class="infra-status" [class]="company.infrastructure?.email?.status">
                      {{company.infrastructure?.email?.status}}
                    </span>
                  </div>
                  <div class="infra-item">
                    <span class="infra-name">GitHub</span>
                    <span class="infra-status" [class]="company.infrastructure?.github?.status">
                      {{company.infrastructure?.github?.status}}
                    </span>
                  </div>
                  <div class="infra-item">
                    <span class="infra-name">Stripe</span>
                    <span class="infra-status" [class]="company.infrastructure?.stripe?.status">
                      {{company.infrastructure?.stripe?.status}}
                    </span>
                  </div>
                </div>
              </mat-card-content>
            </mat-card>
          </div>
        </mat-tab>
        
        <mat-tab label="Tasks">
          <div class="tab-content">
            <p>Tasks will be displayed here</p>
          </div>
        </mat-tab>
        
        <mat-tab label="Billing">
          <div class="tab-content">
            <p>Billing information will be displayed here</p>
          </div>
        </mat-tab>
      </mat-tab-group>
    </div>
  `,
  styles: [`
    .company-detail {
      max-width: 1200px;
      margin: 0 auto;
    }
    
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      
      h1 {
        margin: 0 0 8px 0;
      }
      
      .actions {
        display: flex;
        gap: 12px;
      }
    }
    
    .status-badge {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 16px;
      font-size: 12px;
      text-transform: uppercase;
      font-weight: 500;
      
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
    
    .tab-content {
      padding: 24px 0;
    }
    
    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }
    
    .metric-card {
      mat-card-content {
        text-align: center;
        padding: 20px;
      }
      
      .metric-label {
        font-size: 14px;
        color: #666;
        margin-bottom: 8px;
      }
      
      .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #1a1a2e;
      }
    }
    
    .agents-card {
      .agents-list {
        .agent-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 0;
          border-bottom: 1px solid #eee;
          
          &:last-child {
            border-bottom: none;
          }
          
          .agent-info {
            display: flex;
            align-items: center;
            gap: 12px;
            
            .agent-type {
              text-transform: capitalize;
              font-weight: 500;
            }
          }
          
          .agent-status {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            
            &.active {
              background: #e8f5e9;
              color: #2e7d32;
            }
          }
        }
      }
    }
    
    .infrastructure-list {
      .infra-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 0;
        border-bottom: 1px solid #eee;
        
        &:last-child {
          border-bottom: none;
        }
        
        .infra-name {
          font-weight: 500;
        }
        
        .infra-status {
          padding: 4px 12px;
          border-radius: 12px;
          font-size: 12px;
          text-transform: capitalize;
          
          &.provisioned, &.active {
            background: #e8f5e9;
            color: #2e7d32;
          }
          
          &.pending {
            background: #fff3e0;
            color: #ef6c00;
          }
          
          &.not_provisioned {
            background: #f5f5f5;
            color: #666;
          }
        }
      }
    }
  `]
})
export class CompanyDetailComponent implements OnInit {
  companyId: string = '';
  company: any = null;

  constructor(
    private route: ActivatedRoute,
    private apiService: ApiService
  ) {}

  ngOnInit() {
    this.companyId = this.route.snapshot.params['id'];
    this.loadCompany();
  }

  async loadCompany() {
    try {
      this.company = await this.apiService.getCompanyStatus(this.companyId);
    } catch (error) {
      console.error('Failed to load company:', error);
    }
  }

  async triggerDailyCycle() {
    try {
      await this.apiService.triggerDailyCycle(this.companyId);
      alert('Daily cycle triggered!');
    } catch (error) {
      console.error('Failed to trigger daily cycle:', error);
    }
  }

  async provisionInfrastructure() {
    try {
      await this.apiService.provisionInfrastructure(this.companyId);
      alert('Infrastructure provisioning started!');
    } catch (error) {
      console.error('Failed to provision infrastructure:', error);
    }
  }
}
