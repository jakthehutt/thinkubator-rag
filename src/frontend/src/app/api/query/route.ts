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
  try {
    const response = await fetch(`${BACKEND_URL}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    })

    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Backend API call failed:', error)
    throw error
  }
}

async function callVercelPythonFunction(query: string, request: NextRequest): Promise<BackendResponse> {
  try {
    // Get the base URL from the request
    const baseUrl = new URL(request.url).origin
    const pythonUrl = `${baseUrl}/api/python/query`
    
    console.log(`Calling Python function at: ${pythonUrl}`)
    
    const response = await fetch(pythonUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    })

    if (!response.ok) {
      throw new Error(`Vercel Python function error: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Vercel Python function call failed:', error)
    throw error
  }
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

    console.log('=== Frontend API Route Debug Info ===')
    console.log(`Query: ${query}`)
    console.log(`Environment: ${process.env.NODE_ENV}`)
    console.log(`Is Development: ${isDevelopment}`)
    console.log(`Is Vercel: ${isVercel}`)
    console.log(`Is Local Development: ${isLocalDevelopment}`)
    console.log(`VERCEL_URL: ${process.env.VERCEL_URL}`)
    console.log(`Backend URL: ${BACKEND_URL}`)
    console.log('=====================================')

    try {
      let backendResponse: BackendResponse

      if (isLocalDevelopment) {
        // In local development with vercel dev, call the backend API
        console.log('📡 Calling backend API (local development)...')
        backendResponse = await callBackendAPI(query)
      } else {
        // In Vercel deployment, use the Python function directly
        console.log('📡 Calling Vercel Python function (production)...')
        backendResponse = await callVercelPythonFunction(query, request)
      }

      const processingTime = Date.now() - startTime
      console.log(`✅ API call completed in ${processingTime}ms`)

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

      return NextResponse.json(transformedResponse)

    } catch (backendError) {
      console.error('API Error:', backendError)

      // Fallback to mock response if backend is unavailable
      console.log('🔄 API unavailable, falling back to mock response...')

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
