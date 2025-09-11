# 🐛 Debug Guide - Docker Container Debugging for RAG System

This guide shows you how to set breakpoints and debug your code while running the Thinkubator RAG application in Docker containers.

## 🚀 Quick Start

1. **Start debug environment:**
   ```bash
   make debug
   ```

2. **Open VS Code and set breakpoints** in your Python or TypeScript files

3. **Start debugging:**
   - Press `Ctrl+Shift+D` (Run and Debug)
   - Select "🐍 Debug RAG Backend" or "🔗 Debug Full Stack"
   - Press `F5` to start debugging

4. **Trigger your code** by making API requests or using the frontend

## 🔧 Available Debug Configurations

### Debug Environments

| Environment | Command | Purpose |
|------------|---------|---------|
| **Development** | `make dev` | Standard development with hot reload |
| **Debug** | `make debug` | Development + debugging capabilities |
| **Production** | `make prod` | Production optimization |

### Debug Services

| Service | Port | Debug Port | Purpose |
|---------|------|------------|---------|
| **Backend (FastAPI)** | 8001 | 5679 | Python debugging with debugpy |
| **Frontend (Next.js)** | 3001 | - | Hot reload (debugging via browser) |
| **Redis** | 6380 | - | Optional future Celery integration |

## 🐍 Backend Python Debugging

### Setting Up Breakpoints

1. **Open Python files** in `src/backend/` (e.g., `main.py`, `chain/rag_pipeline.py`)
2. **Click in the left margin** next to line numbers to set breakpoints (red dots)
3. **Start debugging** with VS Code configuration "🐍 Debug RAG Backend"

### Common Debug Scenarios

#### Debugging RAG Pipeline
```python
# Set breakpoint in src/backend/chain/rag_pipeline_supabase.py
def process_query(self, query: str) -> dict:
    # Breakpoint here ← Click to set
    query_embedding = self.embedder.embed(query)
    # Your debugger will pause here when a query is made
    return results
```

#### Debugging API Endpoints  
```python
# Set breakpoint in src/backend/main.py
@app.post("/query")
async def query_rag_pipeline(request: Request, query_data: Dict[str, str]):
    # Breakpoint here ← Click to set
    query = query_data.get("query")
    # Debugger pauses when API is called
    return response
```

#### Debugging Vector Store Operations
```python
# Set breakpoint in src/backend/vector_store/supabase_vector_store.py  
def similarity_search(self, query_embedding: List[float]) -> List[Document]:
    # Breakpoint here ← Click to set
    results = self.client.table("document_embeddings").select("*")
    # Debug vector search operations
    return documents
```

## 🌐 Frontend Debugging

### Browser DevTools (Recommended)
1. **Open http://localhost:3001** in Chrome/Firefox
2. **Press F12** to open DevTools
3. **Go to Sources tab** and set breakpoints in TypeScript files
4. **Interact with the UI** to trigger breakpoints

### VS Code Frontend Debugging
1. **Set breakpoints** in `src/frontend/src/` files
2. **Use "🌐 Debug Frontend (Next.js)"** configuration
3. **Requires browser extension** for advanced debugging

## 🔍 Advanced Debugging Techniques

### Conditional Breakpoints
1. **Right-click on a breakpoint** in VS Code
2. **Select "Edit Breakpoint"**
3. **Add conditions** like:
   - `query == "test"`
   - `len(results) > 0`
   - `user_id == "debug"`

### Watch Variables
1. **In the Debug panel**, click "Watch"
2. **Add variables** to monitor:
   - `query`
   - `embedding_results`
   - `api_response`

### Debug Console
- **Evaluate expressions** during breakpoints:
  ```python
  # Type in Debug Console:
  query_embedding[:5]  # First 5 values
  len(search_results)  # Number of results
  type(response_data)  # Data type
  ```

### Call Stack Navigation
- **Use Call Stack panel** to navigate through function calls
- **Click on stack frames** to see variable values at different levels

## 🎯 Debug Commands Reference

### Environment Management
```bash
# Start debug environment
make debug

# Stop debug environment  
make debug-stop

# View debug logs
make debug-logs

# Check container status
docker compose -f docker-compose-debug.yml ps
```

### Manual Docker Commands
```bash
# Start debug containers
docker compose -f docker-compose-debug.yml up -d

# View specific service logs
docker compose -f docker-compose-debug.yml logs backend -f
docker compose -f docker-compose-debug.yml logs frontend -f

# Execute commands in debug containers
docker compose -f docker-compose-debug.yml exec backend bash
docker compose -f docker-compose-debug.yml exec frontend sh
```

