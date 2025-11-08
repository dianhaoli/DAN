export interface User {
  id: string;
  email: string;
  displayName: string;
  photoURL?: string;
  createdAt: Date;
  updatedAt: Date;
  
  // Gamification
  xp: number;
  level: number;
  streak: number;
  longestStreak: number;
  totalStudyTime: number; // in minutes
  
  // Stats
  weeklyGoal?: number; // minutes per week
  preferredStudyTime?: 'morning' | 'afternoon' | 'evening' | 'night';
  
  // Social
  friends: string[]; // user IDs
  isPublic: boolean;
}

export interface UserStats {
  userId: string;
  totalSessions: number;
  totalHours: number;
  averageFocusScore: number;
  averageProductivityScore: number;
  topicDistribution: Record<string, number>; // topic -> minutes
  studyHeatmap: Record<string, number>; // date -> minutes
  weeklyTrend: number[]; // last 12 weeks
}

export interface Badge {
  id: string;
  name: string;
  description: string;
  icon: string;
  requirement: string;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
}

export interface UserBadge {
  userId: string;
  badgeId: string;
  earnedAt: Date;
}

