import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // In production (Vercel), the Python API is deployed as a serverless function
    // In development, we need to call the local backend
    const isProduction = process.env.NODE_ENV === 'production'
    const apiUrl = isProduction 
      ? '/api/python/query' // Vercel will route this to the Python function
      : 'http://localhost:8000/query' // Local development
    
    console.log(`Calling API at: ${apiUrl}`)
    
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await response.text()
      console.error('Backend error:', errorData)
      return NextResponse.json(
        { detail: `Backend error: ${response.status} - ${errorData}` },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
    
  } catch (error) {
    console.error('API route error:', error)
    return NextResponse.json(
      { detail: `API route error: ${error instanceof Error ? error.message : 'Unknown error'}` },
      { status: 500 }
    )
  }
}
