# Deployment Update Guide - Thinkubator RAG

## 🎯 Overview

This guide provides step-by-step procedures for updating the deployed Thinkubator RAG application on your VPS. It covers different types of updates and rollback procedures.

**Before You Begin:**
- Ensure you have SSH access to the server: `ssh root@217.154.75.92`
- Have your local development environment working
- Test all changes locally before deploying to production

## 📋 Pre-Update Checklist

### Before Every Update

```bash
# ✅ 1. Test locally
cd /Users/jakthehut/Documents/Lohnarbeit/thinkubator-rag
make test-docker

# ✅ 2. Commit your changes
git add .
git commit -m "Your update description"
git push origin main

# ✅ 3. Create backup
ssh root@217.154.75.92
cd /opt/rag-app
tar -czf /backup/pre-update-backup-$(date +%Y%m%d-%H%M).tar.gz .

# ✅ 4. Check current system status
docker compose ps
curl https://api.thinkubator.quasol.eu/health
```

## 🔄 Update Types and Procedures

### 1. Code Changes Update (Most Common)

**For backend/frontend code changes, bug fixes, or new features.**

#### From Local Machine:

```bash
# Navigate to your project
cd /Users/jakthehut/Documents/Lohnarbeit/thinkubator-rag

# Upload updated code to server
rsync -av --progress \
  --exclude='node_modules' \
  --exclude='.git' \
  --exclude='logs' \
  --exclude='__pycache__' \
  --exclude='.env' \
  . root@217.154.75.92:/opt/rag-app/
```

#### On VPS Server:

```bash
# Connect to server
ssh root@217.154.75.92

# Navigate to app directory
cd /opt/rag-app

# Stop, rebuild, and restart services
docker compose down
docker compose --env-file .env.production --profile production up -d --build

# Verify deployment
docker compose ps
curl https://api.thinkubator.quasol.eu/health
curl https://thinkubator.quasol.eu
```

### 2. Environment Variables Update

**For changes to API keys, configuration, or environment settings.**

#### On VPS Server:

```bash
# Connect to server
ssh root@217.154.75.92
cd /opt/rag-app

# Edit production environment
nano .env.production

# Make your changes, then save (Ctrl+X, Y, Enter)

# Restart services to apply changes
docker compose down
docker compose --env-file .env.production --profile production up -d

# Note: No --build needed for env var only changes
```

### 3. Docker Configuration Update

**For changes to docker-compose.yml, Dockerfile, or container configuration.**

#### Upload Changes:

```bash
# From local machine
cd /Users/jakthehut/Documents/Lohnarbeit/thinkubator-rag

# Upload docker configuration files
scp docker-compose.yml root@217.154.75.92:/opt/rag-app/
scp src/backend/Dockerfile root@217.154.75.92:/opt/rag-app/src/backend/
scp src/frontend/Dockerfile root@217.154.75.92:/opt/rag-app/src/frontend/
```

#### Deploy Changes:

```bash
# On VPS
ssh root@217.154.75.92
cd /opt/rag-app

# Force rebuild with no cache
docker compose down
docker compose build --no-cache
docker compose --env-file .env.production --profile production up -d

# Verify deployment
docker compose ps
```

### 4. Dependencies Update

**For changes to Python packages (dev-requirements.txt) or Node.js packages (package.json).**

#### Upload Updated Files:

```bash
# From local machine
scp dev-requirements.txt root@217.154.75.92:/opt/rag-app/
scp src/frontend/package.json root@217.154.75.92:/opt/rag-app/src/frontend/
scp src/frontend/package-lock.json root@217.154.75.92:/opt/rag-app/src/frontend/
```

#### Force Container Rebuild:

```bash
# On VPS
ssh root@217.154.75.92
cd /opt/rag-app

# Complete rebuild (dependencies require fresh build)
docker compose down
docker compose build --no-cache
docker compose --env-file .env.production --profile production up -d --build
```

### 5. Data/PDF Files Update

**For adding new PDF documents or updating processed data.**

#### Upload New Files:

```bash
# From local machine - upload new PDFs
scp new-document.pdf root@217.154.75.92:/opt/rag-app/data/pdfs/

# Or upload processed data
scp data/processed/md/new-document_processed.json \
  root@217.154.75.92:/opt/rag-app/data/processed/md/
```

#### Restart Backend (to load new data):

```bash
# On VPS
ssh root@217.154.75.92
cd /opt/rag-app

# Restart backend to reload data
docker compose restart backend

# Verify new data is loaded
curl -X POST "https://api.thinkubator.quasol.eu/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "test query about new document"}'
```

## 🔄 Complete Update Workflow

### Standard Update Procedure

**Use this for most updates combining code and configuration changes:**

```bash
# === LOCAL MACHINE ===
cd /Users/jakthehut/Documents/Lohnarbeit/thinkubator-rag

# 1. Test changes locally
make test-docker

# 2. Commit changes
git add .
git commit -m "Update: description of changes"
git push origin main

# 3. Upload to server
rsync -av --progress \
  --exclude='node_modules' \
  --exclude='.git' \
  --exclude='logs' \
  --exclude='__pycache__' \
  --exclude='.env' \
  . root@217.154.75.92:/opt/rag-app/

# === VPS SERVER ===
ssh root@217.154.75.92
cd /opt/rag-app

# 4. Create backup
tar -czf /backup/backup-$(date +%Y%m%d-%H%M).tar.gz .

# 5. Deploy update
docker compose down
docker compose --env-file .env.production --profile production up -d --build

# 6. Verify deployment
docker compose ps
docker compose logs --tail=50

# 7. Test endpoints
curl https://api.thinkubator.quasol.eu/health
curl https://thinkubator.quasol.eu

# 8. Monitor for issues
docker compose logs -f
```

