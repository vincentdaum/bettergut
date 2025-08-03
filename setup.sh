#!/bin/bash

# BetterGut Setup Script
# This script sets up the complete development environment

set -e

echo "🚀 BetterGut Setup Script"
echo "=========================="

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

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Check if Node.js is installed
check_node() {
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js 18+ first."
        echo "Visit: https://nodejs.org/"
        exit 1
    fi
    
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        print_error "Node.js version 18+ is required. Current version: $(node --version)"
        exit 1
    fi
    
    print_success "Node.js $(node --version) is installed"
}

# Check if Python is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.11+ first."
        echo "Visit: https://www.python.org/downloads/"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
    print_success "Python $(python3 --version) is installed"
}

# Check if Flutter is installed (optional)
check_flutter() {
    if command -v flutter &> /dev/null; then
        print_success "Flutter $(flutter --version | head -n1 | cut -d' ' -f2) is installed"
        return 0
    else
        print_warning "Flutter is not installed."
        print_warning "You'll need Flutter to develop the mobile app."
        echo "Install Flutter: https://docs.flutter.dev/get-started/install"
        return 1
    fi
}

# Setup environment files
setup_env_files() {
    print_status "Setting up environment files..."
    
    # Backend environment
    if [ ! -f "backend/.env" ]; then
        cp backend/.env.example backend/.env
        print_success "Created backend/.env from template"
        print_warning "Please update backend/.env with your API keys"
    fi
    
    # AI Pipeline environment
    if [ ! -f "ai-pipeline/.env" ]; then
        cp ai-pipeline/.env.example ai-pipeline/.env
        print_success "Created ai-pipeline/.env from template"
        print_warning "Please update ai-pipeline/.env with your API keys"
    fi
    
    # Docker environment
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# API Keys for Docker Compose
OPENAI_API_KEY=your-openai-api-key-here
HUGGINGFACE_API_KEY=your-huggingface-api-key-here
EOF
        print_success "Created .env for Docker Compose"
        print_warning "Please update .env with your API keys"
    fi
}

# Install backend dependencies
install_backend_deps() {
    print_status "Installing backend dependencies..."
    cd backend
    npm install
    cd ..
    print_success "Backend dependencies installed"
}

# Install AI pipeline dependencies
install_ai_deps() {
    print_status "Installing AI pipeline dependencies..."
    cd ai-pipeline
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Created Python virtual environment"
    fi
    
    # Activate virtual environment and install dependencies
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Download spaCy model
    python -m spacy download en_core_web_sm
    
    cd ..
    print_success "AI pipeline dependencies installed"
}

# Install Flutter dependencies (if Flutter is available)
install_flutter_deps() {
    if command -v flutter &> /dev/null; then
        print_status "Installing Flutter dependencies..."
        cd mobile
        flutter pub get
        cd ..
        print_success "Flutter dependencies installed"
    else
        print_warning "Skipping Flutter dependencies (Flutter not installed)"
    fi
}

# Setup Docker containers
setup_docker() {
    print_status "Setting up Docker containers..."
    
    # Pull required images
    docker-compose pull postgres redis nginx
    
    # Build custom images
    docker-compose build backend ai-pipeline
    
    print_success "Docker setup complete"
}

# Create necessary directories
create_directories() {
    print_status "Creating project directories..."
    
    mkdir -p ai-pipeline/data/crawled
    mkdir -p ai-pipeline/data/chroma_db
    mkdir -p ai-pipeline/logs
    mkdir -p backend/uploads
    mkdir -p mobile/assets/images
    mkdir -p mobile/assets/icons
    mkdir -p mobile/assets/fonts
    mkdir -p mobile/assets/lottie
    
    print_success "Project directories created"
}

# Download Ollama and pull Llama 3 model
setup_ollama() {
    print_status "Setting up Ollama and Llama 3..."
    
    # Start Ollama container
    docker-compose up -d ollama
    
    # Wait for Ollama to start
    sleep 10
    
    # Pull Llama 3 model
    print_status "Downloading Llama 3 model (this may take a while)..."
    docker-compose exec ollama ollama pull llama3:8b
    
    print_success "Ollama and Llama 3 setup complete"
}

# Main setup function
main() {
    echo ""
    print_status "Starting BetterGut development environment setup..."
    echo ""
    
    # Check prerequisites
    print_status "Checking prerequisites..."
    check_docker
    check_node
    check_python
    check_flutter
    echo ""
    
    # Setup project
    create_directories
    setup_env_files
    echo ""
    
    # Install dependencies
    print_status "Installing dependencies..."
    install_backend_deps
    install_ai_deps
    install_flutter_deps
    echo ""
    
    # Setup Docker
    setup_docker
    echo ""
    
    # Setup Ollama (optional, can be time-consuming)
    read -p "Do you want to download Llama 3 model now? (This will take 4-7GB of space) [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_ollama
    else
        print_warning "Skipping Llama 3 download. You can do this later with:"
        echo "docker-compose up -d ollama && docker-compose exec ollama ollama pull llama3:8b"
    fi
    echo ""
    
    # Success message
    print_success "🎉 BetterGut setup complete!"
    echo ""
    echo "Next steps:"
    echo "1. Update your API keys in .env, backend/.env, and ai-pipeline/.env"
    echo "2. Start the services: docker-compose up -d"
    echo "3. Run the health data crawler: cd ai-pipeline && python crawl_health_data.py"
    echo "4. Start developing your Flutter app: cd mobile && flutter run"
    echo ""
    echo "Useful commands:"
    echo "• View logs: docker-compose logs -f [service_name]"
    echo "• Stop services: docker-compose down"
    echo "• Rebuild: docker-compose build [service_name]"
    echo ""
    echo "API endpoints will be available at:"
    echo "• Backend API: http://localhost:3000"
    echo "• AI Pipeline API: http://localhost:8001"
    echo "• Database: localhost:5432"
    echo ""
    print_success "Happy coding! 🚀"
}

# Run main function
main "$@"
