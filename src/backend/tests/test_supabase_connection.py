#!/usr/bin/env python3
"""
Early tests for Supabase database connection and vector operations.
Run these tests first to ensure Supabase is properly configured.
"""

import pytest
import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(dotenv_path=project_root / '.env')

class TestSupabaseConnection:
    """Test suite for Supabase database connection and setup."""
    
    @pytest.fixture(scope="class")
    def supabase_client(self):
        """Create Supabase client for testing."""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            pytest.skip("Supabase credentials not configured")
        
        return create_client(supabase_url, supabase_key)
    
    @pytest.fixture(scope="class")
    def postgres_connection(self):
        """Create direct PostgreSQL connection for testing."""
        postgres_url = os.getenv("POSTGRES_URL_NON_POOLING")
        
        if not postgres_url:
            pytest.skip("PostgreSQL URL not configured")
        
        try:
            conn = psycopg2.connect(postgres_url)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            yield conn
        finally:
            if conn:
                conn.close()
    
    def test_supabase_client_creation(self, supabase_client):
        """Test that Supabase client can be created successfully."""
        assert supabase_client is not None
        assert hasattr(supabase_client, 'table')
        assert hasattr(supabase_client, 'auth')
    
    def test_postgres_connection(self, postgres_connection):
        """Test direct PostgreSQL connection."""
        cursor = postgres_connection.cursor()
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()
        assert result[0] == 1
        cursor.close()
    
    def test_pgvector_extension_available(self, postgres_connection):
        """Test if pgvector extension can be enabled."""
        cursor = postgres_connection.cursor()
        
        try:
            # Try to create the extension if it doesn't exist
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            # Verify the extension is installed
            cursor.execute("""
                SELECT extname FROM pg_extension WHERE extname = 'vector';
            """)
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == 'vector'
            
        except Exception as e:
            pytest.fail(f"Failed to enable pgvector extension: {e}")
        finally:
            cursor.close()
    
    def test_vector_operations_basic(self, postgres_connection):
        """Test basic vector operations with pgvector."""
        cursor = postgres_connection.cursor()
        
        try:
            # Create a temporary test table with vector column
            cursor.execute("""
                CREATE TEMPORARY TABLE test_vectors (
                    id SERIAL PRIMARY KEY,
                    embedding vector(3),
                    content TEXT
                );
            """)
            
            # Insert test vectors
            cursor.execute("""
                INSERT INTO test_vectors (embedding, content) VALUES
                ('[1,2,3]', 'test content 1'),
                ('[4,5,6]', 'test content 2');
            """)
            
            # Test similarity search
            cursor.execute("""
                SELECT content, embedding <-> '[1,2,3]' AS distance 
                FROM test_vectors 
                ORDER BY embedding <-> '[1,2,3]' 
                LIMIT 1;
            """)
            
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == 'test content 1'  # Closest to [1,2,3]
            assert result[1] == 0.0  # Distance should be 0 (exact match)
            
        except Exception as e:
            pytest.fail(f"Vector operations failed: {e}")
        finally:
            cursor.close()
    
    def test_supabase_table_operations(self, supabase_client):
        """Test basic Supabase table operations."""
        try:
            # Test creating a simple table (this should work with service role key)
            response = supabase_client.table('test_connection').select('*').limit(1).execute()
            # If table doesn't exist, this will return empty data, not error
            assert hasattr(response, 'data')
            
        except Exception as e:
            # If we get a permissions error, that's also OK - means connection works
            if "permission denied" in str(e).lower():
                pass  # Expected for some operations
            elif "could not find the table" in str(e).lower():
                pass  # Expected - table doesn't exist, but connection works
            else:
                pytest.fail(f"Unexpected error in Supabase operations: {e}")


class TestEnvironmentVariables:
    """Test that all required environment variables are set."""
    
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY", 
        "SUPABASE_SERVICE_ROLE_KEY",
        "POSTGRES_URL",
        "POSTGRES_URL_NON_POOLING",
        "GEMINI_API_KEY"
    ]
    
    @pytest.mark.parametrize("var_name", required_vars)
    def test_env_var_exists(self, var_name):
        """Test that required environment variable exists."""
        value = os.getenv(var_name)
        assert value is not None, f"Environment variable {var_name} is not set"
        assert value.strip() != "", f"Environment variable {var_name} is empty"
    
    def test_supabase_url_format(self):
        """Test that Supabase URL has correct format."""
        url = os.getenv("SUPABASE_URL")
        if url:
            assert url.startswith("https://"), "Supabase URL should start with https://"
            assert "supabase.co" in url, "Supabase URL should contain supabase.co"
    
    def test_postgres_url_format(self):
        """Test that PostgreSQL URL has correct format."""
        url = os.getenv("POSTGRES_URL")
        if url:
            assert url.startswith("postgres://"), "PostgreSQL URL should start with postgres://"
            assert "supabase.com" in url, "PostgreSQL URL should contain supabase.com"


if __name__ == "__main__":
    """Run tests directly if script is executed."""
    print("Running Supabase connection tests...")
    print("=" * 60)
    
    # Run tests
    exit_code = pytest.main([__file__, "-v"])
    
    if exit_code == 0:
        print("\n" + "=" * 60)
        print("✅ All Supabase connection tests passed!")
        print("Your Supabase database is ready for vector operations.")
    else:
        print("\n" + "=" * 60)
        print("❌ Some tests failed. Please check your Supabase configuration.")
    
    sys.exit(exit_code)
