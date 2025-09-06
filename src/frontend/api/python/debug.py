#!/usr/bin/env python3
"""
Diagnostic endpoint for debugging Vercel deployment issues.
"""

import os
import json

def handler(request):
    """Debug handler to check environment variables and configuration."""
    
    try:
        # Check environment variables
        env_check = {
            'has_gemini_key': bool(os.environ.get("GEMINI_API_KEY")),
            'has_supabase_url': bool(os.environ.get("SUPABASE_URL")),
            'has_supabase_service_key': bool(os.environ.get("SUPABASE_SERVICE_ROLE_KEY")),
            'has_supabase_anon_key': bool(os.environ.get("SUPABASE_ANON_KEY")),
            'environment': os.environ.get("NODE_ENV", "unknown"),
            'vercel_url': os.environ.get("VERCEL_URL", "not_set"),
            'python_path': os.environ.get("PYTHONPATH", "not_set")
        }
        
        # Get partial values (first 10 chars) for security
        env_values = {}
        for key in ["GEMINI_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_ANON_KEY"]:
            value = os.environ.get(key, "")
            if value:
                env_values[key] = value[:10] + "..." if len(value) > 10 else value
            else:
                env_values[key] = "NOT_SET"
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'message': 'Vercel Python Function Diagnostics',
                'environment_check': env_check,
                'environment_values': env_values,
                'status': 'diagnostic_complete'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': str(e),
                'message': 'Diagnostic failed'
            })
        }
