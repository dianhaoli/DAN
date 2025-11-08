export interface FriendActivity {
  id: string;
  userId: string;
  userName: string;
  userPhoto?: string;
  
  type: 'session_complete' | 'badge_earned' | 'streak_milestone' | 'level_up';
  
  // Session data
  sessionId?: string;
  topic?: string;
  duration?: number;
  xpEarned?: number;
  
  // Badge data
  badgeId?: string;
  badgeName?: string;
  
  // Streak data
  streakDays?: number;
  
  // Level data
  newLevel?: number;
  
  timestamp: Date;
  reactions: Record<string, string[]>; // emoji -> userIds
}

export interface LeaderboardEntry {
  userId: string;
  userName: string;
  userPhoto?: string;
  rank: number;
  score: number;
  change: number; // rank change from last period
}

export interface Leaderboard {
  id: string;
  name: string;
  type: 'hours' | 'xp' | 'productivity' | 'streak';
  period: 'daily' | 'weekly' | 'monthly' | 'all-time';
  scope: 'global' | 'friends';
  entries: LeaderboardEntry[];
  updatedAt: Date;
}

export interface Challenge {
  id: string;
  creatorId: string;
  participantIds: string[];
  
  name: string;
  description: string;
  
  type: 'duel' | 'sprint' | 'team';
  goal: number; // target minutes or XP
  metric: 'hours' | 'xp' | 'sessions';
  
  startDate: Date;
  endDate: Date;
  
  status: 'pending' | 'active' | 'completed' | 'cancelled';
  
  // Betting
  wager?: number; // virtual points
  
  createdAt: Date;
  updatedAt: Date;
}

