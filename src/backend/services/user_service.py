#!/usr/bin/env python3
"""
Mock user service for session management.
Later this will integrate with Supabase authentication.
"""

import os
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class User:
    """User information."""
    id: str
    first_name: str
    last_name: str
    email: str
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

class MockUserService:
    """
    Mock user service that simulates authentication.
    For now, it uses a default mock user for all sessions.
    Later this will be replaced with Supabase Auth integration.
    """
    
    def __init__(self):
        """Initialize the mock user service."""
        self.postgres_url = os.getenv("POSTGRES_URL_NON_POOLING")
        if not self.postgres_url:
            raise ValueError("POSTGRES_URL_NON_POOLING must be set")
    
    def _get_postgres_connection(self):
        """Get a direct PostgreSQL connection."""
        return psycopg2.connect(
            self.postgres_url,
            cursor_factory=RealDictCursor
        )
    
    def get_mock_user(self) -> User:
        """
        Get a mock user for development.
        This simulates a logged-in user at quasol.eu/knowledgeexplorer.
        """
        try:
            with self._get_postgres_connection() as conn:
                with conn.cursor() as cursor:
                    # Get the first mock user from database
                    cursor.execute("""
                        SELECT id, first_name, last_name, email 
                        FROM users 
                        WHERE email LIKE '%@example.com' 
                        LIMIT 1
                    """)
                    
                    user_data = cursor.fetchone()
                    
                    if user_data:
                        return User(
                            id=str(user_data['id']),
                            first_name=user_data['first_name'],
                            last_name=user_data['last_name'],
                            email=user_data['email']
                        )
                    else:
                        # Fallback to hardcoded mock user
                        return self._get_default_mock_user()
                        
        except Exception as e:
            # Fallback to hardcoded mock user
            return self._get_default_mock_user()
    
    def _get_default_mock_user(self) -> User:
        """Get a hardcoded default mock user as fallback."""
        return User(
            id="mock-user-123e4567-e89b-12d3-a456-426614174000",
            first_name="Demo",
            last_name="User", 
            email="demo.user@quasol.eu"
        )
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID from database."""
        try:
            with self._get_postgres_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT id, first_name, last_name, email 
                        FROM users 
                        WHERE id = %s
                    """, (user_id,))
                    
                    user_data = cursor.fetchone()
                    
                    if user_data:
                        return User(
                            id=str(user_data['id']),
                            first_name=user_data['first_name'],
                            last_name=user_data['last_name'],
                            email=user_data['email']
                        )
                    return None
                        
        except Exception:
            return None
    
    def authenticate_user(self, auth_token: Optional[str] = None) -> User:
        """
        Authenticate user based on auth token.
        For now, always returns the mock user.
        Later this will validate Supabase JWT tokens.
        """
        # TODO: Implement Supabase JWT validation
        # For now, return mock user for all requests
        return self.get_mock_user()

# Global instance
user_service = MockUserService()
