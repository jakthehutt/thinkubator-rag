'use client'

import { useState, useEffect } from 'react'
import Image from 'next/image'
import { QueryInterface } from '@/components/QueryInterface'
import { ResultsDisplay } from '@/components/ResultsDisplay'
import { logger, logApiRequest, logApiResponse, logNetworkError, logUserAction, logPerformance } from '@/utils/logger'
import { performanceMonitor, trackApiCall } from '@/utils/performanceMonitor'

export interface QueryResult {
  answer: string
  chunks: Array<{
    document: string
    metadata: Record<string, string | number | boolean | null>
  }>
}

export default function Home() {
  const [result, setResult] = useState<QueryResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Initialize logging and connection testing on component mount
  useEffect(() => {
    logger.info('ui', '🏠 Home component mounted')
    logUserAction('page_load', { url: window.location.href })
    
    
    return () => {
      logger.info('ui', '🏠 Home component unmounting')
    }
  }, [])

  const getBackendUrl = (): string => {
    // Context-aware backend URL selection
    if (typeof window !== 'undefined') {
      // Browser context - use external host port
      return process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001'
    } else {
      // Server-side rendering - use internal network
      return process.env.NEXT_PUBLIC_BACKEND_URL || 'http://backend:8000'
    }
  }

  const handleQuery = async (query: string) => {
    const queryId = logger.generateQueryId()
    const startTime = performance.now()
    
    logger.info('ui', '🔍 Starting new query', { query, queryId }, queryId)
    logUserAction('start_query', { query, queryId })
    
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      // Get backend URL with context-aware fallback
      const backendUrl = getBackendUrl()
      const apiUrl = `${backendUrl}/query`
      
      logger.info('network', '🌐 Using backend URL', { backendUrl, apiUrl }, queryId)
      
      // Log API request
      logApiRequest('POST', apiUrl, { query }, queryId)
      
      const requestStartTime = performance.now()
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ query }),
        // Add timeout to prevent hanging requests
        signal: AbortSignal.timeout(60000) // 60 second timeout
      })

      const responseTime = Math.round(performance.now() - requestStartTime)
      
      logger.info('api', '📊 Received response', { 
        status: response.status, 
        ok: response.ok, 
        statusText: response.statusText,
        responseTime 
      }, queryId)

      if (!response.ok) {
        let errorData: any
        try {
          errorData = await response.json()
        } catch {
          errorData = { detail: `HTTP ${response.status}: ${response.statusText}` }
        }
        
        logApiResponse(response.status, apiUrl, responseTime, errorData, queryId)
        logger.error('api', '❌ API request failed', { 
          status: response.status, 
          errorData, 
          query 
        }, queryId)
        
        throw new Error(errorData.detail || `Server error: ${response.status} - ${response.statusText}`)
      }

      const data = await response.json()
      const totalTime = Math.round(performance.now() - startTime)
      
      // Log successful response with detailed metrics
      logApiResponse(response.status, apiUrl, responseTime, {
        answerLength: data.answer?.length || 0,
        chunksCount: data.chunks?.length || 0,
        processingTime: data.processing_time_ms || 'unknown',
        sessionId: data.session_id || null
      }, queryId)
      
      // Track API call performance
      trackApiCall(responseTime, '/query', true)
      
      // Log performance metrics
      logPerformance('complete_query', totalTime, {
        networkTime: responseTime,
        processingTime: data.processing_time_ms,
        answerLength: data.answer?.length,
        chunksCount: data.chunks?.length
      }, queryId)
      
      logger.info('api', '✅ Query completed successfully', { 
        totalTime,
        networkTime: responseTime,
        answerLength: data.answer?.length || 0,
        chunksCount: data.chunks?.length || 0
      }, queryId)
      
      logUserAction('query_success', { 
        query,
        totalTime,
        answerLength: data.answer?.length,
        chunksCount: data.chunks?.length 
      })
      
      setResult(data)
      
    } catch (err: any) {
      const totalTime = Math.round(performance.now() - startTime)
      const errorMessage = err instanceof Error ? err.message : 'An unexpected error occurred'
      
      // Log network errors vs API errors differently  
      const backendUrl = getBackendUrl()
      const apiUrl = `${backendUrl}/query`
      if (err.name === 'TypeError' && err.message.includes('fetch')) {
        logNetworkError(apiUrl, err, queryId)
        logger.error('network', '🔌 Network connection failed', { 
          error: errorMessage, 
          query, 
          backendUrl,
          totalTime 
        }, queryId)
      } else {
        logger.error('api', '💥 Query processing failed', { 
          error: errorMessage, 
          query, 
          totalTime 
        }, queryId)
      }
      
      logUserAction('query_error', { query, error: errorMessage, totalTime })
      
      // Track failed API call performance
      trackApiCall(totalTime, '/query', false)
      
      // Enhanced error message based on error type
      let enhancedError = errorMessage
      if (err.name === 'AbortError') {
        enhancedError = 'Query timed out. Please try again with a shorter question.'
      } else if (err.message.includes('fetch')) {
        enhancedError = 'Unable to connect to the backend. Please check if the service is running.'
      }
      
      setError(enhancedError)
      
    } finally {
      setLoading(false)
      const totalTime = Math.round(performance.now() - startTime)
      logger.info('ui', '🏁 Query processing completed', { totalTime }, queryId)
    }
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-gray-200 bg-[#8FB390] sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-2">
            <div className="flex items-center space-x-4">
              <div className="w-28 h-28 rounded-lg flex items-center justify-center">
                <Image 
                  src="/logo.avif" 
                  alt="Thinkubator Logo" 
                  width={107}
                  height={107}
                  className="object-contain"
                />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">
                  Knowledge Explorer
                </h1>
                <p className="text-sm text-green-100 hidden sm:block">
                  Instantly search and synthesize insights from thinkubator&apos;s research library
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Hero Section */}
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-[#3E7652] mb-4">
              What do you want to know?
            </h2>
            <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto">
              Ask anything and recieve a reliable answer generated from 750+ reports.
            </p>
          </div>


          {/* Query Interface */}
          <QueryInterface 
            onQuery={handleQuery} 
            loading={loading}
          />

          {/* Results */}
          <ResultsDisplay 
            result={result}
            loading={loading}
            error={error}
          />
        </div>
      </main>

    </div>
  )
}
