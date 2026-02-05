#!/bin/bash

# Script to run all development servers
# Usage: ./scripts/dev.sh

set -e

echo "🚀 Starting DAN Development Environment"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the root directory
if [ ! -f "package.json" ] || [ ! -d "web" ] || [ ! -d "backend" ] || [ ! -d "extension" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

echo -e "${BLUE}📦 Building shared package...${NC}"
cd shared && npm run build && cd ..

echo ""
echo -e "${GREEN}✅ Ready to start services!${NC}"
echo ""
echo "Please run these commands in separate terminals:"
echo ""
echo -e "${YELLOW}Terminal 1 - Backend:${NC}"
echo "  cd backend && npm run build && npm run serve"
echo ""
echo -e "${YELLOW}Terminal 2 - Web App:${NC}"
echo "  cd web && npm run dev"
echo ""
echo -e "${YELLOW}Terminal 3 - Extension (build once):${NC}"
echo "  cd extension && npm run build"
echo "  (Then load extension/dist/ in Chrome at chrome://extensions/)"
echo ""
echo -e "${YELLOW}Or use watch mode for extension:${NC}"
echo "  cd extension && npm run watch"
echo ""
echo -e "${GREEN}📚 See RUN_EVERYTHING.md for detailed instructions${NC}"




