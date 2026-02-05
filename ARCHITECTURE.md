# DAN Architecture

## System Overview

DAN is a full-stack productivity tracking application with three main components:

1. **Web Application** (Next.js)
2. **Browser Extension** (Chrome Manifest v3)
3. **Backend** (FastAPI + PostgreSQL)

## Data Flow

```
[Browser Extension] → [FastAPI Backend] → [PostgreSQL Database] → [Web App]
                              ↓
                      [OpenAI GPT API]
                              ↓
                      [AI Summaries & Insights]
                              ↓
                      [Celery Workers] (ML, AI, Stats)
```

**Authentication**: Firebase Auth (used by both frontend and backend)

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

### 3. Backend (FastAPI)

**Technology**: FastAPI, PostgreSQL, Python, Celery, Redis

**API Endpoints** (`backend_fastapi/app/api/`):
- `auth.py` - Authentication (Firebase token verification)
- `sessions.py` - Session CRUD operations
- `users.py` - User management
- `todos.py` - Todo/task management
- `social.py` - Friends, activities, feed
- `leaderboards.py` - Rankings and leaderboards
- `ai.py` - AI summaries and insights
- `gamification.py` - XP, levels, badges

**Background Workers** (`backend_fastapi/app/workers/`):
- `ml_tasks.py` - ML inference (DistilBERT + XGBoost)
- `ai_tasks.py` - OpenAI API calls (async)
- `stats_tasks.py` - Statistics calculations

**Database**: PostgreSQL (Supabase recommended)
- SQLAlchemy ORM
- Alembic migrations
- Auto-creates users on first Firebase auth

**Authentication**: 
- Firebase Admin SDK verifies tokens
- Auto-creates users in PostgreSQL from Firebase UID

### 4. Shared Package

**Technology**: TypeScript

**Purpose**: Type definitions and utilities shared across all components

**Exports**:
- Type definitions (User, Session, Badge, etc.)
- Constants (XP rates, badge definitions, study domains)
- Utility functions (XP calculation, level progression, formatting)

## Database Schema (PostgreSQL)

### Tables

**users**
- `id` (UUID, primary key)
- `firebase_uid` (string, unique, indexed)
- `email` (string)
- `display_name` (string, nullable)
- `photo_url` (string, nullable)
- `xp` (integer, default 0)
- `level` (integer, default 1)
- `streak` (integer, default 0)
- `longest_streak` (integer, default 0)
- `total_study_time` (integer, seconds, default 0)
- `is_public` (boolean, default true)
- `created_at` (timestamp)
- `updated_at` (timestamp)

**sessions**
- `id` (UUID, primary key)
- `user_id` (UUID, foreign key → users.id)
- `start_time` (timestamp)
- `end_time` (timestamp, nullable)
- `duration` (integer, seconds)
- `topic` (string, nullable)
- `domains` (JSON array)
- `focus_score` (float, 0-1)
- `productivity_score` (float, 0-100)
- `tab_switches` (integer)
- `active_time` (integer, seconds)
- `idle_time` (integer, seconds)
- `xp_earned` (integer)
- `ai_summary` (text, nullable)
- `topics` (JSON array)
- `source` (enum: 'extension' | 'manual')
- `platform` (string)
- `created_at` (timestamp)

**todos**
- `id` (UUID, primary key)
- `user_id` (UUID, foreign key → users.id)
- `title` (string)
- `description` (text, nullable)
- `estimated_minutes` (integer, nullable)
- `due_date` (timestamp, nullable)
- `scheduled_date` (timestamp, nullable)
- `status` (enum: 'pending' | 'in_progress' | 'completed')
- `priority` (enum: 'low' | 'medium' | 'high')
- `category` (string, nullable)
- `xp_reward` (integer, nullable)
- `linked_session_id` (UUID, nullable, foreign key → sessions.id)
- `created_at` (timestamp)
- `updated_at` (timestamp)

**user_stats** (computed/denormalized)
- `user_id` (UUID, primary key, foreign key → users.id)
- `total_sessions` (integer)
- `total_hours` (float)
- `average_focus_score` (float)
- `average_productivity_score` (float)
- `topic_distribution` (JSON)
- `study_heatmap` (JSON)
- `weekly_trend` (JSON array)
- `updated_at` (timestamp)

**badges** (reference data)
- `id` (UUID, primary key)
- `name` (string)
- `description` (text)
- `icon` (string)
- `requirement` (text)
- `rarity` (enum: 'common' | 'rare' | 'epic' | 'legendary')

**user_badges** (many-to-many)
- `user_id` (UUID, foreign key → users.id)
- `badge_id` (UUID, foreign key → badges.id)
- `earned_at` (timestamp)
- Primary key: (user_id, badge_id)

**activities** (social feed)
- `id` (UUID, primary key)
- `user_id` (UUID, foreign key → users.id)
- `type` (enum: 'session_complete' | 'badge_earned' | 'level_up' | 'streak_milestone')
- `session_id` (UUID, nullable, foreign key → sessions.id)
- `topic` (string, nullable)
- `duration` (integer, nullable)
- `xp_earned` (integer, nullable)
- `badge_id` (UUID, nullable, foreign key → badges.id)
- `new_level` (integer, nullable)
- `reactions` (JSON)
- `created_at` (timestamp)

**leaderboards** (cached rankings)
- `id` (UUID, primary key)
- `name` (string)
- `type` (enum: 'hours' | 'xp' | 'productivity' | 'streak')
- `period` (enum: 'daily' | 'weekly' | 'monthly' | 'all-time')
- `scope` (enum: 'global' | 'friends')
- `entries` (JSON array)
- `updated_at` (timestamp)

## Security

### Database Access

- All database access through FastAPI (no direct client access)
- Row-level security enforced in API layer
- Users can only read/write their own data
- Friends can view each other's sessions (if public)
- Badges and leaderboards: read-only (server-side writes only)

### Authentication

- Firebase Auth with Google OAuth (frontend)
- Firebase Admin SDK verifies tokens (backend)
- JWT tokens in Authorization header: `Bearer <firebase_id_token>`
- Auto-creates users in PostgreSQL on first auth

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
- **Environment**: `NEXT_PUBLIC_API_URL` set to production FastAPI URL

### Backend
- **Platform**: Render, Railway, or any Python host
- **Deploy**: 
  - Set environment variables
  - Run migrations: `alembic upgrade head`
  - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Workers**: Deploy Celery workers separately
- **Database**: PostgreSQL (Supabase, Neon, or managed PostgreSQL)

### Extension
- **Build**: `npm run build` in `extension/` directory
- **Platform**: Chrome Web Store
- **Config**: Update API URL in extension config
- **Updates**: Manual rebuild and upload

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

