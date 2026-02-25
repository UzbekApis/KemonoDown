#!/data/data/com.termux/files/usr/bin/bash
# Kemono WebApp - Termux Installation Script
# This script installs all dependencies and sets up the application

set -e  # Exit on error

echo "=========================================="
echo "Kemono WebApp - Installation"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if running in Termux
if [ ! -d "/data/data/com.termux" ]; then
    print_error "This script must be run in Termux!"
    exit 1
fi

print_success "Running in Termux environment"
echo ""

# Step 1: Update packages
print_info "Step 1/6: Updating Termux packages..."
pkg update -y && pkg upgrade -y
print_success "Packages updated"
echo ""

# Step 2: Install Python
print_info "Step 2/6: Installing Python..."
if command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
    print_success "Python already installed (version $PYTHON_VERSION)"
else
    pkg install python -y
    print_success "Python installed"
fi
echo ""

# Step 3: Install required system packages
print_info "Step 3/6: Installing system dependencies..."
pkg install libxml2 libxslt libjpeg-turbo -y
print_success "System dependencies installed"
echo ""

# Step 4: Install Python dependencies
print_info "Step 4/6: Installing Python packages..."
if [ -f "requirements.txt" ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
    print_success "Python packages installed"
else
    print_error "requirements.txt not found!"
    exit 1
fi
echo ""

# Step 5: Setup directories
print_info "Step 5/6: Creating application directories..."
mkdir -p data
mkdir -p data/cache
mkdir -p downloads
mkdir -p library
mkdir -p library/thumbs
mkdir -p templates/errors
print_success "Directories created"
echo ""

# Step 6: Initialize database
print_info "Step 6/6: Initializing database..."
python -c "from models.database import init_db; init_db()"
print_success "Database initialized"
echo ""

# Create default configuration
print_info "Creating default configuration..."
python -c "from config import create_default_config; create_default_config()"
print_success "Configuration created"
echo ""

# Setup storage permissions (optional)
print_info "Setting up storage access..."
echo "Note: You may need to grant storage permissions manually."
echo "Run: termux-setup-storage"
echo ""

# Installation complete
echo "=========================================="
print_success "Installation completed successfully!"
echo "=========================================="
echo ""
echo "To start the application, run:"
echo "  bash run.sh"
echo ""
echo "Or manually:"
echo "  python app.py"
echo ""
echo "Access the web interface at:"
echo "  http://localhost:5000"
echo ""
