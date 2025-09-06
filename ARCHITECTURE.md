# Thinkubator RAG Architecture

## Overview

The Thinkubator RAG system now uses a clean separation between frontend and backend, with full Vercel compatibility maintained.

## Architecture Components

### 1. Backend (`src/backend/`)
- **RAG Pipeline**: `src/backend/chain/rag_pipeline_supabase.py`
- **Vector Store**: `src/backend/vector_store/supabase_vector_store.py`
- **API Server**: `api/index.py` (FastAPI)
- **Unified Handler**: `src/backend/api/unified_handler.py`

### 2. Frontend (`src/frontend/`)
- **Next.js App**: `src/frontend/src/app/`
- **API Route**: `src/frontend/src/app/api/query/route.ts` (proxies to backend)
- **Vercel Function**: `src/frontend/api/python/index.py` (proxies to backend)

## How It Works

### Local Development
```
Frontend (localhost:3000) → Backend API (localhost:8000) → Supabase + Gemini
```

### Vercel Deployment
```
Frontend (Vercel) → Backend API (Vercel) → Supabase + Gemini
```

## Environment Configuration

### Local Development
- Frontend runs on `localhost:3000` (Vercel dev)
- Backend runs on `localhost:8000` (FastAPI)
- Frontend calls backend via `BACKEND_URL=http://localhost:8000`

### Vercel Deployment
- Frontend deploys to Vercel
- Backend deploys as Vercel serverless function
- Frontend calls backend via `BACKEND_URL=https://your-backend-api.vercel.app`

## Key Benefits

1. **Clean Separation**: Frontend focuses on UI, backend handles RAG logic
2. **Reusability**: Backend functions can be used by multiple frontends
3. **Vercel Compatibility**: Both frontend and backend work on Vercel
4. **Fallback Support**: Frontend gracefully handles backend unavailability
5. **Environment Flexibility**: Easy switching between local and production

## API Endpoints

### Backend API (`localhost:8000` or Vercel)
- `GET /` - Health check
- `GET /health` - Detailed health check
- `POST /query` - RAG query processing

### Frontend API (`localhost:3000` or Vercel)
- `GET /` - Frontend application
- `POST /api/query` - Proxies to backend API
- `POST /api/python/query` - Vercel Python function (also proxies to backend)

## Configuration

### Environment Variables
```bash
# Required for backend
GEMINI_API_KEY=your_gemini_key
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Optional for frontend
BACKEND_URL=http://localhost:8000  # or your production URL
```

## Development Workflow

### 1. Start Backend
```bash
python -m uvicorn api.index:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Start Frontend
```bash
cd src/frontend
npm run dev
```

### 3. Test
```bash
make test-frontend-coverage
```

## Deployment

### Vercel Deployment
1. Deploy backend as Vercel serverless function
2. Deploy frontend to Vercel
3. Set `BACKEND_URL` environment variable in Vercel dashboard
4. Both services will automatically use the backend RAG pipeline

## Fallback Behavior

If the backend is unavailable:
- Frontend shows graceful error message
- No crashes or broken functionality
- User can retry the query
- System remains responsive

## Testing

The system includes comprehensive tests:
- **Document Coverage**: Ensures diverse document retrieval
- **API Endpoints**: Tests all API routes
- **Frontend Components**: Tests UI components
- **End-to-End**: Tests complete user workflows

Run all tests:
```bash
make test-frontend-vercel
```
