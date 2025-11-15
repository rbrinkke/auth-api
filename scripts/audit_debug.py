#!/usr/bin/env python3
"""
Authorization Audit Log - CLI Debugging Tool

Quick command-line access to audit logs for debugging authorization issues.

Usage:
    ./scripts/audit_debug.py user <user_id> <org_id>           # User activity
    ./scripts/audit_debug.py permission <user_id> <org_id> <permission>  # Specific permission
    ./scripts/audit_debug.py failed [hours]                    # Failed attempts
    ./scripts/audit_debug.py brute-force [minutes] [threshold] # Detect attacks
    ./scripts/audit_debug.py resource <resource_id>            # Resource access
    ./scripts/audit_debug.py stats <org_id> [days]             # Permission usage
    ./scripts/audit_debug.py integrity [hours]                 # Verify hash chain
    ./scripts/audit_debug.py cache [hours]                     # Cache performance
    ./scripts/audit_debug.py correlation <request_id>          # Trace request

Examples:
    ./scripts/audit_debug.py user c0a61eba-5805-494c-bc1b-563d3ca49126 1ab0e9fa-b4ec-4a8b-9cfa-7f2bb57db87e
    ./scripts/audit_debug.py permission c0a61eba... 1ab0e9fa... activity:update
    ./scripts/audit_debug.py failed 1
    ./scripts/audit_debug.py brute-force 15 10
    ./scripts/audit_debug.py stats 1ab0e9fa-b4ec-4a8b-9cfa-7f2bb57db87e 7
"""

import sys
import os
import asyncio
import asyncpg
from datetime import datetime, timedelta
from typing import Optional, List
from tabulate import tabulate
from uuid import UUID

# Database connection settings
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5441"))
DB_NAME = os.getenv("POSTGRES_DB", "activitydb")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres_secure_password_change_in_prod")


