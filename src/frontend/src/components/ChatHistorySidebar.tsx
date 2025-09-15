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
  onSessionDeleted?: (sessionId: string) => void // Callback when session is deleted
}

export function ChatHistorySidebar({ onSessionSelect, selectedSessionId, refreshTrigger, clearLoadingSession, onSessionDeleted }: ChatHistorySidebarProps) {
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [loadingSessionId, setLoadingSessionId] = useState<string | null>(null)
  const [deletingSessionId, setDeletingSessionId] = useState<string | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null)

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
      logger.info('ui', '✅ Chat history fetched successfully', { 
        count: data.sessions.length,
        storage_available: data.storage_available 
      })
      
      setSessions(data.sessions)
      
      // Show message if storage is unavailable but request succeeded
      if (data.message && !data.storage_available) {
        logger.warn('ui', '⚠️ Chat history service degraded', { message: data.message })
      }
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch chat history'
      logger.error('ui', '❌ Failed to fetch chat history', { error: errorMessage })
      
      // More user-friendly error messages
      if (errorMessage.includes('Failed to fetch')) {
        setError('Unable to connect to chat history service. Please check your connection.')
      } else if (errorMessage.includes('503')) {
        setError('Chat history service is temporarily unavailable. Please try again later.')
      } else {
        setError(errorMessage)
      }
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

  const handleDeleteClick = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation() // Prevent session selection
    logger.info('ui', '🗑️ Delete chat session requested', { sessionId })
    setShowDeleteConfirm(sessionId)
  }

  const confirmDelete = async (sessionId: string) => {
    setDeletingSessionId(sessionId)
    setShowDeleteConfirm(null)
    
    try {
      logger.info('ui', '🗑️ Deleting chat session...', { sessionId })
      const backendUrl = getBackendUrl()
      
      const response = await fetch(`${backendUrl}/session/${sessionId}`, {
        method: 'DELETE',
      })
      
      if (!response.ok) {
        throw new Error(`Failed to delete session: ${response.status} ${response.statusText}`)
      }
      
      logger.info('ui', '✅ Chat session deleted successfully', { sessionId })
      logUserAction('delete_chat_session', { sessionId })
      
      // Remove session from local state
      setSessions(prev => prev.filter(session => session.id !== sessionId))
      
      // Notify parent component
      if (onSessionDeleted) {
        onSessionDeleted(sessionId)
      }
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete session'
      logger.error('ui', '❌ Failed to delete chat session', { error: errorMessage, sessionId })
      setError(`Failed to delete conversation: ${errorMessage}`)
    } finally {
      setDeletingSessionId(null)
    }
  }

  const cancelDelete = () => {
    setShowDeleteConfirm(null)
    logger.info('ui', '❌ Delete chat session cancelled')
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
              <div key={session.id} className="mb-2">
                <div
                  onClick={() => handleSessionClick(session)}
                  className={`p-3 rounded-lg border cursor-pointer transition-all hover:shadow-md relative ${
                    selectedSessionId === session.id
                      ? 'border-green-500 bg-green-50 shadow-sm'
                      : 'border-gray-200 hover:border-green-300 hover:bg-gray-50'
                  } ${loadingSessionId === session.id ? 'opacity-60' : ''} ${
                    deletingSessionId === session.id ? 'opacity-50' : ''
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1 min-w-0 flex items-center">
                      {loadingSessionId === session.id && (
                        <div className="animate-spin rounded-full h-3 w-3 border border-green-500 border-t-transparent mr-2 flex-shrink-0"></div>
                      )}
                      {deletingSessionId === session.id && (
                        <div className="animate-spin rounded-full h-3 w-3 border border-red-500 border-t-transparent mr-2 flex-shrink-0"></div>
                      )}
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {truncateQuery(session.preview)}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2 ml-2">
                      <span className="text-xs text-gray-500 whitespace-nowrap">
                        {formatDate(session.created_at)}
                      </span>
                      <button
                        onClick={(e) => handleDeleteClick(e, session.id)}
                        className="p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors duration-200"
                        title="Delete conversation"
                        disabled={deletingSessionId === session.id}
                      >
                        {deletingSessionId === session.id ? (
                          <div className="w-4 h-4 animate-spin border border-red-500 border-t-transparent rounded-full"></div>
                        ) : (
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        )}
                      </button>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>{session.chunks_count} sources</span>
                    <div className="flex items-center">
                      {loadingSessionId === session.id ? (
                        <span className="text-green-600">Loading...</span>
                      ) : deletingSessionId === session.id ? (
                        <span className="text-red-600">Deleting...</span>
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

                {/* Delete Confirmation Dialog */}
                {showDeleteConfirm === session.id && (
                  <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex items-start space-x-2">
                      <div className="flex-shrink-0 mt-0.5">
                        <svg className="w-4 h-4 text-red-500" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                        </svg>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-red-800 font-medium mb-1">Delete this conversation?</p>
                        <p className="text-xs text-red-600 mb-3">This action cannot be undone.</p>
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => confirmDelete(session.id)}
                            className="px-3 py-1 text-xs font-medium text-white bg-red-600 hover:bg-red-700 rounded transition-colors duration-200"
                          >
                            Delete
                          </button>
                          <button
                            onClick={cancelDelete}
                            className="px-3 py-1 text-xs font-medium text-gray-700 bg-gray-200 hover:bg-gray-300 rounded transition-colors duration-200"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    </div>
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
