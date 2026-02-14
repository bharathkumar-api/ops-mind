"""Security and CORS middleware configuration."""
from fastapi import Request


def is_docs_endpoint(path: str) -> bool:
    """Check if the request path is a Swagger UI documentation endpoint."""
    return path.startswith("/docs") or path.startswith("/redoc") or path == "/openapi.json"


async def security_headers_middleware(request: Request, call_next):
    """Add security headers to responses, excluding docs endpoints."""
    response = await call_next(request)
    
    # Skip restrictive security headers for Swagger UI endpoints
    if not is_docs_endpoint(request.url.path):
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=()"
    
    return response
