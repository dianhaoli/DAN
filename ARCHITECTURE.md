# DAN Architecture

## System Overview

DAN is a full-stack productivity tracking application with three main components:

1. **Web Application** (Next.js)
2. **Browser Extension** (Chrome Manifest v3)
3. **Backend** (Firebase)

## Data Flow

```
[Browser Extension] → [Firebase Functions] → [Firestore Database] → [Web App]
                              ↓
                      [OpenAI GPT API]
                              ↓
                      [AI Summaries & Insights]
```

## Component Architecture

### 1. Browser Extension

**Technology**: Chrome Manifest v3, TypeScript, Webpack

**Key Files**:
- `background/index.ts` - Service worker for tab tracking
- `background/sessionTracker.ts` - Session logic and metrics
- `content/index.ts` - Content scripts for page analysis
- `popup/` - Popup UI for manual control

**Responsibilities**:
- Track active tabs and domains
- Detect idle/active states
- Calculate focus scores
- Send session data to backend
- Provide manual session controls

**Data Collected**:
- URL and domain
- Page title
- Active time vs idle time
- Tab switches
- Session duration

**Privacy**: No keystrokes, page content, or sensitive data collected

### 2. Web Application

**Technology**: Next.js 14, React, TailwindCSS, Firebase SDK

**Structure**:
```
web/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── page.tsx           # Landing page
│   │   ├── dashboard/         # Main dashboard
│   │   │   ├── page.tsx       # Dashboard home
│   │   │   ├── social/        # Friend feed
│   │   │   ├── leaderboard/   # Rankings
│   │   │   ├── sessions/      # Session history
│   │   │   ├── insights/      # AI insights
│   │   │   └── todos/         # Task management
│   ├── components/            # Reusable components
│   │   ├── dashboard/         # Dashboard-specific
│   │   └── social/            # Social features
│   ├── contexts/              # React contexts
│   │   └── AuthContext.tsx    # Authentication state
│   ├── hooks/                 # Custom hooks
│   │   └── useAuth.ts         # Auth logic
│   └── lib/                   # Utilities
│       └── firebase.ts        # Firebase config
```

**Key Features**:
- Server-side rendering (SSR) for landing
- Client-side for dashboard (real-time updates)
- Firebase Authentication integration
- Firestore real-time listeners
- Responsive design (mobile-first)

### 3. Backend (Firebase)

**Technology**: Firebase Functions, Firestore, TypeScript

**Cloud Functions**:

1. **Express API** (`api`)
   - HTTP endpoint for session creation
   - Receives data from extension

2. **Firestore Triggers**
   - `onSessionCreate` - Update user stats, check badges, create activities
   
3. **Scheduled Functions**
   - `updateLeaderboardsDaily` - Refresh leaderboards
   - `generateWeeklySummaries` - AI summaries every Sunday

4. **Callable Functions**
   - `addFriend` - Friend management
   - `removeFriend` - Remove friend

**Handlers**:
- `sessions.ts` - Session creation
- `ai.ts` - OpenAI integration for summaries
- `gamification.ts` - XP, levels, badges
- `leaderboards.ts` - Ranking calculations
- `weeklySummary.ts` - Weekly digest generation

### 4. Shared Package

**Technology**: TypeScript

**Purpose**: Type definitions and utilities shared across all components

**Exports**:
- Type definitions (User, Session, Badge, etc.)
- Constants (XP rates, badge definitions, study domains)
- Utility functions (XP calculation, level progression, formatting)

## Database Schema (Firestore)

### Collections

**users**
```typescript
{
  id: string (document ID = auth UID)
  email: string
  displayName: string
  photoURL: string
  xp: number
  level: number
  streak: number
  longestStreak: number
  totalStudyTime: number
  friends: string[]
  isPublic: boolean
  createdAt: Timestamp
  updatedAt: Timestamp
}
```

**sessions**
```typescript
{
  id: string (auto-generated)
  userId: string
  startTime: Timestamp
  endTime: Timestamp
  duration: number (seconds)
  topic: string
  domains: string[]
  focusScore: number (0-1)
  productivityScore: number (0-100)
  tabSwitches: number
  activeTime: number
  idleTime: number
  xpEarned: number
  aiSummary: string
  topics: string[]
  source: 'extension' | 'manual'
  platform: string
}
```

**userStats**
```typescript
{
  userId: string (document ID)
  totalSessions: number
  totalHours: number
  averageFocusScore: number
  averageProductivityScore: number
  topicDistribution: { [topic: string]: number }
  studyHeatmap: { [date: string]: number }
  weeklyTrend: number[]
}
```

