import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // More robust Vercel detection
    const isVercel = !!(
      process.env.VERCEL || 
      process.env.VERCEL_URL || 
      process.env.NODE_ENV === 'production' ||
      request.nextUrl.hostname !== 'localhost'
    )
    
    let apiUrl: string
    if (isVercel) {
      // On Vercel, construct absolute URL from the incoming request
      apiUrl = new URL('/api/python/query', request.url).toString()
    } else {
      // Local development
      apiUrl = 'http://localhost:8000/query'
    }
    
    // Enhanced logging for debugging
    console.log('=== Environment Debug Info ===')
    console.log(`VERCEL: ${process.env.VERCEL}`)
    console.log(`VERCEL_URL: ${process.env.VERCEL_URL}`)
    console.log(`NODE_ENV: ${process.env.NODE_ENV}`)
    console.log(`Hostname: ${request.nextUrl.hostname}`)
    console.log(`Origin: ${request.nextUrl.origin}`)
    console.log(`Is Vercel: ${isVercel}`)
    console.log(`API URL: ${apiUrl}`)
    console.log('==============================')
    
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
