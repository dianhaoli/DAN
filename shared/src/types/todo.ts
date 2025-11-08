export interface Todo {
  id: string;
  userId: string;
  
  title: string;
  description?: string;
  
  // Scheduling
  estimatedMinutes?: number;
  dueDate?: Date;
  scheduledDate?: Date;
  
  // Status
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  completedAt?: Date;
  
  // Session linking
  linkedSessionId?: string;
  actualMinutes?: number;
  
  // Categorization
  category?: string;
  priority: 'low' | 'medium' | 'high';
  
  // XP
  xpReward: number;
  
  createdAt: Date;
  updatedAt: Date;
}

