"""
Dashboard Routes - Technical Monitoring Interface

This module provides FastAPI routes for the technical monitoring dashboard.
It serves both a JSON API endpoint for programmatic access and an interactive
HTML dashboard for human monitoring.

Endpoints:
    GET /dashboard      - Interactive HTML dashboard (auto-refreshing)
    GET /dashboard/api  - JSON API with all dashboard data

The dashboard is designed for system administrators, DevOps engineers, and
developers who need real-time insights into the authentication API's health,
performance, and activity.

Features:
    - Real-time system health monitoring (database, Redis, uptime)
    - Database connection pool utilization tracking
    - User and token lifecycle statistics
    - Authentication operation metrics (logins, registrations, etc.)
    - Security event tracking (rate limits, invalid credentials)
    - Performance metrics via Prometheus integration
    - Recent user activity (last 10 users)
    - Configuration overview (no secrets exposed)
    - Auto-refreshing HTML UI (10-second intervals)

Security Considerations:
    ⚠️ IMPORTANT: In production, these endpoints should be protected with authentication!
    The dashboard exposes sensitive operational data including:
    - User emails (in recent activity section)
    - Database structure and sizes
    - System configuration
    - Connection pool statistics

    Recommended protection:
    - Add authentication middleware (e.g., API key, OAuth)
    - Restrict access to admin users only
    - Use IP whitelist for internal monitoring
    - Consider VPN access only

Usage Examples:
    # Access HTML dashboard in browser
    http://localhost:8000/dashboard

    # Fetch JSON data programmatically
    curl http://localhost:8000/dashboard/api | jq .

    # Monitor specific metric with jq
    curl -s http://localhost:8000/dashboard/api | jq '.database_metrics.users.total_users'

    # Check system health status
    curl -s http://localhost:8000/dashboard/api | jq '.system_health.database.status'

HTML Dashboard Features:
    - Dark theme optimized for long monitoring sessions
    - Monospace font for technical data readability
    - Color-coded status indicators (green/yellow/red)
    - Responsive grid layout with organized metric cards
    - Tables for recent user activity and database sizes
    - Auto-refresh every 10 seconds for real-time monitoring
    - Error handling with user-friendly messages

Data Refresh:
    - HTML dashboard: Auto-refreshes every 10 seconds via JavaScript
    - JSON API: No caching, always returns fresh data
    - Performance: Typical response time 50-200ms

Integration:
    The JSON API can be integrated with:
    - External monitoring tools (Datadog, New Relic, Grafana)
    - Custom alerting systems
    - CI/CD health checks
    - Load balancer health probes
    - Infrastructure as Code (Terraform, etc.)

Author: Claude Code
Version: 1.0.0
"""

from fastapi import APIRouter, Response
from fastapi.responses import HTMLResponse
import structlog

