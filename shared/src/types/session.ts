export interface StudySession {
  id: string;
  userId: string;
  
  // Time tracking
  startTime: Date;
  endTime?: Date;
  duration: number; // in seconds
  
  // Content
  topic: string;
  category?: string;
  domains: string[]; // URLs visited
  title?: string;
  
  // Metrics
  focusScore: number; // 0-1
  productivityScore: number; // 0-100
  tabSwitches: number;
  activeTime: number; // seconds actually active
  idleTime: number; // seconds idle
  
  // Metadata
  source: 'extension' | 'manual';
  platform: string;
  
  // AI
  aiSummary?: string;
  topics?: string[];
  
  // Gamification
  xpEarned: number;
  
  createdAt: Date;
  updatedAt: Date;
}

export interface SessionMetrics {
  activeTime: number;
  idleTime: number;
  tabSwitches: number;
  domains: string[];
  keystrokes?: number; // optional, for future use
}

export interface SessionActivity {
  timestamp: Date;
  domain: string;
  title: string;
  isActive: boolean;
  duration: number; // seconds
}

export type SessionStatus = 'active' | 'paused' | 'completed' | 'cancelled';

