# 🔧 Frontend-Backend Sync Check

## Current Architecture (Actual)

✅ **Backend**: FastAPI (Python) on `localhost:8000`
✅ **Database**: PostgreSQL (Supabase recommended)
✅ **Auth**: Firebase Authentication
✅ **Frontend**: Next.js on `localhost:3000`
✅ **Extension**: Chrome Extension → FastAPI

## Quick Diagnostic

Run this to check what's broken:

```bash
# Check if backend is running
curl http://localhost:8000/api/health

# Check if frontend can reach backend
curl http://localhost:3000

# Check Redis
redis-cli ping

# Check database connection (if you have psql)
psql "$DATABASE_URL" -c "SELECT 1;"
```

## What Needs to Be Synced

### 1. Environment Variables

**Backend** (`backend_fastapi/.env`):
```env
DATABASE_URL=postgresql://...
REDIS_URL=redis://localhost:6379/0
FIREBASE_PROJECT_ID=dann-91ae4
FIREBASE_CREDENTIALS_PATH=./dann-91ae4-firebase-adminsdk-fbsvc-c517cef228.json
OPENAI_API_KEY=sk-...
```

**Frontend** (`web/.env.local`):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_FIREBASE_API_KEY=...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=...
NEXT_PUBLIC_FIREBASE_PROJECT_ID=dann-91ae4
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=...
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=...
NEXT_PUBLIC_FIREBASE_APP_ID=...
```

### 2. Services Running

- [ ] FastAPI backend (`uvicorn app.main:app --reload`)
- [ ] Redis (`redis-server` or Docker)
- [ ] PostgreSQL (Supabase or local)
- [ ] Next.js frontend (`npm run dev`)
- [ ] Celery workers (optional, for background jobs)

### 3. Database Migrations

```bash
cd backend_fastapi
alembic upgrade head
```

### 4. Extension Config

Extension should point to: `http://localhost:8000/api`

## Common Sync Issues

### Issue: "Cannot connect to backend"
**Fix**: 
1. Check `NEXT_PUBLIC_API_URL` in `web/.env.local`
2. Verify FastAPI is running on port 8000
3. Check CORS settings in `backend_fastapi/app/main.py`

### Issue: "401 Unauthorized"
**Fix**:
1. Sign in to web app first (creates Firebase token)
2. Extension syncs token automatically
3. Check Firebase credentials path in backend `.env`

### Issue: "Database connection failed"
**Fix**:
1. Verify `DATABASE_URL` in backend `.env`
2. Check Supabase project is active
3. Run migrations: `alembic upgrade head`

### Issue: "Redis connection failed"
**Fix**:
1. Start Redis: `docker run -d -p 6379:6379 redis:7-alpine`
2. Or: `redis-server` (if installed locally)
3. Verify `REDIS_URL` in backend `.env`

## Quick Fix Script

See `fix_sync.sh` for automated fixes.
