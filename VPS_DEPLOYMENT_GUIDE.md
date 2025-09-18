# VPS Deployment Guide - Traefik Setup

## 🎯 Overview
This guide shows how to deploy your RAG application on a VPS using Traefik for automatic HTTPS and modern container orchestration.

## 🏗️ Architecture

```
Internet → Traefik (Port 80/443) → Docker Containers
                ↓                        ↓
         your-domain.com           Port 3000: Frontend
         api.your-domain.com       Port 8000: Backend  
                                   Port 6379: Redis (internal)
```

## 📋 Prerequisites

### 1. VPS Requirements
- **OS**: Ubuntu 22.04 LTS or similar
- **RAM**: 4GB minimum (8GB recommended for AI workloads)
- **Storage**: 40GB+ SSD
- **Docker**: Latest version installed

### 2. Domain Setup
You need a domain with A records pointing to your VPS:
```
A Record: yourdomain.com        → YOUR_VPS_IP
A Record: api.yourdomain.com    → YOUR_VPS_IP
A Record: traefik.yourdomain.com → YOUR_VPS_IP (optional dashboard)
```

## 🚀 Deployment Steps

### Step 1: Prepare VPS
```bash
# Connect to your VPS
ssh root@your-vps-ip

# Install Docker (if not installed)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Create app directory
mkdir -p /opt/rag-app
cd /opt/rag-app
```

### Step 2: Upload Application Code
```bash
# From your local machine
rsync -av --exclude='node_modules' --exclude='.git' --exclude='logs' \
  /path/to/your/thinkubator-rag/ root@your-vps-ip:/opt/rag-app/
```

### Step 3: Configure Production Environment
```bash
# On VPS
cd /opt/rag-app

# Copy and edit production environment
cp deployment/env-examples/production.env .env.production

# Edit with your values
nano .env.production
```

**Required changes in `.env.production`:**
```bash
# Replace with your domain
DOMAIN=yourdomain.com
ACME_EMAIL=admin@yourdomain.com

# Add your API keys
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-actual-key
SUPABASE_SERVICE_ROLE_KEY=your-actual-key
POSTGRES_URL_NON_POOLING=your-postgres-url
GEMINI_API_KEY=your-gemini-key
```

### Step 4: Deploy with Traefik
```bash
# On VPS
make prod

# Or manually:
docker network create traefik-network
docker compose --env-file .env.production --profile production up -d --build
```

### Step 5: Verify Deployment
```bash
# Check containers
docker compose ps

# Check logs
docker compose logs -f

# Test endpoints
curl https://yourdomain.com
curl https://api.yourdomain.com/health
```

## 🔧 Environment Profiles

### Development Profile (Local)
```bash
# Starts without Traefik, uses exposed ports
make dev

# Access:
# Frontend: http://localhost:3001  
# Backend:  http://localhost:8001
```

### Production Profile (VPS)
```bash
# Starts with Traefik, automatic HTTPS
make prod

# Access:
# Frontend: https://yourdomain.com
# Backend:  https://api.yourdomain.com
# Dashboard: https://traefik.yourdomain.com:8080
```

## 🔒 Security Features

### Automatic HTTPS
- ✅ Let's Encrypt certificates
- ✅ HTTP → HTTPS redirects
- ✅ Automatic certificate renewal

### Security Headers
- ✅ HSTS (HTTP Strict Transport Security)
- ✅ X-Frame-Options
- ✅ Content-Type nosniff
- ✅ XSS Protection

### CORS Configuration
- ✅ Proper API CORS headers
- ✅ Domain-specific origin restrictions

## 📊 Monitoring

### Health Checks
```bash
# Backend health
curl https://api.yourdomain.com/health

# Container status
docker compose ps

# Resource usage
docker stats
```

### Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs backend
docker compose logs traefik
```

### Traefik Dashboard
Access at: `https://traefik.yourdomain.com:8080`
- View routes and services
- Monitor certificates
- Check middleware status

## 🔄 Updates & Maintenance

### Update Application
```bash
# Upload new code
rsync -av --exclude='node_modules' \
  /local/path/ root@vps:/opt/rag-app/

# Rebuild and restart
cd /opt/rag-app
docker compose --env-file .env.production --profile production up -d --build
```

### Certificate Renewal
Automatic via Traefik - no manual intervention needed!

### Scale Services
```bash
# Scale backend
docker compose --env-file .env.production up -d --scale backend=3

# Scale frontend  
docker compose --env-file .env.production up -d --scale frontend=2
```

## 🚨 Troubleshooting

### SSL Certificate Issues
```bash
# Check Traefik logs
docker compose logs traefik

# Verify domain DNS
nslookup yourdomain.com

# Check ACME file permissions
ls -la deployment/traefik/acme/acme.json
# Should be: -rw------- (600)
```

### Service Connection Issues
```bash
# Test internal connectivity
docker compose exec backend curl http://localhost:8000/health
docker compose exec frontend curl http://localhost:3000

# Check networks
docker network ls
docker network inspect traefik-network
```

### Performance Issues
```bash
# Check resource usage
docker stats

# Check logs for errors
docker compose logs --tail=100 | grep -i error

# Monitor response times
time curl https://yourdomain.com
time curl https://api.yourdomain.com/health
```

## 💡 Tips & Best Practices

### 1. Resource Management
- Monitor disk space (`df -h`)
- Set up log rotation
- Use Redis for caching to reduce database load

### 2. Security
- Change default passwords
- Keep Docker images updated
- Monitor access logs

### 3. Backup Strategy
- Database backups (Supabase handles this)
- Application code in Git
- Environment files securely stored
- Docker volumes if needed

### 4. Monitoring
- Set up external monitoring (UptimeRobot, etc.)
- Configure log aggregation
- Monitor certificate expiration

## 📈 Scaling Considerations

When your application grows:

1. **Horizontal Scaling**: Add more container instances
2. **Database Scaling**: Upgrade Supabase plan
3. **CDN**: Add Cloudflare for static assets
4. **Load Balancing**: Traefik handles this automatically
5. **Caching**: Redis + application-level caching

Your RAG application is now professionally deployed with modern DevOps practices! 🎉
