# 🚀 Get Started - Fix Your Sync Issues

**You don't need to start over!** Your architecture is actually correct. Here's how to get everything synced.

## Quick Diagnosis

Run the diagnostic script:
```bash
./fix_sync.sh
```

This will tell you exactly what's broken.

## The 5-Minute Fix

### Step 1: Environment Variables

**Backend** (`backend_fastapi/.env`):
```bash
cd backend_fastapi
cp env.example .env
# Edit .env with your actual values:
# - DATABASE_URL (from Supabase)
# - REDIS_URL=redis://localhost:6379/0
# - FIREBASE_PROJECT_ID=dann-91ae4
# - FIREBASE_CREDENTIALS_PATH=./dann-91ae4-firebase-adminsdk-fbsvc-c517cef228.json
# - OPENAI_API_KEY=sk-...
```

**Frontend** (`web/.env.local`):
```bash
cd web
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api" > .env.local
# Add your Firebase config (get from Firebase Console)
```

### Step 2: Start Services

**Terminal 1 - Redis:**
```bash
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

**Terminal 2 - Backend:**
```bash
cd backend_fastapi
source venv/bin/activate  # or: python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head  # Run migrations
uvicorn app.main:app --reload --port 8000
```

**Terminal 3 - Frontend:**
```bash
cd web
npm install
npm run dev
```

### Step 3: Test Connection

1. Open http://localhost:8000/api/health (should return `{"status":"healthy"}`)
2. Open http://localhost:3000
3. Sign in with Google
4. Check browser console for errors

## Common Issues & Fixes

### ❌ "Cannot connect to backend"
- Check `NEXT_PUBLIC_API_URL` in `web/.env.local`
- Verify FastAPI is running: `curl http://localhost:8000/api/health`
- Check CORS in `backend_fastapi/app/main.py` (should allow `localhost:3000`)

### ❌ "401 Unauthorized"
- Sign in to web app first (creates Firebase token)
- Check Firebase credentials path in backend `.env`
- Verify `FIREBASE_PROJECT_ID` matches your Firebase project

### ❌ "Database connection failed"
- Verify `DATABASE_URL` in backend `.env`
- Check Supabase project is active
- Run migrations: `cd backend_fastapi && alembic upgrade head`

### ❌ "Redis connection failed"
- Start Redis: `docker run -d -p 6379:6379 redis:7-alpine`
- Or install locally: `brew install redis && redis-server`
- Verify `REDIS_URL` in backend `.env`

## What's Actually Working

✅ **Architecture is correct:**
- FastAPI backend (not Firebase Functions)
- PostgreSQL database (not Firestore)
- Firebase Auth (still used)
- Next.js frontend
- Chrome extension

✅ **Code is synced:**
- Frontend points to `http://localhost:8000/api`
- Backend accepts Firebase tokens
- Extension configured correctly

## Next Steps

1. Run `./fix_sync.sh` to diagnose
2. Fix environment variables
3. Start all services
4. Test the connection
5. If still broken, check the error messages - they'll tell you exactly what's wrong

## Still Stuck?

The most common issue is **missing environment variables**. Make sure:
- Backend `.env` has all required values
- Frontend `.env.local` has `NEXT_PUBLIC_API_URL`
- Firebase credentials file exists in `backend_fastapi/`

Your project structure is fine - you just need to configure it properly!
