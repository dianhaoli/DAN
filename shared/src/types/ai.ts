export interface AISummary {
  sessionId: string;
  userId: string;
  
  summary: string; // 1-2 sentence summary
  topics: string[];
  keyPoints?: string[];
  
  // Sentiment
  sentiment?: 'positive' | 'neutral' | 'negative';
  
  generatedAt: Date;
}

export interface AIInsight {
  id: string;
  userId: string;
  
  type: 'pattern' | 'suggestion' | 'achievement' | 'warning';
  
  title: string;
  message: string;
  
  // Data backing the insight
  metadata?: Record<string, any>;
  
  // User interaction
  isRead: boolean;
  isDismissed: boolean;
  
  createdAt: Date;
}

export interface WeeklySummary {
  id: string;
  userId: string;
  
  weekStart: Date;
  weekEnd: Date;
  
  // Stats
  totalHours: number;
  totalSessions: number;
  averageFocusScore: number;
  averageProductivityScore: number;
  
  // XP & Gamification
  xpEarned: number;
  newBadges: string[];
  streakAtEnd: number;
  
  // Topics
  topTopics: Array<{ topic: string; minutes: number }>;
  
  // AI insights
  aiSummary: string;
  improvements: string[];
  suggestions: string[];
  
  // Trends
  focusTrend: number; // % change from previous week
  hoursTrend: number;
  
  // Best time to study
  peakProductivityHour?: number;
  
  createdAt: Date;
}

export interface ProductivityScore {
  focus: number; // 0-1
  consistency: number; // 0-1
  depth: number; // 0-1
  engagement: number; // 0-1
  overall: number; // 0-100 weighted score
}

