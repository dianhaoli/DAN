# DAN - Strava for Studying

**Track, gamify, and share your focus.**

## Overview

DAN is a gamified productivity tracker that measures and improves how people study — combining Strava's social model with AI insights and a browser extension for passive tracking.

## Team

- **Ashia** – LLMs / Backend (AI insights, summaries, productivity models)
- **Dan** – Frontend / Backend (integration, data APIs, dashboards)
- **Theo** – Frontend (UI/UX, gamification, feed)
- **Suvas** – Backend (database, extension data ingestion, leaderboards)

## Architecture

```
dan/
├── web/              # Next.js web application
├── extension/        # Chrome browser extension
├── backend/          # Firebase Cloud Functions
└── shared/           # Shared types and utilities
```

## Tech Stack

- **Frontend**: Next.js 14, TailwindCSS, React Query
- **Extension**: Chrome Manifest v3
- **Backend**: Firebase (Firestore, Functions, Auth)
- **AI**: OpenAI GPT-4o-mini
- **Hosting**: Vercel (web), Firebase (backend)


