import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';

import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-company-create',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatButtonModule,
    MatCardModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule
  ],
  template: `
    <div class="company-create-page">
      <div class="header">
        <div>
          <h1>Create Company</h1>
          <p>
            Define the business, its multi-tenant platform shape, and the Bedrock agent blueprint in one pass.
          </p>
        </div>
        <button mat-stroked-button color="primary" (click)="cancel()">
          <mat-icon>arrow_back</mat-icon>
          Back
        </button>
      </div>

      <mat-card class="intro-card">
        <mat-card-content>
          <div class="intro-grid">
            <div>
              <div class="eyebrow">Platform Pattern</div>
              <h2>Vercel-style multi-tenant business shell</h2>
              <p>
                Capture the subdomain and domain strategy up front so each business can become a tenant on the same control plane.
              </p>
            </div>
            <div>
              <div class="eyebrow">Agent Blueprint</div>
              <h2>Bedrock-ready operating contract</h2>
              <p>
                Define scope, knowledge, actions, guardrails, and evaluation before agents start running real work.
              </p>
            </div>
          </div>
        </mat-card-content>
      </mat-card>

      <mat-card>
        <mat-card-content>
          <form class="company-form" (ngSubmit)="submit()">
            <section class="section section--identity">
              <div class="section-title">Business Identity</div>
              <div class="section-copy">Core company information and the operating goal the system should optimize for.</div>

              <mat-form-field appearance="outline">
                <mat-label>Company name</mat-label>
                <input matInput [(ngModel)]="form.name" name="name" required />
              </mat-form-field>

              <mat-form-field appearance="outline">
                <mat-label>Industry</mat-label>
                <input matInput [(ngModel)]="form.industry" name="industry" />
              </mat-form-field>

              <mat-form-field appearance="outline">
                <mat-label>Website</mat-label>
                <input matInput [(ngModel)]="form.website" name="website" />
              </mat-form-field>

              <mat-form-field appearance="outline">
                <mat-label>Operating profile</mat-label>
                <input matInput [(ngModel)]="form.profile" name="profile" />
              </mat-form-field>

              <mat-form-field appearance="outline" class="wide-field">
                <mat-label>Description</mat-label>
                <textarea matInput rows="4" [(ngModel)]="form.description" name="description"></textarea>
              </mat-form-field>

              <mat-form-field appearance="outline" class="wide-field">
                <mat-label>North-star goal</mat-label>
                <textarea matInput rows="4" [(ngModel)]="form.goal" name="goal"></textarea>
              </mat-form-field>
            </section>

            <section class="section section--platform">
              <div class="section-title">Platform Blueprint</div>
              <div class="section-copy">Modeled after a multi-tenant Vercel platform: shared admin surface, tenant routing, and custom domain readiness.</div>

              <mat-form-field appearance="outline">
                <mat-label>Template</mat-label>
                <input matInput [(ngModel)]="form.platform.template" name="platformTemplate" />
              </mat-form-field>

              <mat-form-field appearance="outline">
                <mat-label>Deployment target</mat-label>
                <input matInput [(ngModel)]="form.platform.deploymentTarget" name="deploymentTarget" />
              </mat-form-field>

              <mat-form-field appearance="outline">
                <mat-label>Tenant model</mat-label>
                <input matInput [(ngModel)]="form.platform.tenancy" name="tenancy" />
              </mat-form-field>

              <mat-form-field appearance="outline">
                <mat-label>Admin surface</mat-label>
                <input matInput [(ngModel)]="form.platform.adminSurface" name="adminSurface" />
              </mat-form-field>

              <mat-form-field appearance="outline">
                <mat-label>Requested subdomain</mat-label>
                <input matInput [(ngModel)]="form.platform.requestedSubdomain" name="requestedSubdomain" />
                <mat-hint>Used for wildcard-tenant routing.</mat-hint>
              </mat-form-field>

              <mat-form-field appearance="outline">
                <mat-label>Root domain</mat-label>
                <input matInput [(ngModel)]="form.platform.rootDomain" name="rootDomain" />
                <mat-hint>Example: agentbroker.app</mat-hint>
              </mat-form-field>

              <mat-form-field appearance="outline" class="wide-field">
                <mat-label>Custom domain override</mat-label>
                <input matInput [(ngModel)]="form.platform.customDomain" name="customDomain" />
                <mat-hint>Optional. Use this only if the business should skip the shared wildcard domain.</mat-hint>
              </mat-form-field>

              <div class="preview wide-field">
                <span class="preview-label">Calculated launch URL</span>
                <strong>{{ getPreviewUrl() || 'Will be assigned after DNS is chosen' }}</strong>
              </div>
            </section>

            <section class="section section--agent">
              <div class="section-title">Agent Blueprint</div>
              <div class="section-copy">Structured around Bedrock agent design: clear responsibility, grounded knowledge, scoped actions, guardrails, and evaluation.</div>

              <mat-form-field appearance="outline">
                <mat-label>Model provider</mat-label>
                <input matInput [(ngModel)]="form.agent.provider" name="agentProvider" />
              </mat-form-field>

              <mat-form-field appearance="outline">
                <mat-label>Runtime target</mat-label>
                <input matInput [(ngModel)]="form.agent.runtime" name="agentRuntime" />
              </mat-form-field>

              <mat-form-field appearance="outline">
                <mat-label>Model strategy</mat-label>
                <input matInput [(ngModel)]="form.agent.modelStrategy" name="modelStrategy" />
              </mat-form-field>

              <mat-form-field appearance="outline">
                <mat-label>Primary job to be done</mat-label>
                <input matInput [(ngModel)]="form.agent.primaryJobToBeDone" name="primaryJobToBeDone" />
              </mat-form-field>

              <mat-form-field appearance="outline" class="wide-field">
                <mat-label>Knowledge sources</mat-label>
                <textarea matInput rows="3" [(ngModel)]="form.agent.knowledgeSources" name="knowledgeSources"></textarea>
                <mat-hint>One per line or comma separated.</mat-hint>
              </mat-form-field>

              <mat-form-field appearance="outline" class="wide-field">
                <mat-label>Action groups</mat-label>
                <textarea matInput rows="3" [(ngModel)]="form.agent.actionGroups" name="actionGroups"></textarea>
              </mat-form-field>

              <mat-form-field appearance="outline" class="wide-field">
                <mat-label>Scope in</mat-label>
                <textarea matInput rows="3" [(ngModel)]="form.agent.scopeIn" name="scopeIn"></textarea>
              </mat-form-field>

              <mat-form-field appearance="outline" class="wide-field">
                <mat-label>Scope out</mat-label>
                <textarea matInput rows="3" [(ngModel)]="form.agent.scopeOut" name="scopeOut"></textarea>
              </mat-form-field>

              <mat-form-field appearance="outline" class="wide-field">
                <mat-label>Session attributes</mat-label>
                <textarea matInput rows="3" [(ngModel)]="form.agent.sessionAttributes" name="sessionAttributes"></textarea>
              </mat-form-field>

              <mat-form-field appearance="outline" class="wide-field">
                <mat-label>Prompt session attributes</mat-label>
                <textarea matInput rows="3" [(ngModel)]="form.agent.promptSessionAttributes" name="promptSessionAttributes"></textarea>
              </mat-form-field>

              <mat-form-field appearance="outline" class="wide-field">
                <mat-label>Guardrails</mat-label>
                <textarea matInput rows="3" [(ngModel)]="form.agent.guardrails" name="guardrails"></textarea>
              </mat-form-field>

              <mat-form-field appearance="outline" class="wide-field">
                <mat-label>Human approval points</mat-label>
                <textarea matInput rows="3" [(ngModel)]="form.agent.approvalPoints" name="approvalPoints"></textarea>
              </mat-form-field>

              <mat-form-field appearance="outline" class="wide-field">
                <mat-label>Evaluation metrics</mat-label>
                <textarea matInput rows="3" [(ngModel)]="form.agent.evaluationMetrics" name="evaluationMetrics"></textarea>
              </mat-form-field>

              <mat-form-field appearance="outline" class="wide-field">
                <mat-label>Success metrics</mat-label>
                <textarea matInput rows="3" [(ngModel)]="form.agent.successMetrics" name="successMetrics"></textarea>
              </mat-form-field>
            </section>

            <div class="error" *ngIf="errorMessage">{{ errorMessage }}</div>

            <div class="actions">
              <button mat-stroked-button type="button" (click)="cancel()">Cancel</button>
              <button mat-raised-button color="primary" type="submit" [disabled]="submitting || !form.name.trim()">
                <mat-icon>add_business</mat-icon>
                {{ submitting ? 'Creating...' : 'Create company' }}
              </button>
            </div>
          </form>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [`
    .company-create-page {
      max-width: 1100px;
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

    .header p {
      margin: 0;
      color: #666;
      max-width: 720px;
    }

    .intro-card {
      margin-bottom: 24px;
      background: linear-gradient(135deg, rgba(18, 45, 78, 0.04), rgba(26, 112, 176, 0.08));
    }

    .intro-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 24px;
    }

    .eyebrow {
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: #1d5b8f;
      margin-bottom: 8px;
    }

    .intro-grid h2 {
      margin: 0 0 8px 0;
      font-size: 20px;
    }

    .intro-grid p {
      margin: 0;
      color: #4a5568;
      line-height: 1.5;
    }

    .company-form {
      display: flex;
      flex-direction: column;
      gap: 24px;
    }

    .section {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
      padding: 20px;
      border-radius: 20px;
      background: #fafafa;
      border: 1px solid #eceff3;
    }

    .section--platform {
      background: linear-gradient(135deg, rgba(244, 248, 255, 0.95), rgba(252, 254, 255, 1));
    }

    .section--agent {
      background: linear-gradient(135deg, rgba(247, 250, 252, 1), rgba(242, 248, 255, 0.9));
    }

    .section-title,
    .section-copy,
    .wide-field,
    .preview {
      grid-column: 1 / -1;
    }

    .section-title {
      font-size: 18px;
      font-weight: 700;
      color: #162337;
      margin-bottom: -8px;
    }

    .section-copy {
      color: #5b6472;
      line-height: 1.5;
      margin-bottom: 4px;
    }

    .company-form mat-form-field {
      width: 100%;
    }

    .preview {
      display: flex;
      flex-direction: column;
      gap: 4px;
      padding: 14px 16px;
      border-radius: 14px;
      background: #fff;
      border: 1px dashed #cad5e2;
    }

    .preview-label {
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #637083;
    }

    .actions {
      display: flex;
      justify-content: flex-end;
      gap: 12px;
      margin-top: 8px;
    }

    .error {
      color: #b3261e;
      font-weight: 500;
    }

    @media (max-width: 800px) {
      .header,
      .intro-grid,
      .section {
        grid-template-columns: 1fr;
      }

      .header {
        flex-direction: column;
      }
    }
  `]
})
export class CompanyCreateComponent {
  form = {
    name: '',
    description: '',
    industry: '',
    website: '',
    goal: '',
    profile: 'profitmax',
    platform: {
      template: 'vercel-platforms-starter-kit',
      deploymentTarget: 'vercel',
      tenancy: 'multi-tenant',
      adminSurface: 'shared-dashboard',
      requestedSubdomain: '',
      rootDomain: '',
      customDomain: ''
    },
    agent: {
      provider: 'amazon-bedrock',
      runtime: 'agentcore-ready',
      modelStrategy: 'specialized-agent-supervisor',
      primaryJobToBeDone: '',
      knowledgeSources: `Product and offer documentation
