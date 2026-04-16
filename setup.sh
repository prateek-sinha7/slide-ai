#!/bin/bash

# AI PowerPoint Generator - Setup and Run Script
# This script sets up and runs both backend and frontend servers

# Don't exit on error - we'll handle errors gracefully
# set -e

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
    if command_exists lsof; then
        lsof -i :"$1" >/dev/null 2>&1
    elif command_exists netstat; then
        netstat -an | grep -q ":$1 "
    else
        # Fallback: try to connect
        (echo >/dev/tcp/localhost/$1) >/dev/null 2>&1
    fi
}

# Function to kill process on port
kill_port() {
    local port=$1
    if port_in_use "$port"; then
        print_warning "Port $port is in use. Killing existing process..."
        if command_exists lsof; then
            lsof -ti :"$port" | xargs kill -9 2>/dev/null || true
        elif command_exists fuser; then
            fuser -k "$port/tcp" 2>/dev/null || true
        fi
        sleep 2
    fi
}

# Function to get Python version
get_python_version() {
    python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'
}

print_info "=========================================="
print_info "AI PowerPoint Generator - Setup & Run"
print_info "=========================================="
echo ""

# Check prerequisites
print_info "Checking prerequisites..."

if ! command_exists python3; then
    print_error "Python 3 is not installed. Please install Python 3.9-3.13."
    exit 1
fi

# Check if virtual environment already exists with compatible Python
VENV_PYTHON_OK=false
if [ -f "backend/venv/bin/python" ]; then
    VENV_PYTHON_VERSION=$(backend/venv/bin/python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "0.0")
    VENV_MAJOR=$(echo $VENV_PYTHON_VERSION | cut -d. -f1)
    VENV_MINOR=$(echo $VENV_PYTHON_VERSION | cut -d. -f2)
    
    if [ "$VENV_MAJOR" -eq 3 ] && [ "$VENV_MINOR" -ge 9 ] && [ "$VENV_MINOR" -lt 14 ]; then
        VENV_PYTHON_OK=true
        print_success "Found existing virtual environment with Python $VENV_PYTHON_VERSION"
    fi
fi

# Check system Python version
PYTHON_VERSION=$(get_python_version)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

print_info "Detected system Python $PYTHON_VERSION"

# If venv exists with compatible Python, skip version check
if [ "$VENV_PYTHON_OK" = true ]; then
    print_info "Using existing virtual environment (Python $VENV_PYTHON_VERSION)"
else
    # Warn about Python 3.14+ (too new, compatibility issues)
    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 14 ]; then
        print_warning "Python 3.14+ detected. This version has compatibility issues with some dependencies."
        print_warning "Recommended: Use Python 3.9-3.13 for best compatibility."
        print_warning ""
        print_warning "To install Python 3.13 on macOS:"
        print_warning "  brew install python@3.13"
        print_warning "  Then create venv with: python3.13 -m venv backend/venv"
        print_warning ""
        print_warning "Attempting to continue anyway..."
        echo ""
    fi

    # Warn about Python < 3.9
    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]; then
        print_warning "Python $PYTHON_VERSION detected. Python 3.9+ is recommended."
    fi
fi

if ! command_exists node; then
    print_error "Node.js is not installed. Please install Node.js 16 or higher."
    exit 1
fi

if ! command_exists npm; then
    print_error "npm is not installed. Please install npm."
    exit 1
fi

# Ollama is optional now (can use Groq or other providers)
if ! command_exists ollama; then
    print_warning "Ollama is not installed. You can use Groq API or other LLM providers."
    print_warning "To install Ollama: https://ollama.ai"
    OLLAMA_AVAILABLE=false
else
    OLLAMA_AVAILABLE=true
fi

print_success "All required prerequisites are installed"
echo ""

# Check if Ollama is running (optional)
if [ "$OLLAMA_AVAILABLE" = true ]; then
    print_info "Checking Ollama service..."
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        # Check if mistral model is available
        if ! ollama list | grep -q "mistral"; then
            print_warning "Mistral model not found. You can pull it with:"
            print_warning "  ollama pull mistral:latest"
        else
            print_success "Ollama is running with Mistral model"
        fi
    else
        print_warning "Ollama is not running. You can start it with:"
        print_warning "  ollama serve"
        print_warning "Or configure Groq API in backend/.env"
    fi
    echo ""
fi

# Setup Backend
print_info "Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist or if it needs to be recreated
if [ "$VENV_PYTHON_OK" = true ]; then
    print_info "Using existing virtual environment..."
elif [ ! -d "venv" ]; then
    print_info "Creating Python virtual environment..."
    python3 -m venv venv
else
    print_info "Virtual environment already exists"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
print_info "Installing Python dependencies..."
pip install --upgrade pip setuptools wheel

# Try to install dependencies with better error handling
if pip install -r requirements.txt; then
    print_success "Python dependencies installed successfully"
else
    print_error "Failed to install some Python dependencies"
    print_error ""
    print_error "Common issues:"
    print_error "1. Python 3.14+ is not supported (use Python 3.9-3.13)"
    print_error "2. Missing Rust compiler (needed for pydantic-core, tiktoken)"
    print_error ""
    print_error "To fix:"
    print_error "  - Use Python 3.13: brew install python@3.13"
    print_error "  - Or install Rust: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    print_error ""
    print_error "Check logs above for specific errors"
    exit 1
fi

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
