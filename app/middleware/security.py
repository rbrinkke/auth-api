from fastapi import Request, Response

from app.config import settings


async def add_security_headers(request: Request, call_next) -> Response:
    response = await call_next(request)

    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Content-Security-Policy": "default-src 'self'",
        "Server": "",
    }

    if not settings.debug:
        headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    for header, value in headers.items():
        response.headers[header] = value

    return response
