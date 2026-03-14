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
          <p>Start a new BuizSwarm company with a clear goal and operating context.</p>
        </div>
        <button mat-stroked-button color="primary" (click)="cancel()">
          <mat-icon>arrow_back</mat-icon>
          Back
        </button>
      </div>

      <mat-card>
        <mat-card-content>
          <form class="company-form" (ngSubmit)="submit()">
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
              <mat-label>Description</mat-label>
              <textarea matInput rows="4" [(ngModel)]="form.description" name="description"></textarea>
            </mat-form-field>

            <mat-form-field appearance="outline">
              <mat-label>Primary goal</mat-label>
              <textarea matInput rows="4" [(ngModel)]="form.goal" name="goal"></textarea>
            </mat-form-field>

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
      max-width: 900px;
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
      max-width: 560px;
    }

    .company-form {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }

    .company-form mat-form-field {
      width: 100%;
    }

    .company-form mat-form-field:nth-of-type(4),
    .company-form mat-form-field:nth-of-type(5),
    .error,
    .actions {
      grid-column: 1 / -1;
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
  `]
})
export class CompanyCreateComponent {
  form = {
    name: '',
    description: '',
    industry: '',
    website: '',
    goal: ''
  };

  submitting = false;
  errorMessage = '';

  constructor(
    private apiService: ApiService,
    private router: Router
  ) {}

  async submit() {
    if (!this.form.name.trim()) {
      return;
    }

    this.submitting = true;
    this.errorMessage = '';

    try {
      const response = await this.apiService.createCompany({ ...this.form });
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
