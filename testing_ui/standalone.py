"""
Standalone launcher for the Authentication Testing UI.

This runs the testing UI as a completely separate FastAPI application
on port 8099, independent from the main auth-api.

Usage:
    python testing_ui/standalone.py

    Or with custom port:
    PORT=9000 python testing_ui/standalone.py
"""

import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from router import router

# Create standalone FastAPI app
app = FastAPI(
    title="Auth API Testing UI",
    description="Standalone testing interface for Authentication API",
    version="1.0.0",
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],  # Auth API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include testing router
app.include_router(router)


@app.get("/", include_in_schema=False)
async def root():
    """Redirect to testing page"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/test/auth")


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "auth-testing-ui",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8099"))

    print(f"""
╔═══════════════════════════════════════════════════════════╗
║  🧪 Auth API Testing UI - Standalone Mode                ║
╟───────────────────────────────────────────────────────────╢
║  URL:     http://localhost:{port}/test/auth             ║
║  Health:  http://localhost:{port}/health                ║
║  Docs:    http://localhost:{port}/docs                  ║
╟───────────────────────────────────────────────────────────╢
║  Target:  http://localhost:8000 (auth-api)              ║
╚═══════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "testing_ui.standalone:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