class AuditDebugger:
    """CLI debugger for authorization audit logs."""

    def __init__(self):
        self.conn: Optional[asyncpg.Connection] = None

    async def connect(self):
        """Connect to PostgreSQL database."""
        try:
            self.conn = await asyncpg.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            print(f"✅ Connected to {DB_NAME}@{DB_HOST}:{DB_PORT}\n")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            sys.exit(1)

    async def close(self):
        """Close database connection."""
        if self.conn:
            await self.conn.close()

    async def user_activity(self, user_id: str, org_id: str, hours: int = 24):
        """Get user's authorization activity timeline."""
        print(f"🔍 User Activity (last {hours}h)")
        print(f"   User: {user_id}")
        print(f"   Org:  {org_id}\n")

        query = """
        SELECT
            id,
            to_char(timestamp, 'YYYY-MM-DD HH24:MI:SS') as time,
            permission,
            authorized::text as granted,
            reason,
            cache_source
        FROM activity.authorization_audit_log
        WHERE user_id = $1
          AND organization_id = $2
          AND timestamp >= NOW() - INTERVAL '%s hours'
        ORDER BY timestamp DESC
        LIMIT 50;
        """ % hours

        try:
            rows = await self.conn.fetch(query, UUID(user_id), UUID(org_id))

            if not rows:
                print("⚠️  No audit log entries found")
                return

            # Convert to list of dicts for tabulate
            data = [dict(row) for row in rows]
            headers = ["ID", "Time", "Permission", "Granted", "Reason", "Cache"]

            print(tabulate(data, headers="keys", tablefmt="grid"))
            print(f"\n📊 Total entries: {len(rows)}")

        except Exception as e:
            print(f"❌ Query failed: {e}")

    async def specific_permission(self, user_id: str, org_id: str, permission: str, hours: int = 24):
        """Check specific permission attempts."""
        print(f"🔍 Permission Check (last {hours}h)")
        print(f"   User: {user_id}")
        print(f"   Org:  {org_id}")
        print(f"   Perm: {permission}\n")

        query = """
        SELECT
            id,
            to_char(timestamp, 'YYYY-MM-DD HH24:MI:SS') as time,
            authorized::text as granted,
            reason,
            matched_groups,
            cache_source,
            resource_id
        FROM activity.authorization_audit_log
        WHERE user_id = $1
          AND organization_id = $2
          AND permission = $3
          AND timestamp >= NOW() - INTERVAL '%s hours'
        ORDER BY timestamp DESC
        LIMIT 50;
        """ % hours

        try:
            rows = await self.conn.fetch(query, UUID(user_id), UUID(org_id), permission)

            if not rows:
                print("⚠️  No attempts found for this permission")
                return

            data = [dict(row) for row in rows]
            print(tabulate(data, headers="keys", tablefmt="grid"))
            print(f"\n📊 Total attempts: {len(rows)}")

            # Summary
            granted = sum(1 for row in rows if row["granted"] == "t")
            denied = len(rows) - granted
            print(f"   ✅ Granted: {granted} | ❌ Denied: {denied}")

        except Exception as e:
            print(f"❌ Query failed: {e}")

    async def failed_attempts(self, hours: int = 1):
        """Show all failed authorization attempts."""
        print(f"🚨 Failed Authorization Attempts (last {hours}h)\n")

        query = """
        SELECT
            id,
            to_char(timestamp, 'YYYY-MM-DD HH24:MI:SS') as time,
            user_id,
            permission,
            reason,
            ip_address
        FROM activity.authorization_audit_log
        WHERE authorized = false
          AND timestamp >= NOW() - INTERVAL '%s hours'
        ORDER BY timestamp DESC
        LIMIT 100;
        """ % hours

        try:
            rows = await self.conn.fetch(query)

            if not rows:
                print("✅ No failed attempts (good news!)")
                return

            data = [dict(row) for row in rows]
            print(tabulate(data, headers="keys", tablefmt="grid"))
            print(f"\n📊 Total failed: {len(rows)}")

        except Exception as e:
            print(f"❌ Query failed: {e}")

    async def brute_force_detection(self, minutes: int = 60, threshold: int = 5):
        """Detect potential brute-force attacks."""
        print(f"🚨 Brute-Force Detection (last {minutes} min, threshold: {threshold}+)\n")

        query = """
        SELECT * FROM activity.sp_get_failed_auth_attempts(
            NOW() - INTERVAL '%s minutes',
            %s
        );
        """ % (minutes, threshold)

        try:
            rows = await self.conn.fetch(query)

            if not rows:
                print("✅ No suspicious activity detected")
                return

            data = [dict(row) for row in rows]
            print(tabulate(data, headers="keys", tablefmt="grid"))
            print(f"\n🚨 ALERT: {len(rows)} suspicious user(s) detected!")

        except Exception as e:
            print(f"❌ Query failed: {e}")

    async def resource_access(self, resource_id: str, hours: int = 24):
        """Show who accessed a specific resource."""
        print(f"🔍 Resource Access History (last {hours}h)")
        print(f"   Resource: {resource_id}\n")

        query = """
        SELECT
            id,
            to_char(timestamp, 'YYYY-MM-DD HH24:MI:SS') as time,
            user_id,
            permission,
            authorized::text as granted,
            ip_address
        FROM activity.authorization_audit_log
        WHERE resource_id = $1
          AND timestamp >= NOW() - INTERVAL '%s hours'
        ORDER BY timestamp DESC
        LIMIT 100;
        """ % hours

        try:
            rows = await self.conn.fetch(query, UUID(resource_id))

            if not rows:
                print("⚠️  No access attempts found")
                return

            data = [dict(row) for row in rows]
            print(tabulate(data, headers="keys", tablefmt="grid"))
            print(f"\n📊 Total attempts: {len(rows)}")

            # Unique users
            unique_users = len(set(row["user_id"] for row in rows))
            print(f"   👥 Unique users: {unique_users}")

        except Exception as e:
            print(f"❌ Query failed: {e}")

    async def permission_stats(self, org_id: str, days: int = 7):
        """Permission usage statistics for organization."""
        print(f"📊 Permission Usage Statistics (last {days} days)")
        print(f"   Organization: {org_id}\n")

        query = """
        SELECT * FROM activity.sp_get_permission_usage_stats(
            $1,
            NOW() - INTERVAL '%s days'
        )
        ORDER BY total_checks DESC
        LIMIT 20;
        """ % days

        try:
            rows = await self.conn.fetch(query, UUID(org_id))

            if not rows:
                print("⚠️  No permission usage data")
                return

            data = [dict(row) for row in rows]
            print(tabulate(data, headers="keys", tablefmt="grid"))
            print(f"\n📊 Top permissions shown: {len(rows)}")

        except Exception as e:
            print(f"❌ Query failed: {e}")

    async def verify_integrity(self, hours: int = 24):
        """Verify audit log integrity (hash chain)."""
        print(f"🔐 Verifying Audit Log Integrity (last {hours}h)\n")

        query = """
        SELECT * FROM activity.sp_verify_audit_log_integrity(
            NOW() - INTERVAL '%s hours'
        );
        """ % hours

        try:
            result = await self.conn.fetchrow(query)

            if result["is_valid"]:
                print("✅ Audit log integrity: VALID")
                print(f"   Total entries checked: {result['total_entries']}")
                print(f"   Broken chains: {result['broken_chains']}")
                print("\n🎉 No tampering detected!")
            else:
                print("🚨 ALERT: Audit log integrity: COMPROMISED!")
                print(f"   Total entries checked: {result['total_entries']}")
                print(f"   Broken chains: {result['broken_chains']}")
                print(f"   First broken entry ID: {result['first_broken_id']}")
                print("\n⚠️  IMMEDIATE ACTION REQUIRED: Investigate tampering!")

        except Exception as e:
            print(f"❌ Query failed: {e}")

    async def cache_performance(self, hours: int = 1):
        """Analyze cache performance."""
        print(f"⚡ Cache Performance Analysis (last {hours}h)\n")

        query = """
        SELECT
            cache_source,
            COUNT(*) as checks,
            COUNT(*) FILTER (WHERE authorized = true) as granted,
            COUNT(*) FILTER (WHERE authorized = false) as denied,
            ROUND(AVG(CASE WHEN authorized THEN 1 ELSE 0 END) * 100, 2) as grant_rate_pct
        FROM activity.authorization_audit_log
        WHERE timestamp >= NOW() - INTERVAL '%s hours'
        GROUP BY cache_source
        ORDER BY checks DESC;
        """ % hours

        try:
            rows = await self.conn.fetch(query)

            if not rows:
                print("⚠️  No cache data available")
                return

            data = [dict(row) for row in rows]
            print(tabulate(data, headers="keys", tablefmt="grid"))

            # Calculate total and percentages
            total = sum(row["checks"] for row in rows)
            print(f"\n📊 Total authorization checks: {total}")

            for row in rows:
                pct = (row["checks"] / total * 100) if total > 0 else 0
                print(f"   {row['cache_source']}: {pct:.1f}% ({row['checks']} checks)")

        except Exception as e:
            print(f"❌ Query failed: {e}")

    async def correlation_trace(self, request_id: str):
        """Trace request by correlation ID."""
        print(f"🔍 Request Correlation Trace")
        print(f"   Request ID: {request_id}\n")

        query = """
        SELECT
            id,
            to_char(timestamp, 'YYYY-MM-DD HH24:MI:SS.MS') as time,
            user_id,
            permission,
            authorized::text as granted,
            reason,
            cache_source
        FROM activity.authorization_audit_log
        WHERE request_id = $1
        ORDER BY timestamp ASC;
        """

        try:
            rows = await self.conn.fetch(query, UUID(request_id))

            if not rows:
                print("⚠️  No entries found for this request ID")
                return

            data = [dict(row) for row in rows]
            print(tabulate(data, headers="keys", tablefmt="grid"))
            print(f"\n📊 Total authorization checks: {len(rows)}")

        except Exception as e:
            print(f"❌ Query failed: {e}")


