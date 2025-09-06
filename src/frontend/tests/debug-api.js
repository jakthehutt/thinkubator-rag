#!/usr/bin/env node

const fetch = require('node-fetch')

async function debugVercelAPI() {
  console.log('🐛 Debug Vercel Dev API endpoints...\n')
  
  const testQuery = { query: "What is circular economy?" }
  const baseUrl = 'http://localhost:3000'
  
  console.log(`Base URL: ${baseUrl}`)
  console.log(`Test Query: ${JSON.stringify(testQuery)}\n`)
  
  // Test Next.js API route
  console.log('1. Testing Next.js API route (/api/query)...')
  try {
    const startTime = Date.now()
    const response = await fetch(`${baseUrl}/api/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(testQuery),
      timeout: 30000
    })
    const responseTime = Date.now() - startTime
    
    console.log(`   Status: ${response.status} (${responseTime}ms)`)
    console.log(`   Headers: ${JSON.stringify(Object.fromEntries(response.headers))}`)
    
    if (response.ok) {
      const data = await response.json()
      console.log(`   ✅ Success: ${data.answer?.substring(0, 100)}...`)
      console.log(`   📊 Chunks: ${data.chunks?.length || 0}`)
      if (data.session_id) console.log(`   🆔 Session: ${data.session_id}`)
    } else {
      const errorText = await response.text()
      console.log(`   ❌ Error: ${errorText}`)
    }
  } catch (error) {
    console.log(`   ❌ Connection failed: ${error.message}`)
  }
  
  // Test Vercel Python function directly
  console.log('\n2. Testing Python serverless function (/api/python/query)...')
  try {
    const startTime = Date.now()
    const response = await fetch(`${baseUrl}/api/python/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(testQuery),
      timeout: 30000
    })
    const responseTime = Date.now() - startTime
    
    console.log(`   Status: ${response.status} (${responseTime}ms)`)
    console.log(`   Headers: ${JSON.stringify(Object.fromEntries(response.headers))}`)
    
    if (response.ok) {
      const data = await response.json()
      console.log(`   ✅ Success: ${data.answer?.substring(0, 100)}...`)
      console.log(`   📊 Chunks: ${data.chunks?.length || 0}`)
      if (data.session_id) console.log(`   🆔 Session: ${data.session_id}`)
      if (data.processing_time_ms) console.log(`   ⚡ Processing: ${data.processing_time_ms}ms`)
    } else {
      const errorText = await response.text()
      console.log(`   ❌ Error: ${errorText}`)
    }
  } catch (error) {
    console.log(`   ❌ Connection failed: ${error.message}`)
  }
  
  // Test Python function with GET (health check)
  console.log('\n3. Testing Python function health check (GET)...')
  try {
    const response = await fetch(`${baseUrl}/api/python/query`, {
      method: 'GET',
      timeout: 5000
    })
    
    console.log(`   Status: ${response.status}`)
    
    if (response.ok) {
      const data = await response.json()
      console.log(`   ✅ Health check: ${JSON.stringify(data)}`)
    } else {
      const errorText = await response.text()
      console.log(`   ❌ Health check failed: ${errorText}`)
    }
  } catch (error) {
    console.log(`   ❌ Health check connection failed: ${error.message}`)
  }
  
  // Environment debug info
  console.log('\n📋 Environment Debug:')
  console.log(`   NODE_ENV: ${process.env.NODE_ENV || 'undefined'}`)
  console.log(`   VERCEL: ${process.env.VERCEL || 'undefined'}`)
  console.log(`   VERCEL_ENV: ${process.env.VERCEL_ENV || 'undefined'}`)
  console.log(`   VERCEL_URL: ${process.env.VERCEL_URL || 'undefined'}`)
  console.log(`   DEBUG: ${process.env.DEBUG || 'undefined'}`)
  
  console.log('\n💡 Debug Tips:')
  console.log('   - Check Vercel dev logs in the terminal running "npm run dev"')
  console.log('   - Verify .env.local has GEMINI_API_KEY, SUPABASE_URL, SUPABASE_ANON_KEY')
  console.log('   - Set DEBUG=true for detailed API logging')
  console.log('   - Check network connectivity and API quotas')
}

debugVercelAPI().catch(console.error)

