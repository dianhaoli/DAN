# DAN - Strava for Studying

A gamified productivity tracker that measures and improves how people study — combining Strava's social model with AI insights and a browser extension for passive tracking.

## Quick Start

See **[GET_STARTED.md](./GET_STARTED.md)** for setup instructions.

## Architecture

- **Frontend**: Next.js 14, TailwindCSS, React Query
- **Extension**: Chrome Manifest v3
- **Backend**: FastAPI (Python) + PostgreSQL
- **Auth**: Firebase Authentication
- **AI/ML**: DistilBERT, XGBoost, OpenAI GPT
- **Hosting**: Vercel (web), Render/Railway (backend)

See **[ARCHITECTURE.md](./ARCHITECTURE.md)** for detailed architecture.

## Project Structure

```
DAN/
├── web/                 # Next.js frontend
├── extension/           # Chrome extension
├── backend_fastapi/    # FastAPI backend
├── shared/              # Shared TypeScript types
└── scripts/             # Utility scripts
```

## Features

- Automatic session tracking via browser extension
- Gamification (XP, levels, badges, streaks)
- Social features (friends, leaderboards, activity feed)
- AI-powered insights and summaries
- Todo/task management
- Productivity scoring with ML models

See **[FEATURES.md](./FEATURES.md)** for complete feature list.

## Development

1. **Backend**: `cd backend_fastapi && uvicorn app.main:app --reload`
2. **Frontend**: `cd web && npm run dev`
3. **Extension**: `cd extension && npm run build`

Run `./fix_sync.sh` to diagnose sync issues.

## Documentation

- **[GET_STARTED.md](./GET_STARTED.md)** - Quick setup guide
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - System architecture
- **[SYNC_CHECK.md](./SYNC_CHECK.md)** - Troubleshooting sync issues
- **[FEATURES.md](./FEATURES.md)** - Complete feature list
