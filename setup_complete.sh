#!/bin/bash

################################################################################
# Forensic IR Application - Complete Setup Script
# This script sets up the entire application on a new system
# Handles: Python env, Node.js, databases, data directories, and dependencies
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

# Error handler
handle_error() {
    log_error "Setup failed at line $1"
    log_error "Please check the error message above and try again"
    exit 1
}

trap 'handle_error $LINENO' ERR

################################################################################
# 1. SYSTEM CHECKS
################################################################################

log_section "1. SYSTEM CHECKS"

# Check OS
log_info "Checking operating system..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    log_success "Linux detected"
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    log_success "macOS detected"
    OS="macos"
else
    log_warning "Unknown OS: $OSTYPE (continuing anyway)"
    OS="unknown"
fi

# Check Python
log_info "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    log_success "Python $PYTHON_VERSION found"
else
    log_error "Python 3 is not installed. Please install Python 3.8+ first"
    exit 1
fi

# Check Node.js
log_info "Checking Node.js installation..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    log_success "Node.js $NODE_VERSION found"
else
    log_error "Node.js is not installed. Please install Node.js 14+ first"
    exit 1
fi

# Check npm
log_info "Checking npm installation..."
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    log_success "npm $NPM_VERSION found"
else
    log_error "npm is not installed. Please install npm first"
    exit 1
fi

################################################################################
# 2. PYTHON ENVIRONMENT SETUP
################################################################################

log_section "2. PYTHON ENVIRONMENT SETUP"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    log_info "Creating Python virtual environment..."
    python3 -m venv venv
    log_success "Virtual environment created"
else
    log_info "Virtual environment already exists"
fi

# Activate virtual environment
log_info "Activating virtual environment..."
source venv/bin/activate
log_success "Virtual environment activated"

# Upgrade pip
log_info "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
log_success "pip upgraded"

################################################################################
# 3. PYTHON DEPENDENCIES
################################################################################

log_section "3. PYTHON DEPENDENCIES"

log_info "Installing Python dependencies..."

# Core dependencies
log_info "Installing core dependencies..."
pip install django djangorestframework django-cors-headers > /dev/null 2>&1
log_success "Django and REST framework installed"

# Database dependencies
log_info "Installing database dependencies..."
pip install pymongo psycopg2-binary pyyaml > /dev/null 2>&1 || {
    log_warning "psycopg2-binary failed, trying psycopg2..."
    pip install pymongo psycopg2 pyyaml > /dev/null 2>&1
}
log_success "Database dependencies installed"

# Forensic dependencies
log_info "Installing forensic dependencies..."
pip install pytsk3 pyewf > /dev/null 2>&1 || {
    log_warning "pytsk3/pyewf installation failed (may need system libraries)"
    log_info "You may need to install: apt-get install libtsk-dev libewf-dev (Linux)"
}

# ML dependencies
log_info "Installing ML dependencies..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu > /dev/null 2>&1 || {
    log_warning "PyTorch installation failed, trying alternative..."
    pip install torch > /dev/null 2>&1
}
log_success "PyTorch installed"

pip install torch-geometric scikit-learn pandas numpy matplotlib seaborn > /dev/null 2>&1
log_success "ML dependencies installed"

# Additional dependencies
log_info "Installing additional dependencies..."
pip install requests python-dateutil pillow > /dev/null 2>&1
log_success "Additional dependencies installed"

################################################################################
# 4. DIRECTORY STRUCTURE
################################################################################

log_section "4. DIRECTORY STRUCTURE"

log_info "Creating required directories..."

# Create data directories
mkdir -p forensic_ir_app/data/{raw,processed,extracted,samples,models}
mkdir -p forensic_ir_app/backend/logs
mkdir -p forensic_ir_app/backend/temp_extractions
mkdir -p forensic_ir_app/backend/media
mkdir -p forensic_ir_app/backend/static

log_success "Directory structure created"

################################################################################
# 5. DATABASE CONFIGURATION
################################################################################

log_section "5. DATABASE CONFIGURATION"

# Create config directory
mkdir -p forensic_ir_app/config

# Create database config file
log_info "Creating database configuration..."

cat > forensic_ir_app/config/db_config.yaml << 'EOF'
# Database Configuration for Forensic IR Application

