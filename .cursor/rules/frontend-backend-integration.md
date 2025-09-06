# Frontend-Backend Integration Rules

## ⚠️ CRITICAL: Frontend Must Use Backend Functions for RAG Operations

### Architecture Enforcement

The frontend **MUST ALWAYS** use the backend functions for all RAG pipeline operations. Direct AI API calls from the frontend are **STRICTLY PROHIBITED**.

## Required Backend Integration Pattern

### ✅ Correct Architecture Flow

```
Frontend → Frontend API Route → Backend Functions → AI Services
```

**Components that MUST be used:**

1. **Frontend API Route**: [src/frontend/src/app/api/query/route.ts](mdc:src/frontend/src/app/api/query/route.ts)
   - Environment detection (local vs Vercel)
   - Automatic backend routing
   - Response transformation

2. **Local Backend** (Development): [src/backend/chain/rag_pipeline_supabase.py](mdc:src/backend/chain/rag_pipeline_supabase.py)
   - Full RAG pipeline with Supabase
   - Configurable processors and rerankers
   - Accessed via `http://localhost:8000/query`

3. **Vercel Backend** (Production): [src/frontend/api/python/index.py](mdc:src/frontend/api/python/index.py)
   - Minimal RAG pipeline implementation
   - Direct HTTP calls to AI services
   - Accessed via `/api/python/query`

### ❌ FORBIDDEN: Direct AI API Calls from Frontend

**NEVER** implement these patterns in frontend components:

```typescript
// ❌ PROHIBITED - Direct Gemini API calls
const response = await fetch('https://generativelanguage.googleapis.com/v1beta/models/...', {
  headers: { 'Authorization': `Bearer ${apiKey}` }
})

// ❌ PROHIBITED - Direct Supabase vector operations
const { data } = await supabase.rpc('match_documents', { query_embedding })

// ❌ PROHIBITED - Client-side RAG logic
const embedding = await generateEmbedding(query)
const chunks = await searchVectorDatabase(embedding)
const answer = await generateAnswer(query, chunks)
```

## Mandatory Frontend Integration Points

### 1. Query Interface Component

**Location**: [src/frontend/src/components/QueryInterface.tsx](mdc:src/frontend/src/components/QueryInterface.tsx)

**Requirements**:
- MUST call `/api/query` endpoint only
- MUST handle loading states
- MUST handle error responses gracefully
- MUST NOT contain any AI API keys or direct API calls

```typescript
// ✅ CORRECT - Use frontend API route
const response = await fetch('/api/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: userQuery })
})
```

### 2. Results Display Component

**Location**: [src/frontend/src/components/ResultsDisplay.tsx](mdc:src/frontend/src/components/ResultsDisplay.tsx)

**Requirements**:
- MUST only receive and display backend responses
- MUST NOT process or transform RAG results
- MUST handle citation formatting from backend
- MUST display source metadata from backend

### 3. Frontend API Route

**Location**: [src/frontend/src/app/api/query/route.ts](mdc:src/frontend/src/app/api/query/route.ts)

**Requirements**:
- MUST detect environment automatically
- MUST route to appropriate backend (local vs Vercel)
- MUST transform backend responses for frontend compatibility
- MUST provide fallback responses on backend failure
- MUST NOT contain AI processing logic

```typescript
// ✅ REQUIRED - Environment-based routing
if (isVercel) {
  backendResponse = await callVercelPythonFunction(query, request)
} else {
  backendResponse = await callBackendAPI(query)
}
```

## Backend Function Requirements

### Local Development Backend

**File**: [src/backend/chain/rag_pipeline_supabase.py](mdc:src/backend/chain/rag_pipeline_supabase.py)

**Required Functions**:
- `retrieve(query, n_results)` - Vector search with reranking
- `generate_answer(user_query, top_k_chunks)` - Full RAG generation
- `ingest_pdf(pdf_path, document_name)` - Document ingestion
- `get_pipeline_info()` - Pipeline configuration details

**Required Features**:
- Configurable query processors (basic, enhanced, advanced)
- Configurable rerankers (none, hybrid)
- Supabase vector store integration
- Comprehensive error handling and logging

### Vercel Production Backend

**File**: [src/frontend/api/python/index.py](mdc:src/frontend/api/python/index.py)

**Required Functions**:
- `generate_embedding(text)` - Direct Gemini embedding
- `search_supabase(query_embedding, k)` - Direct Supabase search  
- `generate_answer(query, retrieved_chunks)` - Direct Gemini generation
- `handler(request)` - Vercel serverless function handler

**Required Features**:
- Minimal dependencies (8 packages maximum)
- Direct HTTP API calls (no heavy SDKs)
- Error handling with graceful fallbacks
- Environment variable validation

## Environment Configuration

### Development Environment Detection

```typescript
// ✅ REQUIRED - Environment detection logic
const isDevelopment = process.env.NODE_ENV === 'development'
const isVercel = process.env.VERCEL === '1'
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'
```

### Required Environment Variables

**Local Development** (`.env.local`):
```
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=your_supabase_url  
SUPABASE_ANON_KEY=your_supabase_anon_key
BACKEND_URL=http://localhost:8000
```

**Vercel Production**:
```
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
VERCEL_URL=(automatically set)
```

## Response Format Standards

### Backend Response Format

All backend functions MUST return this exact structure:

