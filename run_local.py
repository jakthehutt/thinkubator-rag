#!/usr/bin/env python3
"""
Local development server script for Thinkubator RAG application.
This script provides both Streamlit and FastAPI options for local development.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def check_environment():
    """Check if all required packages are installed."""
    required_packages = [
        'streamlit', 'supabase', 'psycopg2', 'fastapi', 'uvicorn'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {missing_packages}")
        print("Run: pip install -r requirements.txt")
        return False
    
    return True

def check_env_file():
    """Check if .env file exists and has required variables."""
    env_path = project_root / '.env'
    if not env_path.exists():
        print("❌ .env file not found")
        return False
    
    # Check for required environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False
    
    print("✅ Environment variables configured")
    return True

def run_streamlit():
    """Run the Streamlit application."""
    print("🚀 Starting Streamlit application...")
    print("📍 URL: http://localhost:8501")
    print("Press Ctrl+C to stop\n")
    
    # Set environment variables for the subprocess
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    
    try:
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 
            str(project_root / 'src/frontend/app.py'),
            '--server.headless', 'false'
        ], env=env, cwd=project_root)
    except KeyboardInterrupt:
        print("\n👋 Streamlit application stopped")

def run_fastapi():
    """Run the FastAPI application."""
    print("🚀 Starting FastAPI application...")
    print("📍 URL: http://localhost:8000")
    print("📍 API: http://localhost:8000/api/")
    print("Press Ctrl+C to stop\n")
    
    # Set environment variables
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    
    try:
        subprocess.run([
            sys.executable, '-m', 'uvicorn', 'api.index:app',
            '--host', '0.0.0.0', '--port', '8000', '--reload'
        ], env=env, cwd=project_root)
    except KeyboardInterrupt:
        print("\n👋 FastAPI application stopped")

def main():
    """Main function to run the local development server."""
    print("🔍 THINKUBATOR RAG - LOCAL DEVELOPMENT")
    print("=" * 50)
    
    # Check environment
    print("\n1. Checking Python environment...")
    if not check_environment():
        return
    
    print("\n2. Checking configuration...")
    if not check_env_file():
        print("\nPlease ensure your .env file has the required variables:")
        print("- SUPABASE_URL")
        print("- SUPABASE_SERVICE_ROLE_KEY")
        print("- GEMINI_API_KEY (for full functionality)")
        return
    
    print("\n3. Choose your frontend:")
    print("   [1] Streamlit (Familiar interface)")
    print("   [2] FastAPI + Modern Web UI (Production-like)")
    
    while True:
        choice = input("\nEnter choice (1 or 2): ").strip()
        
        if choice == '1':
            run_streamlit()
            break
        elif choice == '2':
            run_fastapi()
            break
        else:
            print("Please enter 1 or 2")

if __name__ == "__main__":
    main()
