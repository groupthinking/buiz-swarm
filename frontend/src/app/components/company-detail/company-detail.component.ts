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
          <h1>{{ company.company.name }}</h1>
          <div class="header-meta">
            <span class="status-badge" [class]="company.company.status">
              {{ company.company.status }}
            </span>
            <span class="meta-chip">{{ company.company.profile || 'profitmax' }}</span>
            <a *ngIf="platformBlueprint.preview_url" [href]="platformBlueprint.preview_url" target="_blank" rel="noreferrer">
              {{ platformBlueprint.preview_url }}
            </a>
          </div>
          <p *ngIf="company.company.goal" class="goal-copy">{{ company.company.goal }}</p>
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
                    \${{ company.metrics?.total_revenue?.toFixed(2) || '0.00' }}
                  </div>
                </mat-card-content>
              </mat-card>

              <mat-card class="metric-card">
                <mat-card-content>
                  <div class="metric-label">Daily Cycles</div>
                  <div class="metric-value">{{ company.company.daily_cycle_count }}</div>
                </mat-card-content>
              </mat-card>

              <mat-card class="metric-card">
                <mat-card-content>
                  <div class="metric-label">Active Agents</div>
                  <div class="metric-value">{{ company.swarm?.agent_count || 0 }}</div>
                </mat-card-content>
              </mat-card>

              <mat-card class="metric-card">
                <mat-card-content>
                  <div class="metric-label">Pending Tasks</div>
                  <div class="metric-value">{{ company.swarm?.pending_tasks || 0 }}</div>
                </mat-card-content>
              </mat-card>
            </div>

            <div class="overview-grid">
              <mat-card class="agents-card">
                <mat-card-header>
                  <mat-card-title>Agents</mat-card-title>
                </mat-card-header>
                <mat-card-content>
                  <div class="agents-list">
                    <div *ngFor="let agent of company.agents" class="agent-item">
                      <div class="agent-info">
                        <mat-icon>smart_toy</mat-icon>
                        <span class="agent-type">{{ agent.type }}</span>
                      </div>
                      <span class="agent-status" [class]="agent.status">
                        {{ agent.status }}
                      </span>
                    </div>
                  </div>
                </mat-card-content>
              </mat-card>

              <mat-card class="blueprint-card">
                <mat-card-header>
                  <mat-card-title>Platform Blueprint</mat-card-title>
                </mat-card-header>
                <mat-card-content>
                  <div class="definition-grid">
                    <div>
                      <span class="definition-label">Template</span>
                      <strong>{{ platformBlueprint.template || 'n/a' }}</strong>
                    </div>
                    <div>
                      <span class="definition-label">Deployment</span>
                      <strong>{{ platformBlueprint.deployment_target || 'n/a' }}</strong>
                    </div>
                    <div>
                      <span class="definition-label">Tenancy</span>
                      <strong>{{ platformBlueprint.tenancy || 'n/a' }}</strong>
                    </div>
                    <div>
                      <span class="definition-label">Tenant slug</span>
                      <strong>{{ platformBlueprint.tenant_slug || company.company.slug }}</strong>
                    </div>
                    <div>
                      <span class="definition-label">Root domain</span>
                      <strong>{{ platformBlueprint.root_domain || 'pending' }}</strong>
                    </div>
                    <div>
                      <span class="definition-label">Custom domain</span>
                      <strong>{{ platformBlueprint.custom_domain || 'none' }}</strong>
                    </div>
                    <div>
                      <span class="definition-label">Operator console</span>
                      <strong>{{ platformBlueprint.dashboard_domain || 'app.agentbroker.app' }}</strong>
                    </div>
                    <div>
                      <span class="definition-label">Marketing domain</span>
                      <strong>{{ platformBlueprint.marketing_domain || 'agentbroker.app' }}</strong>
                    </div>
                  </div>
                </mat-card-content>
              </mat-card>
            </div>

            <mat-card class="blueprint-card">
              <mat-card-header>
                <mat-card-title>Bedrock Agent Blueprint</mat-card-title>
              </mat-card-header>
              <mat-card-content>
                <div class="definition-grid definition-grid--wide">
                  <div>
                    <span class="definition-label">Provider</span>
                    <strong>{{ agentBlueprint.provider || 'n/a' }}</strong>
                  </div>
                  <div>
                    <span class="definition-label">Runtime</span>
                    <strong>{{ agentBlueprint.runtime || 'n/a' }}</strong>
                  </div>
                  <div>
                    <span class="definition-label">Model strategy</span>
                    <strong>{{ agentBlueprint.model_strategy || 'n/a' }}</strong>
                  </div>
                  <div>
                    <span class="definition-label">Primary job</span>
                    <strong>{{ agentBlueprint.primary_job_to_be_done || company.company.goal || 'n/a' }}</strong>
                  </div>
                </div>

                <div class="list-grid">
                  <div class="list-block" *ngIf="hasItems(agentBlueprint.scope_in)">
                    <div class="definition-label">Scope in</div>
                    <ul>
                      <li *ngFor="let item of agentBlueprint.scope_in">{{ item }}</li>
                    </ul>
                  </div>
                  <div class="list-block" *ngIf="hasItems(agentBlueprint.scope_out)">
                    <div class="definition-label">Scope out</div>
                    <ul>
                      <li *ngFor="let item of agentBlueprint.scope_out">{{ item }}</li>
                    </ul>
                  </div>
                  <div class="list-block" *ngIf="hasItems(agentBlueprint.knowledge_sources)">
                    <div class="definition-label">Knowledge sources</div>
                    <ul>
                      <li *ngFor="let item of agentBlueprint.knowledge_sources">{{ item }}</li>
                    </ul>
                  </div>
                  <div class="list-block" *ngIf="hasItems(agentBlueprint.action_groups)">
                    <div class="definition-label">Action groups</div>
                    <ul>
                      <li *ngFor="let item of agentBlueprint.action_groups">{{ item }}</li>
                    </ul>
                  </div>
                  <div class="list-block" *ngIf="hasItems(agentBlueprint.guardrails)">
                    <div class="definition-label">Guardrails</div>
                    <ul>
                      <li *ngFor="let item of agentBlueprint.guardrails">{{ item }}</li>
                    </ul>
                  </div>
                  <div class="list-block" *ngIf="hasItems(agentBlueprint.approval_points)">
                    <div class="definition-label">Approval points</div>
                    <ul>
                      <li *ngFor="let item of agentBlueprint.approval_points">{{ item }}</li>
                    </ul>
                  </div>
                  <div class="list-block" *ngIf="hasItems(agentBlueprint.evaluation_metrics)">
                    <div class="definition-label">Evaluation metrics</div>
                    <ul>
                      <li *ngFor="let item of agentBlueprint.evaluation_metrics">{{ item }}</li>
                    </ul>
                  </div>
                  <div class="list-block" *ngIf="hasItems(agentBlueprint.success_metrics)">
                    <div class="definition-label">Success metrics</div>
                    <ul>
                      <li *ngFor="let item of agentBlueprint.success_metrics">{{ item }}</li>
                    </ul>
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
                    <span class="infra-status" [class]="company.infrastructure?.web_server_status">
                      {{ company.infrastructure?.web_server_status }}
                    </span>
                  </div>
                  <div class="infra-item">
                    <span class="infra-name">Database</span>
                    <span class="infra-status" [class]="company.infrastructure?.database_status">
                      {{ company.infrastructure?.database_status }}
                    </span>
                  </div>
                  <div class="infra-item">
                    <span class="infra-name">Email</span>
                    <span class="infra-status" [class]="company.infrastructure?.email_status">
                      {{ company.infrastructure?.email_status }}
                    </span>
                  </div>
                  <div class="infra-item">
                    <span class="infra-name">GitHub</span>
                    <span class="infra-status" [class]="company.infrastructure?.github_status">
                      {{ company.infrastructure?.github_status }}
                    </span>
                  </div>
                  <div class="infra-item">
                    <span class="infra-name">Stripe</span>
                    <span class="infra-status" [class]="company.infrastructure?.stripe_status">
                      {{ company.infrastructure?.stripe_status }}
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
      align-items: flex-start;
      gap: 16px;
      margin-bottom: 24px;
    }

    .header h1 {
      margin: 0 0 8px 0;
    }

    .header-meta {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 10px;
      margin-bottom: 12px;
    }

    .header-meta a {
      color: #1565c0;
      text-decoration: none;
      font-weight: 500;
    }

    .goal-copy {
      margin: 0;
      color: #4a5568;
      max-width: 760px;
      line-height: 1.5;
    }

    .actions {
      display: flex;
      gap: 12px;
    }

    .status-badge,
    .meta-chip {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 16px;
      font-size: 12px;
      text-transform: uppercase;
      font-weight: 500;
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

    .tab-content {
      padding: 24px 0;
    }

    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }

    .overview-grid {
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 16px;
      margin-bottom: 16px;
    }

    .metric-card mat-card-content {
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

    .agents-list .agent-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 0;
      border-bottom: 1px solid #eee;
    }

    .agents-list .agent-item:last-child {
      border-bottom: none;
    }

    .agent-info {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .agent-type {
      text-transform: capitalize;
      font-weight: 500;
    }

    .agent-status {
      padding: 4px 12px;
      border-radius: 12px;
      font-size: 12px;
      text-transform: uppercase;
      background: #f5f5f5;
      color: #666;
    }

    .agent-status.active {
      background: #e8f5e9;
      color: #2e7d32;
    }

    .agent-status.error {
      background: #fdecea;
      color: #b3261e;
    }

    .blueprint-card {
      height: 100%;
    }

    .definition-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
      margin-bottom: 16px;
    }

    .definition-grid--wide {
      grid-template-columns: repeat(4, minmax(0, 1fr));
    }

    .definition-label {
      display: block;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #64748b;
      margin-bottom: 6px;
    }

    .list-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }

    .list-block {
      padding: 14px 16px;
      border-radius: 14px;
      background: #fafafa;
      border: 1px solid #eef2f6;
    }

    .list-block ul {
      margin: 0;
      padding-left: 18px;
      color: #334155;
    }

    .list-block li + li {
      margin-top: 6px;
    }

    .infrastructure-list .infra-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 0;
      border-bottom: 1px solid #eee;
    }

    .infrastructure-list .infra-item:last-child {
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
    }

    .infra-status.provisioned,
    .infra-status.active {
      background: #e8f5e9;
      color: #2e7d32;
    }

    .infra-status.pending {
      background: #fff3e0;
      color: #ef6c00;
    }

    .infra-status.not_provisioned,
    .infra-status.not_configured {
      background: #f5f5f5;
      color: #666;
    }

    @media (max-width: 960px) {
      .header,
      .overview-grid,
      .definition-grid,
      .definition-grid--wide,
      .list-grid {
        grid-template-columns: 1fr;
      }

      .header {
        flex-direction: column;
      }

      .actions {
        width: 100%;
        flex-wrap: wrap;
      }
    }
  `]
})
export class CompanyDetailComponent implements OnInit {
  companyId = '';
  company: any = null;

  constructor(
    private route: ActivatedRoute,
    private apiService: ApiService
  ) {}

  ngOnInit() {
    this.companyId = this.route.snapshot.params['id'];
    this.loadCompany();
  }

  get platformBlueprint(): any {
    return this.company?.company?.platform_blueprint || {};
  }

  get agentBlueprint(): any {
    return this.company?.company?.agent_blueprint || {};
  }

  hasItems(items: any): boolean {
    return Array.isArray(items) && items.length > 0;
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
