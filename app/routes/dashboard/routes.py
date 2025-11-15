"""
Dashboard Route Handlers

Minimal, focused route handlers for dashboard endpoints.
Following the "thin controller" pattern - routes handle HTTP concerns only,
delegating all business logic to service and renderer layers.

Endpoints:
    GET /dashboard      - Interactive HTML dashboard with auto-refresh
    GET /dashboard/api  - JSON API with comprehensive metrics

Architecture:
    - Thin Controllers: Routes handle only HTTP request/response
    - Service Layer: Business logic in MetricsService
    - View Layer: HTML rendering in HTMLRenderer
    - Separation of Concerns: Clean boundaries between layers

Security Note:
    ⚠️ In production, protect these endpoints with authentication!
    The dashboard exposes sensitive operational data.

Author: Claude Code
Version: 2.0.0 (Refactored modular design)
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import structlog

from app.routes.dashboard.metrics_service import MetricsService
from app.routes.dashboard.html_renderer import HTMLRenderer

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/api", summary="Get comprehensive dashboard data (JSON)")
async def get_dashboard_data():
    """
    Get comprehensive technical dashboard data in JSON format.

    This endpoint provides all monitoring data in structured JSON format,
    suitable for programmatic access by monitoring tools, scripts, and
    external systems. Data is collected in real-time with no caching.

    **Data Sections:**

    1. **System Health** - Database, Redis status, uptime
    2. **Database Metrics** - Pool stats, users, tokens, recent activity
    3. **Prometheus Metrics** - All counters/gauges by category
    4. **Configuration** - Safe settings (no secrets)

    **Response Format:**
    ```json
    {
        "timestamp": "2024-01-15T10:30:00+00:00",
        "system_health": { ... },
        "database_metrics": { ... },
        "prometheus_metrics": { ... },
        "configuration": { ... }
    }
    ```

    **Performance:**
    - Response time: 50-200ms (depending on database size)
    - All data collected concurrently for optimal performance

    **Security Warning:**
    ⚠️ This endpoint exposes operational data including user emails and system
    configuration. In production, protect this endpoint with authentication!

    Returns:
        Dict: Comprehensive dashboard data with all metrics and statistics

    Raises:
        HTTPException: 500 if critical data collection fails

    Example:
        ```bash
        curl http://localhost:8000/dashboard/api | jq .
        curl -s http://localhost:8000/dashboard/api | jq '.system_health.database.status'
        ```
    """
    logger.info("dashboard_data_requested")

    metrics_service = MetricsService()
    data = await metrics_service.get_comprehensive_dashboard()

    logger.info("dashboard_data_returned", sections=list(data.keys()))
    return data


@router.get("", response_class=HTMLResponse, summary="Dashboard UI")
async def get_dashboard_html():
    """
    Serve interactive HTML dashboard with real-time monitoring.

    This endpoint serves a self-contained HTML page with embedded CSS and JavaScript
    that provides a real-time monitoring interface. The dashboard auto-refreshes
    every 10 seconds to display the latest system metrics.

    **Dashboard Features:**

    - **Dark Theme**: GitHub-inspired dark theme optimized for monitoring
    - **Auto-refresh**: Updates every 10 seconds automatically
    - **Real-time Metrics**: System health, database, Redis, users, tokens
    - **Security Monitoring**: Rate limits, invalid credentials, auth attempts
    - **Performance Tracking**: Connection pool utilization, query counts
    - **Recent Activity**: Last 10 users with verification status

    **UI Components:**

    1. System Health Card - Uptime, database/Redis status
    2. Database Status Card - Host, size, user/token counts
    3. Redis Cache Card - Keys, memory, clients, uptime
    4. Connection Pool Card - Active/idle connections, utilization
    5. User Statistics Card - Total, verified, active, 24h activity
    6. Token Statistics Card - Active, revoked, expired, 1h created
    7. Authentication Metrics Card - Logins, registrations, verifications
    8. Security Metrics Card - Rate limits, invalid credentials
    9. Configuration Card - Debug mode, JWT settings, 2FA status
    10. Recent Activity Table - Last 10 users with details
    11. Table Sizes Card - Database table sizes

    **Browser Compatibility:**
    - Modern browsers with ES6 support
    - Chrome 51+, Firefox 54+, Safari 10+, Edge 15+
    - Requires JavaScript enabled

    **Access:**
    Open in browser: http://localhost:8000/dashboard

    **Security Warning:**

    ⚠️ This dashboard displays sensitive operational data including:
    - User email addresses (last 10 recent users)
    - Database structure and sizes
    - System configuration details
    - Connection pool statistics

    In production environments:
    - Add authentication middleware (API key, OAuth, etc.)
    - Restrict to admin users only
    - Use IP whitelist for internal access
    - Consider VPN-only access

    Returns:
        HTMLResponse: Self-contained HTML page with embedded CSS/JavaScript

    Example:
        ```python
        # Access in browser
        http://localhost:8000/dashboard
        ```
    """
    logger.info("dashboard_ui_requested")

    html_renderer = HTMLRenderer()
    html_content = html_renderer.render()

    return HTMLResponse(content=html_content)
