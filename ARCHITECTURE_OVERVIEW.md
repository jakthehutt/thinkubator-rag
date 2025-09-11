# Thinkubator RAG - Architecture Overview

## Project Overview

**Thinkubator RAG** is a Retrieval-Augmented Generation (RAG) system for circular economy and sustainability research. The system combines a Next.js frontend with a Python backend, utilizing Supabase for vector storage and Google Gemini for AI capabilities. The architecture is designed for both current Vercel deployment and future VPS deployment with enhanced infrastructure.

## Current Architecture

### High-Level Architecture

The system follows a modern microservices architecture with the following main components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Supabase      │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (Vector DB)   │
│   Port: 3000    │    │   Port: 8000    │    │   (External)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                |
                                ▼
                       ┌─────────────────┐
                       │   Google Gemini │
                       │   (AI/Embeddings)│
                       └─────────────────┘
```

## Core Components

### 1. Frontend (`src/frontend/`)

**Technology Stack:**
- Next.js 15.5.2 with TypeScript
- Tailwind CSS for styling
- React components for UI

**Key Components:**
- `src/app/page.tsx` - Main application page
- `src/components/QueryInterface.tsx` - Query input component
- `src/components/ResultsDisplay.tsx` - Results display component
- `src/app/api/query/route.ts` - API route for frontend-backend communication

**Features:**
- Real-time query interface
- Results display with citations
- Responsive design
- Vercel-optimized deployment

### 2. Backend (`src/backend/`)

**Technology Stack:**
- Python with FastAPI
- LangChain for RAG pipeline
- Google Gemini for AI capabilities
- Supabase for vector storage

**Key Components:**

**RAG Pipeline (`chain/`)**
- `rag_pipeline.py` - Main RAG pipeline implementation
- `rag_pipeline_supabase.py` - Supabase-specific RAG pipeline
- `query_processor.py` - Query processing with multiple strategies
- `reranker.py` - Result reranking capabilities
- `config.py` - Configuration management

**Vector Store (`vector_store/`)**
- `supabase_vector_store.py` - Supabase vector database operations
- pgvector integration for similarity search

**Storage (`storage/`)**
- `query_storage.py` - Query session storage and management

**API Layer (`api/`)**
- `unified_handler.py` - Unified API handler for FastAPI and Vercel
- `main.py` - FastAPI application entry point

### 3. Data Processing

**Source Data:**
- PDF documents in `data/pdfs/`
- Processed JSON chunks in `data/processed/md/`
- Vector embeddings stored in Supabase

**Processing Pipeline:**
1. PDF ingestion and chunking
2. Text preprocessing and cleaning
3. Embedding generation using Google Gemini
4. Vector storage in Supabase with pgvector
5. Query processing and retrieval
6. Response generation with citations

## Future Architecture (VPS Deployment)

### Enhanced Infrastructure with Traefik

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Traefik       │    │   Frontend      │    │   Backend       │
│   (Reverse      │◄──►│   (Next.js)     │◄──►│   (FastAPI)     │
│   Proxy)        │    │   Port: 3000    │    │   Port: 8000    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       |                       |
         │                       |                       ▼
         │                       |              ┌─────────────────┐
         │                       |              │   Celery        │
         │                       |              │   (Task Queue)  │
         │                       |              │   Port: 5555    │
         │                       |              └─────────────────┘
         │                       |                       |
         │                       |                       ▼
         │                       |              ┌─────────────────┐
         │                       |              │   Redis         │
         │                       |              │   (Message      │
         │                       |              │   Broker)       │
         │                       |              │   Port: 6379    │
         │                       |              └─────────────────┘
         │                       |
         │                       ▼
         │              ┌─────────────────┐
         │              │   Supabase      │
         │              │   (Vector DB)   │
         │              │   (External)    │
         │              └─────────────────┘
         │
         ▼
┌─────────────────┐
│   Google Gemini │
│   (AI/Embeddings)│
└─────────────────┘
```

### Future Components

**1. Traefik Reverse Proxy**
- SSL termination and certificate management
- Load balancing and routing
- Rate limiting and security
- Automatic service discovery

**2. Celery Task Queue**
- Background document processing
- Scheduled data updates
- Async query processing
- Task monitoring and retry logic

**3. Redis Message Broker**
- Celery task queue backend
- Session storage
- Caching layer
- Real-time data synchronization

**4. Ionos VPS Infrastructure**
- Dedicated server resources
- Custom domain configuration
- Enhanced security and monitoring
- Scalable deployment options

## Data Flow Architecture

### Current Query Flow

1. **User Input**: Frontend receives query from user
2. **API Request**: Query sent to backend via Next.js API route
3. **Query Processing**: Backend processes query using RAG pipeline
4. **Vector Search**: Supabase performs similarity search
5. **Response Generation**: Google Gemini generates response with citations
6. **Result Display**: Frontend displays formatted results

### Future Enhanced Flow

1. **User Input**: Frontend receives query via Traefik
2. **Load Balancing**: Traefik routes request to available backend instance
3. **Query Processing**: Backend processes query (sync or async via Celery)
4. **Vector Search**: Supabase performs similarity search
5. **Response Generation**: Google Gemini generates response
6. **Caching**: Redis caches frequent queries
7. **Result Display**: Frontend displays results with enhanced performance

## Deployment Strategies

### Current: Vercel Deployment

**Advantages:**
- Serverless scaling
- Automatic deployments
- Built-in CDN
- Zero infrastructure management

**Configuration:**
- `src/frontend/api/python.py` - Ultra-minimal serverless function
- `src/frontend/vercel.json` - Vercel configuration
- `src/frontend/next.config.ts` - Next.js optimization

