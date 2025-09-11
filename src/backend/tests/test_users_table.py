#!/usr/bin/env python3
"""
Tests for the users table in Supabase.
"""

import pytest
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(dotenv_path=project_root / '.env')

class TestUsersTable:
    """Test suite for the users table in Supabase."""
    
    @pytest.fixture(scope="class")
    def postgres_connection(self):
        """Create direct PostgreSQL connection for testing."""
        postgres_url = os.getenv("POSTGRES_URL_NON_POOLING")
        
        if not postgres_url:
            pytest.skip("PostgreSQL URL not configured")
        
        try:
            conn = psycopg2.connect(postgres_url, cursor_factory=RealDictCursor)
            yield conn
        finally:
            if conn:
                conn.close()
    
    def test_users_table_exists(self, postgres_connection):
        """Test that the users table exists."""
        cursor = postgres_connection.cursor()
        
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            );
        """)
        
        result = cursor.fetchone()
        table_exists = result['exists']
        assert table_exists, "Users table should exist"
        cursor.close()
    
    def test_users_table_structure(self, postgres_connection):
        """Test the structure of the users table."""
        cursor = postgres_connection.cursor()
        
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        cursor.close()
        
        # Expected columns
        expected_columns = {
            'id': 'uuid',
            'first_name': 'character varying',
            'last_name': 'character varying', 
            'email': 'character varying',
            'created_at': 'timestamp with time zone',
            'updated_at': 'timestamp with time zone'
        }
        
        actual_columns = {col['column_name']: col['data_type'] for col in columns}
        
        # Check all expected columns exist
        for col_name, col_type in expected_columns.items():
            assert col_name in actual_columns, f"Column {col_name} should exist"
            assert actual_columns[col_name] == col_type, f"Column {col_name} should be {col_type}, got {actual_columns[col_name]}"
    
    def test_users_table_indexes(self, postgres_connection):
        """Test that required indexes exist on the users table."""
        cursor = postgres_connection.cursor()
        
        cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'users';
        """)
        
        indexes = cursor.fetchall()
        cursor.close()
        
        index_names = [idx['indexname'] for idx in indexes]
        
        # Check for required indexes
        assert any('email' in idx for idx in index_names), "Email index should exist"
        assert any('name' in idx for idx in index_names), "Name index should exist"
    
    def test_mock_users_exist(self, postgres_connection):
        """Test that mock users were inserted."""
        cursor = postgres_connection.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE email LIKE '%@example.com'")
        count_result = cursor.fetchone()
        cursor.close()
        
        assert count_result['count'] > 0, "Mock users should exist in the database"
        assert count_result['count'] >= 10, f"Expected at least 10 mock users, got {count_result['count']}"
    
    def test_user_data_integrity(self, postgres_connection):
        """Test that user data has proper integrity."""
        cursor = postgres_connection.cursor()
        
        # Test for unique emails
        cursor.execute("""
            SELECT email, COUNT(*) as count 
            FROM users 
            GROUP BY email 
            HAVING COUNT(*) > 1
        """)
        
        duplicate_emails = cursor.fetchall()
        assert len(duplicate_emails) == 0, f"Found duplicate emails: {duplicate_emails}"
        
        # Test for required fields
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM users 
            WHERE first_name IS NULL 
               OR last_name IS NULL 
               OR email IS NULL
               OR id IS NULL
        """)
        
        null_fields = cursor.fetchone()['count']
        assert null_fields == 0, f"Found {null_fields} records with null required fields"
        
        cursor.close()
    
    def test_user_uuid_format(self, postgres_connection):
        """Test that user IDs are proper UUIDs."""
        cursor = postgres_connection.cursor()
        
        cursor.execute("SELECT id FROM users LIMIT 5")
        users = cursor.fetchall()
        cursor.close()
        
        for user in users:
            user_id = str(user['id'])
            # Basic UUID format check (8-4-4-4-12 characters)
            assert len(user_id) == 36, f"UUID should be 36 characters, got {len(user_id)}"
            assert user_id.count('-') == 4, f"UUID should have 4 hyphens, got {user_id.count('-')}"
    
    def test_user_sample_data(self, postgres_connection):
        """Test sample user data quality."""
        cursor = postgres_connection.cursor()
        
        cursor.execute("""
            SELECT first_name, last_name, email 
            FROM users 
            WHERE email LIKE '%@example.com' 
            LIMIT 3
        """)
        
        users = cursor.fetchall()
        cursor.close()
        
        assert len(users) >= 3, "Should have at least 3 sample users"
        
        for user in users:
            assert len(user['first_name']) > 0, "First name should not be empty"
            assert len(user['last_name']) > 0, "Last name should not be empty"
            assert '@' in user['email'], "Email should contain @"
            assert '.' in user['email'], "Email should contain domain extension"

if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