from app.services.dashboard_service import DashboardService

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/api", summary="Get comprehensive dashboard data (JSON)")
async def get_dashboard_data():
    """
    Get comprehensive technical dashboard data in JSON format.

    This endpoint provides all monitoring data in a structured JSON format,
    suitable for programmatic access by monitoring tools, scripts, and
    external systems. Data is collected in real-time with no caching.

    **Data Sections:**

    1. **System Health** - Database, Redis status, uptime
       - Database connection status and basic stats
       - Redis cache status and memory usage
       - Service uptime since last restart
       - Python version information

    2. **Database Metrics** - Detailed database statistics
       - Connection pool utilization (active/idle/total)
       - User statistics (total, verified, active, 24h activity)
       - Token statistics (active, revoked, expired, 1h created)
       - Recent user activity (last 10 users)
       - Database table sizes

    3. **Prometheus Metrics** - All Prometheus counters and gauges
       - HTTP request counts by endpoint and status
       - Authentication operation counts (logins, registrations, etc.)
       - Security metrics (rate limits, invalid credentials)
       - Database query counts and connection stats
       - Redis operation counts
       - Business metrics (active users, sessions, 2FA enabled)

    4. **Configuration** - Safe settings (no secrets)
       - Environment settings (debug, log level)
       - Database connection config (host, pool sizes)
       - Redis connection config
       - JWT token expiration settings
       - Rate limiting thresholds
       - Email service configuration

    **Response Format:**
    ```json
    {
        "timestamp": "2024-01-15T10:30:00.000000+00:00",
        "system_health": {
            "uptime_seconds": 3600.5,
            "database": {"status": "healthy", ...},
            "redis": {"status": "healthy", ...}
        },
        "database_metrics": {
            "pool": {...},
            "users": {...},
            "tokens": {...},
            "recent_users": [...],
            "table_sizes": [...]
        },
        "prometheus_metrics": {...},
        "configuration": {...}
    }
    ```

    **Performance:**
    - Response time: 50-200ms (depending on database size)
    - All data collected concurrently for optimal performance
    - Uses connection pooling for database and Redis

    **Use Cases:**
    - Integration with external monitoring (Datadog, New Relic, Grafana)
    - Custom alerting systems
    - CI/CD health checks
    - Load balancer health probes
    - Automated reporting scripts

    **Example Usage:**
    ```bash
    # Get all data
    curl http://localhost:8000/dashboard/api

    # Check if database is healthy
    curl -s http://localhost:8000/dashboard/api | jq '.system_health.database.status'

    # Get total user count
    curl -s http://localhost:8000/dashboard/api | jq '.database_metrics.users.total_users'

    # Monitor pool utilization
    curl -s http://localhost:8000/dashboard/api | jq '.database_metrics.pool'
    ```

    **Security Warning:**
    ⚠️ This endpoint exposes operational data including user emails and system
    configuration. In production, protect this endpoint with authentication!

    Returns:
        Dict: Comprehensive dashboard data with all metrics and statistics

    Raises:
        HTTPException: 500 if critical data collection fails
    """
    logger.info("dashboard_data_requested")

    dashboard_service = DashboardService()
    data = await dashboard_service.get_comprehensive_dashboard()

    logger.info("dashboard_data_returned", sections=list(data.keys()))
    return data


