import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Optimize bundle size for Vercel functions
  outputFileTracing: true,
  outputFileTracingExcludes: {
    // Exclude large directories from Python function bundle
    'api/python.py': [
      '**/node_modules/**',
      '**/.next/**',
      '**/src/backend/tests/**',
      '**/data/**',
      '**/scripts/**',
      '**/make/**',
      '**/*.md',
      '**/requirements.txt',
      '**/setup.py',
      '**/src/thinkubator_rag.egg-info/**'
    ]
  }
};

export default nextConfig;
