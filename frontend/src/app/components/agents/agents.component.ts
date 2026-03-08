import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-agents',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatIconModule],
  template: `
    <div class="agents-page">
      <h1>Agents</h1>
      
      <div class="agents-grid">
        <mat-card class="agent-card">
          <mat-card-header>
            <mat-icon mat-card-avatar class="agent-icon ceo">psychology</mat-icon>
            <mat-card-title>CEO Agent</mat-card-title>
            <mat-card-subtitle>Strategic Decision Maker</mat-card-subtitle>
          </mat-card-header>
          <mat-card-content>
            <p>Makes strategic decisions, evaluates business state, and coordinates other agents.</p>
            <div class="capabilities">
              <span class="capability">Strategic Planning</span>
              <span class="capability">Decision Making</span>
              <span class="capability">Business Analysis</span>
            </div>
          </mat-card-content>
        </mat-card>
        
        <mat-card class="agent-card">
          <mat-card-header>
            <mat-icon mat-card-avatar class="agent-icon engineering">code</mat-icon>
            <mat-card-title>Engineering Agent</mat-card-title>
            <mat-card-subtitle>Code & Infrastructure</mat-card-subtitle>
          </mat-card-header>
          <mat-card-content>
            <p>Generates code, manages deployments, and handles infrastructure.</p>
            <div class="capabilities">
              <span class="capability">Code Generation</span>
              <span class="capability">Deployment</span>
              <span class="capability">Bug Fixes</span>
            </div>
          </mat-card-content>
        </mat-card>
        
        <mat-card class="agent-card">
          <mat-card-header>
            <mat-icon mat-card-avatar class="agent-icon marketing">campaign</mat-icon>
            <mat-card-title>Marketing Agent</mat-card-title>
            <mat-card-subtitle>Growth & Outreach</mat-card-subtitle>
          </mat-card-header>
          <mat-card-content>
            <p>Manages ad campaigns, creates content, and handles outreach.</p>
            <div class="capabilities">
              <span class="capability">Ad Campaigns</span>
              <span class="capability">Content Creation</span>
              <span class="capability">Email Outreach</span>
            </div>
          </mat-card-content>
        </mat-card>
        
        <mat-card class="agent-card">
          <mat-card-header>
            <mat-icon mat-card-avatar class="agent-icon support">support_agent</mat-icon>
            <mat-card-title>Support Agent</mat-card-title>
            <mat-card-subtitle>Customer Service</mat-card-subtitle>
          </mat-card-header>
          <mat-card-content>
            <p>Handles customer inquiries, manages tickets, and maintains knowledge base.</p>
            <div class="capabilities">
              <span class="capability">Email Responses</span>
              <span class="capability">Ticket Management</span>
              <span class="capability">Knowledge Base</span>
            </div>
          </mat-card-content>
        </mat-card>
      </div>
    </div>
  `,
  styles: [`
    .agents-page {
      max-width: 1200px;
      margin: 0 auto;
    }
    
    h1 {
      margin-bottom: 24px;
    }
    
    .agents-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 20px;
    }
    
    .agent-card {
      .agent-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 48px;
        height: 48px;
        border-radius: 50%;
        color: white;
        
        &.ceo {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        &.engineering {
          background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }
        
        &.marketing {
          background: linear-gradient(135deg, #fc4a1a 0%, #f7b733 100%);
        }
        
        &.support {
          background: linear-gradient(135deg, #2193b0 0%, #6dd5ed 100%);
        }
      }
      
      .capabilities {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 16px;
        
        .capability {
          padding: 4px 12px;
          background: #f5f5f5;
          border-radius: 16px;
          font-size: 12px;
          color: #666;
        }
      }
    }
  `]
})
export class AgentsComponent {}