## 🧪 Testing Debug Setup

### Backend API Testing
```bash
# Test health endpoint
curl http://localhost:8001/health

# Test RAG query (will hit your breakpoints)
curl -X POST "http://localhost:8001/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is circular economy?"}'
```

### Frontend Testing
```bash
# Test frontend accessibility
curl http://localhost:3001

# Open in browser for interactive debugging
open http://localhost:3001
```

## 🔧 Configuration Files

### VS Code Launch Configuration
**Location:** `.vscode/launch.json`
```json
{
    "name": "🐍 Debug RAG Backend (FastAPI)",
    "type": "python",
    "request": "attach",
    "connect": {
        "host": "localhost",
        "port": 5679
    },
    "pathMappings": [
        {
            "localRoot": "${workspaceFolder}/src/backend",
            "remoteRoot": "/app/src/backend"
        }
    ]
}
```

### Docker Debug Configuration  
**Location:** `docker-compose-debug.yml`
- **Debug ports exposed:** 5679 (Python), 9229 (Node.js)
- **Volume mounting:** Live code changes
- **Environment variables:** Debug flags enabled

## ⚠️ Troubleshooting

### Common Issues

#### 1. "Breakpoint not hit"
**Solutions:**
- Ensure debugger is attached (green play button in VS Code)
- Trigger the code path (make API request, click frontend button)
- Check that breakpoint is in executed code, not dead code

#### 2. "Cannot connect to debugger"
**Solutions:**
```bash
# Check if debug port is available
lsof -i :5679

# Restart debug environment
make debug-stop && make debug
```

#### 3. "Source maps not working"
**Solutions:**
- Verify path mappings in `.vscode/launch.json`
- Ensure volumes are mounted correctly in `docker-compose-debug.yml`

#### 4. "Frontend debugging not working"
**Solutions:**
- Use browser DevTools instead of VS Code for React debugging
- Check browser console for errors
- Verify frontend is accessible at http://localhost:3001

### Debug Environment Variables
The debug environment sets these variables automatically:
```bash
DEBUG=True
LOG_LEVEL=DEBUG
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
```

### Port Conflicts
If you encounter port conflicts:
```bash
# Check what's using the ports
lsof -i :5679  # Python debug
lsof -i :9229  # Node.js debug  
lsof -i :6380  # Redis debug

# Kill conflicting processes
kill -9 <PID>
```

## 🎓 Debug Workflow Best Practices

### 1. Start with Simple Breakpoints
- Set breakpoint at function entry points
- Verify the code path is being executed
- Add more specific breakpoints as needed

### 2. Use Logging Combined with Debugging
```python
import logging
logger = logging.getLogger(__name__)

def process_query(query: str):
    logger.debug(f"Processing query: {query}")  # Will show in logs
    # Breakpoint here for detailed inspection
    results = search_function(query)
    return results
```

### 3. Debug in Layers
- **API Layer:** Debug endpoint handlers
- **Business Logic:** Debug RAG pipeline processing
- **Data Layer:** Debug vector store operations
- **Integration:** Debug frontend-backend communication

### 4. Test Debug Scenarios
Create specific test queries to trigger different code paths:
```bash
# Test different query types
curl -X POST "http://localhost:8001/query" -d '{"query": "sustainability"}'
curl -X POST "http://localhost:8001/query" -d '{"query": "circular business models"}'
curl -X POST "http://localhost:8001/query" -d '{"query": ""}'  # Empty query test
```

## 🚀 Next Steps

Once you're comfortable with basic debugging:

1. **Explore Advanced Features:**
   - Multi-threaded debugging
   - Remote debugging across containers
   - Performance profiling

2. **Integration Testing:**
   - Debug full request/response cycles
   - Test error handling paths
   - Validate data transformations

3. **Production Debugging:**
   - Log analysis techniques
   - Performance monitoring
   - Error tracking integration

---

**🎉 Happy Debugging!** Your RAG system is now fully debuggable with professional-grade development tools.

For questions or issues, refer to:
- **VS Code Python Debugging:** https://code.visualstudio.com/docs/python/debugging
- **Docker Debugging:** https://code.visualstudio.com/docs/containers/debug-common
- **Next.js Debugging:** https://nextjs.org/docs/pages/building-your-application/configuring/debugging
