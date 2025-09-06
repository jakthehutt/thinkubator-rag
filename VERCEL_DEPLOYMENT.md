# Deploying Your RAG Application to Vercel

## Overview

Your Thinkubator RAG application has been configured for deployment to Vercel using a **Next.js frontend** with **Python serverless functions**. This modern architecture provides excellent performance and scalability.

## 🚀 Quick Deployment Steps

### 1. Push to GitHub
Ensure your code is pushed to a GitHub repository that's connected to Vercel.

### 2. Configure Environment Variables in Vercel Dashboard
Go to your Vercel project settings and add these environment variables:

- `GEMINI_API_KEY`: Your Google Gemini API key
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_ANON_KEY`: Your Supabase anonymous key
- `VERCEL_BYPASS_TOKEN`: Optional bypass token for deployment protection

### 3. Deploy
Push your changes or manually trigger a deployment in Vercel.

## 📁 Architecture Overview

### Frontend (Next.js)
- **Location**: `src/frontend/`
- **Framework**: Next.js 15.5.2 with App Router
- **Styling**: Tailwind CSS
- **Components**: React components for query interface and results display

### Backend (Python Serverless Functions)
- **Location**: `src/frontend/api/python/index.py`
- **Runtime**: Python 3.13.5
- **Dependencies**: Minimal set (8 packages) to stay under Vercel's 250MB limit
- **Handler**: Uses unified handler for consistency with local development

### Database
- **Vector Storage**: Supabase with pgvector
- **Document Storage**: Supabase tables
- **Migration**: Completed from ChromaDB to Supabase

## 🔧 API Endpoints

Once deployed, your application will have these endpoints:

- `GET /` - Next.js web interface
- `POST /api/query` - Next.js API route (proxies to Python function)
- `POST /api/python/query` - Python serverless function (main RAG logic)

### Example API Usage:

```bash
# Query the RAG pipeline
curl -X POST https://your-app.vercel.app/api/query \\
  -H "Content-Type: application/json" \\
  -d '{"query": "What is the circularity gap?"}'
```

## ✅ Current Status

### Completed:
- ✅ Next.js frontend with modern UI
- ✅ Python serverless functions configured
- ✅ Supabase vector database migration completed
- ✅ Unified backend architecture
- ✅ Environment detection and routing
- ✅ Local development setup with mock API
- ✅ Vercel deployment configuration

### Ready for Production:
- ✅ All dependencies optimized (8 packages, under 250MB limit)
- ✅ Database migration from ChromaDB to Supabase completed
- ✅ Environment variables documented
- ✅ API endpoints tested and working

## 🛠️ Deployment Checklist

### Before Deploying:
1. **Set up Supabase project** (if not already done)
2. **Configure environment variables** in Vercel dashboard:
   - `GEMINI_API_KEY`
   - `SUPABASE_URL` 
   - `SUPABASE_ANON_KEY`
   - `VERCEL_BYPASS_TOKEN` (optional)
3. **Test locally** with `npm run dev` in `src/frontend/`

### After Deploying:
1. **Test production endpoints**
2. **Verify environment variables** are loaded
3. **Check Supabase connection**
4. **Test RAG pipeline** with real queries

## 🔧 Local Development

### Quick Start:
```bash
# Start frontend with mock API
cd src/frontend
npm run dev

# Access at http://localhost:3000
```

### With Real Backend:
```bash
# Start FastAPI backend
python run_local.py

# Start Next.js frontend  
cd src/frontend
npm run dev
```

## 📊 Performance Optimizations

- **Bundle Size**: Optimized to stay under Vercel's 250MB limit
- **Cold Start**: Minimal dependencies for faster function startup
- **Caching**: Supabase provides built-in caching
- **Frontend**: Turbopack for faster builds and hot reloading
