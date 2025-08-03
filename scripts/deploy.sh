#!/bin/bash

# BetterGut Deployment Setup Script for vast.ai
# This script automates the deployment process on a fresh vast.ai instance

set -e

echo "🚀 Starting BetterGut deployment setup..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run as root"
    exit 1
fi

print_header "1. Updating system packages..."
apt update && apt upgrade -y

print_header "2. Installing Docker and Docker Compose..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    print_status "Docker installed successfully"
else
    print_status "Docker already installed"
fi

if ! command -v docker-compose &> /dev/null; then
    apt install -y docker-compose
    print_status "Docker Compose installed successfully"
else
    print_status "Docker Compose already installed"
fi

print_header "3. Installing additional dependencies..."
apt install -y git nginx certbot python3-certbot-nginx htop curl wget unzip ufw

print_header "4. Setting up application directory..."
APP_DIR="/opt/bettergut"
mkdir -p $APP_DIR
cd $APP_DIR

# Check if this is a fresh deployment or update
if [ -d ".git" ]; then
    print_status "Updating existing deployment..."
    git pull
else
    print_status "Fresh deployment - cloning repository..."
    # Note: User needs to replace this with their actual repository URL
    echo "Please run: git clone https://github.com/yourusername/bettergut.git ."
    echo "Then run this script again."
    exit 1
fi

print_header "5. Setting up environment files..."

# Backend environment
if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    
    # Generate secure passwords and secrets
    JWT_SECRET=$(openssl rand -base64 32)
    DB_PASSWORD=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-16)
    
    # Update environment file with secure values
    sed -i "s/your_jwt_secret_here/$JWT_SECRET/" backend/.env
    sed -i "s/your_secure_db_password_here/$DB_PASSWORD/" backend/.env
    
    print_status "Backend environment file created with secure credentials"
    print_warning "Please edit backend/.env to configure email settings and server details"
else
    print_status "Backend environment file already exists"
fi

# AI Pipeline environment
if [ ! -f "ai-pipeline/.env" ]; then
    cp ai-pipeline/.env.example ai-pipeline/.env
    print_status "AI Pipeline environment file created"
else
    print_status "AI Pipeline environment file already exists"
fi

print_header "6. Configuring firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing

# Allow SSH (detect current SSH port)
SSH_PORT=$(ss -tlnp | grep sshd | awk '{print $4}' | cut -d':' -f2 | head -1)
if [ -n "$SSH_PORT" ]; then
    ufw allow $SSH_PORT/tcp
    print_status "Allowed SSH on port $SSH_PORT"
fi

# Allow HTTP and HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Allow application ports
ufw allow 3000/tcp  # Backend API
ufw allow 8001/tcp  # AI Pipeline
ufw allow 11434/tcp # Ollama (if needed externally)

ufw --force enable
print_status "Firewall configured and enabled"

print_header "7. Setting up Docker networks and volumes..."
docker network create bettergut-network 2>/dev/null || true

print_header "8. Building and starting services..."
docker-compose -f docker-compose.prod.yml up -d --build

print_status "Waiting for services to start..."
sleep 30

print_header "9. Setting up Llama 3 model..."
print_status "Pulling Llama 3 model (this may take several minutes)..."
docker exec $(docker-compose -f docker-compose.prod.yml ps -q ollama) ollama pull llama3:8b

print_header "10. Initializing health data crawlers..."
print_status "Starting health data crawling (this may take some time)..."
docker exec $(docker-compose -f docker-compose.prod.yml ps -q ai-pipeline) python -m scripts.crawl_health_data || true

print_header "11. Setting up backup system..."
mkdir -p /opt/scripts /opt/backups

cat > /opt/scripts/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
docker exec $(docker-compose -f /opt/bettergut/docker-compose.prod.yml ps -q postgres) pg_dump -U bettergut bettergut > $BACKUP_DIR/db_backup_$DATE.sql

