import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatChipsModule } from '@angular/material/chips';

@Component({
  selector: 'app-tasks',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatTableModule, MatChipsModule],
  template: `
    <div class="tasks-page">
      <h1>Tasks</h1>
      
      <mat-card>
        <mat-card-content>
          <p>Task management interface coming soon...</p>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [`
    .tasks-page {
      max-width: 1200px;
      margin: 0 auto;
    }
    
    h1 {
      margin-bottom: 24px;
    }
  `]
})
export class TasksComponent {}
