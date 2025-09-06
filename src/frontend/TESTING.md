# Frontend Testing Guide

Comprehensive testing setup for the Thinkubator RAG frontend using **Vercel Dev** environment.

## Overview

This testing framework is designed exclusively for **Vercel Dev** local development environment. All tests run against `http://localhost:3000` when `vercel dev` is running.

## Quick Start

### Option 1: Using Make (Recommended)

From the **project root directory**:

```bash
# Start Vercel dev in one terminal
make run-frontend

# In another terminal, run tests
make test-frontend-vercel    # Complete test suite
make test-frontend-api       # API endpoint tests only
make test-frontend-e2e       # End-to-end workflow tests only  
make test-frontend-components # Frontend component tests only
```

### Option 2: Using npm (Direct)

From the **src/frontend** directory:

```bash
# 1. Start Vercel Dev
npm run dev  # This runs 'vercel dev'

# 2. In another terminal, run tests
npm test                 # Complete test suite
npm run test:api         # API endpoint tests
npm run test:frontend    # Frontend component tests  
npm run test:e2e         # End-to-end workflow tests
npm run test:all         # All tests in sequence

# 3. Debug issues
npm run test:debug       # Debug API endpoints
npm run test:setup       # Environment setup check
```

## Make Integration

The frontend tests are fully integrated with the project's make system:

```bash
# From project root - these all work:
make test-frontend-vercel     # Full Vercel dev test suite
make test-frontend-api        # Test API endpoints
make test-frontend-e2e        # Test complete user workflows
make test-frontend-components # Test UI components and pages
make run-frontend             # Start Vercel dev server
```

### Make vs npm Commands

| Make Command | npm Equivalent | Description |
|--------------|----------------|-------------|
| `make test-frontend-vercel` | `npm test` | Complete test suite |
| `make test-frontend-api` | `npm run test:api` | API endpoint tests |
| `make test-frontend-e2e` | `npm run test:e2e` | End-to-end workflows |
| `make test-frontend-components` | `npm run test:frontend` | UI component tests |
| `make run-frontend` | `npm run dev` | Start Vercel dev |

## Test Suites

### 1. Environment Setup Check (`test-local-setup.js`)
- ✅ Verifies Vercel dev is running
- ✅ Tests basic endpoint connectivity
- ✅ Checks environment variables
- ✅ Validates Vercel environment detection

**What it tests:**
- Frontend page loads (`http://localhost:3000`)
- Next.js API route works (`/api/query`)
- Python serverless function works (`/api/python/query`)

### 2. API Endpoints Testing (`test-vercel-api.js`)
- ✅ Tests all API endpoints comprehensively
- ✅ Validates response structure and content
- ✅ Tests different query types and complexities
- ✅ Tests error handling and edge cases
- ✅ Measures response times and performance

**Test scenarios:**
- Basic queries ("What is circular economy?")
- Specific terms ("What is the circularity gap?")
- Business models ("How do circular business models work?")
- Environmental topics ("What are environmental benefits?")
- Complex multi-topic queries
- Error cases (empty queries, invalid JSON, wrong methods)

### 3. Frontend Component Testing (`test-vercel-frontend.js`)
- ✅ Tests page loading and HTML structure
- ✅ Validates component presence and functionality
- ✅ Tests responsive design elements
- ✅ Basic accessibility checks
- ✅ Static asset availability

**Component checks:**
- Query Interface component
- Results Display component
- Header and footer elements
- Tailwind CSS styling
- React hydration

### 4. End-to-End Workflow Testing (`test-vercel-e2e.js`)
- ✅ Simulates complete user workflows
- ✅ Tests query submission and response handling
- ✅ Validates response quality and relevance
- ✅ Tests error handling in real scenarios
- ✅ Measures end-to-end performance

**E2E scenarios:**
1. User loads page → submits query → receives answer
2. Different query types with relevance scoring
3. Error handling for edge cases
4. Response validation and quality checks

## Test Results

### Success Metrics
- **API Tests**: Response times, status codes, content validation
- **Frontend Tests**: Page load times, component presence, accessibility
- **E2E Tests**: Complete workflow success, relevance scores, error handling

