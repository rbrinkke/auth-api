"""
Dashboard Module - Technical Monitoring Interface

Modular dashboard implementation following best practices:
- Separation of concerns (routes, services, rendering, components)
- Component-based architecture for maintainability
- Clean dependency flow (routes -> services -> components)
- Single responsibility principle throughout

Module Structure:
    - routes.py: HTTP request/response handling
    - metrics_service.py: Metrics collection orchestration
    - html_renderer.py: HTML document assembly
    - components.py: Reusable UI components (CSS, HTML, JS)

Public API:
    - router: FastAPI router with dashboard endpoints

Endpoints:
    GET /dashboard      - Interactive HTML dashboard
    GET /dashboard/api  - JSON API with comprehensive metrics

Author: Claude Code
Version: 2.0.0 (Refactored modular design)
"""

from app.routes.dashboard.routes import router

__all__ = ["router"]
