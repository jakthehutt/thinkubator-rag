'use client'

import { useState } from 'react'
import { ChevronDownIcon, ChevronUpIcon, DocumentTextIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'

interface QueryResult {
  answer: string
  chunks: Array<{
    document: string
    metadata: Record<string, string | number | boolean | null>
  }>
}

interface ResultsDisplayProps {
  result: QueryResult | null
  loading: boolean
  error: string | null
}

export function ResultsDisplay({ result, loading, error }: ResultsDisplayProps) {
  const [expandedChunks, setExpandedChunks] = useState<Set<number>>(new Set())

  const toggleChunk = (index: number) => {
    const newExpanded = new Set(expandedChunks)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedChunks(newExpanded)
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Processing your query...</h3>
        <p className="text-gray-600">Searching through circular economy knowledge base and generating insights.</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-start">
          <ExclamationTriangleIcon className="h-6 w-6 text-red-400 mt-0.5 mr-3 flex-shrink-0" />
          <div>
            <h3 className="text-sm font-medium text-red-800 mb-1">Query Failed</h3>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      </div>
    )
  }

  if (!result) {
    return null
  }

  return (
    <div className="space-y-8">
      {/* Answer Section */}
      <div className="bg-gradient-to-r from-blue-50 to-green-50 border border-blue-200 rounded-xl p-6">
        <div className="flex items-start mb-4">
          <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-green-500 rounded-lg flex items-center justify-center mr-3 flex-shrink-0">
            <span className="text-white font-bold">AI</span>
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-1">Answer</h2>
            <p className="text-sm text-gray-600">Generated from circular economy knowledge base</p>
          </div>
        </div>
        <div className="prose prose-gray max-w-none">
          <div className="text-gray-800 leading-relaxed whitespace-pre-wrap">
            {result.answer}
          </div>
        </div>
      </div>

      {/* Sources Section */}
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <div className="flex items-center mb-6">
          <DocumentTextIcon className="h-6 w-6 text-gray-500 mr-2" />
          <h2 className="text-xl font-bold text-gray-900">
            Sources ({result.chunks.length})
          </h2>
        </div>
        <p className="text-gray-600 mb-6">
          These are the document excerpts that were used to generate the answer above.
        </p>
        
        <div className="space-y-4">
          {result.chunks.map((chunk, index) => {
            const isExpanded = expandedChunks.has(index)
            const metadata = chunk.metadata
            const documentName = metadata.document_name || 'Unknown Document'
            const pageNumber = metadata.page_in_document || 'N/A'
            const isPageApprox = metadata.page_approximation || false
            
            return (
              <div key={index} className="border border-gray-200 rounded-lg overflow-hidden">
                <button
                  onClick={() => toggleChunk(index)}
                  className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors duration-200 flex items-center justify-between text-left"
                >
                  <div className="flex items-center space-x-3">
                    <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded">
                      Source {index + 1}
                    </span>
                    <span className="font-medium text-gray-900">
                      {documentName}
                    </span>
                    <span className="text-sm text-gray-500">
                      Page {isPageApprox ? '~' : ''}{pageNumber}
                    </span>
                  </div>
                  {isExpanded ? (
                    <ChevronUpIcon className="h-5 w-5 text-gray-400" />
                  ) : (
                    <ChevronDownIcon className="h-5 w-5 text-gray-400" />
                  )}
                </button>
                
                {isExpanded && (
                  <div className="p-4 border-t border-gray-200">
                    {/* Document Content */}
                    <div className="mb-4">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Content:</h4>
                      <div className="bg-gray-50 p-3 rounded text-sm font-mono text-gray-800 whitespace-pre-wrap leading-relaxed border">
                        {chunk.document}
                      </div>
                    </div>
                    
                    {/* Metadata */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Metadata:</h4>
                      <div className="bg-white border rounded p-3">
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                          {Object.entries(metadata).map(([key, value]) => (
                            <div key={key} className="flex flex-col">
                              <span className="font-medium text-gray-500 uppercase tracking-wide">
                                {key.replace(/_/g, ' ')}
                              </span>
                              <span className="text-gray-900 mt-1 break-words">
                                {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
