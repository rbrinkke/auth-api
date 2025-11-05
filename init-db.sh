#!/bin/bash
set -e

# This script initializes the PostgreSQL database for the Auth API
# It creates the 'activity' schema and grants necessary permissions

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<'EOSQL'
    -- Create the activity schema
    CREATE SCHEMA IF NOT EXISTS activity;

    -- Grant all privileges on the schema to the user
    GRANT ALL PRIVILEGES ON SCHEMA activity TO activity_user;
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA activity TO activity_user;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA activity TO activity_user;

    -- Set default privileges for future objects
    ALTER DEFAULT PRIVILEGES IN SCHEMA activity GRANT ALL ON TABLES TO activity_user;
    ALTER DEFAULT PRIVILEGES IN SCHEMA activity GRANT ALL ON SEQUENCES TO activity_user;

    -- Give ownership of the schema to the user
    ALTER SCHEMA activity OWNER TO activity_user;

    -- Grant database-level permissions as well
    GRANT ALL PRIVILEGES ON DATABASE activitydb TO activity_user;

    -- Grant connect permission
    GRANT CONNECT ON DATABASE activitydb TO activity_user;
EOSQL

echo "Database initialized successfully!"
echo "Schema 'activity' created with proper permissions for activity_user"
