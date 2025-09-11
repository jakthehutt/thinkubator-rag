/**
 * 🔍 Enhanced Frontend Logging Utility
 * 
 * Provides comprehensive logging for the Thinkubator RAG frontend
 * with detailed connection monitoring and performance tracking.
 */

export type LogLevel = 'debug' | 'info' | 'warn' | 'error'
export type LogCategory = 'api' | 'ui' | 'performance' | 'network' | 'backend' | 'general'

interface LogEntry {
  timestamp: string
  level: LogLevel
  category: LogCategory
  message: string
  data?: any
  sessionId?: string
  queryId?: string
}

class Logger {
  private logs: LogEntry[] = []
  private sessionId: string
  private isDev: boolean

  constructor() {
    this.sessionId = this.generateSessionId()
    this.isDev = process.env.NODE_ENV === 'development'
    this.log('info', 'general', '🚀 Logger initialized', { sessionId: this.sessionId })
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  private formatTimestamp(): string {
    return new Date().toISOString()
  }

  private log(level: LogLevel, category: LogCategory, message: string, data?: any, queryId?: string) {
    const entry: LogEntry = {
      timestamp: this.formatTimestamp(),
      level,
      category,
      message,
      data,
      sessionId: this.sessionId,
      queryId
    }

    this.logs.push(entry)

    // Keep only last 1000 logs to prevent memory issues
    if (this.logs.length > 1000) {
      this.logs = this.logs.slice(-1000)
    }

    // Console output with emoji and formatting
    const emoji = this.getEmoji(level, category)
    const categoryLabel = `[${category.toUpperCase()}]`
    const levelLabel = `[${level.toUpperCase()}]`
    
    if (this.isDev) {
      const consoleMethod = level === 'error' ? 'error' : level === 'warn' ? 'warn' : 'log'
      
      // Ultra-safe console logging - never pass objects directly
      try {
        if (data && typeof data === 'object' && !this.isEmptyObject(data)) {
          // Convert data to safe string representation
          const safeData = this.safeStringify(data)
          console[consoleMethod](`${emoji} ${levelLabel} ${categoryLabel} ${message}`, safeData)
        } else if (data && typeof data !== 'object') {
          // Handle primitive types safely
          console[consoleMethod](`${emoji} ${levelLabel} ${categoryLabel} ${message}`, String(data))
        } else {
          // No data or empty data
          console[consoleMethod](`${emoji} ${levelLabel} ${categoryLabel} ${message}`)
        }
      } catch (err) {
        // Ultimate fallback - never fails
        console[consoleMethod](`${emoji} ${levelLabel} ${categoryLabel} ${message} [data logging failed]`)
      }
    }
  }

  private isEmptyObject(obj: any): boolean {
    if (!obj || typeof obj !== 'object') return true
    if (Array.isArray(obj)) return obj.length === 0
    return Object.keys(obj).length === 0 || Object.getOwnPropertyNames(obj).length === 0
  }

  private safeStringify(data: any): string {
    try {
      // Handle different data types safely
      if (data === null || data === undefined) {
        return String(data)
      }
      
      if (typeof data === 'string' || typeof data === 'number' || typeof data === 'boolean') {
        return String(data)
      }
      
      if (data instanceof Error) {
        return `Error: ${data.message}`
      }
      
      // For objects/arrays, use safe JSON.stringify with fallback
      return JSON.stringify(data, this.getCircularReplacer(), 2)
    } catch (err) {
      // Final fallback for any stringify errors
      return `[Object: ${typeof data}]`
    }
  }

  private getCircularReplacer() {
    const seen = new WeakSet()
    return (key: string, value: any) => {
      if (typeof value === 'object' && value !== null) {
        if (seen.has(value)) {
          return '[Circular Reference]'
        }
        seen.add(value)
      }
      return value
    }
  }

  private getEmoji(level: LogLevel, category: LogCategory): string {
    const categoryEmojis: Record<LogCategory, string> = {
      api: '📡',
      ui: '🎨',
      performance: '⚡',
      network: '🌐',
      backend: '🔧',
      general: '📋'
    }

    const levelEmojis: Record<LogLevel, string> = {
      debug: '🐛',
      info: '💡',
      warn: '⚠️',
      error: '❌'
    }

    return `${categoryEmojis[category]} ${levelEmojis[level]}`
  }

  // Public logging methods
  debug(category: LogCategory, message: string, data?: any, queryId?: string) {
    this.log('debug', category, message, data, queryId)
  }

  info(category: LogCategory, message: string, data?: any, queryId?: string) {
    this.log('info', category, message, data, queryId)
  }

  warn(category: LogCategory, message: string, data?: any, queryId?: string) {
    this.log('warn', category, message, data, queryId)
  }

  error(category: LogCategory, message: string, data?: any, queryId?: string) {
    this.log('error', category, message, data, queryId)
  }

  // Specialized logging methods
  apiRequest(method: string, url: string, data?: any, queryId?: string) {
    this.info('api', `🚀 ${method} Request to ${url}`, { method, url, body: data }, queryId)
  }

  apiResponse(status: number, url: string, responseTime: number, data?: any, queryId?: string) {
    const level = status >= 400 ? 'error' : status >= 300 ? 'warn' : 'info'
    this.log(level, 'api', `📨 Response ${status} from ${url} (${responseTime}ms)`, 
      { status, url, responseTime, response: data }, queryId)
  }

  networkError(url: string, error: any, queryId?: string) {
    this.error('network', `🔌 Network error for ${url}`, { url, error: error.message || error }, queryId)
  }

  backendHealth(status: 'healthy' | 'unhealthy' | 'unknown', details?: any) {
    const level = status === 'healthy' ? 'info' : status === 'unhealthy' ? 'error' : 'warn'
    this.log(level, 'backend', `💗 Backend health: ${status}`, details)
  }

  performance(action: string, duration: number, details?: any, queryId?: string) {
    const level = duration > 5000 ? 'warn' : 'info'
    this.log(level, 'performance', `⏱️  ${action} completed in ${duration}ms`, 
      { action, duration, ...details }, queryId)
  }

  userAction(action: string, details?: any) {
    this.info('ui', `👤 User action: ${action}`, details)
  }

  // Utility methods
  getSessionId(): string {
    return this.sessionId
  }

  generateQueryId(): string {
    return `query_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`
  }

  getLogs(level?: LogLevel, category?: LogCategory): LogEntry[] {
    return this.logs.filter(log => 
      (!level || log.level === level) && 
      (!category || log.category === category)
    )
  }

  getLogsSummary(): { total: number, byLevel: Record<LogLevel, number>, byCategory: Record<LogCategory, number> } {
    const summary = {
      total: this.logs.length,
      byLevel: { debug: 0, info: 0, warn: 0, error: 0 } as Record<LogLevel, number>,
      byCategory: { api: 0, ui: 0, performance: 0, network: 0, backend: 0, general: 0 } as Record<LogCategory, number>
    }

    this.logs.forEach(log => {
      summary.byLevel[log.level]++
      summary.byCategory[log.category]++
    })

    return summary
  }

  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2)
  }
}

// Singleton instance
export const logger = new Logger()

// Convenience functions for common use cases
export const logApiRequest = (method: string, url: string, data?: any, queryId?: string) => 
  logger.apiRequest(method, url, data, queryId)

export const logApiResponse = (status: number, url: string, responseTime: number, data?: any, queryId?: string) =>
  logger.apiResponse(status, url, responseTime, data, queryId)

export const logNetworkError = (url: string, error: any, queryId?: string) =>
  logger.networkError(url, error, queryId)

export const logUserAction = (action: string, details?: any) =>
  logger.userAction(action, details)

export const logPerformance = (action: string, duration: number, details?: any, queryId?: string) =>
  logger.performance(action, duration, details, queryId)

export default logger
