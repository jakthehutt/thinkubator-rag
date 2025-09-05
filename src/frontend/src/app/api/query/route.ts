import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // Detect if we're running on Vercel by checking for VERCEL_URL
    const isVercel = process.env.VERCEL_URL || process.env.NODE_ENV === 'production'
    
    let apiUrl: string
    if (isVercel) {
      // On Vercel, use the absolute URL to the Python function
      const baseUrl = process.env.VERCEL_URL 
        ? `https://${process.env.VERCEL_URL}`
        : request.nextUrl.origin
      apiUrl = `${baseUrl}/api/python/query`
    } else {
      // Local development
      apiUrl = 'http://localhost:8000/query'
    }
    
    console.log(`Environment: ${isVercel ? 'Vercel' : 'Local'}`)
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
