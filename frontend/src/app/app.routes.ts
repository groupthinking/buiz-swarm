import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'dashboard',
    pathMatch: 'full'
  },
  {
    path: 'dashboard',
    loadComponent: () => import('./components/dashboard/dashboard.component').then(m => m.DashboardComponent)
  },
  {
    path: 'companies',
    loadComponent: () => import('./components/companies/companies.component').then(m => m.CompaniesComponent)
  },
  {
    path: 'companies/:id',
    loadComponent: () => import('./components/company-detail/company-detail.component').then(m => m.CompanyDetailComponent)
  },
  {
    path: 'agents',
    loadComponent: () => import('./components/agents/agents.component').then(m => m.AgentsComponent)
  },
  {
    path: 'tasks',
    loadComponent: () => import('./components/tasks/tasks.component').then(m => m.TasksComponent)
  },
  {
    path: 'billing',
    loadComponent: () => import('./components/billing/billing.component').then(m => m.BillingComponent)
  },
  {
    path: 'settings',
    loadComponent: () => import('./components/settings/settings.component').then(m => m.SettingsComponent)
  },
  {
    path: '**',
    redirectTo: 'dashboard'
  }
];
