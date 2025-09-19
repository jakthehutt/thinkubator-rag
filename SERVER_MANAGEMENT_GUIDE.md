# Server Management Guide - Thinkubator RAG VPS

## 🎯 Overview

This guide covers day-to-day server management for the Thinkubator RAG application deployed on a VPS. It includes SSH access, monitoring, troubleshooting, and maintenance procedures.

**Server Details:**
- **VPS IP**: 217.154.75.92
- **Domain**: thinkubator.quasol.eu
- **API Domain**: api.thinkubator.quasol.eu
- **OS**: Ubuntu 22.04 LTS
- **Resources**: 4GB RAM, 120GB Storage

## 🔐 SSH Access and Connection

### Basic SSH Connection

```bash
# Connect to server
ssh root@217.154.75.92

# Or using SSH config alias (if configured)
ssh thinkubator-vps
```

### SSH Configuration (Optional but Recommended)

**Add to `~/.ssh/config` for easier access:**

```bash
Host thinkubator-vps
    HostName 217.154.75.92
    User root
    IdentityFile ~/.ssh/id_rsa
    Port 22
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

### SSH Key Setup (Recommended for Security)

```bash
# Generate SSH key (if you don't have one)
ssh-keygen -t rsa -b 4096 -C "jakob.hutter@quasol.eu"

# Copy public key to server
ssh-copy-id root@217.154.75.92

# Test key-based authentication
ssh root@217.154.75.92
```

## 📁 Server File Structure

### Application Directory Layout

```
/opt/rag-app/                    # Main application directory
├── src/                         # Source code
│   ├── backend/                 # Python FastAPI backend
│   └── frontend/                # Next.js frontend
├── data/                        # PDF files and processed documents
│   ├── pdfs/                   # Original PDF files
│   └── processed/              # Processed document chunks
├── logs/                        # Application logs
├── deployment/                  # Deployment configuration
│   └── traefik/
│       └── acme/               # SSL certificates (auto-managed)
├── docker-compose.yml          # Docker orchestration config
├── .env.production            # Production environment variables
├── Makefile                   # Build commands
└── VPS_DEPLOYMENT_GUIDE.md    # Deployment reference
```

### Important File Locations

```bash
# Main application directory
cd /opt/rag-app

# Production environment variables
nano /opt/rag-app/.env.production

# Docker configuration
cat /opt/rag-app/docker-compose.yml

# SSL certificates (auto-managed by Traefik)
ls -la /opt/rag-app/deployment/traefik/acme/

# Application logs
docker compose logs -f
```

## 🐳 Docker Container Management

### Basic Container Operations

```bash
# Navigate to application directory
cd /opt/rag-app

# Check container status
docker compose ps

# View all logs (real-time)
docker compose logs -f

# View specific service logs
docker compose logs backend
docker compose logs frontend
docker compose logs traefik

# Restart a specific service
docker compose restart backend
docker compose restart frontend

# Restart all services
docker compose restart
```

### Production Deployment Commands

```bash
# Full deployment (with rebuild)
docker compose --env-file .env.production --profile production up -d --build

# Stop all services
docker compose down

# Update and restart (most common update procedure)
docker compose down
docker compose --env-file .env.production --profile production up -d --build
```

### Container Health and Status

```bash
# Check container health
docker compose ps
docker stats

# Check container logs for errors
docker compose logs | grep -i error
docker compose logs | grep -i failed

# Access container shell for debugging
docker compose exec backend bash
docker compose exec frontend sh
```

## 🔧 System Monitoring and Maintenance

### Health Checks

```bash
# Test application endpoints
curl https://thinkubator.quasol.eu
curl https://api.thinkubator.quasol.eu/health

# Check SSL certificates
curl -I https://thinkubator.quasol.eu
curl -I https://api.thinkubator.quasol.eu

# Test DNS resolution
nslookup thinkubator.quasol.eu
nslookup api.thinkubator.quasol.eu
```

### Resource Monitoring

```bash
# System resource overview
htop                    # Interactive system monitor
top                     # Basic system monitor

# Disk usage
df -h                   # Human-readable disk usage
du -sh /opt/rag-app    # Application directory size

# Memory usage
free -m                 # Memory usage in MB
free -h                 # Human-readable memory

# Docker resource usage
docker stats            # Real-time container resource usage
docker system df        # Docker disk usage
```

### Log Management

```bash
# View recent application logs
docker compose logs --tail=100 backend
docker compose logs --tail=100 frontend
docker compose logs --tail=50 traefik

# Search for specific issues
docker compose logs | grep -i "error"
docker compose logs | grep -i "failed"
docker compose logs | grep -i "timeout"

# Follow logs in real-time
docker compose logs -f backend
```

## 🔒 Security and Updates

### System Updates

```bash
# Update package list
apt update

# Upgrade system packages
apt upgrade -y

# Clean up old packages
apt autoremove -y
apt autoclean

# Check for security updates
apt list --upgradable
```

### Docker Maintenance

```bash
# Clean up unused Docker resources
docker system prune -f

# Remove unused images
docker image prune -f

# Remove unused volumes (be careful!)
docker volume prune -f

