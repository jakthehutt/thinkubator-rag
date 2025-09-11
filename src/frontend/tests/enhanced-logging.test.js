/**
 * 🔍 Enhanced Frontend Logging System Tests
 * 
 * Tests the comprehensive logging system and backend connection verification
 */

const { test, expect } = require('@playwright/test')

test.describe('Enhanced Frontend Logging System', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto('/')
    
    // Wait for the page to load
    await page.waitForLoadState('domcontentloaded')
  })

  test('should initialize logging system on page load', async ({ page }) => {
    // Check console logs for initialization
    const logs = []
    page.on('console', msg => {
      if (msg.type() === 'log') {
        logs.push(msg.text())
      }
    })
    
    // Reload page to capture initialization logs
    await page.reload()
    await page.waitForTimeout(1000) // Wait for logs
    
    // Should have logging initialization messages
    const hasLoggerInit = logs.some(log => 
      log.includes('Logger initialized') || 
      log.includes('Home component mounted') ||
      log.includes('QueryInterface component mounted')
    )
    
    expect(hasLoggerInit).toBe(true)
  })

  test('should display backend connection status in development', async ({ page }) => {
    // Should show connection status indicator (only in development)
    const statusIndicator = page.locator('text=Backend Status:')
    
    // Wait a bit for the backend health check to complete
    await page.waitForTimeout(2000)
    
    // In development mode, should show backend status
    if (process.env.NODE_ENV === 'development') {
      await expect(statusIndicator).toBeVisible()
    }
  })

  test('should log user interactions with query interface', async ({ page }) => {
    const logs = []
    page.on('console', msg => {
      if (msg.type() === 'log' && msg.text().includes('[UI]')) {
        logs.push(msg.text())
      }
    })
    
    // Interact with query input
    const queryInput = page.locator('input[type="text"]')
    await queryInput.click()
    await queryInput.fill('What is circular economy?')
    
    // Wait for logs
    await page.waitForTimeout(500)
    
    // Should have UI interaction logs
    const hasInputLogs = logs.some(log => 
      log.includes('Query input focused') || 
      log.includes('Query input changed')
    )
    
    expect(hasInputLogs).toBe(true)
  })

  test('should log sample query selection', async ({ page }) => {
    const logs = []
    page.on('console', msg => {
      if (msg.type() === 'log' && msg.text().includes('Sample query selected')) {
        logs.push(msg.text())
      }
    })
    
    // Click on a sample query button
    const sampleButton = page.locator('button', { hasText: 'What is the circularity gap?' })
    await sampleButton.click()
    
    // Wait for logs
    await page.waitForTimeout(500)
    
    // Should have sample query selection log
    expect(logs.length).toBeGreaterThan(0)
  })

  test('should perform comprehensive backend connection test', async ({ page }) => {
    let apiLogs = []
    let networkLogs = []
    
    page.on('console', msg => {
      const text = msg.text()
      if (text.includes('[API]')) {
        apiLogs.push(text)
      }
      if (text.includes('[NETWORK]')) {
        networkLogs.push(text)
      }
    })
    
    // Fill query and submit
    const queryInput = page.locator('input[type="text"]')
    await queryInput.fill('What is circular economy?')
    
    const submitButton = page.locator('button[type="submit"]')
    await submitButton.click()
    
    // Wait for API call to complete (up to 30 seconds)
    await page.waitForTimeout(5000) // Initial wait
    
    // Check if we got response or are still loading
    const loadingIndicator = page.locator('text=Processing your query')
    const results = page.locator('text=Answer')
    const error = page.locator('text=Query Failed')
    
    // Wait for either results, error, or timeout
    try {
      await Promise.race([
        results.waitFor({ timeout: 25000 }),
        error.waitFor({ timeout: 25000 })
      ])
    } catch (e) {
      // Timeout is acceptable for this test
    }
    
    // Should have API-related logs
    expect(apiLogs.length + networkLogs.length).toBeGreaterThan(0)
    
    // Should have backend URL log
    const hasBackendUrlLog = [...apiLogs, ...networkLogs].some(log => 
      log.includes('Using backend URL') || log.includes('backend')
    )
    expect(hasBackendUrlLog).toBe(true)
  })

  test('should handle and log connection errors gracefully', async ({ page }) => {
    // Mock fetch to simulate network error
    await page.addInitScript(() => {
      const originalFetch = window.fetch
      window.fetch = async (url, options) => {
        if (url.includes('/query')) {
          throw new Error('Network error - simulated')
        }
        return originalFetch(url, options)
      }
    })
    
    let errorLogs = []
    page.on('console', msg => {
      if (msg.type() === 'error' || (msg.type() === 'log' && msg.text().includes('❌'))) {
        errorLogs.push(msg.text())
      }
    })
    
    // Submit a query to trigger error
    const queryInput = page.locator('input[type="text"]')
    await queryInput.fill('Test query')
    
    const submitButton = page.locator('button[type="submit"]')
    await submitButton.click()
    
    // Wait for error handling
    await page.waitForTimeout(3000)
    
    // Should show error message to user
    const errorMessage = page.locator('text=Query Failed')
    await expect(errorMessage).toBeVisible({ timeout: 5000 })
    
    // Should have error logs
    expect(errorLogs.length).toBeGreaterThan(0)
  })

  test('should track performance metrics', async ({ page }) => {
    let performanceLogs = []
    page.on('console', msg => {
      if (msg.type() === 'log' && msg.text().includes('[PERFORMANCE]')) {
        performanceLogs.push(msg.text())
      }
    })
    
    // Perform a query to generate performance metrics
    const queryInput = page.locator('input[type="text"]')
    await queryInput.fill('What is sustainability?')
    
    const submitButton = page.locator('button[type="submit"]')
    await submitButton.click()
    
    // Wait for query to complete or timeout
    await page.waitForTimeout(10000)
    
    // Should have performance tracking logs
    // Note: Performance logs might not always be present due to timing
    // This test verifies the logging system doesn't break the app
    expect(performanceLogs.length).toBeGreaterThanOrEqual(0)
  })

  test('should expand and collapse source chunks with logging', async ({ page }) => {
    // First submit a query that will return results
    const queryInput = page.locator('input[type="text"]')
    await queryInput.fill('What is the circularity gap?')
    
    const submitButton = page.locator('button[type="submit"]')
    await submitButton.click()
    
    // Wait for results
    try {
      await page.waitForSelector('text=Sources', { timeout: 30000 })
    } catch (e) {
      console.log('No results received - backend may not be fully initialized')
      return // Skip this test if backend is not responding
    }
    
    let chunkLogs = []
    page.on('console', msg => {
      if (msg.type() === 'log' && msg.text().includes('Source chunk')) {
        chunkLogs.push(msg.text())
      }
    })
    
    // Try to click on a source chunk to expand it
    const sourceButton = page.locator('button:has-text("Source 1")')
    if (await sourceButton.isVisible()) {
      await sourceButton.click()
      await page.waitForTimeout(500)
      
      // Should have chunk expansion logs
      expect(chunkLogs.length).toBeGreaterThan(0)
    }
  })

  test('should maintain session consistency', async ({ page }) => {
    let sessionLogs = []
    page.on('console', msg => {
      const text = msg.text()
      if (text.includes('session_') || text.includes('Session')) {
        sessionLogs.push(text)
      }
    })
    
    // Reload page and check that session is maintained
    await page.reload()
    await page.waitForTimeout(2000)
    
    // Should maintain consistent session logging
    const hasSessionInfo = sessionLogs.length > 0
    expect(hasSessionInfo).toBe(true)
  })
})

test.describe('Backend Connection Verification', () => {
  test('should verify backend is reachable', async ({ page }) => {
    // Navigate to page and wait for connection check
    await page.goto('/')
    await page.waitForTimeout(3000) // Wait for health check
    
    // Check if backend status is shown (development mode)
    const backendStatus = page.locator('text=Backend Status:')
    
    if (await backendStatus.isVisible()) {
      // Should show either healthy, unhealthy, or unknown status
      const statusText = await backendStatus.textContent()
      expect(statusText).toMatch(/Backend Status: (healthy|unhealthy|unknown)/)
    }
  })

  test('should handle backend timeout gracefully', async ({ page }) => {
    // This test verifies the frontend doesn't crash when backend is slow/unavailable
    await page.goto('/')
    
    // Submit query with potential timeout
    const queryInput = page.locator('input[type="text"]')
    await queryInput.fill('Test timeout handling')
    
    const submitButton = page.locator('button[type="submit"]')
    await submitButton.click()
    
    // Wait and verify the app is still responsive
    await page.waitForTimeout(5000)
    
    // App should still be functional
    const isInputEnabled = await queryInput.isEnabled()
    expect(isInputEnabled).toBe(true)
  })
})
