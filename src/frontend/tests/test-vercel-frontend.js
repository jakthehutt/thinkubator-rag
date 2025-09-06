#!/usr/bin/env node

const fetch = require('node-fetch')

class VercelFrontendTester {
  constructor(baseUrl = 'http://localhost:3000') {
    this.baseUrl = baseUrl
    this.testResults = []
  }

  async testPageLoad(name, path) {
    console.log(`\n🌐 Testing ${name}...`)
    const startTime = Date.now()
    
    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        timeout: 10000,
        method: 'GET'
      })
      
      const responseTime = Date.now() - startTime
      const html = await response.text()
      
      const result = {
        name,
        success: response.ok,
        status: response.status,
        responseTime,
        htmlLength: html.length,
        hasContent: html.includes('Thinkubator')
      }
      
      this.testResults.push(result)
      
      if (response.ok) {
        console.log(`   ✅ Status: ${response.status} (${responseTime}ms)`)
        console.log(`   📄 HTML Size: ${html.length} bytes`)
        console.log(`   🔍 Contains Thinkubator: ${result.hasContent ? 'Yes' : 'No'}`)
        
        // Check for key frontend components
        const checks = {
          'Query Interface': html.includes('Ask about circular economy'),
          'Header': html.includes('Thinkubator AI Knowledge Explorer'),
          'Footer': html.includes('Powered by'),
          'Styling': html.includes('tailwind') || html.includes('css'),
          'React': html.includes('_next') || html.includes('react')
        }
        
        console.log('   📋 Component Checks:')
        Object.entries(checks).forEach(([component, found]) => {
          console.log(`      ${found ? '✅' : '❌'} ${component}`)
        })
        
      } else {
        console.log(`   ❌ Status: ${response.status} (${responseTime}ms)`)
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
      console.log(`   ❌ Failed (${responseTime}ms): ${error.message}`)
      return result
    }
  }

  async testStaticAssets() {
    console.log(`\n📦 Testing Static Assets...`)
    
    const assets = [
      { path: '/favicon.ico', name: 'Favicon' },
      { path: '/_next/static/css', name: 'CSS Assets', expectPartial: true },
      { path: '/_next/static/chunks', name: 'JS Chunks', expectPartial: true }
    ]
    
    for (const asset of assets) {
      try {
        const response = await fetch(`${this.baseUrl}${asset.path}`, {
          timeout: 5000,
          method: 'GET'
        })
        
        if (asset.expectPartial || response.ok) {
          console.log(`   ✅ ${asset.name}: Available`)
        } else {
          console.log(`   ❌ ${asset.name}: ${response.status}`)
        }
      } catch (error) {
        console.log(`   ❌ ${asset.name}: ${error.message}`)
      }
    }
  }

  async testResponsiveness() {
    console.log(`\n📱 Testing Responsive Design...`)
    
    try {
      const response = await fetch(`${this.baseUrl}/`, {
        timeout: 10000,
        headers: {
          'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'
        }
      })
      
      const html = await response.text()
      
      const responsiveChecks = {
        'Viewport Meta': html.includes('viewport'),
        'Mobile CSS': html.includes('sm:') || html.includes('md:') || html.includes('lg:'),
        'Responsive Images': html.includes('responsive') || html.includes('w-full'),
        'Touch Friendly': html.includes('touch') || html.includes('hover:')
      }
      
      console.log('   📋 Responsive Checks:')
      Object.entries(responsiveChecks).forEach(([check, found]) => {
        console.log(`      ${found ? '✅' : '❌'} ${check}`)
      })
      
    } catch (error) {
      console.log(`   ❌ Responsive test failed: ${error.message}`)
    }
  }

  async testAccessibility() {
    console.log(`\n♿ Testing Basic Accessibility...`)
    
    try {
      const response = await fetch(`${this.baseUrl}/`, {
        timeout: 10000
      })
      
      const html = await response.text()
      
      const a11yChecks = {
        'Page Title': /<title>.*<\/title>/.test(html),
        'Meta Description': html.includes('meta name="description"'),
        'Alt Attributes': html.includes('alt='),
        'Form Labels': html.includes('label') || html.includes('aria-label'),
        'Semantic HTML': html.includes('<main>') || html.includes('<header>') || html.includes('<footer>'),
        'ARIA Attributes': html.includes('aria-') || html.includes('role=')
      }
      
      console.log('   📋 Accessibility Checks:')
      Object.entries(a11yChecks).forEach(([check, found]) => {
        console.log(`      ${found ? '✅' : '❌'} ${check}`)
      })
      
    } catch (error) {
      console.log(`   ❌ Accessibility test failed: ${error.message}`)
    }
  }

  async runFrontendTests() {
    console.log('🎨 Testing Vercel Dev Frontend...\n')
    console.log(`Base URL: ${this.baseUrl}`)
    
    // Test main page
    await this.testPageLoad('Home Page', '/')
    
    // Test static assets
    await this.testStaticAssets()
    
    // Test responsive design
    await this.testResponsiveness()
    
    // Test accessibility
    await this.testAccessibility()
  }

  printSummary() {
    console.log('\n' + '='.repeat(60))
    console.log('🎨 FRONTEND TEST SUMMARY')
    console.log('='.repeat(60))
    
    const successful = this.testResults.filter(r => r.success)
    const failed = this.testResults.filter(r => !r.success)
    
    console.log(`✅ Successful: ${successful.length}`)
    console.log(`❌ Failed: ${failed.length}`)
    console.log(`📊 Total: ${this.testResults.length}`)
    
    if (successful.length > 0) {
      const avgResponseTime = successful.reduce((sum, r) => sum + r.responseTime, 0) / successful.length
      console.log(`⚡ Average Load Time: ${avgResponseTime.toFixed(2)}ms`)
    }
    
    if (failed.length > 0) {
      console.log('\n❌ Failed Tests:')
      failed.forEach(test => {
        console.log(`   - ${test.name}: ${test.status} ${test.error ? `(${test.error})` : ''}`)
      })
    }
    
    console.log('\n💡 Frontend Status:')
    console.log('   - Make sure vercel dev is running')
    console.log('   - Check that all components are loading properly')
    console.log('   - Verify responsive design works on different screen sizes')
    console.log('   - Test accessibility with screen readers if needed')
    
    const successRate = this.testResults.length > 0 ? (successful.length / this.testResults.length) * 100 : 0
    console.log(`\n🎯 Success Rate: ${successRate.toFixed(1)}%`)
    
    if (successRate >= 80 || this.testResults.length === 0) {
      console.log('🎉 Frontend is working well!')
      process.exit(0)
    } else {
      console.log('⚠️  Frontend has issues. Check the failed tests above.')
      process.exit(1)
    }
  }
}

async function main() {
  const tester = new VercelFrontendTester()
  
  try {
    await tester.runFrontendTests()
    tester.printSummary()
  } catch (error) {
    console.error('💥 Frontend test runner failed:', error.message)
    process.exit(1)
  }
}

main()