**badges**
```typescript
{
  id: string
  name: string
  description: string
  icon: string
  requirement: string
  rarity: 'common' | 'rare' | 'epic' | 'legendary'
}
```

**userBadges**
```typescript
{
  userId: string
  badgeId: string
  earnedAt: Timestamp
}
```

**activities**
```typescript
{
  id: string
  userId: string
  userName: string
  userPhoto: string
  type: 'session_complete' | 'badge_earned' | 'level_up' | 'streak_milestone'
  sessionId?: string
  topic?: string
  duration?: number
  xpEarned?: number
  badgeId?: string
  badgeName?: string
  newLevel?: number
  timestamp: Timestamp
  reactions: { [emoji: string]: string[] }
}
```

**leaderboards**
```typescript
{
  id: string
  name: string
  type: 'hours' | 'xp' | 'productivity' | 'streak'
  period: 'daily' | 'weekly' | 'monthly' | 'all-time'
  scope: 'global' | 'friends'
  entries: LeaderboardEntry[]
  updatedAt: Timestamp
}
```

**todos**
```typescript
{
  id: string
  userId: string
  title: string
  description: string
  estimatedMinutes: number
  dueDate: Timestamp
  status: 'pending' | 'in_progress' | 'completed'
  priority: 'low' | 'medium' | 'high'
  xpReward: number
  linkedSessionId: string
}
```

**weeklySummaries**
```typescript
{
  id: string
  userId: string
  weekStart: Timestamp
  weekEnd: Timestamp
  totalHours: number
  totalSessions: number
  averageFocusScore: number
  xpEarned: number
  newBadges: string[]
  streakAtEnd: number
  topTopics: { topic: string, minutes: number }[]
  aiSummary: string
  improvements: string[]
  suggestions: string[]
}
```

## Security

### Firestore Rules

- Users can only read/write their own data
- Friends can view each other's sessions (if public)
- Badges and leaderboards: read-only (server-side writes only)
- Activities: create own, read friends'

### Authentication

- Firebase Auth with Google OAuth
- JWT tokens for API requests
- Secure HTTP-only cookies

### Extension Security

- Minimal permissions requested
- No access to sensitive tabs (banking, passwords)
- Data encrypted in transit
- Local storage for session state only

## AI Integration

### OpenAI GPT-4o-mini

**Use Cases**:
1. Session summaries (1-2 sentences)
2. Weekly digest generation
3. Productivity insights
4. Topic extraction

**Implementation**:
- Async, non-blocking
- Fallback to default text if API fails
- Rate limiting and caching planned

## Scalability Considerations

### Current (MVP)

- Single region Firebase
- Direct Firestore queries
- No caching layer
- Suitable for <10k users

### Future Improvements

1. **Caching**: Redis for leaderboards and stats
2. **CDN**: Cloudflare for static assets
3. **Database**: Partition by user ID ranges
4. **Functions**: Increase memory/timeout for large ops
5. **Real-time**: Use Firebase Realtime Database for live sessions
6. **Analytics**: BigQuery for data warehouse

## Monitoring & Observability

### Planned

- Firebase Performance Monitoring
- Firestore usage tracking
- Function execution metrics
- Error logging (Sentry)
- User analytics (PostHog)

## Development Workflow

1. Local development with Firebase Emulators
2. Feature branches for new work
3. PR reviews before merge
4. Staging deployment (Firebase preview channels)
5. Production deployment (Vercel + Firebase)

## Deployment

### Web App
- **Platform**: Vercel
- **Build**: `next build`
- **Environment**: Production env vars

### Backend
- **Platform**: Firebase
- **Deploy**: `firebase deploy`
- **Regions**: us-central1 (default)

### Extension
- **Build**: Webpack bundle
- **Platform**: Chrome Web Store
- **Updates**: Automatic via store

## Performance Targets

- **Web App Load**: < 2s (FCP)
- **Dashboard Render**: < 1s
- **Extension Overhead**: < 5MB memory
- **Function Cold Start**: < 3s
- **Firestore Query**: < 500ms

## Cost Estimates (MVP)

- **Firebase**: Free tier (Spark plan) initially
- **Vercel**: Free tier (hobby)
- **OpenAI**: ~$5-20/month (depending on usage)
- **Chrome Web Store**: $5 one-time fee

For 1000 active users: ~$50-100/month

