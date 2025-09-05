# Testing Guide - No Docker Required! 🚀

This project uses a **serverless, Docker-free architecture** optimized for Vercel deployment. All tests run natively without containers.

## 🧪 Available Test Commands

### Backend Tests
```bash
# Test individual components
make test-chunking          # Test text chunking functionality
make test-storing           # Test document storage in Supabase
make test-retrieving        # Test document retrieval
make test-generation        # Test answer generation

# Test RAG pipeline
make test-rag-pipeline      # Test complete RAG functionality

# Test end-to-end
make test-e2e              # End-to-end RAG tests with real data
```

### Supabase Integration Tests
```bash
make test-supabase         # Comprehensive Supabase setup tests
```

### API Tests (New!)
```bash
make test-api              # Test FastAPI backend with query storage
```

### Frontend Tests (New!)
```bash
make test-frontend         # Test Next.js build, TypeScript, and linting
```

### Run All Tests
```bash
make test-all              # Comprehensive test suite (Backend + Supabase + Frontend)
```

## 🔧 Test Infrastructure

### Backend (Python)
- **Framework**: pytest
- **Location**: `src/backend/tests/`
- **Dependencies**: All mocked for unit tests
- **Integration**: Real Supabase connections for integration tests

### Frontend (Next.js)
- **TypeScript**: Type checking with `tsc --noEmit`
- **Linting**: ESLint with Next.js configuration
- **Build**: Production build verification
- **Location**: `src/frontend/`

### API (FastAPI)
- **Import Tests**: Verify all modules load correctly
- **Integration Tests**: Check FastAPI + Supabase integration
- **Storage Tests**: Verify query storage functionality

## 🚀 Running Development Servers

### Frontend Development Server
```bash
make run-frontend          # Start Next.js dev server (http://localhost:3000)
```

### API Development (Local)
```bash
# If you want to test API locally
cd api
python index.py           # FastAPI with hot reload
```

## 📦 Prerequisites

### Python Dependencies
```bash
pip install -r requirements.txt
```

### Node.js Dependencies
```bash
cd src/frontend
npm install
```

### Environment Variables
Create `.env` file with:
```env
GEMINI_API_KEY=your_gemini_key
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_key
POSTGRES_URL_NON_POOLING=your_postgres_url
```

## 🎯 Test Strategy

### 1. **Unit Tests**
- Mock all external dependencies
- Fast execution
- Isolated component testing

### 2. **Integration Tests** 
- Real Supabase connections
- Test component interactions
- Verify data flow

### 3. **End-to-End Tests**
- Complete user workflows
- Real AI model calls
- Full system validation

### 4. **Build Tests**
- Frontend compilation
- Type checking
- Production readiness

## ❌ What We DON'T Use

### Docker - Not Needed!
- ❌ **Vercel doesn't support Docker**
- ❌ **Serverless functions don't need containers**
- ❌ **Native runtimes are faster and more efficient**
- ✅ **Direct Python + Node.js execution**

### Alternative Container Platforms
If you really need containers:
- **Railway.app** - Docker-friendly
- **Google Cloud Run** - Containerized serverless
- **AWS Fargate** - Container orchestration

But for this RAG application, **Vercel's serverless approach is optimal**.

## 🚨 Common Issues & Solutions

### Backend Tests Failing
```bash
# Check Python environment
python --version                # Should be 3.9+
pip list | grep -E "(supabase|fastapi|pytest)"

# Install missing dependencies
pip install -r requirements.txt
```

### Frontend Tests Failing  
```bash
# Check Node.js environment
node --version                  # Should be 18+
cd src/frontend && npm --version

# Install missing dependencies
cd src/frontend && npm install

# Clear cache
cd src/frontend && npm run build -- --clean
```

### Supabase Connection Issues
```bash
# Test connection
make test-supabase

# Check environment variables
cat .env | grep SUPABASE

# Verify credentials in Supabase dashboard
```

## 🎉 Success Indicators

When all tests pass, you should see:
```
🎉 ALL TESTS COMPLETED!
======================

✅ Backend tests: PASSED
✅ Supabase tests: PASSED  
✅ Frontend tests: PASSED

Your application is ready for deployment! 🚀
```

## 🔄 CI/CD Integration

For automated testing in CI/CD:

```yaml
# Example GitHub Actions
- name: Backend Tests
  run: make test-api && pytest src/backend/tests/

- name: Frontend Tests  
  run: make test-frontend

- name: Integration Tests
  run: make test-supabase
  env:
    SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
    # ... other secrets
```

This testing approach is **faster**, **more reliable**, and **perfectly suited** for the Vercel deployment model! 🚀
