# 🚀 How to Start the Frontend - Complete Guide

This guide explains all the different ways to start the Thinkubator RAG frontend and complete system.

## 🎯 Quick Start (Recommended)

### **Option 1: Complete System (Frontend + Backend)**
```bash
# Start everything in development mode
make dev

# Your system will be available at:
# - Frontend: http://localhost:3001
# - Backend:  http://localhost:8001
# - Health:   http://localhost:8001/health
```

This is the **most common way** to start the system for development.

## 🔧 All Available Startup Options

### **1. Development Environment (Hot Reload)**
```bash
make dev
```
**What it does:**
- Starts frontend (Next.js) on port 3001
- Starts backend (FastAPI) on port 8001
- Enables hot reload for both frontend and backend
- Perfect for active development

**Access Points:**
- Frontend UI: http://localhost:3001
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

### **2. Production Environment**
```bash
make prod
```
**What it does:**
- Starts optimized production builds
- Better performance, smaller containers
- No development tools or hot reload
- Production-ready configuration

### **3. Debug Environment**
```bash
make debug
```
**What it does:**
- Starts development mode + debugging capabilities
- Python debugger on port 5679
- VS Code debugging integration
- Set breakpoints and debug in containers

**After starting debug mode:**
1. Set breakpoints in VS Code
2. Press Ctrl+Shift+D (Run and Debug)
3. Select "🐍 Debug RAG Backend" → Press F5

## 🛑 How to Stop the System

### **Stop All Services**
```bash
make stop
```

### **Stop Specific Environments**
```bash
make debug-stop    # Stop debug environment
# For dev/prod: use 'make stop'
```

## 👀 Monitoring and Logs

### **View All Logs**
```bash
make logs
```

### **View Debug Logs**
```bash
make debug-logs
```

### **Check Container Status**
```bash
docker compose ps
```

## 🔧 Manual Docker Commands (Advanced)

### **Development**
```bash
# Start
docker compose up -d

# Stop
docker compose down

# Rebuild and start
docker compose up --build -d
```

### **Production**
```bash
# Start
docker compose -f docker-compose-prod.yml up -d

# Stop
docker compose -f docker-compose-prod.yml down
```

### **Debug**
```bash
# Start
docker compose -f docker-compose-debug.yml up -d

# Stop
docker compose -f docker-compose-debug.yml down
```

## 🌐 Frontend-Only Development (Alternative)

If you want to run **only the frontend** (with backend running separately):

### **Option A: Frontend in Docker, Backend Separately**
```bash
# 1. Start only backend
docker compose up backend -d

# 2. Start frontend separately (in another terminal)
cd src/frontend
npm run dev
# Frontend runs on http://localhost:3000 (different port!)
```

### **Option B: Both Outside Docker (Not Recommended)**
```bash
# Terminal 1: Backend
cd src/backend
python main.py

# Terminal 2: Frontend  
cd src/frontend
npm run dev
```

## 🔍 Troubleshooting

### **Port Conflicts**
If you get port conflicts:
```bash
# Check what's using the ports
lsof -i :3001  # Frontend
lsof -i :8001  # Backend

# Kill processes if needed
kill -9 <PID>

# Or clean Docker environment
make clean-docker
```

### **Frontend Not Loading**
```bash
# Check container status
docker compose ps

# Check frontend logs
docker compose logs frontend

# Restart just frontend
docker compose restart frontend
```

### **Backend Not Responding**
```bash
# Check backend health
curl http://localhost:8001/health

# Check backend logs
docker compose logs backend

# Restart backend
docker compose restart backend
```

### **Complete Reset**
```bash
# Clean everything and start fresh
make clean-docker
make dev
```

## 📊 System Architecture

```
┌─────────────────┐    ┌──────────────────┐
│   Frontend      │    │     Backend      │
│   (Next.js)     │◄──►│    (FastAPI)     │
│   Port: 3001    │    │   Port: 8001     │
└─────────────────┘    └──────────────────┘
         │                       │
         └───────────────────────┘
              Docker Network
              (rag-network)
```

## 🎯 Environment Comparison

| Feature | Development (`make dev`) | Production (`make prod`) | Debug (`make debug`) |
|---------|-------------------------|-------------------------|---------------------|
| **Hot Reload** | ✅ Yes | ❌ No | ✅ Yes |
| **Performance** | 🟡 Good | 🟢 Excellent | 🟡 Good |
| **Debugging** | 🟡 Basic | ❌ No | 🟢 Advanced |
| **Build Time** | 🟢 Fast | 🟡 Slower | 🟢 Fast |
| **Use Case** | Daily development | Production deployment | Debugging issues |

## 🚀 Recommended Workflows

### **Daily Development**
```bash
# Start your day
make dev

# Code, test, iterate...
# Frontend auto-reloads on changes
# Backend restarts on changes

# End of day
make stop
```

### **Debugging Issues**
```bash
# When you hit a bug
make debug

# Set breakpoints in VS Code
# Press F5 to debug
# Fix the issue

# Switch back to dev mode
make debug-stop
make dev
```

### **Testing Production Build**
```bash
# Test production locally
make prod

# Verify everything works
curl http://localhost:8001/health
open http://localhost:3001

# Back to development
make stop
make dev
```

## ⚡ Quick Reference Commands

| Command | What It Does |
|---------|-------------|
| `make dev` | **Start development** (most common) |
| `make prod` | Start production environment |
| `make debug` | Start with debugging capabilities |
| `make stop` | Stop all containers |
| `make logs` | View all logs |
| `make clean-docker` | Clean and reset everything |

## 🎉 Success Indicators

When your system starts successfully, you should see:

### **Frontend Working:**
- ✅ http://localhost:3001 loads the RAG interface
- ✅ You see "Thinkubator RAG Explorer" title
- ✅ Query input box and search button visible

### **Backend Working:**  
- ✅ http://localhost:8001/health returns `{"status": "healthy"}`
- ✅ API docs available at http://localhost:8001/docs
- ✅ Query processing works end-to-end

### **Integration Working:**
- ✅ Frontend can send queries to backend
- ✅ Results display with sources and citations
- ✅ No CORS or connection errors

## 🆘 Getting Help

If you encounter issues:

1. **Check the logs:** `make logs`
2. **Verify containers:** `docker compose ps`  
3. **Test connectivity:** `curl http://localhost:8001/health`
4. **Clean reset:** `make clean-docker && make dev`
5. **Check documentation:** `ENVIRONMENT_SETUP.md`, `DEBUG_GUIDE.md`

---

**🎯 Bottom Line:** Use `make dev` to start everything for development. That's the simplest and most effective way to get your frontend and backend running together! 🚀