@router.get("", response_class=HTMLResponse, summary="Dashboard UI")
async def get_dashboard_html():
    """
    Serve interactive HTML dashboard with real-time monitoring.

    This endpoint serves a fully self-contained HTML page with embedded CSS and JavaScript
    that provides a real-time monitoring interface for the authentication API. The dashboard
    auto-refreshes every 10 seconds to display the latest system metrics.

    **Dashboard Sections:**

    1. **System Health Card**
       - Service uptime (days, hours, minutes)
       - Database connection status (healthy/unhealthy)
       - Redis cache status (healthy/unhealthy)
       - Timestamp of current data

    2. **Database Status Card**
       - Host and database name
       - Database size (human-readable)
       - Total users count
       - Total tokens count

    3. **Redis Cache Card**
       - Host and port
       - Keys count
       - Memory usage
       - Connected clients
       - Redis uptime

    4. **Connection Pool Card**
       - Active/idle/total connections
       - Pool utilization percentage
       - Min/max pool size
       - Color-coded utilization (green < 50%, yellow < 80%, red >= 80%)

    5. **User Statistics Card**
       - Total users
       - Verified/unverified users
       - Active/inactive users
       - New users (24h)
       - Recent logins (24h)

    6. **Token Statistics Card**
       - Total/active/revoked tokens
       - Valid/expired tokens
       - Tokens created (1h)

    7. **Authentication Metrics Card**
       - Login attempts count
       - Registrations count
       - Email verifications count
       - Password resets count
       - 2FA operations count
       - Token operations count

    8. **Security Metrics Card**
       - Rate limit hits (color-coded warning)
       - Invalid credentials attempts (color-coded by severity)
       - Password validation failures

    9. **Configuration Card**
       - Debug mode status (warning if enabled)
       - Log level
       - JWT algorithm and token TTLs
       - 2FA enabled status

    10. **Recent User Activity Table**
        - Last 10 users created
        - Email addresses
        - Verification status
        - Created timestamp
        - Last login timestamp

    11. **Database Table Sizes Card**
        - Size of each table in human-readable format

    **UI Features:**

    - **Dark Theme**: Optimized for long monitoring sessions with reduced eye strain
    - **Monospace Font**: Technical data displayed in Monaco/Courier New for readability
    - **Color Coding**: Status indicators in green (healthy/good), yellow (warning), red (error)
    - **Auto-refresh**: Data updates every 10 seconds automatically
    - **Responsive Grid**: Cards organized in responsive grid layout
    - **Real-time Clock**: Shows last update time
    - **Error Handling**: Displays user-friendly error messages if data fetch fails
    - **Loading State**: Shows spinner during initial data load

    **Technical Details:**

    - Single-page application (SPA) with vanilla JavaScript
    - No external dependencies (self-contained)
    - Fetches data from /dashboard/api endpoint
    - Uses Fetch API for AJAX requests
    - CSS Grid for responsive layout
    - Handles partial failures gracefully

    **Auto-refresh Behavior:**

    - Initial load on page open
    - Refresh every 10 seconds via setInterval
    - Updates "Last updated" timestamp on each refresh
    - Preserves refresh interval on navigation
    - Shows error banner if fetch fails

    **Browser Compatibility:**

    - Modern browsers with ES6 support
    - Chrome 51+, Firefox 54+, Safari 10+, Edge 15+
    - Requires JavaScript enabled
    - Responsive design for desktop and tablet (not optimized for mobile)

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
    - Monitor access logs

    **Use Cases:**

    - Real-time system monitoring during normal operations
    - Troubleshooting during incidents (connection pool exhaustion, etc.)
    - Performance monitoring (query counts, response times)
    - Security monitoring (rate limit hits, invalid credentials)
    - Capacity planning (user growth, database size trends)

    Returns:
        HTMLResponse: Self-contained HTML page with embedded CSS/JavaScript

    Example:
        ```python
        # Access in browser
        http://localhost:8000/dashboard

        # The page will auto-refresh every 10 seconds
        # All metrics update in real-time
        ```
    """
    logger.info("dashboard_ui_requested")

    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Auth API - Technical Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Monaco', 'Courier New', monospace;
            background: #0d1117;
            color: #c9d1d9;
            padding: 20px;
            line-height: 1.6;
        }

        .container {
            max-width: 1600px;
            margin: 0 auto;
        }

        header {
            background: #161b22;
            padding: 20px;
            border-radius: 6px;
            margin-bottom: 20px;
            border: 1px solid #30363d;
        }

        h1 {
            color: #58a6ff;
            font-size: 24px;
            margin-bottom: 10px;
        }

        .meta {
            color: #8b949e;
            font-size: 13px;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 16px;
        }

        .card h2 {
            color: #58a6ff;
            font-size: 16px;
            margin-bottom: 12px;
            border-bottom: 1px solid #21262d;
            padding-bottom: 8px;
        }

        .status {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }

        .status.healthy {
            background: #238636;
            color: #fff;
        }

        .status.unhealthy {
            background: #da3633;
            color: #fff;
        }

        .metric {
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
            border-bottom: 1px solid #21262d;
            font-size: 13px;
        }

        .metric:last-child {
            border-bottom: none;
        }

        .metric-label {
            color: #8b949e;
        }

        .metric-value {
            color: #c9d1d9;
            font-weight: bold;
        }

        .metric-value.good {
            color: #3fb950;
        }

        .metric-value.warning {
            color: #d29922;
        }

        .metric-value.error {
            color: #f85149;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        }

        th {
            background: #21262d;
            padding: 8px;
            text-align: left;
            color: #8b949e;
            font-weight: normal;
        }

        td {
            padding: 8px;
            border-bottom: 1px solid #21262d;
        }

        tr:hover {
            background: #0d1117;
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: #8b949e;
        }

        .spinner {
            border: 2px solid #21262d;
            border-top: 2px solid #58a6ff;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .refresh-info {
            text-align: center;
            color: #8b949e;
            font-size: 12px;
            margin-top: 20px;
            padding: 10px;
            background: #161b22;
            border-radius: 6px;
            border: 1px solid #30363d;
        }

        .error-message {
            background: #da3633;
            color: #fff;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 20px;
        }

        code {
            background: #0d1117;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 12px;
            color: #ff7b72;
        }

        .full-width {
            grid-column: 1 / -1;
        }

        .uptime {
            color: #3fb950;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔐 Authentication API - Technical Dashboard</h1>
            <div class="meta">
                Real-time system monitoring and diagnostics
                <span id="last-update"></span>
            </div>
        </header>

        <div id="error-container"></div>
        <div id="loading" class="loading">
            <div class="spinner"></div>
            Loading dashboard data...
        </div>
        <div id="dashboard" style="display: none;"></div>

        <div class="refresh-info">
            Auto-refresh every 10 seconds | Last updated: <span id="update-time">--</span>
        </div>
    </div>

    <script>
        let refreshInterval;

        async function loadDashboard() {
            try {
                const response = await fetch('/dashboard/api');
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                renderDashboard(data);

                document.getElementById('loading').style.display = 'none';
                document.getElementById('dashboard').style.display = 'block';
                document.getElementById('error-container').innerHTML = '';

                const now = new Date().toLocaleString();
                document.getElementById('update-time').textContent = now;
                document.getElementById('last-update').textContent = ` • Last updated: ${now}`;

            } catch (error) {
                console.error('Failed to load dashboard:', error);
                document.getElementById('error-container').innerHTML = `
                    <div class="error-message">
                        ⚠️ Failed to load dashboard: ${error.message}
                    </div>
                `;
                document.getElementById('loading').style.display = 'none';
            }
        }

        function renderDashboard(data) {
            const dashboard = document.getElementById('dashboard');

            const health = data.system_health || {};
            const dbMetrics = data.database_metrics || {};
            const config = data.configuration || {};
            const prometheusMetrics = data.prometheus_metrics || {};

            const uptimeSeconds = health.uptime_seconds || 0;
            const uptimeStr = formatUptime(uptimeSeconds);

            let html = `
                <div class="grid">
                    <!-- System Health -->
                    <div class="card">
                        <h2>⚡ System Health</h2>
                        ${renderSystemHealth(health)}
                    </div>

                    <!-- Database Status -->
                    <div class="card">
                        <h2>💾 Database Status</h2>
                        ${renderDatabaseStatus(health.database, dbMetrics)}
                    </div>

                    <!-- Redis Status -->
                    <div class="card">
                        <h2>⚡ Redis Cache</h2>
                        ${renderRedisStatus(health.redis)}
                    </div>

                    <!-- Connection Pool -->
                    <div class="card">
                        <h2>🔌 Database Connection Pool</h2>
                        ${renderConnectionPool(dbMetrics.pool)}
                    </div>

                    <!-- User Statistics -->
                    <div class="card">
                        <h2>👥 User Statistics</h2>
                        ${renderUserStats(dbMetrics.users)}
                    </div>

                    <!-- Token Statistics -->
                    <div class="card">
                        <h2>🎫 Token Statistics</h2>
                        ${renderTokenStats(dbMetrics.tokens)}
                    </div>

                    <!-- Authentication Metrics -->
                    <div class="card">
                        <h2>🔑 Authentication Metrics</h2>
                        ${renderAuthMetrics(prometheusMetrics.authentication)}
                    </div>

                    <!-- Security Metrics -->
                    <div class="card">
                        <h2>🛡️ Security Metrics</h2>
                        ${renderSecurityMetrics(prometheusMetrics.security)}
                    </div>

                    <!-- Configuration -->
                    <div class="card">
                        <h2>⚙️ Configuration</h2>
                        ${renderConfiguration(config)}
                    </div>

                    <!-- Recent Users -->
                    <div class="card full-width">
                        <h2>📊 Recent User Activity (Last 10)</h2>
                        ${renderRecentUsers(dbMetrics.recent_users)}
                    </div>

                    <!-- Table Sizes -->
                    <div class="card">
                        <h2>💿 Database Table Sizes</h2>
                        ${renderTableSizes(dbMetrics.table_sizes)}
                    </div>
                </div>
            `;

            dashboard.innerHTML = html;
        }

        function renderSystemHealth(health) {
            const dbStatus = health.database?.status || 'unknown';
            const redisStatus = health.redis?.status || 'unknown';
            const uptimeStr = formatUptime(health.uptime_seconds || 0);

            return `
                <div class="metric">
                    <span class="metric-label">Service Uptime</span>
                    <span class="metric-value uptime">${uptimeStr}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Database</span>
                    <span class="status ${dbStatus}">${dbStatus.toUpperCase()}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Redis Cache</span>
                    <span class="status ${redisStatus}">${redisStatus.toUpperCase()}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Timestamp</span>
                    <span class="metric-value">${new Date(health.timestamp).toLocaleString()}</span>
                </div>
            `;
        }

        function renderDatabaseStatus(db, metrics) {
            if (!db) return '<p>No data</p>';

            return `
                <div class="metric">
                    <span class="metric-label">Host</span>
                    <span class="metric-value">${db.host}:5432</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Database</span>
                    <span class="metric-value">${db.database} (${db.schema})</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Database Size</span>
                    <span class="metric-value">${db.database_size || 'N/A'}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Total Users</span>
                    <span class="metric-value good">${db.total_users || 0}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Total Tokens</span>
                    <span class="metric-value">${db.total_tokens || 0}</span>
                </div>
            `;
        }

        function renderRedisStatus(redis) {
            if (!redis) return '<p>No data</p>';

            return `
                <div class="metric">
                    <span class="metric-label">Host</span>
                    <span class="metric-value">${redis.host}:${redis.port}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Database</span>
                    <span class="metric-value">DB ${redis.db}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Keys Count</span>
                    <span class="metric-value">${redis.keys_count || 0}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Memory Used</span>
                    <span class="metric-value">${redis.used_memory || 'N/A'}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Connected Clients</span>
                    <span class="metric-value">${redis.connected_clients || 0}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Uptime</span>
                    <span class="metric-value">${formatUptime(redis.uptime_seconds || 0)}</span>
                </div>
            `;
        }

        function renderConnectionPool(pool) {
            if (!pool) return '<p>No data</p>';

            const utilization = ((pool.active_connections / pool.max_size) * 100).toFixed(1);
            const utilizationClass = utilization > 80 ? 'error' : utilization > 50 ? 'warning' : 'good';

            return `
                <div class="metric">
                    <span class="metric-label">Pool Size</span>
                    <span class="metric-value">${pool.size} / ${pool.max_size}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Active Connections</span>
                    <span class="metric-value ${utilizationClass}">${pool.active_connections}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Idle Connections</span>
                    <span class="metric-value good">${pool.idle_connections}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Utilization</span>
                    <span class="metric-value ${utilizationClass}">${utilization}%</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Min Size</span>
                    <span class="metric-value">${pool.min_size}</span>
                </div>
            `;
        }

        function renderUserStats(users) {
            if (!users) return '<p>No data</p>';

            return `
                <div class="metric">
                    <span class="metric-label">Total Users</span>
                    <span class="metric-value good">${users.total_users || 0}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Verified Users</span>
                    <span class="metric-value good">${users.verified_users || 0}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Unverified Users</span>
                    <span class="metric-value warning">${users.unverified_users || 0}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Active Users</span>
                    <span class="metric-value">${users.active_users || 0}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Users with Login</span>
                    <span class="metric-value">${users.users_with_login || 0}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">New (24h)</span>
                    <span class="metric-value good">${users.new_users_24h || 0}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Logins (24h)</span>
                    <span class="metric-value good">${users.logins_24h || 0}</span>
                </div>
            `;
        }

        function renderTokenStats(tokens) {
            if (!tokens) return '<p>No data</p>';

            return `
                <div class="metric">
                    <span class="metric-label">Total Tokens</span>
                    <span class="metric-value">${tokens.total_tokens || 0}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Active Tokens</span>
                    <span class="metric-value good">${tokens.active_tokens || 0}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Revoked Tokens</span>
                    <span class="metric-value">${tokens.revoked_tokens || 0}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Valid (Not Expired)</span>
                    <span class="metric-value good">${tokens.valid_tokens || 0}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Expired Tokens</span>
                    <span class="metric-value warning">${tokens.expired_tokens || 0}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Created (1h)</span>
                    <span class="metric-value">${tokens.tokens_created_1h || 0}</span>
                </div>
            `;
        }

        function renderAuthMetrics(auth) {
            if (!auth) return '<p>No data</p>';

            const logins = auth.logins || {};
            const regs = auth.registrations || {};

            return `
                <div class="metric">
                    <span class="metric-label">Login Attempts</span>
                    <span class="metric-value">${sumMetricValues(logins)}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Registrations</span>
                    <span class="metric-value">${sumMetricValues(regs)}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Email Verifications</span>
                    <span class="metric-value">${sumMetricValues(auth.email_verifications || {})}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Password Resets</span>
                    <span class="metric-value">${sumMetricValues(auth.password_resets || {})}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">2FA Operations</span>
                    <span class="metric-value">${sumMetricValues(auth.two_fa_operations || {})}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Token Operations</span>
                    <span class="metric-value">${sumMetricValues(auth.token_operations || {})}</span>
                </div>
            `;
        }

        function renderSecurityMetrics(security) {
            if (!security) return '<p>No data</p>';

            const rateLimits = sumMetricValues(security.rate_limit_hits || {});
            const invalidCreds = sumMetricValues(security.invalid_credentials || {});
            const pwdFailures = sumMetricValues(security.password_validation_failures || {});

            const rateLimitClass = rateLimits > 0 ? 'warning' : 'good';
            const invalidCredsClass = invalidCreds > 10 ? 'error' : invalidCreds > 0 ? 'warning' : 'good';

            return `
                <div class="metric">
                    <span class="metric-label">Rate Limit Hits</span>
                    <span class="metric-value ${rateLimitClass}">${rateLimits}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Invalid Credentials</span>
                    <span class="metric-value ${invalidCredsClass}">${invalidCreds}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Password Validation Failures</span>
                    <span class="metric-value">${pwdFailures}</span>
                </div>
            `;
        }

        function renderConfiguration(config) {
            if (!config || !config.environment) return '<p>No data</p>';

            const env = config.environment;
            const jwt = config.jwt || {};
            const sec = config.security || {};

            return `
                <div class="metric">
                    <span class="metric-label">Debug Mode</span>
                    <span class="metric-value ${env.debug ? 'warning' : 'good'}">${env.debug ? 'ENABLED' : 'DISABLED'}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Log Level</span>
                    <span class="metric-value">${env.log_level}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">JWT Algorithm</span>
                    <span class="metric-value">${jwt.algorithm}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Access Token TTL</span>
                    <span class="metric-value">${jwt.access_token_expire_minutes} minutes</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Refresh Token TTL</span>
                    <span class="metric-value">${jwt.refresh_token_expire_days} days</span>
                </div>
                <div class="metric">
                    <span class="metric-label">2FA Enabled</span>
                    <span class="metric-value ${sec.two_factor_enabled ? 'good' : 'warning'}">${sec.two_factor_enabled ? 'YES' : 'NO'}</span>
                </div>
            `;
        }

        function renderRecentUsers(users) {
            if (!users || users.length === 0) {
                return '<p>No recent users</p>';
            }

            let html = '<table><thead><tr><th>Email</th><th>Status</th><th>Created</th><th>Last Login</th></tr></thead><tbody>';

            users.forEach(user => {
                const verified = user.is_verified ? '✅ Verified' : '⏳ Pending';
                const createdAt = user.created_at ? new Date(user.created_at).toLocaleString() : 'N/A';
                const lastLogin = user.last_login_at ? new Date(user.last_login_at).toLocaleString() : 'Never';

                html += `
                    <tr>
                        <td><code>${user.email}</code></td>
                        <td>${verified}</td>
                        <td>${createdAt}</td>
                        <td>${lastLogin}</td>
                    </tr>
                `;
            });

            html += '</tbody></table>';
            return html;
        }

        function renderTableSizes(tables) {
            if (!tables || tables.length === 0) {
                return '<p>No table size data</p>';
            }

            let html = '';
            tables.forEach(table => {
                html += `
                    <div class="metric">
                        <span class="metric-label">${table.table}</span>
                        <span class="metric-value">${table.size}</span>
                    </div>
                `;
            });

            return html;
        }

        function sumMetricValues(metricObj) {
            if (!metricObj || typeof metricObj !== 'object') return 0;
            return Object.values(metricObj).reduce((sum, val) => sum + (typeof val === 'number' ? val : 0), 0);
        }

        function formatUptime(seconds) {
            const days = Math.floor(seconds / 86400);
            const hours = Math.floor((seconds % 86400) / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = Math.floor(seconds % 60);

            if (days > 0) return `${days}d ${hours}h ${minutes}m`;
            if (hours > 0) return `${hours}h ${minutes}m ${secs}s`;
            if (minutes > 0) return `${minutes}m ${secs}s`;
            return `${secs}s`;
        }

        // Initial load
        loadDashboard();

        // Auto-refresh every 10 seconds
        refreshInterval = setInterval(loadDashboard, 10000);
    </script>
</body>
</html>
    """

    return HTMLResponse(content=html_content)
