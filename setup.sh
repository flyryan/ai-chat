#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}Setting up AI Chat Assistant...${NC}"

# Create backend environment file
if [ ! -f "./backend/.env" ]; then
    echo -e "${GREEN}Creating backend environment file...${NC}"
    cp ./backend/.env.example ./backend/.env
    echo -e "${RED}Please update backend/.env with your configuration values${NC}"
fi

# Create frontend environment files
if [ ! -f "./frontend/.env.development" ]; then
    echo -e "${GREEN}Creating frontend development environment file...${NC}"
    cp ./frontend/.env.example ./frontend/.env.development
fi

if [ ! -f "./frontend/.env.production" ]; then
    echo -e "${GREEN}Creating frontend production environment file...${NC}"
    cp ./frontend/.env.example ./frontend/.env.production
    echo -e "${RED}Please update frontend/.env.production with your production values${NC}"
fi

# Setup Python virtual environment
echo -e "${GREEN}Setting up Python virtual environment...${NC}"
python -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt

# Install frontend dependencies
echo -e "${GREEN}Installing frontend dependencies...${NC}"
cd frontend
npm install

echo -e "${BLUE}Setup complete!${NC}"
echo -e "${GREEN}To start development:${NC}"
echo "1. Update the environment files with your configuration"
echo "2. Start backend: cd backend && source venv/bin/activate && uvicorn main:app --reload"
echo "3. Start frontend: cd frontend && npm start"