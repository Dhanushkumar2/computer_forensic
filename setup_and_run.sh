#!/bin/bash

# Forensic IR App - Complete Setup and Run Script
# This script installs all dependencies and starts the application

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Print banner
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║          🔍 Forensic IR App - Setup & Run 🔍              ║"
echo "║                                                            ║"
echo "║     Digital Evidence Analysis & Investigation Platform    ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check prerequisites
print_status "Checking prerequisites..."

# Check Python
if ! command_exists python3; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_success "Python $PYTHON_VERSION found"

# Check Node.js
if ! command_exists node; then
    print_error "Node.js is not installed. Please install Node.js 14 or higher."
    exit 1
fi
NODE_VERSION=$(node --version)
print_success "Node.js $NODE_VERSION found"

# Check npm
if ! command_exists npm; then
    print_error "npm is not installed. Please install npm."
    exit 1
fi
NPM_VERSION=$(npm --version)
print_success "npm $NPM_VERSION found"

# Check MongoDB
if ! command_exists mongod; then
    print_warning "MongoDB is not installed or not in PATH."
    print_warning "Please ensure MongoDB is running on localhost:27017"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    print_success "MongoDB found"
fi

echo ""
print_status "Starting setup process..."
echo ""

# Step 1: Install Python dependencies
print_status "Step 1/5: Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt --quiet
    print_success "Python dependencies installed"
else
    print_error "requirements.txt not found!"
    exit 1
fi

# Step 2: Install frontend dependencies
print_status "Step 2/5: Installing frontend dependencies (this may take a few minutes)..."
cd frontend
if [ -f "package.json" ]; then
    npm install --silent
    print_success "Frontend dependencies installed"
else
    print_error "package.json not found in frontend directory!"
    exit 1
fi
cd ..

# Step 3: Setup Django database
print_status "Step 3/5: Setting up Django database..."
cd backend
if [ -f "manage.py" ]; then
    python3 manage.py migrate --noinput > /dev/null 2>&1
    print_success "Django database configured"
    
    # Create superuser if it doesn't exist
    print_status "Creating admin user (if not exists)..."
    python3 manage.py shell << EOF > /dev/null 2>&1
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@forensic-ir.com', 'admin123')
    print('Admin user created')
else:
    print('Admin user already exists')
EOF
    print_success "Admin user ready (username: admin, password: admin123)"
else
    print_error "manage.py not found in backend directory!"
    exit 1
fi
cd ..

# Step 4: Check MongoDB connection
print_status "Step 4/5: Checking MongoDB connection..."
if command_exists mongosh; then
    mongosh --eval "db.version()" --quiet > /dev/null 2>&1 && print_success "MongoDB is running" || print_warning "MongoDB may not be running"
elif command_exists mongo; then
    mongo --eval "db.version()" --quiet > /dev/null 2>&1 && print_success "MongoDB is running" || print_warning "MongoDB may not be running"
else
    print_warning "Cannot verify MongoDB status. Please ensure it's running."
fi

# Step 5: Check for sample data
print_status "Step 5/5: Checking for sample data..."
if [ -d "data/samples" ] && [ "$(ls -A data/samples)" ]; then
    SAMPLE_COUNT=$(ls -1 data/samples | wc -l)
    print_success "Found $SAMPLE_COUNT sample file(s) in data/samples/"
else
    print_warning "No sample disk images found in data/samples/"
    print_warning "You can add disk images (.E01, .dd, .raw, .img) to data/samples/ later"
fi

echo ""
print_success "✅ Setup completed successfully!"
echo ""

# Ask user if they want to start the application
read -p "$(echo -e ${GREEN}Start the application now? \(y/n\)${NC} )" -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    print_status "Setup complete. To start the application later, run:"
    echo ""
    echo "  Terminal 1: cd backend && python3 manage.py runserver"
    echo "  Terminal 2: cd frontend && npm start"
    echo ""
    exit 0
fi

echo ""
print_status "Starting Forensic IR App..."
echo ""
print_status "Backend will start on: http://localhost:8000"
print_status "Frontend will start on: http://localhost:3000"
echo ""
print_warning "Press Ctrl+C to stop both servers"
echo ""

# Create a trap to kill both processes on exit
trap 'kill $(jobs -p) 2>/dev/null' EXIT

# Start backend in background
print_status "Starting Django backend..."
cd backend
python3 manage.py runserver > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Check if backend started successfully
if ps -p $BACKEND_PID > /dev/null; then
    print_success "Backend started (PID: $BACKEND_PID)"
else
    print_error "Backend failed to start. Check backend.log for details."
    exit 1
fi

# Start frontend in background
print_status "Starting React frontend..."
cd frontend
BROWSER=none npm start > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait a moment for frontend to start
sleep 5

# Check if frontend started successfully
if ps -p $FRONTEND_PID > /dev/null; then
    print_success "Frontend started (PID: $FRONTEND_PID)"
else
    print_error "Frontend failed to start. Check frontend.log for details."
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo ""
print_success "╔════════════════════════════════════════════════════════════╗"
print_success "║                                                            ║"
print_success "║          🎉 Application is running! 🎉                     ║"
print_success "║                                                            ║"
print_success "╚════════════════════════════════════════════════════════════╝"
echo ""
print_status "📱 Open your browser and navigate to:"
echo ""
echo -e "   ${GREEN}http://localhost:3000${NC}"
echo ""
print_status "🔐 Login credentials:"
echo ""
echo "   Username: admin"
echo "   Password: admin123"
echo ""
print_status "📚 Quick Start:"
echo ""
echo "   1. Login with the credentials above"
echo "   2. Click 'New Case' to create your first case"
echo "   3. Upload a disk image from data/samples/"
echo "   4. Wait for processing (30s - 2min)"
echo "   5. Explore the forensic data!"
echo ""
print_status "📊 Features:"
echo ""
echo "   • Dashboard - Overview and statistics"
echo "   • Artifacts - Browse all evidence types"
echo "   • Timeline - Chronological event view"
echo "   • Analytics - AI-powered insights"
echo ""
print_status "📝 Logs:"
echo ""
echo "   Backend:  backend.log"
echo "   Frontend: frontend.log"
echo ""
print_warning "Press Ctrl+C to stop the application"
echo ""

# Wait for user to stop
wait
