#!/usr/bin/env node

const { spawn } = require('child_process')
const path = require('path')

class VercelTestRunner {
  constructor() {
    this.testsDir = __dirname
    this.testResults = []
  }

  async runScript(scriptName, description) {
    console.log(`\n${'='.repeat(60)}`)
    console.log(`🚀 ${description}`)
    console.log(`${'='.repeat(60)}`)
    
    const scriptPath = path.join(this.testsDir, scriptName)
    
    return new Promise((resolve) => {
      const child = spawn('node', [scriptPath], {
        stdio: 'inherit',
        cwd: path.dirname(this.testsDir)
      })
      
      child.on('close', (code) => {
        const result = {
          script: scriptName,
          description,
          success: code === 0,
          exitCode: code
        }
        
        this.testResults.push(result)
        
        if (code === 0) {
          console.log(`\n✅ ${description} - PASSED`)
        } else {
          console.log(`\n❌ ${description} - FAILED (exit code: ${code})`)
        }
        
        resolve(result)
      })
      
      child.on('error', (error) => {
        console.error(`\n💥 Failed to run ${scriptName}:`, error.message)
        const result = {
          script: scriptName,
          description,
          success: false,
          error: error.message
        }
        
        this.testResults.push(result)
        resolve(result)
      })
    })
  }

  async checkVercelDevRunning() {
    console.log('🔍 Checking if Vercel dev is running...')
    
    try {
      const fetch = require('node-fetch')
      const response = await fetch('http://localhost:3000', {
        timeout: 5000
      })
      
      if (response.ok) {
        console.log('✅ Vercel dev is running on http://localhost:3000')
        return true
      } else {
        console.log(`❌ Vercel dev responded with status: ${response.status}`)
        return false
      }
    } catch (error) {
      console.log('❌ Vercel dev is not running or not accessible')
      console.log('💡 Please run "npm run dev" (vercel dev) in another terminal first')
      return false
    }
  }

  async runAllTests() {
    console.log('🧪 VERCEL DEV TEST SUITE')
    console.log(`Started at: ${new Date().toISOString()}`)
    
    // Check if Vercel dev is running
    const isRunning = await this.checkVercelDevRunning()
    if (!isRunning) {
      console.log('\n❌ Cannot run tests without Vercel dev running')
      console.log('\n📋 Setup Instructions:')
      console.log('1. Open a new terminal')
      console.log('2. cd src/frontend')
      console.log('3. npm run dev (this runs vercel dev)')
      console.log('4. Wait for "Ready" message')
      console.log('5. Run tests in this terminal')
      process.exit(1)
    }
    
    // Run test scripts in sequence
    await this.runScript('test-local-setup.js', 'Environment Setup Check')
    await this.runScript('test-vercel-api.js', 'API Endpoints Testing')
    await this.runScript('test-vercel-frontend.js', 'Frontend Component Testing')
    await this.runScript('test-vercel-e2e.js', 'End-to-End Workflow Testing')
  }

  printFinalSummary() {
    console.log('\n' + '='.repeat(80))
    console.log('🏁 FINAL TEST SUMMARY')
    console.log('='.repeat(80))
    
    const successful = this.testResults.filter(r => r.success)
    const failed = this.testResults.filter(r => !r.success)
    
    console.log(`\n📊 Overall Results:`)
    console.log(`✅ Passed: ${successful.length}`)
    console.log(`❌ Failed: ${failed.length}`)
    console.log(`📈 Total: ${this.testResults.length}`)
    
    if (successful.length > 0) {
      console.log(`\n✅ Successful Test Suites:`)
      successful.forEach(test => {
        console.log(`   • ${test.description}`)
      })
    }
    
    if (failed.length > 0) {
      console.log(`\n❌ Failed Test Suites:`)
      failed.forEach(test => {
        console.log(`   • ${test.description} (${test.error || `exit code: ${test.exitCode}`})`)
      })
    }
    
    const successRate = this.testResults.length > 0 ? (successful.length / this.testResults.length) * 100 : 0
    console.log(`\n🎯 Overall Success Rate: ${successRate.toFixed(1)}%`)
    
    console.log(`\n💡 Test Environment:`)
    console.log(`   • Vercel Dev: http://localhost:3000`)
    console.log(`   • Test Runner: Node.js ${process.version}`)
    console.log(`   • Platform: ${process.platform}`)
    console.log(`   • Completed: ${new Date().toISOString()}`)
    
    if (successRate >= 75) {
      console.log('\n🎉 Great! Most tests are passing. Your Vercel dev setup is working well!')
      
      if (successRate < 100) {
        console.log('💡 Some tests failed - check the details above for improvements.')
      }
      
      console.log('\n🚀 Next Steps:')
      console.log('   • Deploy to Vercel with: vercel --prod')
      console.log('   • Run tests against production deployment')
      console.log('   • Monitor performance and error rates')
      
      process.exit(0)
    } else {
      console.log('\n⚠️  Many tests failed. Please address the issues above.')
      
      console.log('\n🔧 Troubleshooting:')
      console.log('   • Ensure Vercel dev is running (npm run dev)')
      console.log('   • Check environment variables in .env.local')
      console.log('   • Verify API keys are valid (GEMINI_API_KEY, SUPABASE_*)')
      console.log('   • Check network connectivity')
      console.log('   • Review Vercel dev logs for errors')
      
      process.exit(1)
    }
  }
}

async function main() {
  const runner = new VercelTestRunner()
  
  try {
    await runner.runAllTests()
    runner.printFinalSummary()
  } catch (error) {
    console.error('\n💥 Test runner crashed:', error.message)
    console.error(error.stack)
    process.exit(1)
  }
}

main()