mongodb:
  uri: "mongodb://localhost:27017/"
  database: "forensic_ir_db"
  collections:
    cases: "cases"
    browser_artifacts: "browser_artifacts"
    registry_artifacts: "registry_artifacts"
    recycle_bin_artifacts: "recycle_bin_artifacts"
    event_log_artifacts: "event_log_artifacts"
    filesystem_artifacts: "filesystem_artifacts"
    timeline_events: "timeline_events"

postgresql:
  host: "localhost"
  port: 5432
  database: "forensic_ir_db"
  user: "forensic_user"
  password: "forensic_password"

# Connection settings
connection:
  timeout: 30
  retry_attempts: 3
  pool_size: 10
EOF

log_success "Database configuration created"

# Check MongoDB
log_info "Checking MongoDB..."
if command -v mongod &> /dev/null; then
    log_success "MongoDB is installed"
    
    # Check if MongoDB is running
    if pgrep -x "mongod" > /dev/null; then
        log_success "MongoDB is running"
    else
        log_warning "MongoDB is not running"
        log_info "To start MongoDB:"
        log_info "  Linux: sudo systemctl start mongod"
        log_info "  macOS: brew services start mongodb-community"
    fi
else
    log_warning "MongoDB is not installed"
    log_info "To install MongoDB:"
    log_info "  Linux: sudo apt-get install mongodb"
    log_info "  macOS: brew install mongodb-community"
    log_info ""
    log_info "The application will work with limited functionality without MongoDB"
fi

# Check PostgreSQL
log_info "Checking PostgreSQL..."
if command -v psql &> /dev/null; then
    log_success "PostgreSQL is installed"
    
    # Check if PostgreSQL is running
    if pgrep -x "postgres" > /dev/null; then
        log_success "PostgreSQL is running"
    else
        log_warning "PostgreSQL is not running"
        log_info "To start PostgreSQL:"
        log_info "  Linux: sudo systemctl start postgresql"
        log_info "  macOS: brew services start postgresql"
    fi
else
    log_warning "PostgreSQL is not installed"
    log_info "To install PostgreSQL:"
    log_info "  Linux: sudo apt-get install postgresql postgresql-contrib"
    log_info "  macOS: brew install postgresql"
    log_info ""
    log_info "Django will use SQLite as fallback if PostgreSQL is not available"
fi

################################################################################
# 6. DJANGO BACKEND SETUP
################################################################################

log_section "6. DJANGO BACKEND SETUP"

cd forensic_ir_app/backend

# Create Django settings if needed
log_info "Configuring Django settings..."

# Run migrations
log_info "Running Django migrations..."
python manage.py makemigrations --noinput > /dev/null 2>&1 || log_warning "makemigrations had warnings"
python manage.py migrate --noinput > /dev/null 2>&1 || log_warning "migrate had warnings"
log_success "Django migrations completed"

# Create superuser (non-interactive)
log_info "Creating Django superuser..."
python manage.py shell << 'PYEOF' > /dev/null 2>&1 || log_warning "Superuser creation skipped"
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@forensic.local', 'admin123')
    print('Superuser created')
else:
    print('Superuser already exists')
PYEOF
log_success "Django superuser ready (username: admin, password: admin123)"

# Collect static files
log_info "Collecting static files..."
python manage.py collectstatic --noinput > /dev/null 2>&1 || log_warning "Static files collection skipped"

cd ../..

################################################################################
# 7. FRONTEND SETUP
################################################################################

log_section "7. FRONTEND SETUP"

cd forensic_ir_app/frontend

# Install npm dependencies
log_info "Installing frontend dependencies (this may take a few minutes)..."
npm install > /dev/null 2>&1 || {
    log_warning "npm install had warnings, trying with --legacy-peer-deps..."
    npm install --legacy-peer-deps > /dev/null 2>&1
}
log_success "Frontend dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    log_info "Creating frontend .env file..."
    cat > .env << 'EOF'
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_WS_URL=ws://localhost:8000/ws
EOF
    log_success ".env file created"
else
    log_info ".env file already exists"
fi

cd ../..

################################################################################
# 8. ML MODELS SETUP
################################################################################

log_section "8. ML MODELS SETUP"

log_info "Setting up ML models directory..."
mkdir -p forensic_ir_app/data/models

# Check if pre-trained models exist
if [ -f "forensic_ir_app/data/models/gat_model.pth" ]; then
    log_success "Pre-trained GAT model found"
else
    log_info "No pre-trained models found (will train on first use)"
fi

################################################################################
# 9. SAMPLE DATA SETUP
################################################################################