# Backup uploads
docker run --rm -v bettergut_backend_uploads:/source -v $BACKUP_DIR:/backup alpine tar -czf /backup/uploads_backup_$DATE.tar.gz -C /source .

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /opt/scripts/backup.sh

# Add to crontab for daily backups at 2 AM
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/scripts/backup.sh >> /var/log/backup.log 2>&1") | crontab -

print_status "Backup system configured (daily at 2 AM)"

print_header "12. Creating monitoring script..."
cat > /opt/scripts/monitor.sh << 'EOF'
#!/bin/bash
cd /opt/bettergut

echo "=== BetterGut Service Status ==="
docker-compose -f docker-compose.prod.yml ps

echo -e "\n=== Resource Usage ==="
docker stats --no-stream

echo -e "\n=== Disk Usage ==="
df -h

echo -e "\n=== Service Health ==="
curl -s http://localhost:3000/api/health | jq . 2>/dev/null || curl -s http://localhost:3000/api/health
curl -s http://localhost:8001/health | jq . 2>/dev/null || curl -s http://localhost:8001/health
EOF

chmod +x /opt/scripts/monitor.sh

print_header "13. Testing deployment..."
sleep 10

# Test backend health
if curl -s http://localhost:3000/api/health | grep -q "healthy"; then
    print_status "Backend API is healthy ✅"
else
    print_warning "Backend API health check failed ⚠️"
fi

# Test AI pipeline
if curl -s http://localhost:8001/health | grep -q "healthy"; then
    print_status "AI Pipeline is healthy ✅"
else
    print_warning "AI Pipeline health check failed ⚠️"
fi

# Get server IP
SERVER_IP=$(curl -s ifconfig.me || curl -s ipinfo.io/ip)

print_header "🎉 Deployment Complete!"
echo ""
echo "=== BetterGut Deployment Summary ==="
echo "📍 Server IP: $SERVER_IP"
echo "🔗 Backend API: http://$SERVER_IP:3000/api"
echo "🧠 AI Pipeline: http://$SERVER_IP:8001"
echo "📁 Application Directory: $APP_DIR"
echo ""
echo "=== Next Steps ==="
echo "1. Configure email settings in backend/.env"
echo "2. Set up domain name and SSL certificate (optional)"
echo "3. Update Flutter app configuration with server IP"
echo "4. Test registration and email verification"
echo ""
echo "=== Useful Commands ==="
echo "📊 Monitor services: /opt/scripts/monitor.sh"
echo "💾 Manual backup: /opt/scripts/backup.sh"
echo "📋 View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "🔄 Restart services: docker-compose -f docker-compose.prod.yml restart"
echo "⬆️ Update app: cd $APP_DIR && git pull && docker-compose -f docker-compose.prod.yml up -d --build"
echo ""
echo "=== Important Files ==="
echo "🔧 Backend config: backend/.env"
echo "🤖 AI config: ai-pipeline/.env"
echo "📝 Deployment logs: /var/log/deployment.log"
echo "💾 Backups: /opt/backups/"
echo ""
print_status "Deployment completed successfully! 🚀"

# Save deployment info
cat > /opt/bettergut/deployment-info.txt << EOF
BetterGut Deployment Information
================================
Deployment Date: $(date)
Server IP: $SERVER_IP
Backend URL: http://$SERVER_IP:3000/api
AI Pipeline URL: http://$SERVER_IP:8001
Application Directory: $APP_DIR

Services:
- PostgreSQL: Port 5432
- Backend API: Port 3000
- AI Pipeline: Port 8001
- Ollama: Port 11434
- Redis: Port 6379

Environment Files:
- Backend: backend/.env
- AI Pipeline: ai-pipeline/.env

Useful Scripts:
- Monitor: /opt/scripts/monitor.sh
- Backup: /opt/scripts/backup.sh

Logs Location:
- Docker Compose: docker-compose -f docker-compose.prod.yml logs
- Backup: /var/log/backup.log
- Nginx: /var/log/nginx/
EOF

print_status "Deployment information saved to /opt/bettergut/deployment-info.txt"
