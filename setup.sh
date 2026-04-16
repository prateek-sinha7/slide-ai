#!/bin/bash

# AI PowerPoint Generator - Setup and Run Script
# This script sets up and runs both backend and frontend servers

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -i :"$1" >/dev/null 2>&1
}

# Function to kill process on port
kill_port() {
    local port=$1
    if port_in_use "$port"; then
        print_warning "Port $port is in use. Killing existing process..."
        lsof -ti :"$port" | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

print_info "=========================================="
print_info "AI PowerPoint Generator - Setup & Run"
print_info "=========================================="
echo ""

# Check prerequisites
print_info "Checking prerequisites..."

if ! command_exists python3; then
    print_error "Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

if ! command_exists node; then
    print_error "Node.js is not installed. Please install Node.js 16 or higher."
    exit 1
fi

if ! command_exists npm; then
    print_error "npm is not installed. Please install npm."
    exit 1
fi

if ! command_exists ollama; then
    print_error "Ollama is not installed. Please install Ollama from https://ollama.ai"
    exit 1
fi

print_success "All prerequisites are installed"
echo ""

# Check if Ollama is running
print_info "Checking Ollama service..."
if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    print_error "Ollama is not running. Please start Ollama first:"
    print_error "  Run: ollama serve"
    exit 1
fi

# Check if mistral model is available
if ! ollama list | grep -q "mistral"; then
    print_warning "Mistral model not found. Pulling mistral:latest..."
    ollama pull mistral:latest
fi

print_success "Ollama is running with Mistral model"
echo ""

# Setup Backend
print_info "Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_info "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
print_info "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_info "Please configure .env file with your settings"
    else
        print_error ".env.example not found"
        exit 1
    fi
fi

print_success "Backend setup complete"
cd ..
echo ""

# Setup Frontend
print_info "Setting up frontend..."
cd frontend

# Install dependencies
if [ ! -d "node_modules" ]; then
    print_info "Installing Node.js dependencies..."
    npm install
else
    print_info "Node.js dependencies already installed"
fi

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    print_warning ".env.local file not found. Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env.local
        print_info "Please configure .env.local file with your settings"
    else
        print_error ".env.example not found"
        exit 1
    fi
fi

print_success "Frontend setup complete"
cd ..
echo ""

# Kill existing processes on ports 8000 and 3000
print_info "Checking for existing processes..."
kill_port 8000
kill_port 3000
echo ""

# Start servers
print_info "=========================================="
print_info "Starting servers..."
print_info "=========================================="
echo ""

# Create log directory
mkdir -p logs

# Start backend in background
print_info "Starting backend server on http://localhost:8000..."
cd backend
source venv/bin/activate
nohup python main.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
print_info "Waiting for backend to start..."
sleep 5

# Check if backend is running
if ! port_in_use 8000; then
    print_error "Backend failed to start. Check logs/backend.log for details."
    exit 1
fi

print_success "Backend started (PID: $BACKEND_PID)"
echo ""

# Start frontend in background
print_info "Starting frontend server on http://localhost:3000..."
cd frontend
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
print_info "Waiting for frontend to start..."
sleep 10

# Check if frontend is running
if ! port_in_use 3000; then
    print_error "Frontend failed to start. Check logs/frontend.log for details."
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

print_success "Frontend started (PID: $FRONTEND_PID)"
echo ""

# Save PIDs to file for easy cleanup
echo "$BACKEND_PID" > .backend.pid
echo "$FRONTEND_PID" > .frontend.pid

# Print success message
print_success "=========================================="
print_success "All servers are running!"
print_success "=========================================="
echo ""
print_info "Backend:  http://localhost:8000"
print_info "Frontend: http://localhost:3000"
echo ""
print_info "Logs:"
print_info "  Backend:  logs/backend.log"
print_info "  Frontend: logs/frontend.log"
echo ""
print_info "To view logs in real-time:"
print_info "  Backend:  tail -f logs/backend.log"
print_info "  Frontend: tail -f logs/frontend.log"
echo ""
print_info "To stop the servers, run:"
print_info "  ./stop.sh"
echo ""
print_success "Setup complete! Open http://localhost:3000 in your browser."
