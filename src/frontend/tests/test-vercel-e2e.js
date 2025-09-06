#!/usr/bin/env node

const fetch = require('node-fetch')

class VercelE2ETester {
  constructor(baseUrl = 'http://localhost:3000') {
    this.baseUrl = baseUrl
    this.testResults = []
  }

  async simulateUserQuery(query, expectedKeywords = []) {
    console.log(`\n🤖 Simulating user query: "${query}"`)
    const startTime = Date.now()
    
    try {
      // Step 1: Load the frontend page
      console.log('   1️⃣ Loading frontend page...')
      const pageResponse = await fetch(`${this.baseUrl}/`, {
        timeout: 10000
      })
      
      if (!pageResponse.ok) {
        throw new Error(`Frontend page failed: ${pageResponse.status}`)
      }
      console.log('      ✅ Frontend loaded successfully')
      
      // Step 2: Submit query through API
      console.log('   2️⃣ Submitting query through API...')
      const queryResponse = await fetch(`${this.baseUrl}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
        timeout: 30000 // Longer timeout for AI processing
      })
      
      const responseTime = Date.now() - startTime
      
      if (!queryResponse.ok) {
        const errorText = await queryResponse.text()
        throw new Error(`Query failed: ${queryResponse.status} - ${errorText}`)
      }
      
      const queryResult = await queryResponse.json()
      console.log('      ✅ Query processed successfully')
      
      // Step 3: Validate response structure
      console.log('   3️⃣ Validating response structure...')
      const validation = this.validateQueryResponse(queryResult)
      
      if (!validation.valid) {
        throw new Error(`Invalid response structure: ${validation.errors.join(', ')}`)
      }
      console.log('      ✅ Response structure is valid')
      
      // Step 4: Check content quality
      console.log('   4️⃣ Checking content quality...')
      const qualityCheck = this.checkContentQuality(queryResult, expectedKeywords)
      console.log(`      📊 Answer length: ${queryResult.answer.length} chars`)
      console.log(`      📚 Sources found: ${queryResult.chunks.length}`)
      console.log(`      🎯 Relevance score: ${qualityCheck.relevanceScore}/10`)
      
      const result = {
        query,
        success: true,
        responseTime,
        answerLength: queryResult.answer.length,
        sourcesCount: queryResult.chunks.length,
        relevanceScore: qualityCheck.relevanceScore,
        data: queryResult
      }
      
      this.testResults.push(result)
      console.log(`   ✅ E2E test completed in ${responseTime}ms`)
      
      return result
      
    } catch (error) {
      const responseTime = Date.now() - startTime
      const result = {
        query,
        success: false,
        responseTime,
        error: error.message
      }
      
      this.testResults.push(result)
      console.log(`   ❌ E2E test failed (${responseTime}ms): ${error.message}`)
      
      return result
    }
  }

  validateQueryResponse(response) {
    const errors = []
    
    if (!response || typeof response !== 'object') {
      errors.push('Response is not an object')
      return { valid: false, errors }
    }
    
    if (!response.answer || typeof response.answer !== 'string') {
      errors.push('Missing or invalid answer field')
    }
    
    if (!Array.isArray(response.chunks)) {
      errors.push('Missing or invalid chunks array')
    } else {
      response.chunks.forEach((chunk, index) => {
        if (!chunk.document || typeof chunk.document !== 'string') {
          errors.push(`Chunk ${index} missing document field`)
        }
        if (!chunk.metadata || typeof chunk.metadata !== 'object') {
          errors.push(`Chunk ${index} missing metadata field`)
        }
      })
    }
    
    return {
      valid: errors.length === 0,
      errors
    }
  }

  checkContentQuality(response, expectedKeywords = []) {
    let relevanceScore = 0
    const answer = response.answer.toLowerCase()
    
    // Basic quality checks
    if (response.answer.length > 50) relevanceScore += 2
    if (response.answer.length > 200) relevanceScore += 1
    if (response.chunks.length > 0) relevanceScore += 2
    if (response.chunks.length > 2) relevanceScore += 1
    
    // Keyword relevance
    expectedKeywords.forEach(keyword => {
      if (answer.includes(keyword.toLowerCase())) {
        relevanceScore += 1
      }
    })
    
    // Content coherence (basic checks)
    if (answer.includes('circular') || answer.includes('sustainability')) relevanceScore += 1
    if (answer.includes('.') && answer.includes(' ')) relevanceScore += 1 // Proper sentences
    if (!answer.includes('error') && !answer.includes('failed')) relevanceScore += 1
    
    return {
      relevanceScore: Math.min(relevanceScore, 10)
    }
  }

  async testErrorHandling() {
    console.log(`\n🚨 Testing Error Handling...`)
    
    const errorTests = [
      { query: '', name: 'Empty Query' },
      { query: 'x', name: 'Very Short Query' },
      { query: 'a'.repeat(1000), name: 'Very Long Query' }
    ]
    
    for (const test of errorTests) {
      try {
        console.log(`   Testing ${test.name}...`)
        const response = await fetch(`${this.baseUrl}/api/query`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: test.query }),
          timeout: 10000
        })
        
        if (test.query === '') {
          // Empty query should return an error or handle gracefully
          if (response.status >= 400) {
            console.log(`      ✅ ${test.name}: Properly rejected (${response.status})`)
          } else {
            const result = await response.json()
            if (result.answer && result.answer.includes('information')) {
              console.log(`      ✅ ${test.name}: Handled gracefully`)
            } else {
              console.log(`      ⚠️  ${test.name}: Unexpected response`)
            }
          }
        } else {
          // Other tests should work or fail gracefully
          if (response.ok) {
            console.log(`      ✅ ${test.name}: Handled successfully`)
          } else {
            console.log(`      ⚠️  ${test.name}: Failed with ${response.status}`)
          }
        }
        
      } catch (error) {
        console.log(`      ❌ ${test.name}: ${error.message}`)
      }
    }
  }

  async runE2ETests() {
    console.log('🎬 Running End-to-End Tests...\n')
    console.log(`Base URL: ${this.baseUrl}`)
    
    // Test different types of queries
    const testScenarios = [
      {
        query: "What is circular economy?",
        keywords: ['circular', 'economy', 'waste', 'resources'],
        name: "Basic Concept Query"
      },
      {
        query: "What is the circularity gap?",
        keywords: ['circularity', 'gap', 'materials', 'recycled'],
        name: "Specific Term Query"
      },
      {
        query: "How do circular business models work?",
        keywords: ['business', 'models', 'circular', 'value'],
        name: "Business Model Query"
      },
      {
        query: "What are the environmental benefits of sustainability?",
        keywords: ['environmental', 'benefits', 'sustainability'],
        name: "Environmental Query"
      },
      {
        query: "Tell me about recycling and waste management in circular economy",
        keywords: ['recycling', 'waste', 'management', 'circular'],
        name: "Complex Multi-topic Query"
      }
    ]
    
    console.log(`Running ${testScenarios.length} E2E test scenarios...\n`)
    
    for (const scenario of testScenarios) {
      await this.simulateUserQuery(scenario.query, scenario.keywords)
    }
    
    // Test error handling
    await this.testErrorHandling()
  }

  printSummary() {
    console.log('\n' + '='.repeat(60))
    console.log('🎬 END-TO-END TEST SUMMARY')
    console.log('='.repeat(60))
    
    const successful = this.testResults.filter(r => r.success)
    const failed = this.testResults.filter(r => !r.success)
    
    console.log(`✅ Successful: ${successful.length}`)
    console.log(`❌ Failed: ${failed.length}`)
    console.log(`📊 Total: ${this.testResults.length}`)
    
    if (successful.length > 0) {
      const avgResponseTime = successful.reduce((sum, r) => sum + r.responseTime, 0) / successful.length
      const avgAnswerLength = successful.reduce((sum, r) => sum + (r.answerLength || 0), 0) / successful.length
      const avgSourcesCount = successful.reduce((sum, r) => sum + (r.sourcesCount || 0), 0) / successful.length
      const avgRelevanceScore = successful.reduce((sum, r) => sum + (r.relevanceScore || 0), 0) / successful.length
      
      console.log(`⚡ Average Response Time: ${avgResponseTime.toFixed(2)}ms`)
      console.log(`📝 Average Answer Length: ${avgAnswerLength.toFixed(0)} chars`)
      console.log(`📚 Average Sources Count: ${avgSourcesCount.toFixed(1)}`)
      console.log(`🎯 Average Relevance Score: ${avgRelevanceScore.toFixed(1)}/10`)
    }
    
    if (failed.length > 0) {
      console.log('\n❌ Failed Tests:')
      failed.forEach(test => {
        console.log(`   - "${test.query}": ${test.error}`)
      })
    }
    
    console.log('\n💡 E2E Test Insights:')
    console.log('   - Test complete user workflows from frontend to backend')
    console.log('   - Validate response quality and relevance')
    console.log('   - Check error handling for edge cases')
    console.log('   - Monitor performance across different query types')
    
    const successRate = this.testResults.length > 0 ? (successful.length / this.testResults.length) * 100 : 0
    console.log(`\n🎯 Success Rate: ${successRate.toFixed(1)}%`)
    
    if (successRate >= 80) {
      console.log('🎉 E2E tests are passing! The complete workflow works well.')
      process.exit(0)
    } else {
      console.log('⚠️  E2E tests have issues. Check the failed scenarios above.')
      process.exit(1)
    }
  }
}

async function main() {
  const tester = new VercelE2ETester()
  
  try {
    await tester.runE2ETests()
    tester.printSummary()
  } catch (error) {
    console.error('💥 E2E test runner failed:', error.message)
    process.exit(1)
  }
}

main()