# Update Docker images
docker compose pull
docker compose up -d
```

### Security Monitoring

```bash
# Check active connections
netstat -tulpn | grep LISTEN

# Check firewall status
ufw status

# Check system logs for security issues
journalctl -xe | grep -i "failed\|error"

# Check SSH authentication attempts
grep "Failed password" /var/log/auth.log | tail -20
```

## 🚨 Troubleshooting Common Issues

### Application Not Responding

```bash
# 1. Check container status
docker compose ps

# 2. Check logs for errors
docker compose logs --tail=100

# 3. Check system resources
docker stats
df -h
free -m

# 4. Test connectivity
curl -I https://thinkubator.quasol.eu
curl -I https://api.thinkubator.quasol.eu/health

# 5. Restart services if needed
docker compose restart
```

### SSL Certificate Issues

```bash
# Check Traefik logs for SSL errors
docker compose logs traefik | grep -i "certificate\|ssl\|tls"

# Check ACME certificate file
ls -la /opt/rag-app/deployment/traefik/acme/acme.json
cat /opt/rag-app/deployment/traefik/acme/acme.json | jq .

# Test SSL certificate
openssl s_client -connect thinkubator.quasol.eu:443 -servername thinkubator.quasol.eu

# Force certificate renewal (if needed)
docker compose restart traefik
```

### High Resource Usage

```bash
# Identify resource-heavy containers
docker stats

# Check disk space
df -h
du -sh /var/lib/docker

# Clean up Docker resources
docker system prune -f

# Check for memory leaks
docker compose logs backend | grep -i "memory\|oom"

# Restart resource-heavy services
docker compose restart backend
```

### DNS Issues

```bash
# Test DNS resolution
nslookup thinkubator.quasol.eu
dig thinkubator.quasol.eu

# Check from different DNS servers
dig @8.8.8.8 thinkubator.quasol.eu
dig @1.1.1.1 thinkubator.quasol.eu

# Check DNS propagation
# Use online tools like whatsmydns.net for global DNS checking
```

## 🔄 Backup and Recovery

### Creating Backups

```bash
# Create application backup
tar -czf /backup/rag-app-$(date +%Y%m%d-%H%M).tar.gz /opt/rag-app/

# Backup environment configuration
cp /opt/rag-app/.env.production /backup/.env.production.$(date +%Y%m%d)

# Create backup directory (first time)
mkdir -p /backup
chmod 700 /backup
```

### Recovery Procedures

```bash
# Stop services before recovery
docker compose down

# Restore from backup
cd /
tar -xzf /backup/rag-app-YYYYMMDD-HHMM.tar.gz

# Restore environment file
cp /backup/.env.production.YYYYMMDD /opt/rag-app/.env.production

# Restart services
cd /opt/rag-app
docker compose --env-file .env.production --profile production up -d --build
```

## 🔧 Routine Maintenance Tasks

### Daily Tasks

```bash
# Quick health check
curl https://api.thinkubator.quasol.eu/health
docker compose ps

# Check disk space
df -h

# Review logs for errors
docker compose logs --since="24h" | grep -i error
```

### Weekly Tasks

```bash
# System updates
apt update && apt upgrade -y

# Docker cleanup
docker system prune -f

# Backup application
tar -czf /backup/weekly-backup-$(date +%Y%m%d).tar.gz /opt/rag-app/

# Review resource usage trends
docker stats --no-stream
```

### Monthly Tasks

```bash
# Full system maintenance
apt update && apt upgrade -y && apt autoremove -y

# Docker image updates
docker compose pull
docker compose up -d

# Security audit
grep "Failed password" /var/log/auth.log | wc -l

# Storage cleanup
find /backup -name "*.tar.gz" -mtime +30 -delete
```

## 📞 Emergency Procedures

### Complete Service Restart

```bash
# Full restart procedure
docker compose down
docker system prune -f
cd /opt/rag-app
docker compose --env-file .env.production --profile production up -d --build
```

### Emergency Stop

```bash
# Stop all services immediately
docker compose down
docker stop $(docker ps -aq)
```

### Recovery from Backup

```bash
# If main application is corrupted
docker compose down
rm -rf /opt/rag-app
cd /
tar -xzf /backup/rag-app-LATEST.tar.gz
cd /opt/rag-app
docker compose --env-file .env.production --profile production up -d --build
```

## 📋 Useful Commands Reference

### File Operations

```bash
# Upload files from local machine
scp local-file.txt root@217.154.75.92:/opt/rag-app/
rsync -av local-directory/ root@217.154.75.92:/opt/rag-app/

# Download files to local machine
scp root@217.154.75.92:/opt/rag-app/logs/app.log local-logs/

# Edit files on server
nano /opt/rag-app/.env.production
vim /opt/rag-app/docker-compose.yml
```

### System Information

```bash
# System information
uname -a                # System details
lsb_release -a         # Ubuntu version
uptime                 # System uptime
ps aux | head -20      # Top processes
netstat -tulpn         # Network connections
```

### Docker Information

```bash
# Docker system info
docker info
docker version
docker system df
docker network ls
docker volume ls
```

---

**Remember**: Always test changes in a staging environment first, maintain regular backups, and monitor system health continuously. When in doubt, consult the deployment guide or create a backup before making changes.
