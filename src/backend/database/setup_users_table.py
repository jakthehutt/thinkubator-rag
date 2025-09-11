#!/usr/bin/env python3
"""
Setup users table in Supabase and insert mock users.
This script creates the users table and populates it with sample data.
"""

import os
import sys
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

def setup_users_table():
    """Create the users table in Supabase."""
    
    # Load environment variables
    load_dotenv(dotenv_path=project_root / '.env')
    
    postgres_url = os.getenv("POSTGRES_URL_NON_POOLING")
    if not postgres_url:
        raise ValueError("POSTGRES_URL_NON_POOLING must be set")
    
    # Read the SQL table definition
    sql_file_path = Path(__file__).parent / "create_users_table.sql"
    with open(sql_file_path, "r") as f:
        sql_create_table = f.read()
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(postgres_url, cursor_factory=RealDictCursor)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Creating users table...")
        
        # Execute the SQL table creation
        cursor.execute(sql_create_table)
        
        print("✅ Users table created successfully!")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating users table: {e}")
        return False

def insert_mock_users():
    """Insert mock users into the users table."""
    
    # Load environment variables
    load_dotenv(dotenv_path=project_root / '.env')
    
    postgres_url = os.getenv("POSTGRES_URL_NON_POOLING")
    if not postgres_url:
        raise ValueError("POSTGRES_URL_NON_POOLING must be set")
    
    # Mock users data
    mock_users = [
        {
            "id": str(uuid.uuid4()),
            "first_name": "Alice",
            "last_name": "Johnson",
            "email": "alice.johnson@example.com"
        },
        {
            "id": str(uuid.uuid4()),
            "first_name": "Bob",
            "last_name": "Smith",
            "email": "bob.smith@example.com"
        },
        {
            "id": str(uuid.uuid4()),
            "first_name": "Carol",
            "last_name": "Williams",
            "email": "carol.williams@example.com"
        },
        {
            "id": str(uuid.uuid4()),
            "first_name": "David",
            "last_name": "Brown",
            "email": "david.brown@example.com"
        },
        {
            "id": str(uuid.uuid4()),
            "first_name": "Emma",
            "last_name": "Davis",
            "email": "emma.davis@example.com"
        },
        {
            "id": str(uuid.uuid4()),
            "first_name": "Frank",
            "last_name": "Miller",
            "email": "frank.miller@example.com"
        },
        {
            "id": str(uuid.uuid4()),
            "first_name": "Grace",
            "last_name": "Wilson",
            "email": "grace.wilson@example.com"
        },
        {
            "id": str(uuid.uuid4()),
            "first_name": "Henry",
            "last_name": "Moore",
            "email": "henry.moore@example.com"
        },
        {
            "id": str(uuid.uuid4()),
            "first_name": "Isla",
            "last_name": "Taylor",
            "email": "isla.taylor@example.com"
        },
        {
            "id": str(uuid.uuid4()),
            "first_name": "Jack",
            "last_name": "Anderson",
            "email": "jack.anderson@example.com"
        }
    ]
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(postgres_url, cursor_factory=RealDictCursor)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Inserting mock users...")
        
        # Clear existing mock users (optional, for clean testing)
        cursor.execute("DELETE FROM users WHERE email LIKE '%@example.com'")
        
        # Insert mock users
        insert_query = """
            INSERT INTO users (id, first_name, last_name, email)
            VALUES (%(id)s, %(first_name)s, %(last_name)s, %(email)s)
            ON CONFLICT (email) DO UPDATE SET
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                updated_at = NOW()
        """
        
        cursor.executemany(insert_query, mock_users)
        
        print(f"✅ {len(mock_users)} mock users inserted successfully!")
        
        # Verify the insertion
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE email LIKE '%@example.com'")
        count_result = cursor.fetchone()
        print(f"✅ Verified: {count_result['count']} users found in database")
        
        # Show sample users
        cursor.execute("""
            SELECT id, first_name, last_name, email, created_at 
            FROM users 
            WHERE email LIKE '%@example.com' 
            ORDER BY first_name 
            LIMIT 5
        """)
        
        sample_users = cursor.fetchall()
        print("\n📋 Sample users:")
        for user in sample_users:
            print(f"  - {user['first_name']} {user['last_name']} ({user['email']}) [ID: {user['id'][:8]}...]")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error inserting mock users: {e}")
        return False

def test_users_table():
    """Test the users table setup and functionality."""
    
    # Load environment variables
    load_dotenv(dotenv_path=project_root / '.env')
    
    postgres_url = os.getenv("POSTGRES_URL_NON_POOLING")
    if not postgres_url:
        raise ValueError("POSTGRES_URL_NON_POOLING must be set")
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(postgres_url, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        
        print("\n🧪 Testing users table...")
        
        # Test 1: Check table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        if table_exists:
            print("✅ Users table exists")
        else:
            print("❌ Users table does not exist")
            return False
        
        # Test 2: Check table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print(f"✅ Table has {len(columns)} columns:")
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
        
        # Test 3: Check data
        cursor.execute("SELECT COUNT(*) as count FROM users")
        total_count = cursor.fetchone()['count']
        print(f"✅ Table contains {total_count} users")
        
        # Test 4: Check indexes
        cursor.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'users';
        """)
        
        indexes = cursor.fetchall()
        print(f"✅ Table has {len(indexes)} indexes:")
        for idx in indexes:
            print(f"  - {idx['indexname']}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing users table: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Setting up users table in Supabase...")
    
    # Step 1: Create the table
    if setup_users_table():
        print("✅ Users table setup completed!")
    else:
        print("💥 Users table setup failed!")
        sys.exit(1)
    
    # Step 2: Insert mock users
    if insert_mock_users():
        print("✅ Mock users insertion completed!")
    else:
        print("💥 Mock users insertion failed!")
        sys.exit(1)
    
    # Step 3: Test the setup
    if test_users_table():
        print("✅ Users table testing completed!")
    else:
        print("💥 Users table testing failed!")
        sys.exit(1)
    
    print("\n🎉 Users table setup completed successfully!")
    print("📧 Mock users with @example.com emails have been added to the database.")
