'use client'

import { useState, useEffect } from 'react'
import { ChevronDownIcon, ChevronUpIcon, DocumentTextIcon, ExclamationTriangleIcon, ClipboardIcon, CheckIcon } from '@heroicons/react/24/outline'
import { logger, logUserAction } from '@/utils/logger'

interface QueryResult {
  answer: string
  chunks: Array<{
    document: string
    metadata: Record<string, string | number | boolean | null>
  }>
  query?: string // The original question (for past chats)
}

interface ResultsDisplayProps {
  result: QueryResult | null
  loading: boolean
  error: string | null
}

export function ResultsDisplay({ result, loading, error }: ResultsDisplayProps) {
  const [expandedChunks, setExpandedChunks] = useState<Set<number>>(new Set())
  const [copied, setCopied] = useState(false)
  const [questionCopied, setQuestionCopied] = useState(false)
  const [chunkCopied, setChunkCopied] = useState<Set<number>>(new Set())
  const [metadataCopied, setMetadataCopied] = useState<Set<string>>(new Set())

  // Log component mount and state changes
  useEffect(() => {
    logger.info('ui', '📊 ResultsDisplay component mounted')
  }, [])

  useEffect(() => {
    if (loading) {
      logger.info('ui', '⏳ Results display showing loading state')
      logUserAction('results_loading_started')
    }
  }, [loading])

  useEffect(() => {
    if (error) {
      logger.error('ui', '❌ Results display showing error', { error })
      logUserAction('results_error_displayed', { error })
    }
  }, [error])

  useEffect(() => {
    if (result) {
      logger.info('ui', '✅ Results display showing results', { 
        answerLength: result.answer?.length || 0,
        chunksCount: result.chunks?.length || 0
      })
      logUserAction('results_displayed', { 
        answerLength: result.answer?.length || 0,
        chunksCount: result.chunks?.length || 0
      })
    }
  }, [result])

  const toggleChunk = (index: number) => {
    const newExpanded = new Set(expandedChunks)
    const isExpanding = !newExpanded.has(index)
    
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedChunks(newExpanded)
    
    logger.info('ui', `📖 Source chunk ${isExpanding ? 'expanded' : 'collapsed'}`, { 
      chunkIndex: index,
      action: isExpanding ? 'expand' : 'collapse',
      totalExpanded: newExpanded.size
    })
    logUserAction(`source_chunk_${isExpanding ? 'expanded' : 'collapsed'}`, { 
      chunkIndex: index,
      totalExpanded: newExpanded.size
    })
  }

  const copyToClipboard = async () => {
    if (!result?.answer) return
    
    try {
      await navigator.clipboard.writeText(result.answer)
      setCopied(true)
      
      logger.info('ui', '📋 Answer copied to clipboard', { 
        answerLength: result.answer.length
      })
      logUserAction('answer_copied', { 
        answerLength: result.answer.length
      })
      
      // Reset copied state after 2 seconds
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      logger.error('ui', '❌ Failed to copy answer to clipboard', { error })
      logUserAction('answer_copy_failed', { error: error instanceof Error ? error.message : 'Unknown error' })
    }
  }

  const copyQuestionToClipboard = async () => {
    if (!result?.query) return
    
    try {
      await navigator.clipboard.writeText(result.query)
      setQuestionCopied(true)
      
      logger.info('ui', '📋 Question copied to clipboard', { 
        questionLength: result.query.length
      })
      logUserAction('question_copied', { 
        questionLength: result.query.length
      })
      
      // Reset copied state after 2 seconds
      setTimeout(() => setQuestionCopied(false), 2000)
    } catch (error) {
      logger.error('ui', '❌ Failed to copy question to clipboard', { error })
      logUserAction('question_copy_failed', { error: error instanceof Error ? error.message : 'Unknown error' })
    }
  }

  const copyChunkToClipboard = async (chunkIndex: number, content: string) => {
    try {
      // Clean content by removing <chunk> tags
      const cleanContent = content.replace(/<\/?chunk>/g, '').trim()
      await navigator.clipboard.writeText(cleanContent)
      
      const newChunkCopied = new Set(chunkCopied)
      newChunkCopied.add(chunkIndex)
      setChunkCopied(newChunkCopied)
      
      logger.info('ui', '📋 Chunk copied to clipboard', { chunkIndex, contentLength: cleanContent.length })
      logUserAction('chunk_copied', { chunkIndex, contentLength: cleanContent.length })
      
      // Reset copied state after 2 seconds
      setTimeout(() => {
        const resetChunkCopied = new Set(chunkCopied)
        resetChunkCopied.delete(chunkIndex)
        setChunkCopied(resetChunkCopied)
      }, 2000)
    } catch (error) {
      logger.error('ui', '❌ Failed to copy chunk to clipboard', { error, chunkIndex })
      logUserAction('chunk_copy_failed', { error: error instanceof Error ? error.message : 'Unknown error', chunkIndex })
    }
  }

  const copyMetadataItemToClipboard = async (key: string, value: any, chunkIndex: number) => {
    try {
      const textValue = typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)
      await navigator.clipboard.writeText(textValue)
      
      const metadataKey = `${chunkIndex}-${key}`
      const newMetadataCopied = new Set(metadataCopied)
      newMetadataCopied.add(metadataKey)
      setMetadataCopied(newMetadataCopied)
      
      logger.info('ui', '📋 Metadata item copied to clipboard', { key, chunkIndex, valueLength: textValue.length })
      logUserAction('metadata_item_copied', { key, chunkIndex, valueLength: textValue.length })
      
      // Reset copied state after 2 seconds
      setTimeout(() => {
        const resetMetadataCopied = new Set(metadataCopied)
        resetMetadataCopied.delete(metadataKey)
        setMetadataCopied(resetMetadataCopied)
      }, 2000)
    } catch (error) {
      logger.error('ui', '❌ Failed to copy metadata item to clipboard', { error, key, chunkIndex })
      logUserAction('metadata_item_copy_failed', { error: error instanceof Error ? error.message : 'Unknown error', key, chunkIndex })
    }
  }

  const cleanChunkContent = (content: string) => {
    return content.replace(/<\/?chunk>/g, '').trim()
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
          <div className="w-8 h-8 border-4 border-[#8FB390] border-t-transparent rounded-full animate-spin"></div>
        </div>
        <h3 className="text-lg font-medium text-black mb-2">Processing your query...</h3>
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
      {/* Question Section (for past chats) */}
      {result.query && (
        <div className="bg-gradient-to-r from-blue-50 to-blue-50 border border-blue-200 rounded-xl p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-start">
              <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center mr-3 flex-shrink-0">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h2 className="text-xl font-bold text-black mb-1">Question</h2>
                <p className="text-sm text-gray-600">Your original query from this conversation</p>
              </div>
            </div>
            <button
              onClick={copyQuestionToClipboard}
              className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-white/50 rounded-lg transition-all duration-200 border border-gray-300/50 hover:border-gray-400/50"
              title={questionCopied ? 'Copied!' : 'Copy question to clipboard'}
            >
              {questionCopied ? (
                <>
                  <CheckIcon className="h-4 w-4 text-green-600" />
                  <span className="text-green-600">Copied!</span>
                </>
              ) : (
                <>
                  <ClipboardIcon className="h-4 w-4" />
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>
          <div className="prose prose-gray max-w-none">
            <div className="text-gray-800 leading-relaxed whitespace-pre-wrap font-medium">
              {result.query}
            </div>
          </div>
        </div>
      )}

      {/* Answer Section */}
      <div className="bg-gradient-to-r from-green-50 to-green-50 border border-green-200 rounded-xl p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start">
            <div className="w-10 h-10 bg-[#8FB390] rounded-lg flex items-center justify-center mr-3 flex-shrink-0">
              <span className="text-white font-bold">AI</span>
            </div>
            <div>
              <h2 className="text-xl font-bold text-black mb-1">Answer</h2>
              <p className="text-sm text-gray-600">Generated from circular economy knowledge base</p>
            </div>
          </div>
          <button
            onClick={copyToClipboard}
            className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-white/50 rounded-lg transition-all duration-200 border border-gray-300/50 hover:border-gray-400/50"
            title={copied ? 'Copied!' : 'Copy answer to clipboard'}
          >
            {copied ? (
              <>
                <CheckIcon className="h-4 w-4 text-green-600" />
                <span className="text-green-600">Copied!</span>
              </>
            ) : (
              <>
                <ClipboardIcon className="h-4 w-4" />
                <span>Copy</span>
              </>
            )}
          </button>
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
          <h2 className="text-xl font-bold text-black">
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
                    <span className="bg-green-100 text-green-800 text-xs font-medium px-2.5 py-0.5 rounded">
                      Source {index + 1}
                    </span>
                    <span className="font-medium text-black">
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
                    <div className="mb-6">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-sm font-medium text-gray-700">Content:</h4>
                        <button
                          onClick={() => copyChunkToClipboard(index, chunk.document)}
                          className="flex items-center space-x-1 px-2 py-1 text-xs font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-all duration-200"
                          title={chunkCopied.has(index) ? 'Copied!' : 'Copy chunk content'}
                        >
                          {chunkCopied.has(index) ? (
                            <>
                              <CheckIcon className="h-3 w-3 text-green-600" />
                              <span className="text-green-600">Copied!</span>
                            </>
                          ) : (
                            <>
                              <ClipboardIcon className="h-3 w-3" />
                              <span>Copy</span>
                            </>
                          )}
                        </button>
                      </div>
                      <div className="bg-gray-50 p-4 rounded-lg text-sm text-gray-800 whitespace-pre-wrap leading-relaxed border relative group">
                        {cleanChunkContent(chunk.document)}
                      </div>
                    </div>
                    
                    {/* Metadata */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-3">Metadata:</h4>
                      <div className="bg-white border rounded-lg p-4">
                        <div className="space-y-3">
                          {Object.entries(metadata).map(([key, value]) => {
                            const metadataKey = `${index}-${key}`
                            const isMetadataCopied = metadataCopied.has(metadataKey)
                            
                            return (
                              <div key={key} className="flex items-start justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors duration-200">
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center mb-1">
                                    <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                                      {key.replace(/_/g, ' ')}
                                    </span>
                                  </div>
                                  <div className="text-sm text-gray-900 break-words">
                                    {typeof value === 'object' ? (
                                      <pre className="text-xs bg-gray-100 p-2 rounded border overflow-x-auto">
                                        {JSON.stringify(value, null, 2)}
                                      </pre>
                                    ) : (
                                      <span className="font-mono">{String(value)}</span>
                                    )}
                                  </div>
                                </div>
                                <button
                                  onClick={() => copyMetadataItemToClipboard(key, value, index)}
                                  className="ml-3 flex items-center space-x-1 px-2 py-1 text-xs font-medium text-gray-400 hover:text-gray-600 hover:bg-white rounded transition-all duration-200 flex-shrink-0"
                                  title={isMetadataCopied ? 'Copied!' : `Copy ${key.replace(/_/g, ' ')}`}
                                >
                                  {isMetadataCopied ? (
                                    <>
                                      <CheckIcon className="h-3 w-3 text-green-600" />
                                      <span className="text-green-600 text-xs">✓</span>
                                    </>
                                  ) : (
                                    <>
                                      <ClipboardIcon className="h-3 w-3" />
                                    </>
                                  )}
                                </button>
                              </div>
                            )
                          })}
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
