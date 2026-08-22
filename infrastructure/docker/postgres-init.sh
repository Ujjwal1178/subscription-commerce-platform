#!/bin/bash
# ============================================================================
# PostgreSQL Initialization Script
# ============================================================================
# This script runs ONCE when PostgreSQL container starts for the first time
# Creates separate databases for each service (microservices pattern)
# ============================================================================

set -e  # Exit on error

# Function to create database if not exists
create_db_if_not_exists() {
    local database=$1
    echo "Checking database: $database"
    
    # Check if database exists
    if psql -U postgres -lqt | cut -d \| -f 1 | grep -qw "$database"; then
        echo "  Database '$database' already exists, skipping"
    else
        echo "  Creating database '$database'..."
        psql -U postgres -c "CREATE DATABASE $database;"
        echo "  Database '$database' created successfully"
    fi
}

echo "============================================"
echo "Starting database initialization..."
echo "============================================"

# Create all databases
create_db_if_not_exists "auth_db"
create_db_if_not_exists "user_subs_db"
create_db_if_not_exists "payment_db"
create_db_if_not_exists "notification_db"

# Grant privileges
echo ""
echo "Granting privileges..."
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE auth_db TO postgres;"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE user_subs_db TO postgres;"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE payment_db TO postgres;"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE notification_db TO postgres;"

echo ""
echo "============================================"
echo "Database initialization complete!"
echo "Available databases:"
echo "  - auth_db"
echo "  - user_subs_db"
echo "  - payment_db"
echo "  - notification_db"
echo "============================================"
