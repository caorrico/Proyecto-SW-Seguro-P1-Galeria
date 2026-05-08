from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Aplica headers de seguridad HTTP a todas las respuestas.

    Controles implementados:
    - Content-Security-Policy (CSP): previene XSS y carga de recursos no autorizados
    - X-Content-Type-Options: nosniff — previene MIME type sniffing
    - X-Frame-Options: DENY — previene Clickjacking
    - Strict-Transport-Security (HSTS) — fuerza HTTPS en producción
    - Referrer-Policy — minimiza fuga de información en el header Referer
    - Permissions-Policy — deshabilita APIs sensibles del navegador
    """

    _CSP = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: blob:; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        response.headers["Content-Security-Policy"]    = self._CSP
        response.headers["X-Content-Type-Options"]     = "nosniff"
        response.headers["X-Frame-Options"]            = "DENY"
        response.headers["X-XSS-Protection"]           = "0"          # CSP es preferido
        response.headers["Referrer-Policy"]            = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"]         = (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), magnetometer=()"
        )
        # HSTS — solo en producción (si se sirve por HTTPS)
        response.headers["Strict-Transport-Security"]  = (
            "max-age=31536000; includeSubDomains; preload"
        )

        return response
