'use client'

import { useState } from 'react'
import { QueryInterface } from '@/components/QueryInterface'
import { ResultsDisplay } from '@/components/ResultsDisplay'

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

  const handleQuery = async (query: string) => {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `Server error: ${response.status}`)
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white/70 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-green-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">T</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  Thinkubator AI Knowledge Explorer
                </h1>
                <p className="text-sm text-gray-600 hidden sm:block">
                  Instantly search and synthesize insights from Thinkubator’s research library
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
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              What do you want to know about sustainability, circularity, or the environment?
            </h2>
            <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto">
              Ask anything and recieve a reliable answer generated from 750+ reports and scientific documents.
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

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-gray-50 mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-gray-600">
            <p>
              Powered by{" "}
              <a 
                href="https://www.thinkubator.earth/" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                Thinkubator
              </a>{" "}
              • Building a circular future through education, research, and advisory services
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
