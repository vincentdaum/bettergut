# BetterGut Deployment Guide for vast.ai

This guide will help you deploy the BetterGut application on a vast.ai server instance.

## Prerequisites

1. A vast.ai account with sufficient credits
2. Basic knowledge of SSH and Docker
3. Domain name (optional but recommended for production)

## Step 1: Create vast.ai Instance

### Recommended Specifications:
- **GPU**: RTX 4090 or A6000 (for Llama 3 model)
- **RAM**: 32GB minimum (64GB recommended)
- **Storage**: 100GB+ SSD
- **CPU**: 8+ cores
- **Bandwidth**: Unlimited or high limit

### Instance Setup:
1. Go to [vast.ai](https://vast.ai)
2. Click "Create" and select "On-Demand"
3. Filter by the recommended specifications above
4. Choose an instance and launch it
5. Note down the SSH connection details

## Step 2: Connect and Setup Server

### Connect via SSH:
```bash
ssh -p [PORT] root@[IP_ADDRESS]
```

### Update system and install dependencies:
```bash
# Update system
apt update && apt upgrade -y

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
apt install -y docker-compose

# Install git
apt install -y git

# Create application directory
mkdir -p /opt/bettergut
cd /opt/bettergut
```

## Step 3: Clone and Setup Application

```bash
# Clone your repository (replace with your actual repo)
git clone https://github.com/yourusername/bettergut.git .

# Create environment files
cp backend/.env.example backend/.env
cp ai-pipeline/.env.example ai-pipeline/.env

# Generate secure passwords and secrets
openssl rand -base64 32  # Use for JWT_SECRET
openssl rand -base64 16  # Use for DB_PASSWORD
```

## Step 4: Configure Environment Variables

### Edit backend/.env:
```bash
nano backend/.env
```

Configure the following variables for production:
```env
# Database Configuration
DB_HOST=postgres
DB_PORT=5432
DB_NAME=bettergut
DB_USER=bettergut
DB_PASSWORD=your_secure_db_password_here

# JWT Configuration
JWT_SECRET=your_jwt_secret_here
JWT_EXPIRES_IN=7d

# Email Configuration (for American users)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=your_gmail@gmail.com
SMTP_PASS=your_app_specific_password
EMAIL_FROM=noreply@yourdomain.com
FRONTEND_URL=http://your_server_ip:3000

# Server Configuration
NODE_ENV=production
PORT=3000
CORS_ORIGIN=http://your_server_ip:3000,http://localhost:3000

# File Upload Configuration
UPLOAD_MAX_SIZE=10485760
ALLOWED_EXTENSIONS=jpg,jpeg,png,pdf
UPLOAD_PATH=/app/uploads

# American Timezone
TZ=America/New_York
```

### Edit ai-pipeline/.env:
```bash
nano ai-pipeline/.env
```

```env
# Ollama Configuration
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3:8b

# ChromaDB Configuration
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Data Sources
PUBMED_API_KEY=your_pubmed_api_key_if_needed
```

## Step 5: Setup SSL/TLS (Recommended)

### Install Nginx and Certbot:
```bash
apt install -y nginx certbot python3-certbot-nginx

# Configure Nginx
nano /etc/nginx/sites-available/bettergut
```

### Nginx Configuration:
```nginx
server {
    listen 80;
    server_name your_domain.com;  # Replace with your domain

    # API routes
    location /api/ {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Frontend routes (if serving Flutter web)
    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

```bash
# Enable the site
ln -s /etc/nginx/sites-available/bettergut /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

# Get SSL certificate (if you have a domain)
certbot --nginx -d your_domain.com
```

## Step 6: Deploy with Docker

### Create production docker-compose.yml:
```bash
nano docker-compose.prod.yml
```

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: bettergut
      POSTGRES_USER: bettergut
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      TZ: America/New_York
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/database/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U bettergut -d bettergut"]
      interval: 30s
      timeout: 10s
      retries: 3

  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - NODE_ENV=production
      - TZ=America/New_York
    ports:
      - "3000:3000"
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - backend_uploads:/app/uploads
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "node", "healthcheck.js"]
      interval: 30s
      timeout: 10s
      retries: 3

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - TZ=America/New_York
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  ai-pipeline:
    build:
      context: ./ai-pipeline
      dockerfile: Dockerfile
    ports:
      - "8001:8000"
    depends_on:
      - ollama
    environment:
      - TZ=America/New_York
    volumes:
      - chroma_data:/app/chroma_data
    restart: unless-stopped

volumes:
  postgres_data:
  backend_uploads:
  ollama_data:
  chroma_data:
```

### Deploy the application:
```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up -d --build

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Pull and setup Llama 3 model
docker exec -it bettergut_ollama_1 ollama pull llama3:8b
```

## Step 7: Initialize Database and AI Pipeline

### Setup database:
```bash
# The database will be automatically initialized from init.sql
# Check if tables were created
docker exec -it bettergut_postgres_1 psql -U bettergut -d bettergut -c "\dt"
```

### Initialize AI knowledge base:
```bash
# Run health data crawlers
docker exec -it bettergut_ai-pipeline_1 python -m scripts.crawl_health_data

# Check if data was ingested
docker exec -it bettergut_ai-pipeline_1 python -c "
from services.rag_service import RAGService
rag = RAGService()
print(f'Knowledge base has {rag.collection.count()} documents')
"
```

## Step 8: Configure Firewall and Security

```bash
# Install and configure UFW firewall
apt install -y ufw

# Allow SSH (change port if needed)
ufw allow 22/tcp

# Allow HTTP and HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Allow application ports
ufw allow 3000/tcp  # Backend API
ufw allow 8001/tcp  # AI Pipeline

# Enable firewall
ufw --force enable
ufw status
```

## Step 9: Setup Monitoring and Backups

### Create backup script:
```bash
nano /opt/scripts/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
docker exec bettergut_postgres_1 pg_dump -U bettergut bettergut > $BACKUP_DIR/db_backup_$DATE.sql

# Backup uploads
tar -czf $BACKUP_DIR/uploads_backup_$DATE.tar.gz -C /var/lib/docker/volumes/bettergut_backend_uploads/_data .

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

```bash
chmod +x /opt/scripts/backup.sh

# Add to crontab for daily backups
echo "0 2 * * * /opt/scripts/backup.sh >> /var/log/backup.log 2>&1" | crontab -
```

## Step 10: Email Configuration for American Users

### Gmail App Password Setup:
1. Enable 2-factor authentication on your Gmail account
2. Generate an app-specific password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
   - Use this password in `SMTP_PASS`

### Email Template Customization:
The email templates are already configured for American users with:
- EST/EDT timezone awareness
- American English spelling and phrasing
- Professional business email format

## Step 11: Testing Deployment

### Test API endpoints:
```bash
# Health check
curl http://your_server_ip:3000/api/health

# Registration (should send verification email)
curl -X POST http://your_server_ip:3000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "firstName": "Test",
    "lastName": "User"
  }'
