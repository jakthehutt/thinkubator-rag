-- Add user_id column to query_sessions table to associate sessions with users
-- This migration links query sessions to specific users

-- Add user_id column
ALTER TABLE query_sessions 
ADD COLUMN IF NOT EXISTS user_id UUID;

-- Create foreign key constraint to users table (skip if exists)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_query_sessions_user_id' 
        AND table_name = 'query_sessions'
    ) THEN
        ALTER TABLE query_sessions 
        ADD CONSTRAINT fk_query_sessions_user_id 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Create index on user_id for fast user session lookups
CREATE INDEX IF NOT EXISTS idx_query_sessions_user_id 
ON query_sessions (user_id);

-- Create composite index for user sessions ordered by creation time
CREATE INDEX IF NOT EXISTS idx_query_sessions_user_created 
ON query_sessions (user_id, created_at DESC);

-- Grant permissions for the updated table
GRANT SELECT, INSERT ON query_sessions TO authenticated;
GRANT SELECT ON query_sessions TO anon;
