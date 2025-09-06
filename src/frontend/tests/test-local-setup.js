#!/usr/bin/env node

const http = require('http')
const https = require('https')

function testEndpoint(url, name, method = 'GET') {
  return new Promise((resolve) => {
    const client = url.startsWith('https') ? https : http
    const options = {
      method: method,
      headers: method === 'POST' ? { 'Content-Type': 'application/json' } : {}
    }
    
    const req = client.request(url, options, (res) => {
      // For API routes, 405 (Method Not Allowed) is expected for GET requests
      // For Python functions, 404 is expected in vercel dev
      const isExpectedError = (
        (name.includes('API Route') && res.statusCode === 405) ||
        (name.includes('Python') && res.statusCode === 404)
      )
      
      resolve({
        name,
        url,
        status: res.statusCode,
        success: res.statusCode >= 200 && res.statusCode < 300 || isExpectedError
      })
    })
    
    if (method === 'POST') {
      req.write(JSON.stringify({ query: 'test' }))
    }
    
    req.end()
    
    req.on('error', (err) => {
      resolve({
        name,
        url,
        status: 'ERROR',
        success: false,
        error: err.message
      })
    })
    
    req.setTimeout(5000, () => {
      req.destroy()
      resolve({
        name,
        url,
        status: 'TIMEOUT',
        success: false,
        error: 'Connection timeout'
      })
    })
  })
}

async function testVercelDev() {
  console.log('🚀 Testing Vercel Dev Environment...\n')
  
  const endpoints = [
    { url: 'http://localhost:3000', name: 'Vercel Dev Frontend', method: 'GET' },
    { url: 'http://localhost:3000/api/query', name: 'Next.js API Route', method: 'POST' },
    { url: 'http://localhost:3000/api/python/query', name: 'Python Serverless Function', method: 'POST' }
  ]
  
  console.log('Testing Vercel dev endpoints...\n')
  
  let allPassed = true
  for (const endpoint of endpoints) {
    const result = await testEndpoint(endpoint.url, endpoint.name, endpoint.method)
    
    if (result.success) {
      console.log(`✅ ${result.name}: ${result.status}`)
    } else {
      console.log(`❌ ${result.name}: ${result.status} ${result.error ? `(${result.error})` : ''}`)
      allPassed = false
    }
  }
  
  console.log('\n📋 Vercel Environment Check:')
  console.log(`VERCEL: ${process.env.VERCEL || 'undefined'}`)
  console.log(`VERCEL_ENV: ${process.env.VERCEL_ENV || 'undefined'}`)
  console.log(`VERCEL_URL: ${process.env.VERCEL_URL || 'undefined'}`)
  console.log(`NODE_ENV: ${process.env.NODE_ENV || 'undefined'}`)
  console.log(`DEBUG: ${process.env.DEBUG || 'undefined'}`)
  
  console.log('\n💡 Setup Instructions:')
  console.log('1. Run "npm run dev" (which runs vercel dev)')
  console.log('2. Ensure .env.local has required environment variables:')
  console.log('   - GEMINI_API_KEY')
  console.log('   - SUPABASE_URL')
  console.log('   - SUPABASE_ANON_KEY')
  console.log('3. Set DEBUG=true for detailed logging')
  
  if (allPassed) {
    console.log('\n🎉 All Vercel dev endpoints are working!')
    process.exit(0)
  } else {
    console.log('\n⚠️  Some endpoints failed. Check the setup instructions above.')
    process.exit(1)
  }
}

testVercelDev().catch(console.error)

