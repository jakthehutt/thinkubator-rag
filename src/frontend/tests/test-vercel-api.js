#!/usr/bin/env node

const fetch = require('node-fetch')

class VercelAPITester {
  constructor(baseUrl = null) {
    this.baseUrl = baseUrl
    this.testResults = []
  }

  async detectVercelPort() {
    const ports = [3000, 3001, 3002]
    for (const port of ports) {
      try {
        const fetch = require('node-fetch')
        const response = await fetch(`http://localhost:${port}`, { timeout: 2000 })
        if (response.ok) {
          this.baseUrl = `http://localhost:${port}`
          console.log(`🔍 Detected Vercel dev on port ${port}`)
          return port
        }
      } catch (error) {
        // Continue to next port
      }
    }
    throw new Error('Vercel dev not found on ports 3000, 3001, or 3002')
  }

  async testEndpoint(name, url, options = {}) {
    console.log(`\n🧪 Testing ${name}...`)
    const startTime = Date.now()
    
    try {
      const response = await fetch(url, {
        timeout: 10000,
        ...options
      })
      
      const responseTime = Date.now() - startTime
      const contentType = response.headers.get('content-type')
      
      let responseData
      try {
        const responseText = await response.text()
        try {
          responseData = JSON.parse(responseText)
        } catch {
          responseData = responseText
        }
      } catch {
        responseData = 'Unable to read response'
      }
      
      // Some responses are expected to fail (400, 500 for error handling tests)
      const isExpectedFailure = (
        (name.includes('Empty Query') && response.status === 400) ||
        (name.includes('Invalid JSON') && response.status === 500) ||
        (name.includes('Method Not Allowed') && response.status === 405)
      )
      
      const result = {
        name,
        success: response.ok || isExpectedFailure,
        status: response.status,
        responseTime,
        contentType,
        data: responseData,
        isExpectedFailure
      }
      
      this.testResults.push(result)
      
      if (response.ok || isExpectedFailure) {
        const statusIcon = isExpectedFailure ? '✅' : '✅'
        console.log(`   ${statusIcon} Status: ${response.status} (${responseTime}ms)`)
        console.log(`   📄 Content-Type: ${contentType}`)
        if (typeof responseData === 'object' && responseData.answer) {
          console.log(`   💬 Answer: ${responseData.answer.substring(0, 100)}...`)
        } else if (isExpectedFailure) {
          console.log(`   🎯 Expected behavior: ${typeof responseData === 'string' ? responseData : JSON.stringify(responseData)}`)
        }
      } else {
        console.log(`   ❌ Status: ${response.status} (${responseTime}ms)`)
        console.log(`   💥 Error: ${typeof responseData === 'string' ? responseData : JSON.stringify(responseData)}`)
      }
      
      return result
    } catch (error) {
      const responseTime = Date.now() - startTime
      const result = {
        name,
        success: false,
        status: 'ERROR',
        responseTime,
        error: error.message
      }
      
      this.testResults.push(result)
      console.log(`   ❌ Connection failed (${responseTime}ms): ${error.message}`)
      return result
    }
  }

  async runAPITests() {
    console.log('🚀 Testing Vercel Dev API Endpoints...\n')
    
    // Detect Vercel port if not set
    if (!this.baseUrl) {
      await this.detectVercelPort()
    }
    
    console.log(`Base URL: ${this.baseUrl}`)
    
    // Test queries with different complexities
    const testQueries = [
      { query: "What is circular economy?", name: "Basic Query" },
      { query: "What is the circularity gap?", name: "Specific Term Query" },
      { query: "How do circular business models work?", name: "Business Model Query" },
      { query: "What are the environmental benefits of sustainability?", name: "Environmental Query" },
      { query: "Tell me about recycling and waste management", name: "Complex Query" }
    ]

    // Test 1: Frontend page
    await this.testEndpoint(
      'Frontend Page',
      `${this.baseUrl}/`,
      { method: 'GET' }
    )

    // Test 2: Next.js API Route (GET)
    await this.testEndpoint(
      'Next.js API Route (GET)',
      `${this.baseUrl}/api/query`,
      { method: 'GET' }
    )

    // Test 3: Python Function (GET)
    await this.testEndpoint(
      'Python Function (GET)',
      `${this.baseUrl}/api/python/query`,
      { method: 'GET' }
    )

    // Test 4: Next.js API Route with different queries
    for (const testQuery of testQueries) {
      await this.testEndpoint(
        `Next.js API - ${testQuery.name}`,
        `${this.baseUrl}/api/query`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: testQuery.query })
        }
      )
    }

    // Test 5: Python Function with different queries
    for (const testQuery of testQueries) {
      await this.testEndpoint(
        `Python Function - ${testQuery.name}`,
        `${this.baseUrl}/api/python/query`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: testQuery.query })
        }
      )
    }

    // Test 6: Error handling
    await this.testEndpoint(
      'Empty Query Test',
      `${this.baseUrl}/api/query`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: "" })
      }
    )

    await this.testEndpoint(
      'Invalid JSON Test',
      `${this.baseUrl}/api/query`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: "invalid json"
      }
    )

    // Test 7: Method not allowed
    await this.testEndpoint(
      'Method Not Allowed Test',
      `${this.baseUrl}/api/query`,
      { method: 'DELETE' }
    )
  }

  printSummary() {
    console.log('\n' + '='.repeat(60))
    console.log('📊 TEST SUMMARY')
    console.log('='.repeat(60))
    
    const successful = this.testResults.filter(r => r.success)
    const failed = this.testResults.filter(r => !r.success)
    
    console.log(`✅ Successful: ${successful.length}`)
    console.log(`❌ Failed: ${failed.length}`)
    console.log(`📊 Total: ${this.testResults.length}`)
    
    if (successful.length > 0) {
      const avgResponseTime = successful.reduce((sum, r) => sum + r.responseTime, 0) / successful.length
      console.log(`⚡ Average Response Time: ${avgResponseTime.toFixed(2)}ms`)
    }
    
    if (failed.length > 0) {
      console.log('\n❌ Failed Tests:')
      failed.forEach(test => {
        console.log(`   - ${test.name}: ${test.status} ${test.error ? `(${test.error})` : ''}`)
      })
    }
    
    console.log('\n💡 Environment Check:')
    console.log(`   VERCEL: ${process.env.VERCEL || 'undefined'}`)
    console.log(`   VERCEL_ENV: ${process.env.VERCEL_ENV || 'undefined'}`)
    console.log(`   VERCEL_URL: ${process.env.VERCEL_URL || 'undefined'}`)
    console.log(`   NODE_ENV: ${process.env.NODE_ENV || 'undefined'}`)
    
    const successRate = (successful.length / this.testResults.length) * 100
    console.log(`\n🎯 Success Rate: ${successRate.toFixed(1)}%`)
    
    if (successRate >= 80) {
      console.log('🎉 API tests are mostly passing!')
      process.exit(0)
    } else {
      console.log('⚠️  Many tests failed. Check Vercel dev setup and environment variables.')
      process.exit(1)
    }
  }
}

async function main() {
  const tester = new VercelAPITester()
  
  try {
    await tester.runAPITests()
    tester.printSummary()
  } catch (error) {
    console.error('💥 Test runner failed:', error.message)
    process.exit(1)
  }
}

main()
