import { NextRequest, NextResponse } from 'next/server'

// Direct Supabase connection functions (same logic as Python function)
async function generateEmbedding(text: string): Promise<number[]> {
  const apiKey = process.env.GEMINI_API_KEY
  if (!apiKey) {
    throw new Error("GEMINI_API_KEY not configured")
  }
  
  const url = `https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent?key=${apiKey}`
  
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      content: {
        parts: [{ text }]
      }
    })
  })
  
  if (!response.ok) {
    throw new Error(`Embedding API error: ${response.status}`)
  }
  
  const result = await response.json()
  return result.embedding.values
}

async function searchSupabase(queryEmbedding: number[], k: number = 5) {
  const supabaseUrl = process.env.SUPABASE_URL
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_ANON_KEY
  
  if (!supabaseUrl || !supabaseKey) {
    throw new Error("Supabase credentials not configured")
  }
  
  // Use vector similarity search with RPC function
  const response = await fetch(`${supabaseUrl}/rest/v1/rpc/match_documents`, {
    method: 'POST',
    headers: {
      'apikey': supabaseKey,
      'Authorization': `Bearer ${supabaseKey}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      query_embedding: queryEmbedding,
      match_threshold: 0.5,
      match_count: k
    })
  })
  
  if (!response.ok) {
    const errorText = await response.text()
    console.log('RPC search failed, trying direct query...')
    
    // Fallback to direct query if RPC fails
    const fallbackResponse = await fetch(`${supabaseUrl}/rest/v1/document_embeddings?select=id,content,metadata&limit=${k}`, {
      method: 'GET',
      headers: {
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
        'Content-Type': 'application/json'
      }
    })
    
    if (!fallbackResponse.ok) {
      throw new Error(`Supabase search error: ${fallbackResponse.status} - ${await fallbackResponse.text()}`)
    }
    
    const results = await fallbackResponse.json()
    return results.map((result: any) => ({
      document: result.content || "",
      metadata: result.metadata || {}
    }))
  }
  
  const results = await response.json()
  
  return results.map((result: any) => ({
    document: result.content || "",
    metadata: result.metadata || {}
  }))
}

async function generateAnswer(query: string, retrievedChunks: any[]): Promise<string> {
  const apiKey = process.env.GEMINI_API_KEY
  if (!apiKey) {
    throw new Error("GEMINI_API_KEY not configured")
  }
  
  const context = retrievedChunks.map(chunk => chunk.document).join("\n\n")
  
  const prompt = `Based on the following context about circular economy and sustainability, please answer the question: ${query}

Context:
${context}

Please provide a comprehensive answer based on the context provided. If the context doesn't contain enough information to answer the question, please say so.`
  
  const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      contents: [{
        parts: [{ text: prompt }]
      }]
    })
  })
  
  if (!response.ok) {
    throw new Error(`Generation API error: ${response.status}`)
  }
  
  const result = await response.json()
  return result.candidates[0].content.parts[0].text
}

export async function POST(request: NextRequest) {
  const startTime = Date.now()
  
  try {
    const body = await request.json()
    const query = body.query
    
    if (!query) {
      return NextResponse.json(
        { detail: "Query is required" },
        { status: 400 }
      )
    }
    
    console.log('=== RAG Pipeline Debug Info ===')
    console.log(`Query: ${query}`)
    console.log(`Environment: ${process.env.NODE_ENV}`)
    console.log(`Has GEMINI_API_KEY: ${!!process.env.GEMINI_API_KEY}`)
    console.log(`Has SUPABASE_URL: ${!!process.env.SUPABASE_URL}`)
    console.log(`Has SUPABASE_ANON_KEY: ${!!process.env.SUPABASE_ANON_KEY}`)
    console.log(`Has SUPABASE_SERVICE_ROLE_KEY: ${!!process.env.SUPABASE_SERVICE_ROLE_KEY}`)
    console.log(`Using Supabase Key: ${process.env.SUPABASE_SERVICE_ROLE_KEY ? 'SERVICE_ROLE' : 'ANON'}`)
    console.log('===============================')
    
    try {
      // Step 1: Generate query embedding
      console.log('🔍 Generating query embedding...')
      const queryEmbedding = await generateEmbedding(query)
      
      // Step 2: Search Supabase for similar documents
      console.log('📚 Searching Supabase database...')
      const similarDocs = await searchSupabase(queryEmbedding, 5)
      
      console.log(`📊 Found ${similarDocs.length} similar documents`)
      
      if (similarDocs.length === 0) {
        return NextResponse.json({
          answer: "I do not have enough information to answer your question. No relevant documents were found.",
          chunks: [],
          session_id: null,
          processing_time_ms: Date.now() - startTime
        })
      }
      
      // Step 3: Generate answer
      console.log('🤖 Generating answer...')
      const answer = await generateAnswer(query, similarDocs)
      
      const processingTime = Date.now() - startTime
      console.log(`✅ RAG pipeline completed in ${processingTime}ms`)
      
      return NextResponse.json({
        answer,
        chunks: similarDocs,
        session_id: null, // Could implement session storage later
        processing_time_ms: processingTime
      })
      
    } catch (ragError) {
      console.error('RAG Pipeline Error:', ragError)
      
      // Fallback to mock response only if RAG completely fails
      console.log('🔄 Falling back to mock response...')
      
      const mockResponse = {
        answer: `I encountered an issue accessing the document database for your query "${query}". This appears to be a temporary technical issue. Please try again later or contact support if the problem persists.`,
        chunks: [],
        session_id: null,
        processing_time_ms: Date.now() - startTime,
        error_fallback: true
      }
      
      return NextResponse.json(mockResponse)
    }
    
  } catch (error) {
    console.error('API route error:', error)
    return NextResponse.json(
      { detail: `API route error: ${error instanceof Error ? error.message : 'Unknown error'}` },
      { status: 500 }
    )
  }
}
