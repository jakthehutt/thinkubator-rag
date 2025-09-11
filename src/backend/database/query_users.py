#!/usr/bin/env python3
"""
Quick script to query and display users from the Supabase users table.
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

def query_users():
    """Query and display users from the users table."""
    
    # Load environment variables
    load_dotenv(dotenv_path=project_root / '.env')
    
    postgres_url = os.getenv("POSTGRES_URL_NON_POOLING")
    if not postgres_url:
        raise ValueError("POSTGRES_URL_NON_POOLING must be set")
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(postgres_url, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        
        print("👥 Querying users table...\n")
        
        # Get all users
        cursor.execute("""
            SELECT id, first_name, last_name, email, created_at, updated_at
            FROM users 
            ORDER BY first_name, last_name
        """)
        
        users = cursor.fetchall()
        
        if not users:
            print("❌ No users found in the database")
            return False
        
        print(f"✅ Found {len(users)} users:\n")
        
        # Display users in a nice table format
        print("┌─" + "─" * 36 + "─┬─" + "─" * 25 + "─┬─" + "─" * 35 + "─┬─" + "─" * 25 + "─┐")
        print(f"│ {'UUID (first 8 chars)':<36} │ {'Name':<25} │ {'Email':<35} │ {'Created':<25} │")
        print("├─" + "─" * 36 + "─┼─" + "─" * 25 + "─┼─" + "─" * 35 + "─┼─" + "─" * 25 + "─┤")
        
        for user in users:
            uuid_short = str(user['id'])[:8] + "..."
            full_name = f"{user['first_name']} {user['last_name']}"
            created_short = user['created_at'].strftime('%Y-%m-%d %H:%M')
            
            print(f"│ {uuid_short:<36} │ {full_name:<25} │ {user['email']:<35} │ {created_short:<25} │")
        
        print("└─" + "─" * 36 + "─┴─" + "─" * 25 + "─┴─" + "─" * 35 + "─┴─" + "─" * 25 + "─┘")
        
        # Show summary stats
        cursor.execute("SELECT COUNT(*) as total_users FROM users")
        total = cursor.fetchone()['total_users']
        
        cursor.execute("SELECT COUNT(*) as mock_users FROM users WHERE email LIKE '%@example.com'")
        mock = cursor.fetchone()['mock_users']
        
        print(f"\n📊 Summary:")
        print(f"   • Total users: {total}")
        print(f"   • Mock users:  {mock}")
        print(f"   • Other users: {total - mock}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error querying users: {e}")
        return False

if __name__ == "__main__":
    query_users()
