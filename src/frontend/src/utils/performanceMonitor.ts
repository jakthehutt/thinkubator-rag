/**
 * 🚀 Frontend Performance Monitor
 * 
 * Monitors and reports on frontend performance metrics
 */

import { logger, logPerformance } from './logger'

interface PerformanceMetrics {
  pageLoad: number
  firstContentfulPaint: number
  largestContentfulPaint: number
  firstInputDelay: number
  cumulativeLayoutShift: number
  apiResponseTime: number[]
  renderTime: number[]
  memoryUsage: number
}

class PerformanceMonitor {
  private metrics: Partial<PerformanceMetrics> = {
    apiResponseTime: [],
    renderTime: []
  }
  private isEnabled: boolean
  private observer: PerformanceObserver | null = null

  constructor() {
    this.isEnabled = process.env.NODE_ENV === 'development'
    
    if (this.isEnabled && typeof window !== 'undefined') {
      this.initializeMonitoring()
    }
  }

  private initializeMonitoring() {
    // Monitor page load performance
    this.monitorPageLoad()
    
    // Monitor Web Vitals
    this.monitorWebVitals()
    
    // Monitor memory usage periodically
    this.startMemoryMonitoring()
    
    logger.info('performance', '📊 Performance monitoring initialized')
  }

  private monitorPageLoad() {
    window.addEventListener('load', () => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
      
      if (navigation) {
        this.metrics.pageLoad = navigation.loadEventEnd - navigation.fetchStart
        
        logPerformance('page_load', this.metrics.pageLoad, {
          domContentLoaded: navigation.domContentLoadedEventEnd - navigation.fetchStart,
          firstByte: navigation.responseStart - navigation.fetchStart,
          domInteractive: navigation.domInteractive - navigation.fetchStart
        })
        
        logger.info('performance', '📄 Page load metrics captured', {
          pageLoad: this.metrics.pageLoad,
          domContentLoaded: navigation.domContentLoadedEventEnd - navigation.fetchStart,
          firstByte: navigation.responseStart - navigation.fetchStart
        })
      }
    })
  }

  private monitorWebVitals() {
    try {
      // Use PerformanceObserver if available
      if ('PerformanceObserver' in window) {
        // Monitor LCP (Largest Contentful Paint)
        const lcpObserver = new PerformanceObserver((entryList) => {
          const entries = entryList.getEntries()
          const lastEntry = entries[entries.length - 1] as any
          
          this.metrics.largestContentfulPaint = lastEntry.startTime
          logPerformance('largest_contentful_paint', lastEntry.startTime, {
            element: lastEntry.element?.tagName || 'unknown'
          })
        })
        
        lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true })
        
        // Monitor FID (First Input Delay)
        const fidObserver = new PerformanceObserver((entryList) => {
          const entries = entryList.getEntries()
          entries.forEach((entry: any) => {
            this.metrics.firstInputDelay = entry.processingStart - entry.startTime
            logPerformance('first_input_delay', this.metrics.firstInputDelay, {
              eventType: entry.name
            })
          })
        })
        
        fidObserver.observe({ type: 'first-input', buffered: true })
        
        // Monitor CLS (Cumulative Layout Shift)
        let clsValue = 0
        const clsObserver = new PerformanceObserver((entryList) => {
          entries.forEach((entry: any) => {
            if (!entry.hadRecentInput) {
              clsValue += entry.value
            }
          })
          
          this.metrics.cumulativeLayoutShift = clsValue
          if (clsValue > 0.1) { // Only log if CLS is concerning
            logPerformance('cumulative_layout_shift', clsValue, {
              threshold: 'concerning'
            })
          }
        })
        
        clsObserver.observe({ type: 'layout-shift', buffered: true })
        
        this.observer = lcpObserver // Keep reference for cleanup
      }
      
      // Monitor Paint Timing
      if ('PerformancePaintTiming' in window) {
        const paintEntries = performance.getEntriesByType('paint')
        paintEntries.forEach((entry) => {
          if (entry.name === 'first-contentful-paint') {
            this.metrics.firstContentfulPaint = entry.startTime
            logPerformance('first_contentful_paint', entry.startTime)
          }
        })
      }
      
    } catch (error) {
      logger.warn('performance', '⚠️ Web Vitals monitoring failed', { error })
    }
  }

  private startMemoryMonitoring() {
    if ('memory' in performance) {
      const checkMemory = () => {
        const memory = (performance as any).memory
        this.metrics.memoryUsage = memory.usedJSHeapSize / 1024 / 1024 // MB
        
        // Log memory usage if it's high
        if (this.metrics.memoryUsage > 50) { // More than 50MB
          logger.warn('performance', '🧠 High memory usage detected', {
            usedMB: Math.round(this.metrics.memoryUsage),
            totalMB: Math.round(memory.totalJSHeapSize / 1024 / 1024),
            limitMB: Math.round(memory.jsHeapSizeLimit / 1024 / 1024)
          })
        }
      }
      
      // Check memory every 30 seconds
      setInterval(checkMemory, 30000)
      checkMemory() // Initial check
    }
  }

  // Public methods for tracking specific metrics
  trackApiCall(responseTime: number, endpoint: string, success: boolean) {
    if (!this.isEnabled) return
    
    this.metrics.apiResponseTime = this.metrics.apiResponseTime || []
    this.metrics.apiResponseTime.push(responseTime)
    
    // Keep only last 50 measurements
    if (this.metrics.apiResponseTime.length > 50) {
      this.metrics.apiResponseTime = this.metrics.apiResponseTime.slice(-50)
    }
    
    // Calculate average response time
    const avgResponseTime = this.metrics.apiResponseTime.reduce((a, b) => a + b, 0) / this.metrics.apiResponseTime.length
    
    logPerformance('api_call', responseTime, {
      endpoint,
      success,
      averageResponseTime: Math.round(avgResponseTime),
      totalCalls: this.metrics.apiResponseTime.length
    })
    
    // Warn about slow API calls
    if (responseTime > 10000) { // More than 10 seconds
      logger.warn('performance', '🐌 Slow API call detected', {
        endpoint,
        responseTime,
        averageResponseTime: Math.round(avgResponseTime)
      })
    }
  }

  trackRenderTime(componentName: string, renderTime: number) {
    if (!this.isEnabled) return
    
    this.metrics.renderTime = this.metrics.renderTime || []
    this.metrics.renderTime.push(renderTime)
    
    // Keep only last 50 measurements
    if (this.metrics.renderTime.length > 50) {
      this.metrics.renderTime = this.metrics.renderTime.slice(-50)
    }
    
    logPerformance('component_render', renderTime, {
      component: componentName,
      averageRenderTime: Math.round(this.metrics.renderTime.reduce((a, b) => a + b, 0) / this.metrics.renderTime.length)
    })
    
    // Warn about slow renders
    if (renderTime > 100) { // More than 100ms
      logger.warn('performance', '🐌 Slow component render', {
        component: componentName,
        renderTime
      })
    }
  }

  // Get current metrics snapshot
  getMetrics(): Partial<PerformanceMetrics> {
    return { ...this.metrics }
  }

  // Get performance summary
  getPerformanceSummary() {
    const apiResponseTime = this.metrics.apiResponseTime || []
    const renderTime = this.metrics.renderTime || []
    
    return {
      pageLoad: this.metrics.pageLoad,
      webVitals: {
        fcp: this.metrics.firstContentfulPaint,
        lcp: this.metrics.largestContentfulPaint,
        fid: this.metrics.firstInputDelay,
        cls: this.metrics.cumulativeLayoutShift
      },
      api: {
        averageResponseTime: apiResponseTime.length > 0 
          ? Math.round(apiResponseTime.reduce((a, b) => a + b, 0) / apiResponseTime.length)
          : 0,
        totalCalls: apiResponseTime.length,
        slowCalls: apiResponseTime.filter(time => time > 5000).length
      },
      rendering: {
        averageRenderTime: renderTime.length > 0
          ? Math.round(renderTime.reduce((a, b) => a + b, 0) / renderTime.length)
          : 0,
        totalRenders: renderTime.length,
        slowRenders: renderTime.filter(time => time > 100).length
      },
      memory: {
        currentUsageMB: Math.round(this.metrics.memoryUsage || 0)
      }
    }
  }

  // Export performance data
  exportPerformanceData() {
    return JSON.stringify({
      timestamp: new Date().toISOString(),
      metrics: this.getMetrics(),
      summary: this.getPerformanceSummary(),
      userAgent: navigator.userAgent,
      url: window.location.href
    }, null, 2)
  }

  // Cleanup
  destroy() {
    if (this.observer) {
      this.observer.disconnect()
      this.observer = null
    }
    logger.info('performance', '🔄 Performance monitoring destroyed')
  }
}

// Singleton instance
export const performanceMonitor = new PerformanceMonitor()

// Convenience functions
export const trackApiCall = (responseTime: number, endpoint: string, success: boolean) =>
  performanceMonitor.trackApiCall(responseTime, endpoint, success)

export const trackRenderTime = (componentName: string, renderTime: number) =>
  performanceMonitor.trackRenderTime(componentName, renderTime)

export const getPerformanceSummary = () => performanceMonitor.getPerformanceSummary()

export default performanceMonitor
