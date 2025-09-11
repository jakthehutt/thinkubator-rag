'use client'

import { useState, useEffect } from 'react'
import * as React from 'react'
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline'
import { logger, logUserAction } from '@/utils/logger'

interface QueryInterfaceProps {
  onQuery: (query: string) => Promise<void>
  loading: boolean
}

export function QueryInterface({ onQuery, loading }: QueryInterfaceProps) {
  const [query, setQuery] = useState('What is the circularity gap?')

  // Log component mount
  useEffect(() => {
    logger.info('ui', '🔍 QueryInterface component mounted')
    logUserAction('query_interface_loaded')
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    const trimmedQuery = query.trim()
    logger.info('ui', '🚀 Form submitted', { 
      query: trimmedQuery, 
      queryLength: trimmedQuery.length,
      loading 
    })
    
    if (!trimmedQuery || loading) {
      logger.warn('ui', '❌ Form submission blocked', { 
        reason: !trimmedQuery ? 'empty_query' : 'loading_in_progress',
        query: trimmedQuery,
        loading 
      })
      logUserAction('query_submission_blocked', { 
        reason: !trimmedQuery ? 'empty_query' : 'loading_in_progress' 
      })
      return
    }
    
    logger.info('ui', '✅ Executing query submission', { query: trimmedQuery })
    logUserAction('query_submitted', { 
      query: trimmedQuery, 
      queryLength: trimmedQuery.length 
    })
    
    try {
      await onQuery(trimmedQuery)
    } catch (error) {
      logger.error('ui', '❌ Query submission failed', { 
        query: trimmedQuery, 
        error: error instanceof Error ? error.message : 'Unknown error' 
      })
      logUserAction('query_submission_failed', { 
        query: trimmedQuery, 
        error: error instanceof Error ? error.message : 'Unknown error' 
      })
    }
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
            onChange={(e) => {
              const newQuery = e.target.value
              setQuery(newQuery)
              logger.debug('ui', '⌨️ Query input changed', { 
                queryLength: newQuery.length,
                isEmpty: !newQuery.trim() 
              })
            }}
            onFocus={() => {
              logger.info('ui', '🎯 Query input focused')
              logUserAction('query_input_focused')
            }}
            onBlur={() => {
              logger.info('ui', '👀 Query input blurred', { queryLength: query.length })
              logUserAction('query_input_blurred', { queryLength: query.length })
            }}
            placeholder="Ask about circular economy, sustainability, business models..."
            className="block w-full pl-12 pr-32 py-4 border border-gray-300 rounded-xl text-lg placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#8FB390] focus:border-transparent shadow-sm hover:shadow-md transition-all duration-200"
            disabled={loading}
          />
          <div className="absolute inset-y-0 right-0 pr-2 flex items-center">
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="bg-[#8FB390] text-white px-6 py-2 rounded-lg font-medium hover:bg-[#3E7652] focus:outline-none focus:ring-2 focus:ring-[#8FB390] focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center space-x-2"
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
              onClick={() => {
                setQuery(sampleQuery)
                logger.info('ui', '💡 Sample query selected', { sampleQuery })
                logUserAction('sample_query_selected', { sampleQuery })
              }}
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