def print_usage():
    """Print CLI usage instructions."""
    print(__doc__)


async def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1].lower()
    debugger = AuditDebugger()

    try:
        await debugger.connect()

        if command == "user" and len(sys.argv) >= 4:
            user_id = sys.argv[2]
            org_id = sys.argv[3]
            hours = int(sys.argv[4]) if len(sys.argv) > 4 else 24
            await debugger.user_activity(user_id, org_id, hours)

        elif command == "permission" and len(sys.argv) >= 5:
            user_id = sys.argv[2]
            org_id = sys.argv[3]
            permission = sys.argv[4]
            hours = int(sys.argv[5]) if len(sys.argv) > 5 else 24
            await debugger.specific_permission(user_id, org_id, permission, hours)

        elif command == "failed":
            hours = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            await debugger.failed_attempts(hours)

        elif command == "brute-force":
            minutes = int(sys.argv[2]) if len(sys.argv) > 2 else 60
            threshold = int(sys.argv[3]) if len(sys.argv) > 3 else 5
            await debugger.brute_force_detection(minutes, threshold)

        elif command == "resource" and len(sys.argv) >= 3:
            resource_id = sys.argv[2]
            hours = int(sys.argv[3]) if len(sys.argv) > 3 else 24
            await debugger.resource_access(resource_id, hours)

        elif command == "stats" and len(sys.argv) >= 3:
            org_id = sys.argv[2]
            days = int(sys.argv[3]) if len(sys.argv) > 3 else 7
            await debugger.permission_stats(org_id, days)

        elif command == "integrity":
            hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
            await debugger.verify_integrity(hours)

        elif command == "cache":
            hours = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            await debugger.cache_performance(hours)

        elif command == "correlation" and len(sys.argv) >= 3:
            request_id = sys.argv[2]
            await debugger.correlation_trace(request_id)

        else:
            print(f"❌ Unknown command or missing arguments: {command}\n")
            print_usage()
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await debugger.close()


if __name__ == "__main__":
    asyncio.run(main())