### Example Output
```
🚀 Testing Vercel Dev API Endpoints...

🧪 Testing Basic Query...
   ✅ Status: 200 (1,234ms)
   📄 Content-Type: application/json
   💬 Answer: The circular economy is a systemic approach to economic...
   
📊 TEST SUMMARY
✅ Successful: 12
❌ Failed: 1
📊 Total: 13
⚡ Average Response Time: 1,456ms
🎯 Success Rate: 92.3%
```

## Environment Requirements

### Required Environment Variables
Create `.env.local` in `src/frontend/`:
```bash
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
```

### Optional Debug Variables
```bash
DEBUG=true          # Enable detailed logging
NODE_ENV=development # Ensure development mode
```

## Troubleshooting

### Common Issues

#### 1. "Connection failed" errors
```
❌ Connection failed: ECONNREFUSED
```
**Solution**: Ensure `vercel dev` is running on port 3000

#### 2. "API route error" messages
```
❌ API route error: Backend error: 500
```
**Solutions**:
- Check environment variables in `.env.local`
- Verify API keys are valid
- Check Vercel dev logs for detailed errors

#### 3. Python function timeouts
```
❌ Python Function: TIMEOUT
```
**Solutions**:
- Check internet connectivity
- Verify Supabase credentials
- Check Google AI API quotas

#### 4. Environment detection issues
```
❌ Environment detection failed
```
**Solutions**:
- Ensure running `vercel dev` (not `next dev`)
- Check VERCEL environment variables are set
- Verify vercel.json configuration

### Debug Steps

1. **Check Vercel Dev Status**
   ```bash
   # Should show "Ready" and port 3000
   npm run dev
   ```

2. **Test Individual Endpoints**
   ```bash
   curl http://localhost:3000
   curl http://localhost:3000/api/query
   curl http://localhost:3000/api/python/query
   ```

3. **Check Environment Variables**
   ```bash
   npm run debug:api  # Shows environment debug info
   ```

4. **Review Vercel Dev Logs**
   - Check the terminal running `npm run dev`
   - Look for Python function errors
   - Check API route execution logs

## Test Architecture

### File Structure
```
src/frontend/tests/
├── test-vercel.js           # Main test runner
├── test-local-setup.js      # Environment checks
├── test-vercel-api.js       # API endpoint tests
├── test-vercel-frontend.js  # Frontend component tests
├── test-vercel-e2e.js       # End-to-end workflow tests
└── debug-api.js             # API debugging utility
```

### Test Flow
1. **Environment Check** → Verify Vercel dev is running
2. **API Tests** → Test all endpoints with various queries
3. **Frontend Tests** → Validate page structure and components
4. **E2E Tests** → Simulate complete user workflows
5. **Summary** → Aggregate results and provide insights

## Advanced Usage

### Custom Test Scenarios
Modify test scripts to add custom scenarios:

```javascript
// In test-vercel-e2e.js
const customScenarios = [
  {
    query: "Your custom query here",
    keywords: ['expected', 'keywords'],
    name: "Custom Test Scenario"
  }
]
```

### Performance Monitoring
Tests automatically measure:
- Response times for each endpoint
- Answer quality and relevance scores
- Error rates and types
- Success rates across different scenarios

### Continuous Testing
Set up automated testing:
```bash
# Run tests every 5 minutes
watch -n 300 'npm test'

# Or integrate with CI/CD
npm run test:all && echo "Tests passed" || echo "Tests failed"
```

## Integration with Development

### Pre-deployment Checklist
```bash
# 1. Start Vercel dev
npm run dev

# 2. Run full test suite
npm run test:all

# 3. Fix any issues
npm run debug:api  # For API issues

# 4. Deploy when tests pass
vercel --prod
```

### Test-Driven Development
1. Write tests for new features first
2. Run tests to see them fail
3. Implement features
4. Run tests to see them pass
5. Refactor and repeat

## Next Steps

### Production Testing
After local testing passes:
```bash
# Deploy to Vercel
vercel --prod

# Test production deployment
# (Update test scripts to use production URL)
```

### Monitoring
- Set up Vercel Analytics
- Monitor error rates in production
- Track performance metrics
- Set up alerts for failures

---

🎉 **Happy Testing!** This comprehensive test suite ensures your Vercel dev environment works perfectly before deployment.
