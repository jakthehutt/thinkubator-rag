#!/usr/bin/env python3
"""
Enhanced local development server with Vercel simulation and debugging.
"""

import os
import sys
import subprocess
import time
import threading
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def check_vercel_cli():
    """Check if Vercel CLI is installed."""
    try:
        result = subprocess.run(['vercel', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Vercel CLI: {result.stdout.strip()}")
            return True
        else:
            print("❌ Vercel CLI not found")
            return False
    except FileNotFoundError:
        print("❌ Vercel CLI not installed")
        return False

def run_vercel_dev():
    """Run Vercel development server."""
    print("🚀 Starting Vercel development server...")
    print("📍 URL: http://localhost:3000")
    print("📍 Python API: http://localhost:3000/api/python/query")
    print("Press Ctrl+C to stop\n")
    
    # Set environment variables
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    env['DEBUG'] = 'true'
    
    try:
        subprocess.run([
            'vercel', 'dev', '--listen', '3000'
        ], env=env, cwd=project_root / 'src' / 'frontend')
    except KeyboardInterrupt:
        print("\n👋 Vercel development server stopped")

def run_fastapi():
    """Run FastAPI backend."""
    print("🚀 Starting FastAPI backend...")
    print("📍 URL: http://localhost:8000")
    print("📍 API: http://localhost:8000/query")
    print("Press Ctrl+C to stop\n")
    
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    
    try:
        subprocess.run([
            sys.executable, '-m', 'uvicorn', 'api.index:app',
            '--host', '0.0.0.0', '--port', '8000', '--reload'
        ], env=env, cwd=project_root)
    except KeyboardInterrupt:
        print("\n👋 FastAPI backend stopped")

def run_nextjs():
    """Run Next.js development server."""
    print("🚀 Starting Next.js development server...")
    print("📍 URL: http://localhost:3000")
    print("Press Ctrl+C to stop\n")
    
    env = os.environ.copy()
    env['DEBUG'] = 'true'
    
    try:
        subprocess.run([
            'npm', 'run', 'dev'
        ], env=env, cwd=project_root / 'src' / 'frontend')
    except KeyboardInterrupt:
        print("\n👋 Next.js development server stopped")

def main():
    """Main function with enhanced options."""
    print("🔍 THINKUBATOR RAG - ENHANCED LOCAL DEVELOPMENT")
    print("=" * 60)
    
    print("\n1. Checking environment...")
    vercel_available = check_vercel_cli()
    
    print("\n2. Choose development mode:")
    print("   [1] Vercel Dev (Full Vercel simulation)")
    print("   [2] Next.js + FastAPI (Separate servers)")
    print("   [3] Next.js only (Frontend only)")
    print("   [4] FastAPI only (Backend only)")
    
    while True:
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == '1' and vercel_available:
            run_vercel_dev()
            break
        elif choice == '1' and not vercel_available:
            print("❌ Vercel CLI not available. Install with: npm install -g vercel")
            continue
        elif choice == '2':
            print("🚀 Starting both servers...")
            # Start FastAPI in background
            fastapi_thread = threading.Thread(target=run_fastapi)
            fastapi_thread.daemon = True
            fastapi_thread.start()
            
            # Wait a bit for FastAPI to start
            time.sleep(3)
            
            # Start Next.js
            run_nextjs()
            break
        elif choice == '3':
            run_nextjs()
            break
        elif choice == '4':
            run_fastapi()
            break
        else:
            print("Please enter 1-4")

if __name__ == "__main__":
    main()

