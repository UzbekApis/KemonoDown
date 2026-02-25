#!/data/data/com.termux/files/usr/bin/bash
# Kemono WebApp - Startup Script
# This script checks dependencies and starts the Flask server

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Clear screen
clear

# Print banner
echo "=========================================="
print_header "    Kemono WebApp - Starting Server    "
echo "=========================================="
echo ""

# Check if running in Termux
if [ ! -d "/data/data/com.termux" ]; then
    print_error "This script must be run in Termux!"
    exit 1
fi

# Step 1: Check Python installation
print_info "Checking Python installation..."
if ! command -v python &> /dev/null; then
    print_error "Python is not installed!"
    echo "Please run: bash install.sh"
    exit 1
fi

PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
print_success "Python $PYTHON_VERSION found"

# Step 2: Check required Python packages
print_info "Checking Python dependencies..."
REQUIRED_PACKAGES=("flask" "requests" "cloudscraper" "PIL")
MISSING_PACKAGES=()

for package in "${REQUIRED_PACKAGES[@]}"; do
    if ! python -c "import $package" 2>/dev/null; then
        MISSING_PACKAGES+=("$package")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    print_error "Missing packages: ${MISSING_PACKAGES[*]}"
    echo "Installing missing packages..."
    pip install -r requirements.txt
    print_success "Packages installed"
else
    print_success "All dependencies installed"
fi

# Step 3: Check directory structure
print_info "Checking directory structure..."
REQUIRED_DIRS=("data" "downloads" "library" "templates" "static")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        print_error "Directory '$dir' not found!"
        echo "Creating directory..."
        mkdir -p "$dir"
    fi
done
print_success "Directory structure OK"

# Step 4: Check database
print_info "Checking database..."
if [ ! -f "data/webapp.db" ]; then
    print_error "Database not found! Initializing..."
    python -c "from models.database import init_db; init_db()"
    print_success "Database initialized"
else
    print_success "Database found"
fi

# Step 5: Check configuration
print_info "Checking configuration..."
if [ ! -f "data/config.json" ]; then
    print_error "Configuration not found! Creating default..."
    python -c "from config import create_default_config; create_default_config()"
    print_success "Configuration created"
else
    print_success "Configuration found"
fi

# Step 6: Get network information
print_info "Getting network information..."
echo ""

# Get IP address
IP_ADDRESS=$(ifconfig 2>/dev/null | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -n1)

if [ -z "$IP_ADDRESS" ]; then
    IP_ADDRESS="<your-ip>"
fi

# Get port from config
PORT=$(python -c "from config import config; print(config.get('flask_port', 5000))" 2>/dev/null || echo "5000")

# Step 7: Display access information
echo "=========================================="
print_header "       Server Access Information       "
echo "=========================================="
echo ""
echo "Local access:"
echo "  → http://localhost:$PORT"
echo "  → http://127.0.0.1:$PORT"
echo ""
echo "Network access (from other devices):"
echo "  → http://$IP_ADDRESS:$PORT"
echo ""
echo "=========================================="
echo ""
print_info "Starting Flask server..."
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Step 8: Start Flask server
python app.py

# If server stops
echo ""
print_info "Server stopped"
