# Vercel Deployment Troubleshooting Guide

## Current Issue: Fallback Response in Production

### Problem
The Vercel deployment shows: *"I encountered an issue accessing the document database for your query. This appears to be a temporary technical issue."*

### Root Cause Analysis
The fallback response indicates the Vercel Python function is failing to access either:
1. **Gemini API** (for embeddings/generation)
2. **Supabase database** (for vector search)
3. **match_documents RPC function** (database function)

## Required Environment Variables

### Critical Variables (Must be set in Vercel Dashboard)
```bash
GEMINI_API_KEY=your_gemini_api_key_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
# OR
SUPABASE_ANON_KEY=your_anon_key_here
```

### How to Set Environment Variables in Vercel
1. Go to your Vercel dashboard
2. Select your project
3. Go to **Settings** → **Environment Variables**
4. Add each variable with the exact names above
5. Set them for **Production**, **Preview**, and **Development** environments
6. **Redeploy** after adding variables

## Diagnostic Steps

### Step 1: Check Vercel Function Logs
1. Go to Vercel Dashboard → Your Project → Functions
2. Click on the failing deployment
3. Look for Python function logs
4. Check for specific error messages

### Step 2: Test Environment Variables
Create a simple test endpoint to verify environment variables:
```python
def handler(request):
    return {
        'statusCode': 200,
        'body': json.dumps({
            'has_gemini_key': bool(os.environ.get("GEMINI_API_KEY")),
            'has_supabase_url': bool(os.environ.get("SUPABASE_URL")),
            'has_supabase_key': bool(os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")),
            'environment_vars': list(os.environ.keys())
        })
    }
```

### Step 3: Test Supabase Connection
The `match_documents` RPC function must exist in your Supabase database.

**Check if RPC function exists:**
1. Go to Supabase Dashboard → SQL Editor
2. Run: `SELECT * FROM pg_proc WHERE proname = 'match_documents';`
3. Should return one row if function exists

**If function doesn't exist, run:**
```sql
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding vector(768),
  match_threshold float DEFAULT 0.5,
  match_count int DEFAULT 5
)
RETURNS TABLE (
  id text,
  content text,
  metadata jsonb,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    document_embeddings.id,
    document_embeddings.content,
    document_embeddings.metadata,
    1 - (document_embeddings.embedding <=> query_embedding) AS similarity
  FROM document_embeddings
  WHERE 1 - (document_embeddings.embedding <=> query_embedding) > match_threshold
  ORDER BY document_embeddings.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

GRANT EXECUTE ON FUNCTION match_documents(vector(768), float, int) TO authenticated;
GRANT EXECUTE ON FUNCTION match_documents(vector(768), float, int) TO anon;
```

### Step 4: Test Gemini API Access
Verify the Gemini API key works:
```bash
curl -H "Content-Type: application/json" \
     -d '{"content":{"parts":[{"text":"test"}]}}' \
     "https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent?key=YOUR_API_KEY"
```

## Common Issues & Solutions

### Issue 1: Missing Environment Variables
**Symptoms**: Function fails immediately with configuration errors
**Solution**: Add all required environment variables in Vercel Dashboard

### Issue 2: Incorrect Supabase Keys
**Symptoms**: "Supabase credentials not configured" or 401/403 errors
**Solution**: 
- Use `SUPABASE_SERVICE_ROLE_KEY` for full database access
- Ensure keys are copied correctly (no extra spaces/characters)

### Issue 3: Missing RPC Function
**Symptoms**: "match_documents not found" or 404 errors from Supabase
**Solution**: Create the `match_documents` function in Supabase SQL Editor

### Issue 4: Network/Timeout Issues
**Symptoms**: Intermittent failures or timeout errors
**Solution**: 
- Increase timeout in function (currently 30s)
- Check Supabase region vs Vercel region proximity

### Issue 5: Bundle Size Issues
**Symptoms**: Function fails to deploy or cold start timeouts
**Solution**: Current setup should be under 250MB limit with minimal dependencies

## Verification Commands

### Test Vercel Deployment
```bash
# Test the deployed function
curl -X POST https://your-app.vercel.app/api/query \
     -H "Content-Type: application/json" \
     -d '{"query": "test"}'
```

### Test Local Development
```bash
# Test local development
curl -X POST http://localhost:3000/api/query \
     -H "Content-Type: application/json" \
     -d '{"query": "test"}'
```

## Next Steps

1. **Check Environment Variables**: Verify all required variables are set in Vercel Dashboard
2. **Check Vercel Logs**: Look for specific error messages in function logs
3. **Verify Supabase RPC**: Ensure `match_documents` function exists and works
4. **Test API Keys**: Verify Gemini and Supabase keys are valid and have proper permissions

The most likely issue is missing environment variables in the Vercel deployment. Once these are set correctly, the deployment should work exactly like local development.