CRM and pipeline data
Website and positioning copy`,
      actionGroups: `lead qualification
outbound personalization
offer pricing review`,
      scopeIn: `Revenue operations
Lead handling
Pipeline support`,
      scopeOut: `Irreversible billing changes
Legal commitments
High-risk account actions without approval`,
      sessionAttributes: `company_id
industry
operator_role`,
      promptSessionAttributes: `north_star_goal
active_offer
current_campaign_window`,
      guardrails: `Ground responses in approved company sources
Escalate pricing and policy exceptions for human approval`,
      approvalPoints: `New pricing changes
Customer-facing commitments
Outbound launches to new lists`,
      evaluationMetrics: `grounding_quality
task_success_rate
tool_success_rate
latency`,
      successMetrics: `qualified_opportunities
meetings_booked
pipeline_value_influenced`
    }
  };

  submitting = false;
  errorMessage = '';

  constructor(
    private apiService: ApiService,
    private router: Router
  ) {}

  getPreviewUrl(): string {
    const customDomain = this.form.platform.customDomain.trim();
    if (customDomain) {
      return `https://${customDomain}`;
    }

    const rootDomain = this.form.platform.rootDomain.trim();
    const tenantSlug = this.getTenantSlug();
    if (rootDomain && tenantSlug) {
      return `https://${tenantSlug}.${rootDomain}`;
    }

    return '';
  }

  private getTenantSlug(): string {
    const candidate = (this.form.platform.requestedSubdomain || this.form.name)
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9-]+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '');

    return candidate;
  }

  private listFromText(value: string): string[] {
    return value
      .split(/\n|,/)
      .map(item => item.trim())
      .filter(Boolean);
  }

  async submit() {
    if (!this.form.name.trim()) {
      return;
    }

    this.submitting = true;
    this.errorMessage = '';

    try {
      const response = await this.apiService.createCompany({
        name: this.form.name.trim(),
        description: this.form.description.trim(),
        industry: this.form.industry.trim(),
        website: this.form.website.trim(),
        goal: this.form.goal.trim(),
        profile: this.form.profile.trim(),
        platform_blueprint: {
          template: this.form.platform.template.trim(),
          deployment_target: this.form.platform.deploymentTarget.trim(),
          tenancy: this.form.platform.tenancy.trim(),
          admin_surface: this.form.platform.adminSurface.trim(),
          requested_subdomain: this.getTenantSlug(),
          root_domain: this.form.platform.rootDomain.trim() || undefined,
          custom_domain: this.form.platform.customDomain.trim() || undefined
        },
        agent_blueprint: {
          provider: this.form.agent.provider.trim(),
          runtime: this.form.agent.runtime.trim(),
          model_strategy: this.form.agent.modelStrategy.trim(),
          primary_job_to_be_done: this.form.agent.primaryJobToBeDone.trim() || this.form.goal.trim() || undefined,
          knowledge_sources: this.listFromText(this.form.agent.knowledgeSources),
          action_groups: this.listFromText(this.form.agent.actionGroups),
          scope_in: this.listFromText(this.form.agent.scopeIn),
          scope_out: this.listFromText(this.form.agent.scopeOut),
          session_attributes: this.listFromText(this.form.agent.sessionAttributes),
          prompt_session_attributes: this.listFromText(this.form.agent.promptSessionAttributes),
          guardrails: this.listFromText(this.form.agent.guardrails),
          approval_points: this.listFromText(this.form.agent.approvalPoints),
          evaluation_metrics: this.listFromText(this.form.agent.evaluationMetrics),
          success_metrics: this.listFromText(this.form.agent.successMetrics)
        }
      });
      const companyId = response?.company?.id;

      if (companyId) {
        await this.router.navigate(['/companies', companyId]);
        return;
      }

      await this.router.navigate(['/companies']);
    } catch (error) {
      console.error('Failed to create company:', error);
      this.errorMessage = 'Failed to create company. Check the API response and try again.';
    } finally {
      this.submitting = false;
    }
  }

  async cancel() {
    await this.router.navigate(['/companies']);
  }
}
