#!/bin/bash

# Frontend-Backend Sync Fix Script
# This script checks and fixes common sync issues

set -e

echo "🔍 Checking Frontend-Backend Sync..."
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend is running
echo "1. Checking FastAPI backend..."
if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is running${NC}"
else
    echo -e "${RED}❌ Backend is NOT running${NC}"
    echo "   Start it with: cd backend_fastapi && uvicorn app.main:app --reload"
fi

# Check if frontend is running
echo ""
echo "2. Checking Next.js frontend..."
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend is running${NC}"
else
    echo -e "${RED}❌ Frontend is NOT running${NC}"
    echo "   Start it with: cd web && npm run dev"
fi

# Check Redis
echo ""
echo "3. Checking Redis..."
if command -v redis-cli &> /dev/null; then
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Redis is running${NC}"
    else
        echo -e "${RED}❌ Redis is NOT running${NC}"
        echo "   Start it with: docker run -d -p 6379:6379 --name redis redis:7-alpine"
    fi
else
    echo -e "${YELLOW}⚠️  redis-cli not found (Redis might still be running)${NC}"
fi

# Check environment files
echo ""
echo "4. Checking environment files..."

# Backend .env
if [ -f "backend_fastapi/.env" ]; then
    echo -e "${GREEN}✅ Backend .env exists${NC}"
    
    # Check for required vars
    if grep -q "DATABASE_URL=" backend_fastapi/.env && ! grep -q "DATABASE_URL=postgresql://localhost:5432/dan" backend_fastapi/.env; then
        echo -e "${GREEN}✅ DATABASE_URL is configured${NC}"
    else
        echo -e "${YELLOW}⚠️  DATABASE_URL needs to be set${NC}"
    fi
    
    if grep -q "FIREBASE_PROJECT_ID=" backend_fastapi/.env && ! grep -q "FIREBASE_PROJECT_ID=$" backend_fastapi/.env; then
        echo -e "${GREEN}✅ FIREBASE_PROJECT_ID is configured${NC}"
    else
        echo -e "${YELLOW}⚠️  FIREBASE_PROJECT_ID needs to be set${NC}"
    fi
else
    echo -e "${RED}❌ Backend .env file missing${NC}"
    echo "   Copy from: backend_fastapi/env.example"
fi

# Frontend .env.local
if [ -f "web/.env.local" ]; then
    echo -e "${GREEN}✅ Frontend .env.local exists${NC}"
    
    if grep -q "NEXT_PUBLIC_API_URL=" web/.env.local; then
        API_URL=$(grep "NEXT_PUBLIC_API_URL=" web/.env.local | cut -d '=' -f2)
        echo -e "${GREEN}✅ NEXT_PUBLIC_API_URL is set to: $API_URL${NC}"
    else
        echo -e "${YELLOW}⚠️  NEXT_PUBLIC_API_URL needs to be set${NC}"
        echo "   Add: NEXT_PUBLIC_API_URL=http://localhost:8000/api"
    fi
else
    echo -e "${RED}❌ Frontend .env.local file missing${NC}"
    echo "   Create it with: NEXT_PUBLIC_API_URL=http://localhost:8000/api"
fi

# Check Firebase credentials
echo ""
echo "5. Checking Firebase credentials..."
if [ -f "backend_fastapi/dann-91ae4-firebase-adminsdk-fbsvc-c517cef228.json" ]; then
    echo -e "${GREEN}✅ Firebase credentials file exists${NC}"
else
    echo -e "${YELLOW}⚠️  Firebase credentials file not found${NC}"
    echo "   Download from Firebase Console > Project Settings > Service Accounts"
fi

# Check database migrations
echo ""
echo "6. Checking database migrations..."
if [ -d "backend_fastapi/migrations" ]; then
    echo -e "${GREEN}✅ Migrations directory exists${NC}"
    echo "   Run migrations with: cd backend_fastapi && alembic upgrade head"
else
    echo -e "${YELLOW}⚠️  Migrations directory not found${NC}"
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "To get everything synced:"
echo ""
echo "1. Start services:"
echo "   - Backend: cd backend_fastapi && uvicorn app.main:app --reload"
echo "   - Frontend: cd web && npm run dev"
echo "   - Redis: docker run -d -p 6379:6379 redis:7-alpine"
echo ""
echo "2. Configure environment:"
echo "   - Backend: Edit backend_fastapi/.env"
echo "   - Frontend: Create web/.env.local with NEXT_PUBLIC_API_URL"
echo ""
echo "3. Run migrations:"
echo "   cd backend_fastapi && alembic upgrade head"
echo ""
echo "4. Test connection:"
echo "   curl http://localhost:8000/api/health"
echo ""
