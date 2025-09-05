# Thinkubator RAG Explorer 🚀

A modern, serverless RAG (Retrieval-Augmented Generation) application for exploring circular economy knowledge. Built with Next.js 14, FastAPI, and Supabase - optimized for Vercel deployment.

## ✨ Features

- **🔍 Intelligent Query Interface**: Modern search with sample questions
- **🤖 AI-Powered Answers**: RAG pipeline with source attribution
- **📚 Source Exploration**: Expandable document chunks with metadata
- **💾 Session Storage**: All queries and answers stored in Supabase
- **📊 Analytics Ready**: Query history and performance tracking
- **🎨 Modern Design**: Responsive UI inspired by thinkubator.earth

## 🏗️ Architecture

### Frontend - Next.js 14
- **Location**: `src/frontend/`
- **Tech**: TypeScript, Tailwind CSS, App Router
- **Deployment**: Vercel static hosting

### Backend - FastAPI Serverless
- **Location**: `api/index.py`
- **Tech**: Python, FastAPI, Supabase integration
- **Deployment**: Vercel serverless functions

### Database - Supabase
- **Vector Storage**: pgvector for document embeddings
- **Query Storage**: Session tracking and analytics
- **Full-text Search**: PostgreSQL capabilities

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Python backend
pip install -r requirements.txt

# Node.js frontend
cd src/frontend && npm install
```

### 2. Environment Setup
Create `.env` file:
```env
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
POSTGRES_URL_NON_POOLING=your_postgres_direct_url
```

### 3. Development
```bash
# Start frontend dev server
make run-frontend              # http://localhost:3000

# Test everything works
make test-all                  # Comprehensive test suite
```

### 4. Deploy to Vercel
```bash
vercel --prod                  # One-command deployment
```

## 🧪 Testing (No Docker Required!)

Our testing infrastructure runs natively - no containers needed:

```bash
# Quick Tests
make test-api              # FastAPI backend + query storage
make test-frontend         # Next.js build + TypeScript
make test-supabase         # Database connectivity

# Comprehensive Testing  
make test-all              # Everything together (~2-3 minutes)

# Individual Components
make test-chunking         # Text processing
make test-storing          # Document storage
make test-retrieving       # Document retrieval
make test-generation       # AI answer generation
make test-e2e             # End-to-end workflows
```

## 📁 Project Structure

```
thinkubator-rag/
├── src/
│   ├── frontend/              # Next.js 14 application
│   │   ├── src/app/           # App Router pages
│   │   └── src/components/    # React components
│   └── backend/               # Python RAG pipeline
│       ├── chain/             # RAG implementation
│       ├── storage/           # Query storage service
│       └── tests/             # Test suites
├── api/
│   └── index.py              # FastAPI serverless function
├── make/                     # Test scripts
├── vercel.json               # Vercel configuration
└── requirements.txt          # Python dependencies
```

## 🎯 API Endpoints

### Core RAG
- `POST /api/query` - Process query and return answer with sources
- `GET /api/health` - System health check

### Session Management  
- `GET /api/sessions/recent` - Recent query sessions
- `GET /api/sessions/{id}` - Specific session details
- `GET /api/sessions/search/{query}` - Search past sessions
- `GET /api/stats` - System performance metrics

## 🔧 Development Workflow

### Frontend Development
```bash
cd src/frontend
npm run dev                # Hot reload development
npm run build              # Production build
npm run lint               # Code quality checks
```

### Backend Development
```bash
# Test individual components
pytest src/backend/tests/chain/test_storing.py -v

# Run with real Supabase (needs .env)
python scripts/test_supabase_setup.py
```

## 🚀 Why No Docker?

This application uses a **serverless-first architecture**:

### ✅ Benefits
- **Faster deployments**: No container building
- **Better performance**: Native runtimes, no container overhead  
- **Cost efficiency**: Pay-per-request vs always-on containers
- **Vercel optimized**: Native Next.js + Python support
- **Zero configuration**: Push to deploy

### 🐳 Alternative Container Options
If you need containers:
- **Railway.app**: Docker-friendly hosting
- **Google Cloud Run**: Serverless containers
- **AWS Fargate**: Container orchestration

## 📚 Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)**: Complete deployment instructions
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)**: Comprehensive testing documentation
- **[MIGRATION_SUMMARY.md](MIGRATION_SUMMARY.md)**: Docker → Serverless migration details
- **[SUPABASE_MIGRATION_GUIDE.md](SUPABASE_MIGRATION_GUIDE.md)**: Database migration guide

## 🌍 About Thinkubator

This RAG explorer supports [Thinkubator's](https://www.thinkubator.earth/) mission to advance circular economy knowledge through:

- **📚 Education**: Interactive learning experiences
- **🔬 Research**: Knowledge discovery and synthesis  
- **💼 Advisory**: Evidence-based insights for organizations

## 🛠️ Built With

- **[Next.js 14](https://nextjs.org/)**: React framework with App Router
- **[FastAPI](https://fastapi.tiangolo.com/)**: Python web framework
- **[Supabase](https://supabase.com/)**: Database and backend services
- **[Vercel](https://vercel.com/)**: Deployment and hosting
- **[Tailwind CSS](https://tailwindcss.com/)**: Utility-first styling
- **[TypeScript](https://www.typescriptlang.org/)**: Type-safe development

## 📈 Performance

- **Frontend**: < 2s initial load, instant interactions
- **Backend**: < 1s cold start, sub-second API responses  
- **Database**: Millisecond vector similarity searches
- **Deployment**: Zero-downtime, automatic scaling

---

**Ready to explore circular economy insights?** Deploy to Vercel and start asking questions! 🌱