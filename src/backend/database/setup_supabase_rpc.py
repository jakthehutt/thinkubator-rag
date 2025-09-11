#!/usr/bin/env python3
"""
Setup Supabase RPC function for vector similarity search.
This script creates the match_documents function in Supabase.
"""

import os
import psycopg2
from dotenv import load_dotenv

def setup_match_documents_function():
    """Create the match_documents RPC function in Supabase."""
    
    # Load environment variables
    load_dotenv()
    
    postgres_url = os.getenv("POSTGRES_URL_NON_POOLING")
    if not postgres_url:
        raise ValueError("POSTGRES_URL_NON_POOLING must be set")
    
    # Read the SQL function definition
    with open("scripts/create_match_documents_function.sql", "r") as f:
        sql_function = f.read()
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(postgres_url)
        cursor = conn.cursor()
        
        print("Creating match_documents function...")
        
        # Execute the SQL function creation
        cursor.execute(sql_function)
        
        # Commit the changes
        conn.commit()
        
        print("✅ match_documents function created successfully!")
        
        # Test the function
        print("Testing the function...")
        test_embedding = [0.1] * 768  # Dummy embedding
        cursor.execute("""
            SELECT * FROM match_documents(%s::vector, 0.5, 3)
        """, (test_embedding,))
        
        results = cursor.fetchall()
        print(f"✅ Function test successful! Returned {len(results)} results")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating function: {e}")
        return False

if __name__ == "__main__":
    success = setup_match_documents_function()
    if success:
        print("🎉 Supabase RPC function setup completed!")
    else:
        print("💥 Setup failed!")
        exit(1)
