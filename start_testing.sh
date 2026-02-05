#!/bin/bash

# Quick Start Script for Testing DAN Extension
# This script helps you start all services needed for testing

set -e

echo "🚀 Starting DAN Testing Environment..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Redis is running
echo "📦 Checking Redis..."
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is running${NC}"
else
    echo -e "${YELLOW}⚠️  Redis is not running${NC}"
    echo "Starting Redis with Docker..."
    if docker ps -a | grep -q redis; then
        docker start redis
    else
        docker run -d -p 6379:6379 --name redis redis:7-alpine
    fi
    sleep 2
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Redis started successfully${NC}"
    else
        echo -e "${RED}❌ Failed to start Redis${NC}"
        echo "Please start Redis manually: docker run -d -p 6379:6379 --name redis redis:7-alpine"
        exit 1
    fi
fi

echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Start FastAPI Backend (Terminal 1):"
echo "   cd backend_fastapi"
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --reload --port 8000"
echo ""
echo "2. Start Web App (Terminal 2):"
echo "   cd web"
echo "   npm run dev"
echo ""
echo "3. Load Extension in Chrome:"
echo "   - Open chrome://extensions/"
echo "   - Enable Developer mode"
echo "   - Click 'Load unpacked'"
echo "   - Select: extension/dist"
echo ""
echo "4. Test:"
echo "   - Open http://localhost:3000 and sign in"
echo "   - Visit https://github.com (extension should track)"
echo "   - Check extension popup for status"
echo ""
echo -e "${GREEN}✅ Setup complete! Follow the steps above to start testing.${NC}"
echo ""
echo "📖 For detailed instructions, see: TEST_SETUP.md"
