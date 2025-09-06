# 🚀 Enhanced Local Development Guide

This guide provides comprehensive local development setup with multiple options for testing and debugging.

## 🚀 **Quick Start (Recommended)**

### **Option 1: Mock API Development (Fastest)**
```bash
cd src/frontend
npm run dev
# Access: http://localhost:3000
```
- ✅ **No backend dependencies needed**
- ✅ **Instant startup**
- ✅ **Mock responses for testing UI**
- ✅ **Perfect for frontend development**

### **Option 2: Full Vercel Simulation**
```bash
cd src/frontend
vercel dev --listen 3000
# Access: http://localhost:3000
```
- ✅ **Full Vercel environment simulation**
- ✅ **Python functions work locally**
- ✅ **Production-like behavior**
- ✅ **Requires Vercel CLI setup**

### **Option 3: Separate Servers**
```bash
# Terminal 1: Start FastAPI backend
python run_local.py

# Terminal 2: Start Next.js frontend
cd src/frontend && npm run dev
```
- ✅ **FastAPI backend on port 8000**
- ✅ **Next.js frontend on port 3000**
- ✅ **Independent development**
- ✅ **Easy debugging**

## 🛠️ **Setup Instructions**

### **1. Install Dependencies**

```bash
# Install Vercel CLI globally
npm install -g vercel

# Install frontend dependencies
cd src/frontend
npm install
```

### **2. Environment Configuration**

Create `src/frontend/.env.local`:
```bash
# Development environment variables
DEBUG=true
NODE_ENV=development

# API Keys (same as production)
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key

# Local development overrides
VERCEL_ENV=development
```

### **3. Choose Your Development Mode**

## 🎯 **Development Options**

### **Option 1: Full Vercel Simulation (Recommended)**
```bash
python run_local_enhanced.py
# Choose option 1: Vercel Dev
```
- ✅ **Full Vercel environment simulation**
- ✅ **Python functions work locally**
- ✅ **Production-like behavior**
- ✅ **Automatic environment detection**

### **Option 2: Separate Servers**
```bash
# Terminal 1: FastAPI backend
python run_local_enhanced.py
# Choose option 4: FastAPI only

# Terminal 2: Next.js frontend  
cd src/frontend
npm run dev
```
- ✅ **Independent server control**
- ✅ **Easy debugging of individual components**
- ✅ **Fast restart times**

### **Option 3: Frontend Only**
```bash
cd src/frontend
npm run dev
```
- ✅ **Quick frontend development**
- ✅ **Mock API responses**

## 🔍 **Debugging Tools**

### **API Testing**
```bash
cd src/frontend
npm run debug:api
```
Tests all API endpoints:
- FastAPI backend (localhost:8000)
- Next.js API route (localhost:3000/api/query)
- Vercel Python function (localhost:3000/api/python/query)

### **Local Setup Testing**
```bash
cd src/frontend
npm run test:local
```
Checks all local endpoints and environment configuration.

### **Enhanced Logging**
Set `DEBUG=true` in your environment to see:
- 🔍 Request/response details
- ⏱️ Response timing
- 🌍 Environment detection
- ❌ Detailed error information

## 📊 **Debugging Features**

### **1. Enhanced API Route Logging**
The API route now logs:
- Request body and headers
- Environment detection logic
- API URL construction
- Response status and timing
- Success/error details

### **2. Environment Detection**
Automatic detection of:
- **Production Vercel**: Uses absolute URLs
- **Local Vercel**: Uses localhost URLs
- **Local Development**: Uses FastAPI backend

### **3. Performance Monitoring**
- Response time tracking
- Request/response size logging
- Error rate monitoring

## 🚨 **Troubleshooting**

### **Common Issues**

#### **1. Vercel CLI Not Found**
```bash
npm install -g vercel
```

#### **2. Port Conflicts**
- Next.js: Change port with `npm run dev -- -p 3001`
- FastAPI: Change port in `run_local_enhanced.py`

#### **3. Environment Variables**
Ensure `.env.local` has all required variables:
- `GEMINI_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`

#### **4. Python Dependencies**
```bash
pip install -r requirements.txt
```

### **Debug Commands**

```bash
# Test all endpoints
npm run debug:api

# Check local setup
npm run test:local

# Start with debugging
DEBUG=true npm run dev

# Vercel development
vercel dev
```

## 🎯 **Best Practices**

### **1. Development Workflow**
1. Start with Vercel dev for full simulation
2. Use separate servers for component debugging
3. Test APIs regularly with debug scripts
4. Monitor logs for performance issues

### **2. Environment Management**
- Use `.env.local` for local overrides
- Set `DEBUG=true` for detailed logging
- Keep production variables separate

### **3. Testing Strategy**
- Test all endpoints before deployment
- Use debug scripts for quick validation
- Monitor response times and errors

## 📈 **Performance Tips**

### **1. Faster Development**
- Use `--turbopack` for faster builds
- Enable hot reloading
- Use debug mode only when needed

### **2. Resource Management**
- Monitor memory usage
- Close unused servers
- Use appropriate development modes

## 🔧 **Advanced Configuration**

### **Custom Ports**
```bash
# Next.js on custom port
npm run dev -- -p 3001

# FastAPI on custom port
uvicorn api.index:app --port 8001
```

### **Environment Overrides**
```bash
# Override environment
VERCEL_ENV=development DEBUG=true npm run dev
```

### **Debugging Specific Components**
```bash
# Debug only API routes
DEBUG=true npm run dev

# Debug only Python functions
VERCEL_ENV=development vercel dev
```

This enhanced setup provides comprehensive debugging capabilities while maintaining the flexibility to work in different development modes based on your needs.