## 🚨 Troubleshooting Updates

### Update Fails - Container Won't Start

```bash
# Check container status
docker compose ps

# Check logs for errors
docker compose logs backend
docker compose logs frontend

# Common fixes:
# 1. Environment variable issues
nano .env.production  # Check for typos

# 2. Port conflicts
docker compose down
docker system prune -f
docker compose --env-file .env.production --profile production up -d --build

# 3. Resource issues
df -h  # Check disk space
free -m  # Check memory
```

### Application Responds But Behaves Incorrectly

```bash
# Check backend logs
docker compose logs backend | grep -i error

# Test API directly
curl -X POST "https://api.thinkubator.quasol.eu/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'

# Check database connectivity
docker compose exec backend python -c "
from src.backend.vector_store.supabase_vector_store import SupabaseVectorStore
store = SupabaseVectorStore()
print('Database connection: OK')
"
```

### Slow Performance After Update

```bash
# Check resource usage
docker stats

# Check for memory leaks
docker compose logs backend | grep -i memory

# Restart specific service
docker compose restart backend

# Clean up Docker resources
docker system prune -f
```

## ⏪ Rollback Procedures

### Quick Rollback (Last Working Version)

```bash
# On VPS
ssh root@217.154.75.92
cd /opt/rag-app

# Stop current services
docker compose down

# Restore from latest backup
tar -xzf /backup/pre-update-backup-YYYYMMDD-HHMM.tar.gz

# Start services with restored configuration
docker compose --env-file .env.production --profile production up -d --build
```

### Rollback to Specific Version

```bash
# If you need to rollback to a specific git commit
# From local machine:
cd /Users/jakthehut/Documents/Lohnarbeit/thinkubator-rag

# Find the commit you want to rollback to
git log --oneline -10

# Checkout that commit
git checkout COMMIT_HASH

# Deploy the rolled-back version
rsync -av --progress \
  --exclude='node_modules' \
  --exclude='.git' \
  --exclude='logs' \
  --exclude='__pycache__' \
  --exclude='.env' \
  . root@217.154.75.92:/opt/rag-app/

# On VPS - deploy
ssh root@217.154.75.92
cd /opt/rag-app
docker compose down
docker compose --env-file .env.production --profile production up -d --build
```

### Emergency Rollback Script

**Create this script on your VPS for emergency situations:**

```bash
# On VPS, create emergency rollback script
nano /root/emergency-rollback.sh

# Add this content:
#!/bin/bash
cd /opt/rag-app
docker compose down
tar -xzf /backup/$(ls -t /backup/*.tar.gz | head -1)
docker compose --env-file .env.production --profile production up -d --build
echo "Emergency rollback completed"

# Make executable
chmod +x /root/emergency-rollback.sh
```

## 📊 Post-Update Verification

### Verification Checklist

```bash
# ✅ 1. Container status
docker compose ps
# All containers should show "Up" status

# ✅ 2. Health checks
curl https://api.thinkubator.quasol.eu/health
# Should return: {"status": "healthy"}

# ✅ 3. Frontend accessibility
curl -I https://thinkubator.quasol.eu
# Should return: HTTP/2 200

# ✅ 4. SSL certificates
curl -I https://thinkubator.quasol.eu | grep -i "strict-transport-security"
# Should show security headers

# ✅ 5. RAG functionality
curl -X POST "https://api.thinkubator.quasol.eu/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is circular economy?"}'
# Should return meaningful RAG response

# ✅ 6. Log monitoring (run for 2-3 minutes)
docker compose logs -f
# Watch for any errors or warnings
```

## 🔄 Automated Update Script

**Create this script for easier updates:**

```bash
# On your local machine, create update script
nano ~/update-thinkubator.sh

# Add this content:
#!/bin/bash
set -e

echo "=== Thinkubator RAG Update Script ==="

# Navigate to project
cd /Users/jakthehut/Documents/Lohnarbeit/thinkubator-rag

# Test locally
echo "Testing locally..."
make test-docker

# Upload to server
echo "Uploading to server..."
rsync -av --progress \
  --exclude='node_modules' \
  --exclude='.git' \
  --exclude='logs' \
  --exclude='__pycache__' \
  --exclude='.env' \
  . root@217.154.75.92:/opt/rag-app/

# Deploy on server
echo "Deploying on server..."
ssh root@217.154.75.92 '
  cd /opt/rag-app
  tar -czf /backup/auto-backup-$(date +%Y%m%d-%H%M).tar.gz .
  docker compose down
  docker compose --env-file .env.production --profile production up -d --build
  sleep 10
  docker compose ps
  curl https://api.thinkubator.quasol.eu/health
'

echo "Update completed!"

# Make executable
chmod +x ~/update-thinkubator.sh
```

**Usage:**
```bash
~/update-thinkubator.sh
```

## 📅 Update Schedule Recommendations

### Regular Update Schedule

- **Daily**: Monitor health and logs
- **Weekly**: Apply security updates, review performance
- **Monthly**: Update dependencies, clean Docker resources
- **As Needed**: Deploy feature updates, bug fixes

### Best Practices

1. **Always test locally first**
2. **Create backups before updates**
3. **Update during low-traffic hours**
4. **Monitor for 15-30 minutes after updates**
5. **Keep rollback procedures ready**
6. **Document all changes**

---

**Remember**: Updates should be planned and tested. Always have a rollback plan ready, and never update production without testing the changes in development first.
