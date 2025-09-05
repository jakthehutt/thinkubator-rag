'use client'

import { useState } from 'react'
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline'

interface QueryInterfaceProps {
  onQuery: (query: string) => Promise<void>
  loading: boolean
}

export function QueryInterface({ onQuery, loading }: QueryInterfaceProps) {
  const [query, setQuery] = useState('What is the circularity gap?')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim() || loading) return
    await onQuery(query.trim())
  }

  return (
    <div className="mb-8">
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about circular economy, sustainability, business models..."
            className="block w-full pl-12 pr-32 py-4 border border-gray-300 rounded-xl text-lg placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm hover:shadow-md transition-all duration-200"
            disabled={loading}
          />
          <div className="absolute inset-y-0 right-0 pr-2 flex items-center">
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="bg-gradient-to-r from-blue-500 to-green-500 text-white px-6 py-2 rounded-lg font-medium hover:from-blue-600 hover:to-green-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center space-x-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Thinking...</span>
                </>
              ) : (
                <span>Search</span>
              )}
            </button>
          </div>
        </div>
      </form>
      
      {/* Sample Questions */}
      <div className="mt-4">
        <p className="text-sm text-gray-500 mb-2">Try these example questions:</p>
        <div className="flex flex-wrap gap-2">
          {[
            "What is the circularity gap?",
            "How do circular business models work?",
            "What are the main challenges in transitioning to circular economy?",
            "How does recycling impact the circular economy?"
          ].map((sampleQuery) => (
            <button
              key={sampleQuery}
              onClick={() => setQuery(sampleQuery)}
              className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded-full transition-colors duration-200"
              disabled={loading}
            >
              {sampleQuery}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
