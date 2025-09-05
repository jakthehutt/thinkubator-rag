# Deploying Your RAG Application to Vercel

## Overview

Your Thinkubator RAG application has been configured for deployment to Vercel using a **FastAPI backend** with a **modern HTML frontend**. This approach works better than deploying Streamlit directly to Vercel due to serverless constraints.

## 🚀 Quick Deployment Steps

### 1. Push to GitHub
Ensure your code is pushed to a GitHub repository that's connected to Vercel.

### 2. Configure Environment Variables in Vercel Dashboard
Go to your Vercel project settings and add these environment variables:

- `GEMINI_API_KEY`: Your Google Gemini API key
- `PYTHONPATH`: Set to `.` (this is already configured in vercel.json)

### 3. Deploy
Push your changes or manually trigger a deployment in Vercel.

## 📁 What We Created

### Files Added/Modified:
- `api/index.py` - FastAPI application with RAG endpoints
- `public/index.html` - Modern web interface 
- `vercel.json` - Vercel deployment configuration
- `requirements.txt` - Updated with `mangum` for ASGI compatibility

## 🔧 API Endpoints

Once deployed, your application will have these endpoints:

- `GET /` - Web interface
- `GET /api/health` - Health check
- `POST /api/query` - Main RAG query endpoint
- `GET /api/chunks/{query}` - Retrieve chunks without generating answer

### Example API Usage:

```bash
# Health check
curl https://your-app.vercel.app/api/health

# Query the RAG pipeline
curl -X POST https://your-app.vercel.app/api/query \\
  -H "Content-Type: application/json" \\
  -d '{"query": "What is the circularity gap?"}'
```

## ⚠️ Important Considerations

### ChromaDB Storage Issue
**CRITICAL**: Your current setup uses a local ChromaDB database stored in `data/processed/chroma_db/`. This **will not work** on Vercel because:

1. Vercel serverless functions are stateless
2. File system is read-only except for `/tmp`
3. Data doesn't persist between function invocations

### Solutions for Database Storage:

#### Option 1: Pinecone (Recommended)
```python
# Switch to Pinecone vector database
pip install pinecone-client
```
Update your RAG pipeline to use Pinecone instead of ChromaDB.

#### Option 2: Supabase Vector
```python
# Use Supabase's pgvector
pip install supabase vecs
```

#### Option 3: Weaviate Cloud
```python
# Use Weaviate cloud service
pip install weaviate-client
```

#### Option 4: Deploy ChromaDB Separately
Deploy ChromaDB as a separate service (e.g., Railway, Render) and connect via HTTP.

### Environment Variables Needed:
- `GEMINI_API_KEY` - Your Google Gemini API key
- Vector DB credentials (depending on chosen solution)

## 🔄 Migration Steps for Database

1. **Choose a cloud vector database** (Pinecone recommended)
2. **Update your `RAGPipeline` class** to use the new database
3. **Migrate your existing embeddings** from ChromaDB to the new service
4. **Update environment variables** in Vercel

## 🎯 Alternative: Keep Streamlit + Use Different Platform

If you prefer to keep your Streamlit interface, consider these platforms:

- **Streamlit Community Cloud** (Free, purpose-built for Streamlit)
- **Railway** (Supports persistent storage)
- **Render** (Good for Python applications)
- **Heroku** (Classic choice)

## 📝 Current Status

✅ FastAPI wrapper created
✅ Modern web interface ready  
✅ Vercel configuration complete
❌ Database storage needs migration
❌ Environment variables need setup in Vercel

## 🛠️ Next Steps

1. **Set up environment variables** in Vercel dashboard
2. **Choose and implement vector database solution**
3. **Migrate your existing data**
4. **Test deployment**

Would you like help with any of these steps?