```typescript
interface BackendResponse {
  answer: string                    // Generated answer text
  chunks: Array<{                  // Retrieved document chunks
    content?: string               // Chunk text content
    document?: string              // Alternative chunk content field
    metadata?: Record<string, unknown>  // Document metadata
  }>
  session_id: string | null        // Session tracking (optional)
  processing_time_ms: number       // Processing duration
  error_fallback?: boolean         // Indicates fallback response
}
```

### Frontend Transformation

The frontend API route MUST transform backend responses:

```typescript
// ✅ REQUIRED - Response transformation
const transformedResponse = {
  answer: backendResponse.answer,
  chunks: backendResponse.chunks.map((chunk: BackendChunk) => ({
    document: chunk.content || chunk.document || "",
    metadata: chunk.metadata || {}
  })),
  session_id: backendResponse.session_id,
  processing_time_ms: processingTime
}
```

## Error Handling Requirements

### Backend Function Errors

- Backend functions MUST provide detailed error logging
- Backend functions MUST raise exceptions with descriptive messages
- Backend errors MUST be caught and handled by the frontend API route

### Frontend Error Handling

```typescript
// ✅ REQUIRED - Graceful fallback handling
catch (backendError) {
  console.error('Backend API call failed:', backendError)
  
  // Provide user-friendly fallback response
  const mockResponse = {
    answer: `I encountered an issue accessing the document database for your query "${query}". This appears to be a temporary technical issue. Please try again later or contact support if the problem persists.`,
    chunks: [],
    session_id: null,
    processing_time_ms: Date.now() - startTime,
    error_fallback: true
  }
  
  return NextResponse.json(mockResponse)
}
```

## Testing Requirements

### Integration Tests

**MUST test all integration points**:

1. **Frontend → API Route**: Component interaction with `/api/query`
2. **API Route → Local Backend**: Development environment routing
3. **API Route → Vercel Backend**: Production environment routing  
4. **Backend Error Handling**: Graceful degradation scenarios

### Required Test Files

- [src/frontend/tests/test-vercel-e2e.js](mdc:src/frontend/tests/test-vercel-e2e.js)
- [make/test_frontend_e2e.sh](mdc:make/test_frontend_e2e.sh)
- [make/test_e2e_rag.sh](mdc:make/test_e2e_rag.sh)

## Deployment Compatibility

### Vercel Constraints

The frontend MUST remain compatible with Vercel deployment:

- **Bundle Size**: Under 250MB function limit
- **Dependencies**: Minimal Python requirements (8 packages max)
- **Cold Start**: Optimized initialization time
- **Memory Usage**: Efficient resource utilization

### Next.js Configuration

Required optimizations in [src/frontend/next.config.ts](mdc:src/frontend/next.config.ts):

```typescript
// ✅ REQUIRED - Vercel optimization settings
const nextConfig = {
  experimental: {
    turbo: { /* Turbopack config */ }
  },
  outputFileTracingExcludes: {
    '*': ['**/.git/**', '**/node_modules/@swc/**']
  }
}
```

## Security Requirements

### API Key Management

- Frontend components MUST NOT contain hardcoded API keys
- Environment variables MUST be properly scoped (VERCEL_* for client, others for server)
- Sensitive operations MUST occur in backend functions only

### Request Validation  

```typescript
// ✅ REQUIRED - Input validation in API routes
if (!query || typeof query !== 'string') {
  return NextResponse.json(
    { detail: "Valid query string is required" },
    { status: 400 }
  )
}
```

## Monitoring and Logging

### Required Logging Points

```typescript
// ✅ REQUIRED - Comprehensive logging
console.log('=== Frontend API Route Debug Info ===')
console.log(`Query: ${query}`)
console.log(`Environment: ${process.env.NODE_ENV}`)
console.log(`Is Vercel: ${isVercel}`)
console.log(`Backend URL: ${BACKEND_URL}`)
console.log('=====================================')
```

### Performance Tracking

- MUST track `processing_time_ms` for all requests
- MUST log successful completions and failures
- MUST provide user feedback during processing

## Enforcement Guidelines

### Code Review Checklist

Before implementing or modifying frontend code, verify:

- [ ] No direct AI API calls in frontend components
- [ ] All RAG operations go through backend functions
- [ ] Environment detection and routing implemented correctly
- [ ] Error handling provides graceful fallbacks
- [ ] Response formats match backend interface
- [ ] Testing covers all integration points
- [ ] Vercel deployment compatibility maintained

### Violation Prevention

**Automated checks should catch**:
- Direct imports of AI libraries in frontend code
- Hardcoded AI API endpoints in frontend
- Missing backend function calls
- Incorrect response format handling
- Environment detection bypassing

### Migration Support

When migrating existing code:

1. **Identify Direct AI Calls**: Search for `fetch()` calls to AI APIs
2. **Extract to Backend**: Move AI logic to appropriate backend function
3. **Update Frontend**: Replace with backend function calls
4. **Test Integration**: Verify end-to-end functionality
5. **Update Documentation**: Reflect architecture changes

## Summary

The frontend **MUST ALWAYS** use backend functions for RAG operations. This architecture ensures:

- **Separation of Concerns**: Frontend handles UI, backend handles AI
- **Security**: API keys and sensitive operations stay in backend
- **Scalability**: Backend can be optimized independently
- **Maintainability**: Clear interface boundaries
- **Deployment Flexibility**: Environment-specific implementations
- **Error Resilience**: Centralized error handling and fallbacks

**Remember**: Direct AI API calls from the frontend are **STRICTLY PROHIBITED**. All RAG functionality must flow through the established backend functions.