### Future: VPS Deployment

**Advantages:**
- Full control over infrastructure
- Custom domain and SSL
- Enhanced performance
- Scheduled tasks with Celery
- Cost-effective for high traffic

**Configuration:**
- Docker Compose for service orchestration
- Traefik for reverse proxy and SSL
- Celery for background tasks
- Redis for caching and message queuing

## Environment Management

### Environment Variables

**Required Variables:**
- `GEMINI_API_KEY` - Google AI API key
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anonymous key
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `POSTGRES_URL_NON_POOLING` - Direct PostgreSQL connection

**Future Variables:**
- `REDIS_URL` - Redis connection string
- `CELERY_BROKER_URL` - Celery message broker URL
- `TRAEFIK_DOMAIN` - Custom domain for Traefik
- `SSL_EMAIL` - Email for SSL certificate generation

## Development Workflow

### Local Development

```bash
# Quick start
make dev                    # Setup development environment
make dev-docker            # Start all services with Docker
make dev-docker-down       # Stop all services
```

### Service Ports

**Current:**
- Frontend: 3000 (3001 in Docker)
- Backend: 8000 (8001 in Docker)

**Future:**
- Frontend: 3000 (via Traefik)
- Backend: 8000 (via Traefik)
- Redis: 6379
- Celery: 5555 (monitoring)

### Docker Architecture

**Current Services:**
- `backend` - Python FastAPI service
- `frontend` - Next.js application
- `redis` - Message broker (production only)

**Future Services:**
- `traefik` - Reverse proxy and SSL
- `celery-worker` - Background task processor
- `celery-beat` - Scheduled task scheduler
- `celery-flower` - Task monitoring dashboard

## Testing & Quality Assurance

### Test Structure

**Current Tests:**
- Unit tests for individual components
- Integration tests for RAG pipeline
- End-to-end tests for complete workflow
- Performance tests for response times

**Test Commands:**
```bash
make test_all              # Run all tests
make test_rag_pipeline     # Test RAG pipeline
make test_frontend         # Test frontend components
make test_e2e_rag          # End-to-end RAG tests
```

### Future Testing

**Enhanced Test Coverage:**
- Celery task testing
- Traefik routing tests
- Redis integration tests
- Load balancing tests
- SSL certificate validation

## Monitoring & Observability

### Current Monitoring

**Logging:**
- Python logging throughout services
- Docker container logs
- Vercel function logs

**Health Checks:**
- Backend health endpoint
- Database connection monitoring
- Service availability checks

### Future Monitoring

**Enhanced Observability:**
- Celery task monitoring with Flower
- Traefik metrics and logs
- Redis performance monitoring
- Custom application metrics
- Uptime monitoring and alerting

## Security Considerations

### Current Security

**Measures:**
- Environment variable encryption
- CORS configuration
- API endpoint security
- Supabase row-level security

### Future Security

**Enhanced Security:**
- Traefik rate limiting
- SSL/TLS encryption
- VPS firewall configuration
- Regular security updates
- Backup and disaster recovery

## Scalability & Performance

### Current Optimizations

**Bundle Size:**
- Minimal Vercel function size (8 packages)
- Optimized Next.js configuration
- Efficient vector storage with Supabase

**Performance:**
- Cached embeddings
- Optimized queries
- Fast response times

### Future Optimizations

**Enhanced Performance:**
- Redis caching layer
- Celery async processing
- Traefik load balancing
- CDN integration
- Database query optimization

## Migration Strategy

### Phase 1: Current Vercel Deployment
- Maintain existing Vercel deployment
- Continue development and testing
- Optimize current architecture

### Phase 2: VPS Preparation
- Set up Ionos VPS server
- Configure Docker Compose with Traefik
- Implement Celery task queue
- Set up Redis infrastructure

### Phase 3: Migration
- Deploy to VPS with Traefik
- Migrate domain and SSL
- Implement scheduled tasks
- Monitor and optimize performance

### Phase 4: Enhancement
- Add advanced monitoring
- Implement additional Celery tasks
- Optimize for high traffic
- Add backup and recovery procedures

## Conclusion

The Thinkubator RAG system represents a modern, scalable architecture for AI-powered research assistance. The current Vercel deployment provides excellent development and deployment experience, while the future VPS architecture with Traefik, Celery, and Redis will offer enhanced performance, control, and scalability for production use.

The modular design allows for seamless migration between deployment strategies while maintaining the core RAG functionality and user experience. The addition of Celery for background tasks will enable advanced features like scheduled document updates, batch processing, and enhanced user analytics.

## Sources

- [src/frontend/src/app/page.tsx](src/frontend/src/app/page.tsx) - Main application page
- [src/frontend/src/components/QueryInterface.tsx](src/frontend/src/components/QueryInterface.tsx) - Query input component
- [src/frontend/src/components/ResultsDisplay.tsx](src/frontend/src/components/ResultsDisplay.tsx) - Results display component
- [src/backend/chain/rag_pipeline.py](src/backend/chain/rag_pipeline.py) - Main RAG pipeline
- [src/backend/chain/rag_pipeline_supabase.py](src/backend/chain/rag_pipeline_supabase.py) - Supabase-specific RAG pipeline
- [src/backend/vector_store/supabase_vector_store.py](src/backend/vector_store/supabase_vector_store.py) - Vector database operations
- [src/backend/storage/query_storage.py](src/backend/storage/query_storage.py) - Query session storage
- [docker-compose.yml](docker-compose.yml) - Development Docker configuration
- [docker-compose-prod.yml](docker-compose-prod.yml) - Production Docker configuration
