import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatProgressBarModule
  ],
  template: `
    <div class="dashboard">
      <div class="page-header">
        <div>
          <div class="eyebrow">ProfitMax Control Plane</div>
          <h1>Company Dashboard</h1>
          <p>Launch new businesses with a tenant-aware platform blueprint and a Bedrock-ready operating contract.</p>
        </div>
      </div>

      <div class="stats-grid">
        <mat-card class="stat-card">
          <mat-card-content>
            <div class="stat-icon companies">
              <mat-icon>business</mat-icon>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ overview?.companies?.total || 0 }}</span>
              <span class="stat-label">Companies</span>
            </div>
          </mat-card-content>
        </mat-card>

        <mat-card class="stat-card">
          <mat-card-content>
            <div class="stat-icon revenue">
              <mat-icon>payments</mat-icon>
            </div>
            <div class="stat-info">
              <span class="stat-value">\${{ overview?.revenue?.total_gmv?.toFixed(2) || '0.00' }}</span>
              <span class="stat-label">Total Revenue</span>
            </div>
          </mat-card-content>
        </mat-card>

        <mat-card class="stat-card">
          <mat-card-content>
            <div class="stat-icon agents">
              <mat-icon>smart_toy</mat-icon>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ getTotalAgents() }}</span>
              <span class="stat-label">Active Agents</span>
            </div>
          </mat-card-content>
        </mat-card>

        <mat-card class="stat-card">
          <mat-card-content>
            <div class="stat-icon tasks">
              <mat-icon>assignment</mat-icon>
            </div>
            <div class="stat-info">
              <span class="stat-value">{{ getTotalTasks() }}</span>
              <span class="stat-label">Tasks Completed</span>
            </div>
          </mat-card-content>
        </mat-card>
      </div>

      <mat-card class="companies-card">
        <mat-card-header>
          <mat-card-title>Your Companies</mat-card-title>
          <button mat-raised-button color="primary" routerLink="/companies/new">
            <mat-icon>add</mat-icon>
            New Company
          </button>
        </mat-card-header>
        <mat-card-content>
          <div class="empty-state" *ngIf="!overview?.companies?.list?.length && !loading">
            <h3>No companies yet</h3>
            <p>Start with the structured intake so every business launches with routing, guardrails, and clear success metrics.</p>
            <button mat-raised-button color="primary" routerLink="/companies/new">Create your first company</button>
          </div>

          <div class="companies-list" *ngIf="overview?.companies?.list?.length">
            <div *ngFor="let company of overview?.companies?.list" class="company-item">
              <div class="company-info">
                <div class="company-heading">
                  <h3>{{ company.name }}</h3>
                  <span class="status-badge" [class]="company.status">
                    {{ company.status }}
                  </span>
                </div>
                <div class="company-meta">
                  <span>{{ company.profile || 'profitmax' }}</span>
                  <span *ngIf="company.deployment_target">{{ company.deployment_target }}</span>
                  <a *ngIf="company.preview_url" [href]="company.preview_url" target="_blank" rel="noreferrer">
                    {{ company.preview_url }}
                  </a>
                </div>
              </div>
              <div class="company-metrics">
                <div class="metric">
                  <span class="metric-value">\${{ company.revenue?.toFixed(2) || '0.00' }}</span>
                  <span class="metric-label">Revenue</span>
                </div>
                <div class="metric">
                  <span class="metric-value">{{ company.daily_cycles }}</span>
                  <span class="metric-label">Cycles</span>
                </div>
              </div>
              <button mat-icon-button [routerLink]="['/companies', company.id]">
                <mat-icon>arrow_forward</mat-icon>
              </button>
            </div>
          </div>
        </mat-card-content>
      </mat-card>

      <mat-card class="agents-card">
        <mat-card-header>
          <mat-card-title>Agent Activity</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <div class="agent-activity">
            <div class="activity-item" *ngFor="let agent of getAgentActivity()">
              <div class="agent-type">{{ agent.type }}</div>
              <div class="activity-bar">
                <div class="activity-fill" [style.width.%]="agent.activity"></div>
              </div>
              <div class="activity-value">{{ agent.activity }}%</div>
            </div>
          </div>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [`
    .dashboard {
      max-width: 1400px;
      margin: 0 auto;
    }

    .page-header {
      margin-bottom: 24px;
    }

    .eyebrow {
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: #1d5b8f;
      margin-bottom: 8px;
    }

    h1 {
      margin: 0 0 8px 0;
      font-size: 28px;
      font-weight: 600;
    }

    .page-header p {
      margin: 0;
      color: #64748b;
      max-width: 760px;
      line-height: 1.5;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 20px;
      margin-bottom: 24px;
    }

    .stat-card mat-card-content {
      display: flex;
      align-items: center;
      padding: 20px;
    }

    .stat-icon {
      width: 56px;
      height: 56px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 16px;
    }

    .stat-icon mat-icon {
      font-size: 28px;
      width: 28px;
      height: 28px;
      color: white;
    }

    .stat-icon.companies {
      background: linear-gradient(135deg, #0f4c81 0%, #2d6fa3 100%);
    }

    .stat-icon.revenue {
      background: linear-gradient(135deg, #0d7a5f 0%, #31b47c 100%);
    }

    .stat-icon.agents {
      background: linear-gradient(135deg, #e36b2c 0%, #f4bb59 100%);
    }

    .stat-icon.tasks {
      background: linear-gradient(135deg, #1168a6 0%, #5cc0e6 100%);
    }

    .stat-info {
      display: flex;
      flex-direction: column;
    }

    .stat-value {
      font-size: 28px;
      font-weight: 700;
      color: #1a1a2e;
    }

    .stat-label {
      font-size: 14px;
      color: #666;
    }

    .companies-card,
    .agents-card {
      margin-bottom: 24px;
    }

    .empty-state {
      padding: 32px;
      border-radius: 20px;
      background: linear-gradient(135deg, rgba(244, 248, 255, 0.95), rgba(252, 254, 255, 1));
      border: 1px solid #e5edf6;
      text-align: center;
    }

    .empty-state h3 {
      margin: 0 0 8px 0;
    }

    .empty-state p {
      margin: 0 0 16px 0;
      color: #64748b;
    }

    .companies-list .company-item {
      display: flex;
      align-items: center;
      padding: 18px 16px;
      border-bottom: 1px solid #eee;
      gap: 16px;
    }

    .companies-list .company-item:last-child {
      border-bottom: none;
    }

    .company-info {
      flex: 1;
      min-width: 0;
    }

    .company-heading {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 8px;
    }

    .company-heading h3 {
      margin: 0;
      font-size: 16px;
    }

    .status-badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 12px;
      text-transform: uppercase;
      background: #f1f5f9;
      color: #334155;
    }

    .status-badge.active {
      background: #e8f5e9;
      color: #2e7d32;
    }

    .status-badge.paused {
      background: #fff3e0;
      color: #ef6c00;
    }

    .status-badge.onboarding {
      background: #e3f2fd;
      color: #1565c0;
    }

    .company-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      color: #64748b;
      font-size: 13px;
    }

    .company-meta a {
      color: #1565c0;
      text-decoration: none;
      font-weight: 500;
    }

    .company-metrics {
      display: flex;
      gap: 32px;
      margin-right: 16px;
    }

    .company-metrics .metric {
      text-align: center;
    }

    .company-metrics .metric-value {
      display: block;
      font-weight: 600;
      font-size: 16px;
    }

    .company-metrics .metric-label {
      font-size: 12px;
      color: #666;
    }

    .agent-activity .activity-item {
      display: flex;
      align-items: center;
      padding: 12px 0;
    }

    .agent-type {
      width: 100px;
      font-weight: 500;
      text-transform: capitalize;
    }

    .activity-bar {
      flex: 1;
      height: 8px;
      background: #e0e0e0;
      border-radius: 4px;
      overflow: hidden;
      margin: 0 16px;
    }

    .activity-fill {
      height: 100%;
      background: linear-gradient(90deg, #0f4c81 0%, #3b82f6 100%);
      border-radius: 4px;
      transition: width 0.3s ease;
    }

    .activity-value {
      width: 50px;
      text-align: right;
      font-weight: 500;
    }

    @media (max-width: 900px) {
      .companies-list .company-item {
        flex-direction: column;
        align-items: flex-start;
      }

      .company-metrics {
        margin-right: 0;
      }
    }
  `]
})
export class DashboardComponent implements OnInit {
  overview: any = null;
  loading = true;

  constructor(private apiService: ApiService) {}

  ngOnInit() {
    this.loadDashboardData();
  }

  async loadDashboardData() {
    try {
      this.overview = await this.apiService.getDashboardOverview();
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      this.loading = false;
    }
  }

  getTotalAgents(): number {
    if (!this.overview?.agents?.companies) return 0;
    return this.overview.agents.companies.reduce((sum: number, c: any) =>
      sum + (c.agent_count || 0), 0);
  }

  getTotalTasks(): number {
    if (!this.overview?.agents?.companies) return 0;
    return this.overview.agents.companies.reduce((sum: number, c: any) =>
      sum + (c.completed_tasks || 0), 0);
  }

  getAgentActivity(): any[] {
    return [
      { type: 'CEO', activity: 85 },
      { type: 'Engineering', activity: 92 },
      { type: 'Marketing', activity: 78 },
      { type: 'Support', activity: 65 }
    ];
  }
}
