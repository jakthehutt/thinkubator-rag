/**
 * Backend API configuration for different environments
 */

const config = {
  // Default backend URL for local development
  default: 'http://localhost:8000',
  
  // Environment-specific configurations
  development: 'http://localhost:8000',
  production: process.env.BACKEND_URL || 'http://backend:8000',
  
  // Fallback behavior
  fallbackToMock: true,
  timeout: 30000
}

/**
 * Get the appropriate backend URL for the current environment
 */
function getBackendUrl() {
  // Check for explicit BACKEND_URL environment variable
  if (process.env.BACKEND_URL) {
    return process.env.BACKEND_URL
  }
  
  // Use environment-specific URL
  const env = process.env.NODE_ENV || 'development'
  return config[env] || config.default
}

module.exports = {
  getBackendUrl,
  config
}
