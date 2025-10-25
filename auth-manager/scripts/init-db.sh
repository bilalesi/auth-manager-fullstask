#!/bin/bash
set -e

echo "Initializing databases..."


psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create keycloak user
    CREATE USER keycloak WITH PASSWORD 'keycloak';
    
    -- Create keycloak database
    CREATE DATABASE keycloak OWNER keycloak;
    
    -- Grant privileges
    GRANT ALL PRIVILEGES ON DATABASE keycloak TO keycloak;
    
    -- Create auth_manager database if auth_manager is the main user
    -- Note: auth_manager user should already exist as POSTGRES_USER
    CREATE DATABASE auth_manager OWNER $POSTGRES_USER;
    
    GRANT ALL PRIVILEGES ON DATABASE auth_manager TO $POSTGRES_USER;
EOSQL

echo "Databases created successfully"
