/**
 * 🔗 Frontend-Backend Connection Test Utility
 * 
 * Comprehensive testing and monitoring of the frontend-backend connection
 */

import { logger } from './logger'

export interface ConnectionTestResult {
  success: boolean
  responseTime: number
  status?: number
  error?: string
  details: {
    backendUrl: string
    timestamp: string
    healthCheck: boolean
    apiTest: boolean
    networkLatency: number
  }
}

export interface BackendHealthStatus {
  status: 'healthy' | 'unhealthy' | 'unknown'
  service?: string
  pipeline_initialized?: boolean
  responseTime: number
  error?: string
}

class ConnectionTester {
  private backendUrl: string

  constructor() {
    // Get backend URL based on runtime context
    this.backendUrl = this.getBackendUrl()
    
    logger.info('network', '🔗 ConnectionTester initialized', { 
      backendUrl: this.backendUrl 
    })
  }

  private getBackendUrl(): string {
    // Check if we're running in browser (client-side) or Docker
    if (typeof window !== 'undefined') {
      // Browser context - use external host port
      return process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001'
    } else {
      // Server-side rendering or Docker context - use internal network
      return process.env.NEXT_PUBLIC_BACKEND_URL || 'http://backend:8000'
    }
  }

  /**
   * Test backend health endpoint
   */
  async testBackendHealth(): Promise<BackendHealthStatus> {
    const startTime = performance.now()
    
    try {
      logger.info('backend', '🏥 Testing backend health...')
      
      const response = await fetch(`${this.backendUrl}/health`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json'
        },
        // Add timeout to prevent hanging
        signal: AbortSignal.timeout(10000)
      })
      
      const responseTime = Math.round(performance.now() - startTime)
      
      if (!response.ok) {
        const error = `Health check failed with status ${response.status}`
        logger.error('backend', error, { status: response.status, responseTime })
        return {
          status: 'unhealthy',
          responseTime,
          error
        }
      }
      
      const healthData = await response.json()
      logger.info('backend', '✅ Backend health check successful', { healthData, responseTime })
      
      return {
        status: 'healthy',
        service: healthData.service,
        pipeline_initialized: healthData.pipeline_initialized,
        responseTime
      }
      
    } catch (error: any) {
      const responseTime = Math.round(performance.now() - startTime)
      const errorMessage = error.message || 'Unknown error'
      
      logger.error('backend', '❌ Backend health check failed', { error: errorMessage, responseTime })
      
      return {
        status: 'unknown',
        responseTime,
        error: errorMessage
      }
    }
  }

  /**
   * Test backend API with a simple query
   */
  async testBackendAPI(testQuery = 'What is circular economy?'): Promise<ConnectionTestResult> {
    const startTime = performance.now()
    const testId = logger.generateQueryId()
    
    try {
      logger.info('api', '🧪 Testing backend API...', { testQuery }, testId)
      
      const response = await fetch(`${this.backendUrl}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ query: testQuery }),
        signal: AbortSignal.timeout(30000) // 30 second timeout for API calls
      })
      
      const responseTime = Math.round(performance.now() - startTime)
      
      if (!response.ok) {
        const errorText = await response.text()
        const error = `API test failed with status ${response.status}: ${errorText}`
        logger.error('api', error, { status: response.status, responseTime }, testId)
        
        return {
          success: false,
          responseTime,
          status: response.status,
          error,
          details: {
            backendUrl: this.backendUrl,
            timestamp: new Date().toISOString(),
            healthCheck: false,
            apiTest: false,
            networkLatency: responseTime
          }
        }
      }
      
      const apiData = await response.json()
      logger.info('api', '✅ Backend API test successful', { 
        answerLength: apiData.answer?.length || 0,
        chunksCount: apiData.chunks?.length || 0,
        responseTime 
      }, testId)
      
      return {
        success: true,
        responseTime,
        status: response.status,
        details: {
          backendUrl: this.backendUrl,
          timestamp: new Date().toISOString(),
          healthCheck: true,
          apiTest: true,
          networkLatency: responseTime
        }
      }
      
    } catch (error: any) {
      const responseTime = Math.round(performance.now() - startTime)
      const errorMessage = error.message || 'Unknown error'
      
      logger.error('api', '❌ Backend API test failed', { error: errorMessage, responseTime }, testId)
      
      return {
        success: false,
        responseTime,
        error: errorMessage,
        details: {
          backendUrl: this.backendUrl,
          timestamp: new Date().toISOString(),
          healthCheck: false,
          apiTest: false,
          networkLatency: responseTime
        }
      }
    }
  }

  /**
   * Comprehensive connection test
   */
  async runFullConnectionTest(): Promise<{
    overall: boolean
    health: BackendHealthStatus
    api: ConnectionTestResult
    summary: string
  }> {
    logger.info('network', '🔬 Running comprehensive connection test...')
    
    const healthResult = await this.testBackendHealth()
    const apiResult = await this.testBackendAPI()
    
    const overall = healthResult.status === 'healthy' && apiResult.success
    
    const summary = overall 
      ? `✅ All tests passed - Backend healthy (${healthResult.responseTime}ms), API working (${apiResult.responseTime}ms)`
      : `❌ Tests failed - Health: ${healthResult.status}, API: ${apiResult.success ? 'OK' : 'Failed'}`
    
    logger.info('network', summary, { healthResult, apiResult })
    
    return {
      overall,
      health: healthResult,
      api: apiResult,
      summary
    }
  }

  /**
   * Monitor connection continuously
   */
  startConnectionMonitoring(intervalMs = 60000) { // Default: check every minute
    logger.info('network', '📊 Starting connection monitoring', { intervalMs })
    
    const monitoringInterval = setInterval(async () => {
      const healthResult = await this.testBackendHealth()
      logger.backendHealth(healthResult.status, { 
        responseTime: healthResult.responseTime,
        service: healthResult.service,
        pipeline_initialized: healthResult.pipeline_initialized
      })
    }, intervalMs)
    
    // Return function to stop monitoring
    return () => {
      clearInterval(monitoringInterval)
      logger.info('network', '🛑 Connection monitoring stopped')
    }
  }

  /**
   * Get backend URL being used
   */
  getBackendUrl(): string {
    return this.backendUrl
  }

  /**
   * Test if backend URL is reachable
   */
  async isBackendReachable(): Promise<boolean> {
    try {
      const response = await fetch(this.backendUrl, {
        method: 'HEAD',
        signal: AbortSignal.timeout(5000)
      })
      return response.ok
    } catch {
      return false
    }
  }
}

// Singleton instance
export const connectionTester = new ConnectionTester()

// Convenience functions
export const testBackendHealth = () => connectionTester.testBackendHealth()
export const testBackendAPI = (query?: string) => connectionTester.testBackendAPI(query)
export const runFullConnectionTest = () => connectionTester.runFullConnectionTest()
export const startConnectionMonitoring = (intervalMs?: number) => connectionTester.startConnectionMonitoring(intervalMs)
export const getBackendUrl = () => connectionTester.getBackendUrl()

export default connectionTester
