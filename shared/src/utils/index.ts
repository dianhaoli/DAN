import { LEVEL_THRESHOLDS, XP_PER_MINUTE, FOCUS_MULTIPLIER_MAX, FOCUS_MULTIPLIER_MIN, PRODUCTIVITY_WEIGHTS } from '../constants';
import type { ProductivityScore } from '../types';

/**
 * Calculate XP earned from a study session
 */
export function calculateXP(durationMinutes: number, focusScore: number): number {
  const focusMultiplier = FOCUS_MULTIPLIER_MIN + (focusScore * (FOCUS_MULTIPLIER_MAX - FOCUS_MULTIPLIER_MIN));
  return Math.floor(durationMinutes * XP_PER_MINUTE * focusMultiplier);
}

/**
 * Calculate user level from total XP
 */
export function calculateLevel(totalXP: number): number {
  let level = 0;
  for (let i = LEVEL_THRESHOLDS.length - 1; i >= 0; i--) {
    if (totalXP >= LEVEL_THRESHOLDS[i]) {
      level = i;
      break;
    }
  }
  return level;
}

/**
 * Get XP required for next level
 */
export function getXPForNextLevel(currentLevel: number): number {
  if (currentLevel >= LEVEL_THRESHOLDS.length - 1) {
    return LEVEL_THRESHOLDS[LEVEL_THRESHOLDS.length - 1];
  }
  return LEVEL_THRESHOLDS[currentLevel + 1];
}

/**
 * Get XP progress towards next level (0-1)
 */
export function getLevelProgress(totalXP: number): number {
  const currentLevel = calculateLevel(totalXP);
  const currentLevelXP = LEVEL_THRESHOLDS[currentLevel];
  const nextLevelXP = getXPForNextLevel(currentLevel);
  
  if (nextLevelXP === currentLevelXP) return 1;
  
  return (totalXP - currentLevelXP) / (nextLevelXP - currentLevelXP);
}

/**
 * Calculate focus score from session metrics
 */
export function calculateFocusScore(
  activeTime: number,
  totalTime: number,
  tabSwitches: number
): number {
  if (totalTime === 0) return 0;
  
  // Active time ratio (0-1)
  const activeRatio = activeTime / totalTime;
  
  // Tab switch penalty (more switches = lower score)
  const avgSwitchesPerMinute = (tabSwitches / (totalTime / 60));
  const switchPenalty = Math.max(0, 1 - (avgSwitchesPerMinute / 10));
  
  // Combined focus score
  return (activeRatio * 0.7) + (switchPenalty * 0.3);
}

/**
 * Calculate productivity score (0-100)
 */
export function calculateProductivityScore(
  focusScore: number,
  consistencyScore: number,
  depthScore: number,
  engagementScore: number
): ProductivityScore {
  const overall = Math.round(
    (focusScore * PRODUCTIVITY_WEIGHTS.focus +
     consistencyScore * PRODUCTIVITY_WEIGHTS.consistency +
     depthScore * PRODUCTIVITY_WEIGHTS.depth +
     engagementScore * PRODUCTIVITY_WEIGHTS.engagement) * 100
  );
  
  return {
    focus: focusScore,
    consistency: consistencyScore,
    depth: depthScore,
    engagement: engagementScore,
    overall: Math.min(100, Math.max(0, overall)),
  };
}

/**
 * Check if a domain is a study domain
 */
export function isStudyDomain(domain: string, studyDomains: string[]): boolean {
  return studyDomains.some(d => domain.includes(d));
}

/**
 * Extract domain from URL
 */
export function extractDomain(url: string): string {
  try {
    const urlObj = new URL(url);
    return urlObj.hostname.replace('www.', '');
  } catch {
    return '';
  }
}

/**
 * Format duration in minutes to human-readable string
 */
export function formatDuration(minutes: number): string {
  if (minutes < 60) {
    return `${Math.round(minutes)}m`;
  }
  
  const hours = Math.floor(minutes / 60);
  const mins = Math.round(minutes % 60);
  
  if (mins === 0) {
    return `${hours}h`;
  }
  
  return `${hours}h ${mins}m`;
}

/**
 * Calculate consistency score based on sessions over time
 */
export function calculateConsistencyScore(
  sessionsThisWeek: number,
  streak: number
): number {
  // Sessions per week (target: 5+)
  const sessionScore = Math.min(1, sessionsThisWeek / 5);
  
  // Streak bonus (target: 7+ days)
  const streakScore = Math.min(1, streak / 7);
  
  return (sessionScore * 0.6) + (streakScore * 0.4);
}

/**
 * Format date for display
 */
export function formatDate(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(date);
}

/**
 * Format time for display
 */
export function formatTime(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(date);
}

/**
 * Get relative time string (e.g., "2 hours ago")
 */
export function getRelativeTime(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  
  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  
  const diffWeeks = Math.floor(diffDays / 7);
  return `${diffWeeks}w ago`;
}