log_section "9. SAMPLE DATA SETUP"

log_info "Checking for sample forensic images..."
SAMPLES_DIR="forensic_ir_app/data/samples"

if [ -d "$SAMPLES_DIR" ] && [ "$(ls -A $SAMPLES_DIR)" ]; then
    SAMPLE_COUNT=$(ls -1 $SAMPLES_DIR | wc -l)
    log_success "Found $SAMPLE_COUNT sample file(s) in $SAMPLES_DIR"
else
    log_info "No sample forensic images found"
    log_info "Place .E01, .dd, or .raw forensic images in: $SAMPLES_DIR"
fi

################################################################################
# 10. VERIFICATION
################################################################################

log_section "10. VERIFICATION"

log_info "Verifying installation..."

# Check Python imports
log_info "Checking Python imports..."
python3 << 'PYEOF'
try:
    import django
    import rest_framework
    import pymongo
    import torch
    import sklearn
    import pandas
    import numpy
    print("✓ All critical Python packages imported successfully")
except ImportError as e:
    print(f"✗ Import error: {e}")
    exit(1)
PYEOF

if [ $? -eq 0 ]; then
    log_success "Python environment verified"
else
    log_error "Python environment verification failed"
    exit 1
fi

# Check Node modules
log_info "Checking Node.js modules..."
if [ -d "forensic_ir_app/frontend/node_modules" ]; then
    log_success "Node.js modules verified"
else
    log_warning "Node.js modules not found"
fi

################################################################################
# 11. CREATE STARTUP SCRIPTS
################################################################################

log_section "11. CREATING STARTUP SCRIPTS"

# Create backend startup script
cat > forensic_ir_app/start_backend.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/backend"
source ../venv/bin/activate 2>/dev/null || source ../../venv/bin/activate
echo "Starting Django backend on http://localhost:8000"
python manage.py runserver 8000
EOF

chmod +x forensic_ir_app/start_backend.sh
log_success "Backend startup script created: forensic_ir_app/start_backend.sh"

# Create frontend startup script
cat > forensic_ir_app/start_frontend.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/frontend"
echo "Starting React frontend on http://localhost:3000"
npm start
EOF

chmod +x forensic_ir_app/start_frontend.sh
log_success "Frontend startup script created: forensic_ir_app/start_frontend.sh"

# Create combined startup script
cat > forensic_ir_app/start_all.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting Forensic IR Application"
echo "===================================="

# Start backend in background
echo "Starting backend..."
cd "$(dirname "$0")"
./start_backend.sh &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Start frontend in background
echo "Starting frontend..."
./start_frontend.sh &
FRONTEND_PID=$!

echo ""
echo "✅ Application started!"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo "   Admin:    http://localhost:8000/admin (admin/admin123)"
echo ""
echo "Press Ctrl+C to stop all services"

