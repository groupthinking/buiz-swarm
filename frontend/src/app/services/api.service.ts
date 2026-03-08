import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  // Dashboard
  async getDashboardOverview(): Promise<any> {
    return this.http.get(`${this.baseUrl}/dashboard/overview`).toPromise();
  }

  // Companies
  async getCompanies(): Promise<any> {
    return this.http.get(`${this.baseUrl}/companies`).toPromise();
  }

  async getCompany(id: string): Promise<any> {
    return this.http.get(`${this.baseUrl}/companies/${id}`).toPromise();
  }

  async createCompany(data: any): Promise<any> {
    return this.http.post(`${this.baseUrl}/companies`, data).toPromise();
  }

  async deleteCompany(id: string): Promise<any> {
    return this.http.delete(`${this.baseUrl}/companies/${id}`).toPromise();
  }

  async triggerDailyCycle(companyId: string): Promise<any> {
    return this.http.post(`${this.baseUrl}/companies/${companyId}/daily-cycle`, {}).toPromise();
  }

  // Tasks
  async getCompanyTasks(companyId: string): Promise<any> {
    return this.http.get(`${this.baseUrl}/companies/${companyId}/tasks`).toPromise();
  }

  async createTask(companyId: string, data: any): Promise<any> {
    return this.http.post(`${this.baseUrl}/companies/${companyId}/tasks`, data).toPromise();
  }

  // Billing
  async getCompanyBilling(companyId: string): Promise<any> {
    return this.http.get(`${this.baseUrl}/companies/${companyId}/billing`).toPromise();
  }

  async getCompanyTransactions(companyId: string): Promise<any> {
    return this.http.get(`${this.baseUrl}/companies/${companyId}/transactions`).toPromise();
  }

  async recordRevenue(companyId: string, data: any): Promise<any> {
    return this.http.post(`${this.baseUrl}/companies/${companyId}/revenue`, data).toPromise();
  }

  // Infrastructure
  async getInfrastructure(companyId: string): Promise<any> {
    return this.http.get(`${this.baseUrl}/companies/${companyId}/infrastructure`).toPromise();
  }

  async provisionInfrastructure(companyId: string): Promise<any> {
    return this.http.post(`${this.baseUrl}/companies/${companyId}/infrastructure/provision`, {}).toPromise();
  }

  // System
  async getSystemHealth(): Promise<any> {
    return this.http.get(`${this.baseUrl}/system/health`).toPromise();
  }

  async getMcpStatus(): Promise<any> {
    return this.http.get(`${this.baseUrl}/system/mcp-status`).toPromise();
  }
}
