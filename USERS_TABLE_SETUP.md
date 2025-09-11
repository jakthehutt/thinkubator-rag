# Users Table Setup - Supabase

## Overview

A users table has been successfully added to the Supabase database with mock user data for development and testing purposes.

## Table Structure

The `users` table includes the following columns:

- **`id`**: UUID (Primary Key, auto-generated)
- **`first_name`**: VARCHAR(100) - User's first name
- **`last_name`**: VARCHAR(100) - User's last name  
- **`email`**: VARCHAR(255) - User's email address (unique)
- **`created_at`**: TIMESTAMP WITH TIME ZONE - Record creation time
- **`updated_at`**: TIMESTAMP WITH TIME ZONE - Last update time

## Database Features

### Indexes
- **Email Index**: Fast lookups by email address
- **Name Index**: Search functionality by first and last name

### Security
- **Row Level Security (RLS)**: Enabled for data protection
- **Policies**: 
  - Authenticated users can view all users
  - Users can update their own profile
- **Permissions**: Read access for authenticated and anonymous users

## Mock Users

10 sample users have been inserted with @example.com email addresses:

1. Alice Johnson (alice.johnson@example.com)
2. Bob Smith (bob.smith@example.com)
3. Carol Williams (carol.williams@example.com)
4. David Brown (david.brown@example.com)
5. Emma Davis (emma.davis@example.com)
6. Frank Miller (frank.miller@example.com)
7. Grace Wilson (grace.wilson@example.com)
8. Henry Moore (henry.moore@example.com)
9. Isla Taylor (isla.taylor@example.com)
10. Jack Anderson (jack.anderson@example.com)

## Available Commands

### Setup Commands
```bash
# Create users table and insert mock data
make setup-users
```

### Testing Commands
```bash
# Run comprehensive tests on users table
make test-users
```

### Query Commands
```bash
# Display all users in a formatted table
make query-users
```

## Files Created

### Database Files
- `src/backend/database/create_users_table.sql` - SQL table definition
- `src/backend/database/setup_users_table.py` - Setup and data insertion script
- `src/backend/database/query_users.py` - Query and display utility

### Test Files
- `src/backend/tests/test_users_table.py` - Comprehensive test suite

## Test Coverage

The test suite includes:
- ✅ Table existence verification
- ✅ Table structure validation
- ✅ Index presence checks
- ✅ Mock user data verification
- ✅ Data integrity validation
- ✅ UUID format validation
- ✅ Sample data quality checks

All tests pass successfully (7/7).

## Environment Requirements

The following environment variables must be set:
- `POSTGRES_URL_NON_POOLING` - Direct PostgreSQL connection URL
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key

## Integration

The users table is ready for integration with:
- Authentication systems
- User profile management
- RAG query attribution
- Session tracking
- User analytics

---

**Status**: ✅ **Complete** - Users table successfully created with 10 mock users and comprehensive testing.