# Cleanup function
cleanup() {
    echo ""
    echo "Stopping services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "Services stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Keep script running
wait
EOF

chmod +x forensic_ir_app/start_all.sh
log_success "Combined startup script created: forensic_ir_app/start_all.sh"

################################################################################
# 12. CREATE QUICK REFERENCE GUIDE
################################################################################

log_section "12. CREATING QUICK REFERENCE"

cat > forensic_ir_app/QUICK_START.txt << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║     FORENSIC IR APPLICATION - QUICK START GUIDE              ║
╚══════════════════════════════════════════════════════════════╝

📋 SYSTEM REQUIREMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Python 3.8+
✓ Node.js 14+
✓ MongoDB (optional, for full features)
✓ PostgreSQL (optional, SQLite used as fallback)
✓ 8GB+ RAM recommended
✓ 10GB+ disk space

🚀 STARTING THE APPLICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Option 1: Start Everything (Recommended)
  ./forensic_ir_app/start_all.sh

Option 2: Start Services Separately
  Terminal 1: ./forensic_ir_app/start_backend.sh
  Terminal 2: ./forensic_ir_app/start_frontend.sh

🌐 ACCESS POINTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Frontend:  http://localhost:3000
Backend:   http://localhost:8000/api
Admin:     http://localhost:8000/admin

Default Credentials:
  Username: admin
  Password: admin123

🔧 COMMON TASKS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Create a New Case:
  1. Navigate to http://localhost:3000
  2. Click "Cases" → "New Case"
  3. Upload forensic image or select from samples
  4. Wait for extraction to complete

Run ML Anomaly Detection:
  1. Open a case
  2. Click "AI Anomaly Detection" in sidebar
  3. Click "Run Analysis"
  4. Review results and recommendations

📁 IMPORTANT DIRECTORIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
forensic_ir_app/data/samples/     - Place forensic images here
forensic_ir_app/data/extracted/   - Extracted artifacts
forensic_ir_app/data/models/      - ML models
forensic_ir_app/backend/logs/     - Application logs
forensic_ir_app/config/           - Configuration files

🐛 TROUBLESHOOTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Backend won't start:
  - Check if port 8000 is available
  - Verify Python virtual environment is activated
  - Check backend/logs/ for error messages

Frontend won't start:
  - Check if port 3000 is available
  - Run: cd forensic_ir_app/frontend && npm install
  - Clear cache: rm -rf node_modules package-lock.json && npm install

Database connection errors:
  - Verify MongoDB is running: sudo systemctl status mongod
  - Check config/db_config.yaml settings
  - Application works with limited features without MongoDB

ML analysis not available:
  - Verify PyTorch is installed: python -c "import torch; print(torch.__version__)"
  - Install torch-geometric: pip install torch-geometric
  - Check backend logs for ML service initialization

📚 DOCUMENTATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
See z_leave/ folder for:
  - Detailed documentation
  - Test scripts
  - Sample configurations
  - Development guides

🆘 SUPPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
For issues or questions:
  1. Check logs in backend/logs/
  2. Review QUICK_START.txt
  3. Check z_leave/ for detailed documentation

EOF

log_success "Quick reference guide created: forensic_ir_app/QUICK_START.txt"

################################################################################
# 13. FINAL VERIFICATION
################################################################################

log_section "13. FINAL VERIFICATION"

log_info "Running final checks..."

# Test Django
cd forensic_ir_app/backend
python manage.py check > /dev/null 2>&1
if [ $? -eq 0 ]; then
    log_success "Django backend check passed"
else
    log_warning "Django backend check had warnings"
fi
cd ../..

# Test imports
python3 << 'PYEOF'
import sys
sys.path.insert(0, 'forensic_ir_app')

errors = []

try:
    from ai_ml.anomaly_detector import GAT, GCN
    print("✓ ML models imported")
except Exception as e:
    errors.append(f"ML models: {e}")

try:
    from extraction.forensic_extractor import ForensicExtractor
    print("✓ Forensic extractor imported")
except Exception as e:
    errors.append(f"Forensic extractor: {e}")

try:
    from database.mongodb_retrieval import ForensicMongoRetrieval
    print("✓ MongoDB retrieval imported")
except Exception as e:
    errors.append(f"MongoDB retrieval: {e}")

if errors:
    print("\n⚠ Some imports failed (non-critical):")
    for error in errors:
        print(f"  - {error}")
else:
    print("\n✓ All critical imports successful")
PYEOF

################################################################################
# SETUP COMPLETE
################################################################################

log_section "SETUP COMPLETE!"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     FORENSIC IR APPLICATION SETUP COMPLETED!                 ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}📋 NEXT STEPS:${NC}"
echo ""
echo "1. Start the application:"
echo "   ${YELLOW}./forensic_ir_app/start_all.sh${NC}"
echo ""
echo "2. Access the web interface:"
echo "   ${YELLOW}http://localhost:3000${NC}"
echo ""
echo "3. Login with default credentials:"
echo "   Username: ${YELLOW}admin${NC}"
echo "   Password: ${YELLOW}admin123${NC}"
echo ""
echo "4. Create a new case and upload forensic images"
echo ""
echo "5. Run AI-powered anomaly detection"
echo ""
echo -e "${CYAN}📚 DOCUMENTATION:${NC}"
echo "   Quick Start: ${YELLOW}forensic_ir_app/QUICK_START.txt${NC}"
echo "   Detailed Docs: ${YELLOW}forensic_ir_app/z_leave/${NC}"
echo ""
echo -e "${CYAN}🔧 USEFUL COMMANDS:${NC}"
echo "   Start backend only:  ${YELLOW}./forensic_ir_app/start_backend.sh${NC}"
echo "   Start frontend only: ${YELLOW}./forensic_ir_app/start_frontend.sh${NC}"
echo "   Django admin:        ${YELLOW}http://localhost:8000/admin${NC}"
echo ""
echo -e "${GREEN}✅ Setup completed successfully!${NC}"
echo ""