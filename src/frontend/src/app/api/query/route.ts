import { NextRequest, NextResponse } from 'next/server'

// Backend API configuration
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

// Environment detection - prioritize local development
const isDevelopment = process.env.NODE_ENV === 'development'
const isVercel = process.env.VERCEL === '1'
const isLocalDevelopment = isDevelopment && !process.env.VERCEL_URL

// Type definitions
interface BackendChunk {
  content?: string
  document?: string
  metadata?: Record<string, unknown>
}

interface BackendResponse {
  answer: string
  chunks: BackendChunk[]
  session_id: string | null
  processing_time_ms: number
}

async function callBackendAPI(query: string): Promise<BackendResponse> {
  console.log('🔍 [BACKEND API] Starting call to backend...')
  console.log(`🔍 [BACKEND API] URL: ${BACKEND_URL}/query`)
  
  try {
    const response = await fetch(`${BACKEND_URL}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    })

    console.log(`🔍 [BACKEND API] Response status: ${response.status}`)
    console.log(`🔍 [BACKEND API] Response headers:`, Object.fromEntries(response.headers))

    if (!response.ok) {
      const errorText = await response.text()
      console.log(`❌ [BACKEND API] Error response: ${errorText}`)
      throw new Error(`Backend API error: ${response.status} - ${errorText}`)
    }

    const data = await response.json()
    console.log(`✅ [BACKEND API] Success! Chunks: ${data.chunks?.length || 0}`)
    return data
  } catch (error) {
    console.error('❌ [BACKEND API] Call failed:', error)
    throw error
  }
}

async function callVercelPythonFunction(query: string, request: NextRequest): Promise<BackendResponse> {
  console.log('🔍 [PYTHON FUNC] Starting call to Vercel Python function...')
  
  try {
    // Get the base URL from the request
    const baseUrl = new URL(request.url).origin
    const pythonUrl = `${baseUrl}/api/python/query`
    
    console.log(`🔍 [PYTHON FUNC] Base URL: ${baseUrl}`)
    console.log(`🔍 [PYTHON FUNC] Python URL: ${pythonUrl}`)
    console.log(`🔍 [PYTHON FUNC] Query: ${query}`)
    
    const response = await fetch(pythonUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    })

    console.log(`🔍 [PYTHON FUNC] Response status: ${response.status}`)
    console.log(`🔍 [PYTHON FUNC] Response headers:`, Object.fromEntries(response.headers))

    if (!response.ok) {
      const errorText = await response.text()
      console.log(`❌ [PYTHON FUNC] Error response: ${errorText}`)
      throw new Error(`Vercel Python function error: ${response.status} - ${errorText}`)
    }

    const data = await response.json()
    console.log(`✅ [PYTHON FUNC] Success! Chunks: ${data.chunks?.length || 0}`)
    return data
  } catch (error) {
    console.error('❌ [PYTHON FUNC] Call failed:', error)
    throw error
  }
}

export async function POST(request: NextRequest) {
  const startTime = Date.now()

  try {
    const body = await request.json()
    const query = body.query

    if (!query) {
      console.log('❌ [API ROUTE] Empty query received')
      return NextResponse.json(
        { detail: "Query is required" },
        { status: 400 }
      )
    }

    console.log('=== Frontend API Route Debug Info ===')
    console.log(`🔍 [API ROUTE] Query: "${query}"`)
    console.log(`🔍 [API ROUTE] Environment: ${process.env.NODE_ENV}`)
    console.log(`🔍 [API ROUTE] Is Development: ${isDevelopment}`)
    console.log(`🔍 [API ROUTE] Is Vercel: ${isVercel}`)
    console.log(`🔍 [API ROUTE] Is Local Development: ${isLocalDevelopment}`)
    console.log(`🔍 [API ROUTE] VERCEL_URL: ${process.env.VERCEL_URL || 'undefined'}`)
    console.log(`🔍 [API ROUTE] Backend URL: ${BACKEND_URL}`)
    console.log(`🔍 [API ROUTE] Request URL: ${request.url}`)
    console.log(`🔍 [API ROUTE] Request Origin: ${new URL(request.url).origin}`)
    console.log('=====================================')

    try {
      let backendResponse: BackendResponse

      if (isLocalDevelopment) {
        // In local development with vercel dev, call the backend API
        console.log('📡 [API ROUTE] Using backend API (local development)...')
        backendResponse = await callBackendAPI(query)
      } else {
        // In Vercel deployment, use the Python function directly
        console.log('📡 [API ROUTE] Using Vercel Python function (production)...')
        backendResponse = await callVercelPythonFunction(query, request)
      }

      const processingTime = Date.now() - startTime
      console.log(`✅ [API ROUTE] Total processing time: ${processingTime}ms`)

      // Transform backend response to match frontend expectations
      const transformedResponse = {
        answer: backendResponse.answer,
        chunks: backendResponse.chunks.map((chunk: BackendChunk) => ({
          document: chunk.content || chunk.document || "",
          metadata: chunk.metadata || {}
        })),
        session_id: backendResponse.session_id,
        processing_time_ms: processingTime
      }

      console.log(`✅ [API ROUTE] Returning ${transformedResponse.chunks.length} chunks`)
      return NextResponse.json(transformedResponse)

    } catch (backendError) {
      console.error('❌ [API ROUTE] Backend/Python function error:', backendError)
      console.log('🔄 [API ROUTE] Falling back to mock response...')

      const mockResponse = {
        answer: `I encountered an issue accessing the document database for your query "${query}". This appears to be a temporary technical issue. Please try again later or contact support if the problem persists.`,
        chunks: [],
        session_id: null,
        processing_time_ms: Date.now() - startTime,
        error_fallback: true
      }

      console.log(`🔄 [API ROUTE] Fallback response created for query: "${query}"`)
      return NextResponse.json(mockResponse)
    }

  } catch (error) {
    console.error('❌ [API ROUTE] General error:', error)
    return NextResponse.json(
      { detail: `API route error: ${error instanceof Error ? error.message : 'Unknown error'}` },
      { status: 500 }
    )
  }
}
