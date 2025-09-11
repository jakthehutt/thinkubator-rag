import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Docker-compatible configuration
  output: 'standalone', // For Docker deployment
  
  // Enable experimental features for better performance
  experimental: {
    // Enable Turbopack for development
    turbo: {
      rules: {
        '*.svg': {
          loaders: ['@svgr/webpack'],
          as: '*.js',
        },
      },
    },
  },
  
  // Optional: configure for API routes if needed in future
  async rewrites() {
    return [
      // Example: proxy API calls to backend service in Docker setup
      // {
      //   source: '/api/:path*',
      //   destination: 'http://backend:8000/:path*',
      // },
    ];
  },
};

export default nextConfig;
