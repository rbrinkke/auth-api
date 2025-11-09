"""
Dashboard Service - Comprehensive Technical Monitoring

Collects and aggregates all technical metrics for system monitoring and troubleshooting.
"""

import asyncio
import sys
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import structlog
from fastapi import HTTPException

from app.config import get_settings
from app.db.connection import DatabaseConnectionManager
from app.core.redis_client import RedisConnectionManager
from app.core.metrics import (
    http_requests_total,
    login_attempts_total,
    registrations_total,
    email_verifications_total,
    password_resets_total,
    two_fa_operations_total,
    token_operations_total,
    rate_limit_hits_total,
    invalid_credentials_total,
    password_validation_failures_total,
    db_queries_total,
    db_pool_active_connections,
    db_pool_idle_connections,
    redis_operations_total,
    active_users_total,
    active_sessions_total,
    two_fa_enabled_users_total,
    email_operations_total,
)

logger = structlog.get_logger(__name__)

# Track service start time for uptime calculation
SERVICE_START_TIME = datetime.now(timezone.utc)


class DashboardService:
    """Service for collecting and providing comprehensive dashboard metrics."""

    def __init__(self):
        self.settings = get_settings()
        self.db_manager = DatabaseConnectionManager()
        self.redis_manager = RedisConnectionManager()

    async def get_system_health(self) -> Dict[str, Any]:
        """
        Get system health status for all critical components.

        Returns:
            Dict with health status of database, redis, and uptime
        """
        health = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": (datetime.now(timezone.utc) - SERVICE_START_TIME).total_seconds(),
            "database": await self._check_database_health(),
            "redis": await self._check_redis_health(),
            "python_version": sys.version,
        }

        return health

    async def _check_database_health(self) -> Dict[str, Any]:
        """Check PostgreSQL database health."""
        try:
            pool = await self.db_manager.get_pool()
            async with pool.acquire() as conn:
                # Test query
                result = await conn.fetchval("SELECT 1")

                # Get database stats
                db_size = await conn.fetchval("""
                    SELECT pg_size_pretty(pg_database_size(current_database()))
                """)

                # Get table counts
                user_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM activity.users
                """)

                token_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM activity.refresh_tokens
                """)

                return {
                    "status": "healthy" if result == 1 else "unhealthy",
                    "host": self.settings.POSTGRES_HOST,
                    "database": self.settings.POSTGRES_DB,
                    "schema": self.settings.POSTGRES_SCHEMA,
                    "database_size": db_size,
                    "total_users": user_count,
                    "total_tokens": token_count,
                    "pool_min_size": self.settings.POSTGRES_POOL_MIN_SIZE,
                    "pool_max_size": self.settings.POSTGRES_POOL_MAX_SIZE,
                }
        except Exception as e:
            logger.error("database_health_check_failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "host": self.settings.POSTGRES_HOST,
            }

    async def _check_redis_health(self) -> Dict[str, Any]:
        """Check Redis cache health."""
        try:
            redis = await self.redis_manager.get_client()

            # Test ping
            pong = await redis.ping()

            # Get Redis info
            info = await redis.info()

            # Get key count estimate
            dbsize = await redis.dbsize()

            return {
                "status": "healthy" if pong else "unhealthy",
                "host": self.settings.REDIS_HOST,
                "port": self.settings.REDIS_PORT,
                "db": self.settings.REDIS_DB,
                "keys_count": dbsize,
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
            }
        except Exception as e:
            logger.error("redis_health_check_failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "host": self.settings.REDIS_HOST,
            }

    async def get_database_metrics(self) -> Dict[str, Any]:
        """
        Get detailed database metrics and statistics.

        Returns:
            Dict with database connection pool stats, table stats, and query counts
        """
        try:
            pool = await self.db_manager.get_pool()

            # Connection pool stats
            pool_stats = {
                "size": pool.get_size(),
                "idle_connections": pool.get_idle_size(),
                "active_connections": pool.get_size() - pool.get_idle_size(),
                "max_size": self.settings.POSTGRES_POOL_MAX_SIZE,
                "min_size": self.settings.POSTGRES_POOL_MIN_SIZE,
            }

            async with pool.acquire() as conn:
                # User statistics
                user_stats = await conn.fetchrow("""
                    SELECT
                        COUNT(*) as total_users,
                        COUNT(*) FILTER (WHERE is_verified = TRUE) as verified_users,
                        COUNT(*) FILTER (WHERE is_verified = FALSE) as unverified_users,
                        COUNT(*) FILTER (WHERE is_active = TRUE) as active_users,
                        COUNT(*) FILTER (WHERE is_active = FALSE) as inactive_users,
                        COUNT(*) FILTER (WHERE last_login_at IS NOT NULL) as users_with_login,
                        COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as new_users_24h,
                        COUNT(*) FILTER (WHERE last_login_at > NOW() - INTERVAL '24 hours') as logins_24h
                    FROM activity.users
                """)

                # Token statistics
                token_stats = await conn.fetchrow("""
                    SELECT
                        COUNT(*) as total_tokens,
                        COUNT(*) FILTER (WHERE revoked = FALSE) as active_tokens,
                        COUNT(*) FILTER (WHERE revoked = TRUE) as revoked_tokens,
                        COUNT(*) FILTER (WHERE expires_at > NOW()) as valid_tokens,
                        COUNT(*) FILTER (WHERE expires_at <= NOW()) as expired_tokens,
                        COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '1 hour') as tokens_created_1h
                    FROM activity.refresh_tokens
                """)

                # Recent activity - last 10 users
                recent_users = await conn.fetch("""
                    SELECT
                        id,
                        email,
                        is_verified,
                        created_at,
                        last_login_at
                    FROM activity.users
                    ORDER BY created_at DESC
                    LIMIT 10
                """)

                # Database table sizes
                table_sizes = await conn.fetch("""
                    SELECT
                        schemaname || '.' || tablename as table_name,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                    FROM pg_tables
                    WHERE schemaname = 'activity'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                """)

            return {
                "pool": pool_stats,
                "users": dict(user_stats) if user_stats else {},
                "tokens": dict(token_stats) if token_stats else {},
                "recent_users": [
                    {
                        "id": str(r["id"]),
                        "email": r["email"],
                        "is_verified": r["is_verified"],
                        "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                        "last_login_at": r["last_login_at"].isoformat() if r["last_login_at"] else None,
                    }
                    for r in recent_users
                ],
                "table_sizes": [
                    {"table": r["table_name"], "size": r["size"]}
                    for r in table_sizes
                ],
            }
        except Exception as e:
            logger.error("database_metrics_collection_failed", error=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to collect database metrics: {str(e)}")

    async def get_prometheus_metrics_summary(self) -> Dict[str, Any]:
        """
        Get summary of Prometheus metrics from the collectors.

        Returns:
            Dict with current metric values
        """
        try:
            metrics = {
                "http_requests": self._get_metric_value(http_requests_total),
                "authentication": {
                    "logins": self._get_metric_value(login_attempts_total),
                    "registrations": self._get_metric_value(registrations_total),
                    "email_verifications": self._get_metric_value(email_verifications_total),
                    "password_resets": self._get_metric_value(password_resets_total),
                    "two_fa_operations": self._get_metric_value(two_fa_operations_total),
                    "token_operations": self._get_metric_value(token_operations_total),
                },
                "security": {
                    "rate_limit_hits": self._get_metric_value(rate_limit_hits_total),
                    "invalid_credentials": self._get_metric_value(invalid_credentials_total),
                    "password_validation_failures": self._get_metric_value(password_validation_failures_total),
                },
                "database": {
                    "queries": self._get_metric_value(db_queries_total),
                    "active_connections": self._get_gauge_value(db_pool_active_connections),
                    "idle_connections": self._get_gauge_value(db_pool_idle_connections),
                },
                "redis": {
                    "operations": self._get_metric_value(redis_operations_total),
                },
                "business": {
                    "active_users": self._get_gauge_value(active_users_total),
                    "active_sessions": self._get_gauge_value(active_sessions_total),
                    "two_fa_enabled_users": self._get_gauge_value(two_fa_enabled_users_total),
                    "email_operations": self._get_metric_value(email_operations_total),
                },
            }

            return metrics
        except Exception as e:
            logger.error("prometheus_metrics_summary_failed", error=str(e))
            return {"error": str(e)}

    def _get_metric_value(self, metric) -> Dict[str, int]:
        """
        Extract values from a Counter metric.

        Args:
            metric: Prometheus Counter metric

        Returns:
            Dict with label combinations and their counts
        """
        try:
            result = {}
            for sample in metric.collect()[0].samples:
                labels = sample.labels
                value = int(sample.value)

                # Create a key from the labels
                if labels:
                    key = "_".join([f"{k}_{v}" for k, v in sorted(labels.items())])
                else:
                    key = "total"

                result[key] = value

            return result if result else {"total": 0}
        except Exception as e:
            logger.warning("metric_value_extraction_failed", metric=str(metric), error=str(e))
            return {"error": str(e)}

    def _get_gauge_value(self, gauge) -> float:
        """
        Extract value from a Gauge metric.

        Args:
            gauge: Prometheus Gauge metric

        Returns:
            Current gauge value
        """
        try:
            samples = list(gauge.collect()[0].samples)
            if samples:
                return samples[0].value
            return 0.0
        except Exception as e:
            logger.warning("gauge_value_extraction_failed", gauge=str(gauge), error=str(e))
            return 0.0

    async def get_configuration_info(self) -> Dict[str, Any]:
        """
        Get safe configuration information (no secrets).

        Returns:
            Dict with configuration settings
        """
        return {
            "environment": {
                "debug": self.settings.DEBUG,
                "log_level": self.settings.LOG_LEVEL,
                "host": self.settings.HOST,
                "port": self.settings.PORT,
            },
            "database": {
                "host": self.settings.POSTGRES_HOST,
                "port": self.settings.POSTGRES_PORT,
                "database": self.settings.POSTGRES_DB,
                "schema": self.settings.POSTGRES_SCHEMA,
                "pool_min_size": self.settings.POSTGRES_POOL_MIN_SIZE,
                "pool_max_size": self.settings.POSTGRES_POOL_MAX_SIZE,
            },
            "redis": {
                "host": self.settings.REDIS_HOST,
                "port": self.settings.REDIS_PORT,
                "db": self.settings.REDIS_DB,
            },
            "jwt": {
                "algorithm": self.settings.JWT_ALGORITHM,
                "access_token_expire_minutes": self.settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
                "refresh_token_expire_days": self.settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS,
            },
            "security": {
                "cors_origins": self.settings.CORS_ORIGINS,
                "two_factor_enabled": self.settings.TWO_FACTOR_ENABLED,
                "verification_token_ttl": self.settings.VERIFICATION_TOKEN_TTL,
                "reset_token_ttl": self.settings.RESET_TOKEN_TTL,
            },
            "rate_limiting": {
                "register_per_hour": self.settings.RATE_LIMIT_REGISTER_PER_HOUR,
                "login_per_minute": self.settings.RATE_LIMIT_LOGIN_PER_MINUTE,
                "password_reset_per_5min": self.settings.RATE_LIMIT_PASSWORD_RESET_PER_5MIN,
            },
            "email": {
                "service_url": self.settings.EMAIL_SERVICE_URL,
                "timeout": self.settings.EMAIL_SERVICE_TIMEOUT,
                "frontend_url": self.settings.FRONTEND_URL,
            },
        }

    async def get_comprehensive_dashboard(self) -> Dict[str, Any]:
        """
        Get all dashboard data in one comprehensive call.

        Returns:
            Dict with all dashboard sections
        """
        try:
            # Collect all data concurrently for performance
            system_health, db_metrics, config_info = await asyncio.gather(
                self.get_system_health(),
                self.get_database_metrics(),
                asyncio.to_thread(self.get_configuration_info),
                return_exceptions=True
            )

            # Get Prometheus metrics summary (sync operation)
            prometheus_metrics = self.get_prometheus_metrics_summary()

            dashboard = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "system_health": system_health if not isinstance(system_health, Exception) else {"error": str(system_health)},
                "database_metrics": db_metrics if not isinstance(db_metrics, Exception) else {"error": str(db_metrics)},
                "prometheus_metrics": prometheus_metrics,
                "configuration": config_info if not isinstance(config_info, Exception) else {"error": str(config_info)},
            }

            return dashboard
        except Exception as e:
            logger.error("comprehensive_dashboard_collection_failed", error=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to collect dashboard data: {str(e)}")
