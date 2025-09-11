/**
 * Frontend-Backend Integration Tests
 * Tests the complete flow between Next.js frontend and FastAPI backend
 */

const { chromium } = require('playwright-chromium');

describe('Frontend-Backend Integration', () => {
  let browser;
  let page;
  const frontendUrl = process.env.FRONTEND_URL || 'http://localhost:3001';
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8001';

  beforeAll(async () => {
    browser = await chromium.launch({ headless: true });
    page = await browser.newPage();
  });

  afterAll(async () => {
    if (browser) {
      await browser.close();
    }
  });

  beforeEach(async () => {
    // Clear console logs and local storage
    await page.evaluate(() => {
      console.clear();
      localStorage.clear();
    });
  });

  test('Frontend loads successfully', async () => {
    await page.goto(frontendUrl);
    
    // Check page title
    const title = await page.title();
    expect(title).toContain('Thinkubator RAG Explorer');
    
    // Check for main components
    await expect(page.locator('h1:has-text("Knowledge Explorer")')).toBeVisible();
    await expect(page.locator('input[placeholder*="circular economy"]')).toBeVisible();
    await expect(page.locator('button:has-text("Search")')).toBeVisible();
  });

  test('Backend health endpoint is accessible', async () => {
    const response = await page.request.get(`${backendUrl}/health`);
    expect(response.status()).toBe(200);
    
    const health = await response.json();
    expect(health.status).toBe('healthy');
    expect(health.pipeline_initialized).toBe(true);
  });

  test('Query submission works end-to-end', async () => {
    await page.goto(frontendUrl);
    
    // Set up network monitoring
    const responses = [];
    page.on('response', response => {
      if (response.url().includes('/query')) {
        responses.push(response);
      }
    });

    // Fill in query
    const testQuery = 'What is circular economy?';
    await page.fill('input[placeholder*="circular economy"]', testQuery);
    
    // Submit form
    await page.click('button:has-text("Search")');
    
    // Wait for loading state
    await expect(page.locator('text=Processing your query')).toBeVisible();
    
    // Wait for results (up to 30 seconds for RAG processing)
    await expect(page.locator('text=Answer')).toBeVisible({ timeout: 30000 });
    
    // Verify response structure
    const answerSection = page.locator('div:has(h2:text("Answer"))');
    await expect(answerSection).toBeVisible();
    
    const sourcesSection = page.locator('div:has(h2:text("Sources"))');
    await expect(sourcesSection).toBeVisible();
    
    // Check that we got a network response
    expect(responses.length).toBeGreaterThan(0);
    expect(responses[0].status()).toBe(200);
    
    // Verify answer content exists and is not empty
    const answerText = await page.locator('div.prose div.whitespace-pre-wrap').textContent();
    expect(answerText.trim().length).toBeGreaterThan(50);
  });

  test('Error handling works correctly', async () => {
    await page.goto(frontendUrl);
    
    // Intercept network request and force it to fail
    await page.route('**/query', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Test error message' })
      });
    });
    
    // Submit query
    await page.fill('input[placeholder*="circular economy"]', 'Test error query');
    await page.click('button:has-text("Search")');
    
    // Wait for error to appear
    await expect(page.locator('text=Query Failed')).toBeVisible();
    await expect(page.locator('text=Test error message')).toBeVisible();
  });

  test('Sample queries work correctly', async () => {
    await page.goto(frontendUrl);
    
    // Click on first sample query
    const sampleButton = page.locator('button:has-text("What is the circularity gap?")').first();
    await sampleButton.click();
    
    // Verify input field is filled
    const inputValue = await page.inputValue('input[placeholder*="circular economy"]');
    expect(inputValue).toBe('What is the circularity gap?');
  });

  test('Loading states work correctly', async () => {
    await page.goto(frontendUrl);
    
    // Intercept request to add delay
    await page.route('**/query', async route => {
      // Add 2 second delay to see loading state
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.continue();
    });
    
    // Submit query
    await page.fill('input[placeholder*="circular economy"]', 'Test loading');
    await page.click('button:has-text("Search")');
    
    // Check loading states
    await expect(page.locator('button:has-text("Thinking...")')).toBeVisible();
    await expect(page.locator('text=Processing your query')).toBeVisible();
    
    // Button should be disabled during loading
    const submitButton = page.locator('button:has-text("Thinking...")');
    expect(await submitButton.isDisabled()).toBe(true);
  });

  test('Responsive design works on mobile', async () => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(frontendUrl);
    
    // Check that mobile layout loads correctly
    await expect(page.locator('h1:has-text("Knowledge Explorer")')).toBeVisible();
    await expect(page.locator('input[placeholder*="circular economy"]')).toBeVisible();
    
    // Test that query still works on mobile
    await page.fill('input[placeholder*="circular economy"]', 'Mobile test');
    await page.click('button:has-text("Search")');
    
    await expect(page.locator('text=Processing your query')).toBeVisible();
  });

  test('Console logs are working for debugging', async () => {
    await page.goto(frontendUrl);
    
    const logs = [];
    page.on('console', msg => {
      logs.push(msg.text());
    });
    
    // Submit query to generate logs
    await page.fill('input[placeholder*="circular economy"]', 'Debug test');
    await page.click('button:has-text("Search")');
    
    // Wait a bit for logs
    await page.waitForTimeout(1000);
    
    // Check that our debug logs are present
    const hasStartingLog = logs.some(log => log.includes('🔍 Starting query'));
    const hasApiRequestLog = logs.some(log => log.includes('📡 Making API request'));
    
    expect(hasStartingLog).toBe(true);
    expect(hasApiRequestLog).toBe(true);
  });
});
