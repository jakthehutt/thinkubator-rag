# Environment Setup and Docker Development Guide

This document explains how to set up and manage the Thinkubator RAG development environment using Docker. The project has been fully containerized for consistent development and deployment across different platforms.

## Overview

The Thinkubator RAG system uses a modern Docker-based development environment with:

1. **Docker Compose** for orchestration and local development
2. **Containerized services** for consistent development environments
3. **Automated testing** with comprehensive test suites
4. **Environment-specific configurations** for development and production

## Project Structure

The project contains the following key components:

- `src/backend/` - FastAPI backend with RAG pipeline
- `src/frontend/` - Next.js frontend application
- `docker-compose.yml` - Development environment configuration
- `docker-compose-prod.yml` - Production environment configuration
- `dev-requirements.txt` - Python backend dependencies
- `make/` - Build and test automation scripts

## Prerequisites

### Required Software

1. **Docker Desktop** (latest version recommended)
   - Windows: [Docker Desktop for Windows](https://docs.docker.com/desktop/windows/install/)
   - macOS: [Docker Desktop for Mac](https://docs.docker.com/desktop/mac/install/)
   - Linux: [Docker Engine](https://docs.docker.com/engine/install/)

2. **Make** (for running automation scripts)
   - macOS: Install via Xcode Command Line Tools: `xcode-select --install`
   - Linux: Usually pre-installed, or install via package manager
   - Windows: Install via [Chocolatey](https://chocolatey.org/): `choco install make`

3. **Git** (for version control)
4. **curl** (for API testing - usually pre-installed)

### Required Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# === SUPABASE CONFIGURATION ===
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
POSTGRES_URL_NON_POOLING=your_postgres_connection_string

# === AI CONFIGURATION ===
GEMINI_API_KEY=your_google_gemini_api_key
```

**Important**: Contact the project maintainer to get these values. Never commit the `.env` file to version control.

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd thinkubator-rag

# Verify Docker is running
docker --version
docker compose version

# Check environment variables
cat .env  # Should show your environment variables
```

### 2. Start Development Environment

```bash
# Start all services in development mode
make dev

# This will:
# - Build Docker containers
# - Start backend (FastAPI) on http://localhost:8001
# - Start frontend (Next.js) on http://localhost:3001
# - Set up networking between containers
```

### 3. Verify Setup

```bash
# Run comprehensive tests
make test-docker

# Test backend API directly
curl http://localhost:8001/health

# Test frontend
curl http://localhost:3001/

# Test RAG functionality
curl -X POST "http://localhost:8001/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is circular economy?"}'
```

## Available Commands

### Docker Management

```bash
# Development environment
make dev          # Start development environment
make prod         # Start production environment
make stop         # Stop all containers
make logs         # View container logs
make build        # Build containers without starting

# Testing
make test-docker    # Comprehensive Docker setup test
make test-frontend  # Frontend-specific tests
make test-all      # All backend tests

# Cleanup
make clean-docker  # Remove containers, volumes, and clean up
```

### Manual Docker Commands

If you prefer direct Docker commands:

```bash
# Development
docker compose up --build -d
docker compose down

# Production
docker compose -f docker-compose-prod.yml up --build -d
docker compose -f docker-compose-prod.yml down

# View logs
docker compose logs backend
docker compose logs frontend

# Execute commands in containers
docker compose exec backend bash
docker compose exec frontend sh
```

## Service Details

### Backend Service (FastAPI + RAG Pipeline)

- **Port**: 8001 (external) → 8000 (internal)
- **Technology**: Python 3.11, FastAPI, Supabase, Google Gemini
- **Health Check**: http://localhost:8001/health
- **API Documentation**: http://localhost:8001/docs
- **Key Features**:
  - RAG (Retrieval-Augmented Generation) pipeline
  - Vector search with Supabase + pgvector
  - AI-powered text generation with Google Gemini
  - PDF document processing and chunking

### Frontend Service (Next.js)

- **Port**: 3001 (external) → 3000 (internal)
- **Technology**: Next.js 15.5.2, React 19, TypeScript, Tailwind CSS
- **URL**: http://localhost:3001
- **Key Features**:
  - Modern responsive UI with Tailwind CSS
  - Real-time query processing interface
  - Source attribution and expandable results
  - Hot reload in development mode

## Development Workflow

### Making Changes

1. **Backend Changes**: 
   - Edit files in `src/backend/`
   - Container will automatically restart on code changes
   - View logs: `make logs` or `docker compose logs backend`

2. **Frontend Changes**:
   - Edit files in `src/frontend/src/`
   - Next.js hot reload provides instant updates
   - View logs: `docker compose logs frontend`

3. **Testing Changes**:
   ```bash
   # Test specific components
   make test-docker      # Full integration test
   make test-frontend    # Frontend tests
   make test-all        # Backend unit tests
   ```

### Environment-Specific Development

#### Development Mode
- Hot reload enabled
- Debug logging
- Development optimizations
- Source maps enabled

#### Production Mode
```bash
make prod  # Uses docker-compose-prod.yml
```
- Optimized builds
- Production-ready configuration
- No development tools
- Compressed assets

## Troubleshooting

### Common Issues

#### 1. "Port already in use" Error
```bash
# Check what's using the ports
lsof -i :8001  # Backend port
lsof -i :3001  # Frontend port

# Kill processes if needed
kill -9 <PID>

# Or use different ports in docker-compose.yml
```

#### 2. "Docker daemon not running"
- Start Docker Desktop application
- On Linux: `sudo systemctl start docker`

#### 3. "Environment variables not set"
```bash
# Check .env file exists and has correct format
cat .env

# Verify no extra spaces or quotes around values
# Each line should be: KEY=value (no spaces around =)
```

#### 4. "Container build fails"
```bash
# Clean Docker cache and rebuild
make clean-docker
docker system prune -f
make dev
```

#### 5. "Backend API not responding"
```bash
# Check backend container logs
docker compose logs backend

# Common issues:
# - Missing environment variables
# - Database connection problems
# - Python dependency issues

# Restart backend only
docker compose restart backend
```

#### 6. "Frontend not loading"
```bash
# Check frontend container logs
docker compose logs frontend

# Common issues:
# - Node.js build errors
# - Missing dependencies
# - Port conflicts

# Rebuild frontend
docker compose build frontend --no-cache
docker compose up frontend
```

### Performance Optimization

#### For Better Development Experience

1. **Allocate more resources to Docker**:
   - Docker Desktop → Settings → Resources
   - Increase CPU: 4+ cores recommended
   - Increase Memory: 8GB+ recommended

2. **Use Docker BuildKit** (enabled by default):
   ```bash
   export DOCKER_BUILDKIT=1
   ```

3. **Enable file sharing optimizations**:
   - Docker Desktop → Settings → Resources → File Sharing
   - Add project directory to shared paths

### Getting Help

If you encounter issues:

1. **Check the error messages** carefully - they often contain specific guidance
2. **Verify environment variables** are correctly set
3. **Check Docker logs** for service-specific errors: `make logs`
4. **Run diagnostic tests**: `make test-docker`
5. **Clean and restart**: `make clean-docker && make dev`

## Security Notes

- **Never commit `.env` files** - they contain sensitive API keys
- **Keep your Docker images updated** - run `docker pull` regularly
- **Use strong, unique values** for API keys and database credentials
- **Rotate secrets periodically** for enhanced security
- **Use different values for different environments** (development, staging, production)

## File Locations Summary

| File/Directory | Purpose | Key Points |
|----------------|---------|------------|
| `.env` | Environment variables | **Never commit** - contains secrets |
| `docker-compose.yml` | Development configuration | Port 8001 backend, 3001 frontend |
| `docker-compose-prod.yml` | Production configuration | Optimized for production deployment |
| `src/backend/` | Python backend code | FastAPI + RAG pipeline |
| `src/frontend/` | Next.js frontend code | React + TypeScript + Tailwind |
| `make/` | Build and test scripts | Automation for common tasks |
| `dev-requirements.txt` | Python dependencies | Backend package requirements |

## Quick Reference

### Essential Commands
```bash
# Start everything
make dev

# Check if everything is working
make test-docker

# View all logs
make logs

# Stop everything
make stop

# Start fresh (clean slate)
make clean-docker && make dev
```

### Service URLs
- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8001
- **Backend Health**: http://localhost:8001/health
- **API Documentation**: http://localhost:8001/docs

### Contact Information
- **Project Repository**: [Add repository URL]
- **Documentation**: This file and inline code comments
- **Issues**: Use GitHub issues for bug reports and feature requests

---

**Your Thinkubator RAG system is now ready for development! 🚀**
