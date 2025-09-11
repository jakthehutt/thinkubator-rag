'use client'

import { useState, useEffect } from 'react'
import { logger, logUserAction } from '@/utils/logger'

export interface ChatSession {
  id: string
  query: string
  answer: string
  user_id: string
  user_name: string
  processing_time_ms: number
  created_at: string
  chunks_count: number
  preview: string
}

interface ChatHistorySidebarProps {
  onSessionSelect: (session: ChatSession) => void
  selectedSessionId?: string
  refreshTrigger?: number // Used to trigger refresh from parent
  clearLoadingSession?: () => void // Callback to clear loading state
}

export function ChatHistorySidebar({ onSessionSelect, selectedSessionId, refreshTrigger, clearLoadingSession }: ChatHistorySidebarProps) {
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [loadingSessionId, setLoadingSessionId] = useState<string | null>(null)

  const getBackendUrl = (): string => {
    if (typeof window !== 'undefined') {
      return process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001'
    } else {
      return process.env.NEXT_PUBLIC_BACKEND_URL || 'http://backend:8000'
    }
  }

  const fetchSessions = async () => {
    setLoading(true)
    setError(null)
    
    try {
      logger.info('ui', '🔄 Fetching chat history...')
      const backendUrl = getBackendUrl()
      
      const response = await fetch(`${backendUrl}/user/current/sessions?limit=50`)
      
      if (!response.ok) {
        throw new Error(`Failed to fetch sessions: ${response.status} ${response.statusText}`)
      }
      
      const data = await response.json()
      logger.info('ui', '✅ Chat history fetched successfully', { count: data.sessions.length })
      
      setSessions(data.sessions)
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch chat history'
      logger.error('ui', '❌ Failed to fetch chat history', { error: errorMessage })
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  // Fetch sessions on component mount and when refreshTrigger changes
  useEffect(() => {
    fetchSessions()
  }, [refreshTrigger])

  // Clear loading state when session selection changes
  useEffect(() => {
    if (selectedSessionId && loadingSessionId === selectedSessionId) {
      // Session has been loaded, clear loading state
      setLoadingSessionId(null)
    }
  }, [selectedSessionId, loadingSessionId])

  const handleSessionClick = (session: ChatSession) => {
    logger.info('ui', '📜 Chat session selected', { sessionId: session.id })
    logUserAction('select_chat_history', { sessionId: session.id, query: session.preview })
    
    // Set loading state for this specific session
    setLoadingSessionId(session.id)
    
    // Call parent handler - this will reset loading state when done
    onSessionSelect(session)
    
    // Reset loading state after a reasonable timeout as fallback
    setTimeout(() => {
      setLoadingSessionId(null)
    }, 5000)
  }

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString)
      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
      const diffDays = Math.floor(diffHours / 24)
      
      if (diffHours < 1) {
        const diffMins = Math.floor(diffMs / (1000 * 60))
        return diffMins < 1 ? 'Just now' : `${diffMins}m ago`
      } else if (diffHours < 24) {
        return `${diffHours}h ago`
      } else if (diffDays < 7) {
        return `${diffDays}d ago`
      } else {
        return date.toLocaleDateString()
      }
    } catch {
      return 'Unknown'
    }
  }

  const truncateQuery = (query: string, maxLength: number = 60) => {
    return query.length > maxLength ? query.substring(0, maxLength) + '...' : query
  }

  if (isCollapsed) {
    return (
      <div className="w-12 bg-gray-50 border-r border-gray-200 flex flex-col items-center py-4">
        <button
          onClick={() => setIsCollapsed(false)}
          className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
          title="Show chat history"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
        
        <div className="mt-4 flex flex-col items-center space-y-2">
          {sessions.slice(0, 3).map((session) => (
            <div
              key={session.id}
              className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center cursor-pointer hover:bg-green-200"
              onClick={() => handleSessionClick(session)}
              title={session.preview}
            >
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            </div>
          ))}
          {sessions.length > 3 && (
            <div className="text-xs text-gray-400 font-medium">
              +{sessions.length - 3}
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="w-80 bg-white border-r border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Chat History</h2>
          <p className="text-sm text-gray-500">{sessions.length} conversations</p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={fetchSessions}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
            title="Refresh"
            disabled={loading}
          >
            <svg 
              className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
          <button
            onClick={() => setIsCollapsed(true)}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
            title="Collapse sidebar"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-4 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mx-auto mb-2"></div>
            <p className="text-sm text-gray-500">Loading chat history...</p>
          </div>
        ) : error ? (
          <div className="p-4 text-center">
            <div className="text-red-500 mb-2">
              <svg className="w-8 h-8 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-sm text-gray-500 mb-3">{error}</p>
            <button
              onClick={fetchSessions}
              className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded-md hover:bg-red-200 transition-colors"
            >
              Retry
            </button>
          </div>
        ) : sessions.length === 0 ? (
          <div className="p-4 text-center">
            <div className="text-gray-400 mb-2">
              <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <p className="text-sm text-gray-500 mb-1">No conversations yet</p>
            <p className="text-xs text-gray-400">Start a conversation to see your chat history</p>
          </div>
        ) : (
          <div className="p-2">
            {sessions.map((session) => (
              <div
                key={session.id}
                onClick={() => handleSessionClick(session)}
                className={`mb-2 p-3 rounded-lg border cursor-pointer transition-all hover:shadow-md ${
                  selectedSessionId === session.id
                    ? 'border-green-500 bg-green-50 shadow-sm'
                    : 'border-gray-200 hover:border-green-300 hover:bg-gray-50'
                } ${loadingSessionId === session.id ? 'opacity-60' : ''}`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1 min-w-0 flex items-center">
                    {loadingSessionId === session.id && (
                      <div className="animate-spin rounded-full h-3 w-3 border border-green-500 border-t-transparent mr-2 flex-shrink-0"></div>
                    )}
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {truncateQuery(session.preview)}
                    </p>
                  </div>
                  <span className="ml-2 text-xs text-gray-500 whitespace-nowrap">
                    {formatDate(session.created_at)}
                  </span>
                </div>
                
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>{session.chunks_count} sources</span>
                  <div className="flex items-center">
                    {loadingSessionId === session.id ? (
                      <span className="text-green-600">Loading...</span>
                    ) : (
                      <span>{session.processing_time_ms}ms</span>
                    )}
                  </div>
                </div>
                
                {session.user_name && (
                  <div className="mt-1 flex items-center text-xs text-gray-400">
                    <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                    </svg>
                    {session.user_name}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