```

### Test AI pipeline:
```bash
curl http://your_server_ip:8001/health
```

## Step 12: Mobile App Configuration

### Update Flutter app configuration:
In your Flutter app's `lib/config/api_config.dart`:

```dart
class ApiConfig {
  static const String baseUrl = 'http://your_server_ip:3000/api';
  // Or with domain: 'https://yourdomain.com/api'
  
  static const String wsUrl = 'ws://your_server_ip:3000';
  // Or with domain: 'wss://yourdomain.com'
}
```

## Maintenance Commands

### Update application:
```bash
cd /opt/bettergut
git pull
docker-compose -f docker-compose.prod.yml up -d --build
```

### View logs:
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Restart services:
```bash
docker-compose -f docker-compose.prod.yml restart
```

### Monitor resource usage:
```bash
# Docker stats
docker stats

# System resources
htop
df -h
```

## Troubleshooting

### Common Issues:

1. **Email not sending**: Check SMTP credentials and Gmail app password
2. **Database connection failed**: Verify environment variables and service startup order
3. **Ollama model not loading**: Ensure sufficient GPU memory and model is pulled
4. **High memory usage**: Monitor Llama 3 model memory usage, consider smaller model variants

### Log Locations:
- Application logs: `docker-compose logs`
- Nginx logs: `/var/log/nginx/`
- System logs: `/var/log/syslog`

## Security Considerations

1. **Change default passwords**: Update all default passwords in environment files
2. **Firewall configuration**: Only open necessary ports
3. **SSL/TLS**: Use HTTPS in production with proper certificates
4. **Regular updates**: Keep system and Docker images updated
5. **Backup encryption**: Encrypt sensitive backup data
6. **API rate limiting**: Consider implementing rate limiting for API endpoints

This deployment guide provides a production-ready setup for the BetterGut application on vast.ai servers, optimized for American users with proper email verification and security measures.
