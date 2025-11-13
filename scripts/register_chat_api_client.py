#!/usr/bin/env python3
"""
Register chat-api-service OAuth client for service-to-service authentication.

This script registers the Chat API as an OAuth client with Client Credentials grant.
"""

import asyncio
import asyncpg
import hashlib
import os
from pathlib import Path

# Load environment from .env file
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                # Remove quotes if present
                value = value.strip('"').strip("'")
                os.environ[key] = value


async def main():
    """Register chat-api-service client."""

    # Database connection parameters
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = int(os.getenv("POSTGRES_PORT", "5433"))
    db_name = os.getenv("POSTGRES_DB", "activity_db")
    db_user = os.getenv("POSTGRES_USER", "activity_user")
    db_password = os.getenv("POSTGRES_PASSWORD", "activity_pass")

    # OAuth client parameters
    client_id = "chat-api-service"
    client_secret = "your-service-secret-change-in-production"  # Match Chat-API .env
    allowed_scopes = ["groups:read", "groups:write", "members:read"]

    print(f"🔐 Registering OAuth Client: {client_id}")
    print(f"📍 Database: {db_host}:{db_port}/{db_name}")
    print(f"🔑 Scopes: {', '.join(allowed_scopes)}")
    print()

    try:
        # Connect to database
        conn = await asyncpg.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )

        print("✅ Connected to database")

        # Hash client secret using SHA-256 (as expected by Auth-API)
        client_secret_hash = hashlib.sha256(client_secret.encode()).hexdigest()

        # Check if client already exists
        existing = await conn.fetchrow(
            """
            SELECT client_id, allowed_scopes
            FROM activity.oauth_clients
            WHERE client_id = $1
            """,
            client_id
        )

        if existing:
            print(f"⚠️  Client '{client_id}' already exists!")
            print(f"   Current scopes: {existing['allowed_scopes']}")

            # Update scopes and secret
            await conn.execute(
                """
                UPDATE activity.oauth_clients
                SET client_secret_hash = $1,
                    allowed_scopes = $2,
                    updated_at = NOW()
                WHERE client_id = $3
                """,
                client_secret_hash,
                allowed_scopes,
                client_id
            )

            print(f"✅ Updated client with new scopes: {', '.join(allowed_scopes)}")
        else:
            # Insert new client
            await conn.execute(
                """
                INSERT INTO activity.oauth_clients (
                    client_id,
                    client_name,
                    client_secret_hash,
                    is_confidential,
                    allowed_scopes,
                    redirect_uris,
                    grant_types,
                    created_at,
                    updated_at
                ) VALUES (
                    $1,  -- client_id
                    $2,  -- client_name
                    $3,  -- client_secret_hash
                    $4,  -- is_confidential
                    $5,  -- allowed_scopes
                    $6,  -- redirect_uris (empty for service accounts)
                    $7,  -- grant_types
                    NOW(),
                    NOW()
                )
                """,
                client_id,
                "Chat API Service",
                client_secret_hash,
                True,  # Confidential client (has client_secret)
                allowed_scopes,
                [],  # No redirect URIs for client_credentials
                ["client_credentials"]  # Only client_credentials grant
            )

            print(f"✅ Registered new OAuth client: {client_id}")

        # Verify registration
        verification = await conn.fetchrow(
            """
            SELECT client_id, client_name, allowed_scopes, grant_types, is_confidential
            FROM activity.oauth_clients
            WHERE client_id = $1
            """,
            client_id
        )

        print()
        print("📋 Client Details:")
        print(f"   ID: {verification['client_id']}")
        print(f"   Name: {verification['client_name']}")
        print(f"   Confidential: {verification['is_confidential']}")
        print(f"   Grant Types: {verification['grant_types']}")
        print(f"   Allowed Scopes: {verification['allowed_scopes']}")

        await conn.close()

        print()
        print("🎉 SUCCESS! Chat-API can now authenticate with Auth-API")
        print()
        print("📝 Next steps:")
        print("   1. Ensure Chat-API .env has matching SERVICE_CLIENT_SECRET")
        print("   2. Restart Chat-API to pick up OAuth client")
        print("   3. Test with: bash test_chat_live.sh")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
