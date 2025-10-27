#!/bin/bash

# Investment Research System - Frontend Startup Script
# This script automates the frontend setup and launch process

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project paths
PROJECT_ROOT="/Users/mayuhao/PythonProject/PythonProject"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_PORT=8000
FRONTEND_PORT=3000

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}Investment Research System${NC}"
echo -e "${BLUE}Frontend Startup Script${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Function to check if a port is in use
check_port() {
    lsof -i :$1 > /dev/null 2>&1
}

# Function to check if backend is running
check_backend() {
    curl -s http://localhost:$BACKEND_PORT/api/research/sessions > /dev/null 2>&1
}

# Step 1: Check if backend is running
echo -e "${YELLOW}[1/5] Checking backend status...${NC}"
if check_backend; then
    echo -e "${GREEN}✓ Backend is running on port $BACKEND_PORT${NC}"
else
    echo -e "${RED}✗ Backend is not running!${NC}"
    echo -e "${YELLOW}Please start the backend first:${NC}"
    echo -e "  cd $PROJECT_ROOT"
    echo -e "  source .venv/bin/activate"
    echo -e "  uvicorn backend.main:app --reload --port $BACKEND_PORT"
    echo ""
    exit 1
fi

# Step 2: Check if Node.js is installed
echo -e "${YELLOW}[2/5] Checking Node.js installation...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js is not installed!${NC}"
    echo -e "${YELLOW}Please install Node.js 18+ from https://nodejs.org${NC}"
    exit 1
fi

NODE_VERSION=$(node -v)
echo -e "${GREEN}✓ Node.js $NODE_VERSION is installed${NC}"

# Step 3: Navigate to frontend directory
echo -e "${YELLOW}[3/5] Navigating to frontend directory...${NC}"
if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}✗ Frontend directory not found at $FRONTEND_DIR${NC}"
    exit 1
fi

cd "$FRONTEND_DIR"
echo -e "${GREEN}✓ Changed to $FRONTEND_DIR${NC}"

# Step 4: Install dependencies if needed
echo -e "${YELLOW}[4/5] Checking dependencies...${NC}"
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing dependencies (this may take a minute)...${NC}"
    npm install
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Dependencies already installed${NC}"
fi

# Step 5: Check if frontend port is available
echo -e "${YELLOW}[5/5] Checking port $FRONTEND_PORT...${NC}"
if check_port $FRONTEND_PORT; then
    echo -e "${RED}✗ Port $FRONTEND_PORT is already in use!${NC}"
    echo -e "${YELLOW}Please stop the process using port $FRONTEND_PORT or change the port in vite.config.ts${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Port $FRONTEND_PORT is available${NC}"
echo ""

# All checks passed, start the development server
echo -e "${BLUE}=====================================${NC}"
echo -e "${GREEN}✓ All checks passed!${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""
echo -e "${GREEN}Starting frontend development server...${NC}"
echo ""
echo -e "${BLUE}Frontend URL:${NC} http://localhost:$FRONTEND_PORT"
echo -e "${BLUE}Backend URL:${NC}  http://localhost:$BACKEND_PORT"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""
echo -e "${BLUE}=====================================${NC}"
echo ""

# Start the development server
npm run dev

# This script will keep running until Ctrl+C
