from fastapi import FastAPI, Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import time
from typing import Callable
import secrets
import hashlib
import os

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.nonce_cache = {}
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate nonce for CSP
        nonce = secrets.token_hex(16)
        
        response = await call_next(request)
        
        # Security headers
        security_headers = {
            # XSS Protection
            "X-XSS-Protection": "1; mode=block",
            
            # Content Type Options
            "X-Content-Type-Options": "nosniff",
            
            # Frame Options
            "X-Frame-Options": "DENY",
            
            # Referrer Policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Permissions Policy
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            
            # Content Security Policy
            "Content-Security-Policy": f"""
                default-src 'self';
                script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net https://unpkg.com;
                style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
                font-src 'self' https://fonts.gstatic.com;
                img-src 'self' data: https: blob:;
                connect-src 'self' ws: wss:;
                media-src 'self' data: blob:;
                object-src 'none';
                base-uri 'self';
                form-action 'self';
                frame-ancestors 'none';
                upgrade-insecure-requests;
            """.replace('\n', ' ').strip(),
        }
        
        # Add HSTS in production
        if os.getenv("ENVIRONMENT") == "production":
            security_headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Add headers to response
        for header, value in security_headers.items():
            response.headers[header] = value
        
        # Add nonce to request state for templates
        request.state.nonce = nonce
        
        return response

class RateLimitSecurityMiddleware(BaseHTTPMiddleware):
    """Basic rate limiting and abuse prevention"""
    
    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.request_counts = {}
        self.blocked_ips = set()
        self.suspicious_patterns = [
            # Common attack patterns
            "union select",
            "script>",
            "../",
            "<?php",
            "eval(",
            "base64_decode",
            "system(",
            "exec(",
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host
        current_time = time.time()
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            return JSONResponse(
                status_code=403,
                content={"detail": "Access denied"}
            )
        
        # Check for suspicious patterns in query parameters and body
        if await self._is_suspicious_request(request):
            self.blocked_ips.add(client_ip)
            return JSONResponse(
                status_code=403,
                content={"detail": "Suspicious activity detected"}
            )
        
        # Basic rate limiting (more advanced rate limiting is in rate_limit.py)
        minute_window = int(current_time // 60)
        key = f"{client_ip}:{minute_window}"
        
        if key not in self.request_counts:
            self.request_counts[key] = 0
        
        self.request_counts[key] += 1
        
        # Allow 200 requests per minute per IP (basic protection)
        if self.request_counts[key] > 200:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"}
            )
        
        # Clean old entries every hour
        if current_time % 3600 < 60:  # Once per hour
            self._cleanup_old_entries(current_time)
        
        response = await call_next(request)
        return response
    
    async def _is_suspicious_request(self, request: Request) -> bool:
        """Check if request contains suspicious patterns"""
        
        # Check URL path
        path = str(request.url.path).lower()
        for pattern in self.suspicious_patterns:
            if pattern in path:
                return True
        
        # Check query parameters
        query_string = str(request.url.query).lower()
        for pattern in self.suspicious_patterns:
            if pattern in query_string:
                return True
        
        # Check user agent for common bot patterns
        user_agent = request.headers.get("user-agent", "").lower()
        bot_patterns = ["sqlmap", "nikto", "nmap", "masscan", "zap"]
        for pattern in bot_patterns:
            if pattern in user_agent:
                return True
        
        # Check for excessively long headers (potential buffer overflow)
        for header_name, header_value in request.headers.items():
            if len(header_value) > 8192:  # 8KB limit
                return True
        
        return False
    
    def _cleanup_old_entries(self, current_time: float):
        """Remove old rate limiting entries"""
        current_minute = int(current_time // 60)
        keys_to_remove = []
        
        for key in self.request_counts:
            try:
                _, minute_str = key.rsplit(":", 1)
                minute = int(minute_str)
                if current_minute - minute > 5:  # Keep last 5 minutes
                    keys_to_remove.append(key)
            except (ValueError, AttributeError):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.request_counts[key]

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests for security monitoring"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log request details
        client_ip = request.client.host
        method = request.method
        path = request.url.path
        user_agent = request.headers.get("user-agent", "")
        
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Import here to avoid circular imports
        from ..core.logging import log_request, log_security_event
        
        # Log the request
        log_request(
            method=method,
            path=path,
            status_code=response.status_code,
            duration=process_time,
            client_ip=client_ip,
            user_agent=user_agent
        )
        
        # Log security events for suspicious activity
        if response.status_code == 403:
            log_security_event(
                "access_denied",
                {
                    "client_ip": client_ip,
                    "path": path,
                    "method": method,
                    "user_agent": user_agent
                },
                "warning"
            )
        elif response.status_code >= 400:
            log_security_event(
                "client_error",
                {
                    "client_ip": client_ip,
                    "path": path,
                    "method": method,
                    "status_code": response.status_code
                },
                "info"
            )
        
        # Add security headers to response
        response.headers["X-Request-ID"] = getattr(request.state, "request_id", "unknown")
        response.headers["X-Response-Time"] = str(round(process_time * 1000, 2))
        
        return response

def add_security_middleware(app: FastAPI):
    """Add all security middleware to the FastAPI app"""
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitSecurityMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)