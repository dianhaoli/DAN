// Study domain whitelist
export const STUDY_DOMAINS = [
  // Learning platforms
  'coursera.org',
  'udemy.com',
  'edx.org',
  'khanacademy.org',
  'brilliant.org',
  'codecademy.com',
  'freecodecamp.org',
  'leetcode.com',
  'hackerrank.com',
  
  // Documentation
  'developer.mozilla.org',
  'docs.python.org',
  'stackoverflow.com',
  'github.com',
  'gitlab.com',
  
  // Productivity tools
  'notion.so',
  'docs.google.com',
  'overleaf.com',
  'quizlet.com',
  'anki.com',
  
  // Research
  'scholar.google.com',
  'arxiv.org',
  'jstor.org',
  'researchgate.net',
  
  // Note-taking
  'evernote.com',
  'onenote.com',
  'roamresearch.com',
  'obsidian.md',
];

// Entertainment/distraction domains (to stop tracking)
export const DISTRACTION_DOMAINS = [
  'youtube.com',
  'netflix.com',
  'reddit.com',
  'twitter.com',
  'facebook.com',
  'instagram.com',
  'tiktok.com',
  'twitch.tv',
  'discord.com',
  'spotify.com',
];

// XP calculation constants
export const XP_PER_MINUTE = 10;
export const FOCUS_MULTIPLIER_MAX = 2.0;
export const FOCUS_MULTIPLIER_MIN = 0.5;

// Level thresholds (XP required for each level)
export const LEVEL_THRESHOLDS = [
  0,      // Level 0
  100,    // Level 1
  250,    // Level 2
  500,    // Level 3
  1000,   // Level 4
  2000,   // Level 5
  3500,   // Level 6
  5500,   // Level 7
  8000,   // Level 8
  11000,  // Level 9
  15000,  // Level 10
  20000,  // Level 11
  26000,  // Level 12
  33000,  // Level 13
  41000,  // Level 14
  50000,  // Level 15
];

// Badge definitions
export interface BadgeDefinition {
  id: string;
  name: string;
  description: string;
  icon: string;
  requirement: string;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  checkFunction: (userData: any) => boolean;
}

export const BADGES: BadgeDefinition[] = [
  {
    id: 'first-session',
    name: 'First Steps',
    description: 'Complete your first study session',
    icon: '🎯',
    requirement: '1 session',
    rarity: 'common',
    checkFunction: (data) => data.totalSessions >= 1,
  },
  {
    id: 'streak-5',
    name: 'Consistent',
    description: 'Maintain a 5-day study streak',
    icon: '🔥',
    requirement: '5 day streak',
    rarity: 'common',
    checkFunction: (data) => data.streak >= 5,
  },
  {
    id: 'streak-30',
    name: 'Dedicated',
    description: 'Maintain a 30-day study streak',
    icon: '🔥🔥',
    requirement: '30 day streak',
    rarity: 'rare',
    checkFunction: (data) => data.streak >= 30,
  },
  {
    id: 'streak-100',
    name: 'Unstoppable',
    description: 'Maintain a 100-day study streak',
    icon: '🔥🔥🔥',
    requirement: '100 day streak',
    rarity: 'legendary',
    checkFunction: (data) => data.streak >= 100,
  },
  {
    id: 'hours-10',
    name: 'Getting Started',
    description: 'Study for 10 total hours',
    icon: '⏰',
    requirement: '10 hours',
    rarity: 'common',
    checkFunction: (data) => data.totalStudyTime >= 600,
  },
  {
    id: 'hours-100',
    name: 'Committed Learner',
    description: 'Study for 100 total hours',
    icon: '📚',
    requirement: '100 hours',
    rarity: 'rare',
    checkFunction: (data) => data.totalStudyTime >= 6000,
  },
  {
    id: 'hours-1000',
    name: 'Master Scholar',
    description: 'Study for 1000 total hours',
    icon: '🎓',
    requirement: '1000 hours',
    rarity: 'legendary',
    checkFunction: (data) => data.totalStudyTime >= 60000,
  },
  {
    id: 'focus-hero',
    name: 'Focus Hero',
    description: 'Achieve 95%+ focus score in a session',
    icon: '🎯',
    requirement: '95% focus',
    rarity: 'rare',
    checkFunction: (data) => data.highestFocusScore >= 0.95,
  },
  {
    id: 'early-bird',
    name: 'Early Bird',
    description: 'Study before 7 AM for 5 days',
    icon: '🌅',
    requirement: '5 early sessions',
    rarity: 'rare',
    checkFunction: (data) => data.earlyMorningSessions >= 5,
  },
  {
    id: 'night-owl',
    name: 'Night Owl',
    description: 'Study after 11 PM for 5 days',
    icon: '🦉',
    requirement: '5 late sessions',
    rarity: 'rare',
    checkFunction: (data) => data.lateNightSessions >= 5,
  },
];

// Productivity score weights
export const PRODUCTIVITY_WEIGHTS = {
  focus: 0.3,
  consistency: 0.25,
  depth: 0.25,
  engagement: 0.2,
};

// Session tracking constants
export const IDLE_THRESHOLD_SECONDS = 120; // 2 minutes
export const TRACKING_INTERVAL_SECONDS = 30;
export const MIN_SESSION_DURATION_SECONDS = 60; // 1 minute

