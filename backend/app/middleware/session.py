"""
Session Middleware for User Isolation

This middleware assigns each user a unique session ID based on:
1. Existing session cookie (if present)
2. New UUID (if no cookie)

The session ID is used to isolate user outputs in separate directories.
"""

import uuid
import hashlib
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

SESSION_COOKIE_NAME = "ppt_session_id"
SESSION_COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days

# Context variable to store current session_id for the request
current_session_id: ContextVar[str] = ContextVar('current_session_id', default='default')


def get_current_session_id() -> str:
    """Get the current session ID from context. Use this in services."""
    return current_session_id.get()


def generate_session_id(client_ip: str) -> str:
    """Generate a unique session ID incorporating client IP for extra uniqueness."""
    unique_part = uuid.uuid4().hex[:12]
    ip_hash = hashlib.md5(client_ip.encode()).hexdigest()[:4]
    return f"{ip_hash}_{unique_part}"


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, handling proxies."""
    # Check X-Forwarded-For header first (for proxied requests)
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # Take the first IP in the chain
        return forwarded.split(",")[0].strip()
    
    # Check X-Real-IP header
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    
    # Fall back to direct client IP
    if request.client:
        return request.client.host
    
    return "unknown"


class SessionMiddleware(BaseHTTPMiddleware):
    """
    Middleware that manages user sessions for output isolation.
    
    Injects into request.state:
    - session_id: Unique identifier for the user session
    - client_ip: The client's IP address
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Get client IP
        client_ip = get_client_ip(request)
        
        # Check for existing session cookie
        session_id = request.cookies.get(SESSION_COOKIE_NAME)
        
        # Generate new session if not present or invalid
        new_session = False
        if not session_id or len(session_id) < 10:
            session_id = generate_session_id(client_ip)
            new_session = True
        
        # Store in request state for access by endpoints
        request.state.session_id = session_id
        request.state.client_ip = client_ip
        
        # Set context variable for services to access
        token = current_session_id.set(session_id)
        
        try:
            # Process request
            response = await call_next(request)
        finally:
            # Reset context variable
            current_session_id.reset(token)
        
        # Set session cookie if new
        if new_session:
            response.set_cookie(
                key=SESSION_COOKIE_NAME,
                value=session_id,
                max_age=SESSION_COOKIE_MAX_AGE,
                httponly=True,
                samesite="lax",
                secure=False,  # Set to True in production with HTTPS
            )
        
        return response
