#!/usr/bin/env python3
"""
Vercel Python serverless function using unified handler for consistency.
"""

import os
import json
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

# Import the unified handler
from src.backend.api.unified_handler import handle_request

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests using unified handler."""
        print("🔍 [HANDLER] GET request received")
        
        try:
            # Use unified handler for GET requests
            request_data = {
                'method': 'GET',
                'path': self.path
            }
            response = handle_request(request_data)
            
            self.send_response(response['statusCode'])
            for header, value in response['headers'].items():
                self.send_header(header, value)
            self.end_headers()
            self.wfile.write(response['body'].encode())
            
        except Exception as e:
            print(f"❌ [HANDLER] GET request error: {str(e)}")
            self._send_error_response(500, f"Internal server error: {str(e)}")

    def do_POST(self):
        """Handle POST requests using unified handler."""
        print("=" * 60)
        print("🚀 [HANDLER] Vercel Python Function POST Started (Unified Handler)")
        print("=" * 60)
        
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            print(f"🔍 [HANDLER] Content-Length: {content_length}")
            print(f"🔍 [HANDLER] Raw body: {post_data}")
            
            # Environment diagnostics
            print("🔍 [HANDLER] Environment Variables:")
            print(f"  - NODE_ENV: {os.environ.get('NODE_ENV', 'not_set')}")
            print(f"  - VERCEL: {os.environ.get('VERCEL', 'not_set')}")
            print(f"  - VERCEL_URL: {os.environ.get('VERCEL_URL', 'not_set')}")
            print(f"  - Has GEMINI_API_KEY: {bool(os.environ.get('GEMINI_API_KEY'))}")
            print(f"  - Has SUPABASE_URL: {bool(os.environ.get('SUPABASE_URL'))}")
            print(f"  - Has SUPABASE_SERVICE_ROLE_KEY: {bool(os.environ.get('SUPABASE_SERVICE_ROLE_KEY'))}")
            print(f"  - Has SUPABASE_ANON_KEY: {bool(os.environ.get('SUPABASE_ANON_KEY'))}")
            
            # Use unified handler for POST requests
            request_data = {
                'method': 'POST',
                'body': post_data.decode('utf-8')
            }
            
            print("🚀 [HANDLER] Calling unified handler...")
            response = handle_request(request_data)
            
            print(f"✅ [HANDLER] Unified handler response status: {response['statusCode']}")
            
            # Send response
            self.send_response(response['statusCode'])
            for header, value in response['headers'].items():
                self.send_header(header, value)
            self.end_headers()
            self.wfile.write(response['body'].encode())
            
            print("✅ [HANDLER] Response sent successfully")
                
        except Exception as e:
            print(f"❌ [HANDLER] General error: {str(e)}")
            print(f"❌ [HANDLER] Error type: {type(e).__name__}")
            self._send_error_response(500, f"Internal server error: {str(e)}")
        finally:
            print("🏁 [HANDLER] Function execution completed")
            print("=" * 60)

    def _send_error_response(self, status_code, message):
        """Send an error JSON response."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        error_data = {"detail": message}
        self.wfile.write(json.dumps(error_data).encode())
