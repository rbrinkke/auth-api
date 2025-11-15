"""
Dashboard Metrics Collection Service

Thin adapter layer between route handlers and the core DashboardService.
This service encapsulates metrics collection logic and provides a clean
interface for route handlers.

Architecture:
    - Adapter Pattern: Adapts DashboardService for route layer
    - Dependency Injection: DashboardService injected via constructor
    - Single Responsibility: Only responsible for metrics orchestration

Design Philosophy:
    - Keep routes thin - complex logic stays in service layer
    - Provide clear, domain-specific interface
    - Enable easy testing through dependency injection

Author: Claude Code
Version: 2.0.0 (Refactored modular design)
"""

from typing import Dict, Any

from app.services.dashboard_service import DashboardService


class MetricsService:
    """
    Service for collecting and orchestrating dashboard metrics.

    This class acts as an adapter between the route layer and the core
    DashboardService. It provides a clean interface for route handlers
    while delegating actual metrics collection to the service layer.

    Attributes:
        dashboard_service: Core service for dashboard data collection

    Methods:
        get_comprehensive_dashboard() -> Dict: Collect all dashboard metrics

    Example:
        ```python
        service = MetricsService()
        data = await service.get_comprehensive_dashboard()
        return JSONResponse(content=data)
        ```
    """

    def __init__(self):
        """
        Initialize the metrics service.

        Creates an instance of the core DashboardService for metrics collection.
        This design enables easy dependency injection and testing.
        """
        self.dashboard_service = DashboardService()

    async def get_comprehensive_dashboard(self) -> Dict[str, Any]:
        """
        Get comprehensive technical dashboard data.

        Delegates to DashboardService to collect all system metrics including:
        - System health (database, Redis, uptime)
        - Database metrics (pool, users, tokens, activity)
        - Prometheus metrics (HTTP, auth, security)
        - Configuration info (safe settings without secrets)

        Returns:
            Dict: Comprehensive dashboard data with all metrics and statistics

        Raises:
            HTTPException: If critical data collection fails

        Example:
            ```python
            metrics = await service.get_comprehensive_dashboard()
            print(f"Total users: {metrics['database_metrics']['users']['total_users']}")
            ```
        """
        return await self.dashboard_service.get_comprehensive_dashboard()
