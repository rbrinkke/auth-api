#!/bin/bash
set -e

# This script initializes the PostgreSQL database with stored procedures
# It runs the stored_procedures.sql file

echo "Running stored procedures initialization..."

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /app/stored_procedures.sql

echo "Stored procedures initialized successfully!"
echo "All database objects created in schema 'activity'"
