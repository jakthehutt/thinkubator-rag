#!/usr/bin/env python3
"""
Migration script to add user_id column to query_sessions table.
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

def run_migration():
    """Run the user sessions migration."""
    
    # Load environment variables
    load_dotenv(dotenv_path=project_root / '.env')
    
    postgres_url = os.getenv("POSTGRES_URL_NON_POOLING")
    if not postgres_url:
        raise ValueError("POSTGRES_URL_NON_POOLING must be set")
    
    # Read the SQL migration
    sql_file_path = Path(__file__).parent / "add_user_id_to_query_sessions.sql"
    with open(sql_file_path, "r") as f:
        migration_sql = f.read()
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(postgres_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("🚀 Running user sessions migration...")
        
        # Execute the migration
        cursor.execute(migration_sql)
        
        print("✅ Migration completed successfully!")
        
        # Verify the migration
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'query_sessions' AND column_name = 'user_id';
        """)
        
        result = cursor.fetchone()
        if result:
            print(f"✅ Verified: user_id column added ({result[1]}, nullable: {result[2]})")
        else:
            print("❌ Verification failed: user_id column not found")
            return False
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("🎉 User sessions migration completed!")
    else:
        print("💥 Migration failed!")
        sys.exit(1)
