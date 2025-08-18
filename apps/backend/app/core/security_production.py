"""Production-ready security module with enhanced protections"""
from datetime import datetime, timedelta
from typing import Optional, Union, Any, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import uuid
import logging
import hashlib
import secrets
import time
from functools import wraps

from .config_production import get_production_settings
from .database import get_db
from ..models.user import User

# Security logger
security_logger = logging.getLogger("security")

# Production settings
settings = get_production_settings()

# Enhanced password hashing for production
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Higher rounds for production
    bcrypt__ident="2b"
)

# OAuth2 scheme with strict production settings
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login",
    auto_error=True  # Always require authentication in production
)

# Rate limiting storage
_rate_limit_storage = {}

class SecurityError(Exception):
    """Custom security exception"""
    pass

def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure random token"""
    return secrets.token_urlsafe(length)

def hash_sensitive_data(data: str) -> str:
    """Hash sensitive data for logging (one-way)"""
    return hashlib.sha256(data.encode()).hexdigest()[:8]

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password with timing attack protection"""
    try:
        # Add small random delay to prevent timing attacks
        time.sleep(secrets.randbelow(50) / 1000)  # 0-50ms
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        security_logger.warning(f"Password verification failed: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Generate secure password hash"""
    if len(password) < 8:
        raise SecurityError("Password must be at least 8 characters")
    
    # Check for common weak passwords
    weak_passwords = {'password', '123456', 'password123', 'admin', 'test'}
    if password.lower() in weak_passwords:
        raise SecurityError("Password is too weak")
    
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create secure JWT token with enhanced claims"""
    to_encode = data.copy()
    
    # Add security claims
    issued_at = datetime.utcnow()
    if expires_delta:
        expire = issued_at + expires_delta
    else:
        expire = issued_at + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": issued_at,
        "iss": settings.APP_NAME,
        "aud": "icfes-users",
        "jti": generate_secure_token(16),  # Unique token ID
    })
    
    try:
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)
        
        # Log token creation for security audit
        user_id = data.get("sub", "unknown")
        security_logger.info(f"Token created for user: {hash_sensitive_data(user_id)}")
        
        return encoded_jwt
    except Exception as e:
        security_logger.error(f"Token creation failed: {e}")
        raise SecurityError("Failed to create access token")

def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token with enhanced security checks"""
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET, 
            algorithms=[settings.ALGORITHM],
            audience="icfes-users",
            issuer=settings.APP_NAME
        )
        
        # Additional security checks
        if not payload.get("sub"):
            security_logger.warning("Token missing subject claim")
            return None
        
        if not payload.get("jti"):
            security_logger.warning("Token missing JTI claim") 
            return None
            
        return payload
        
    except jwt.ExpiredSignatureError:
        security_logger.info("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        security_logger.warning(f"Invalid token: {e}")
        return None
    except Exception as e:
        security_logger.error(f"Token verification error: {e}")
        return None

def rate_limit_check(identifier: str, limit: int, window: int = 60) -> bool:
    """Check rate limiting with sliding window"""
    current_time = time.time()
    window_start = current_time - window
    
    # Clean old entries
    if identifier in _rate_limit_storage:
        _rate_limit_storage[identifier] = [
            timestamp for timestamp in _rate_limit_storage[identifier]
            if timestamp > window_start
        ]
    else:
        _rate_limit_storage[identifier] = []
    
    # Check limit
    if len(_rate_limit_storage[identifier]) >= limit:
        security_logger.warning(f"Rate limit exceeded for: {hash_sensitive_data(identifier)}")
        return False
    
    # Add current request
    _rate_limit_storage[identifier].append(current_time)
    return True

def require_rate_limit(limit: int = None, window: int = 60):
    """Decorator for rate limiting endpoints"""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Use IP + endpoint as identifier
            identifier = f"{request.client.host}:{request.url.path}"
            rate_limit = limit or settings.RATE_LIMIT_PER_MINUTE
            
            if not rate_limit_check(identifier, rate_limit, window):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current user with enhanced security checks - NO DEV BYPASS"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Log authentication attempt
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "unknown")
    security_logger.info(f"Auth attempt from IP: {client_ip}, UA: {hash_sensitive_data(user_agent)}")
    
    # Rate limiting for authentication
    if not rate_limit_check(f"auth:{client_ip}", 10, 300):  # 10 attempts per 5 minutes
        security_logger.warning(f"Auth rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts"
        )
    
    if not token:
        security_logger.warning(f"Missing token from IP: {client_ip}")
        raise credentials_exception
    
    try:
        payload = verify_token(token)
        if payload is None:
            raise credentials_exception
            
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
    except JWTError as e:
        security_logger.warning(f"JWT error from IP {client_ip}: {e}")
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        security_logger.warning(f"User not found for token from IP: {client_ip}")
        raise credentials_exception
    
    if not user.is_active:
        security_logger.warning(f"Inactive user login attempt: {hash_sensitive_data(user_id)}")
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Log successful authentication
    security_logger.info(f"Successful auth for user: {hash_sensitive_data(user_id)} from IP: {client_ip}")
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Get admin user with enhanced checks"""
    # Check if user has admin privileges (implement based on your user model)
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
        security_logger.warning(f"Admin access denied for user: {hash_sensitive_data(str(current_user.id))}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    security_logger.info(f"Admin access granted to user: {hash_sensitive_data(str(current_user.id))}")
    return current_user

def validate_ip_whitelist(request: Request, allowed_ips: List[str]) -> bool:
    """Validate request IP against whitelist"""
    client_ip = request.client.host
    
    if not allowed_ips:
        return True  # No restrictions if list is empty
    
    if client_ip in allowed_ips:
        return True
    
    # Check for IP ranges (basic implementation)
    for allowed_ip in allowed_ips:
        if '/' in allowed_ip:  # CIDR notation
            # Implement CIDR check if needed
            pass
    
    security_logger.warning(f"IP access denied: {client_ip}")
    return False

def require_admin_ip(func):
    """Decorator to restrict admin endpoints to specific IPs"""
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        if not validate_ip_whitelist(request, settings.ADMIN_IPS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied from this IP"
            )
        return await func(request, *args, **kwargs)
    return wrapper

# Enhanced security functions for game mechanics
def calculate_level(experience: int) -> int:
    """Calculate level with bounds checking"""
    if experience < 0:
        return 1
    level = int((experience / 100) ** 0.5) + 1
    return min(level, settings.MAX_LEVEL)

def calculate_rank(level: int) -> str:
    """Calculate rank with validation"""
    level = max(1, min(level, settings.MAX_LEVEL))
    
    if level >= 90:
        return "SSS"
    elif level >= 80:
        return "SS"
    elif level >= 70:
        return "S"
    elif level >= 60:
        return "A"
    elif level >= 50:
        return "B"
    elif level >= 30:
        return "C"
    elif level >= 15:
        return "D"
    else:
        return "E"

def sanitize_user_input(input_string: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent injection attacks"""
    if not isinstance(input_string, str):
        raise SecurityError("Input must be a string")
    
    # Limit length
    if len(input_string) > max_length:
        raise SecurityError(f"Input too long (max {max_length} characters)")
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\r', '\n']
    for char in dangerous_chars:
        input_string = input_string.replace(char, '')
    
    return input_string.strip()

def validate_file_upload(filename: str, file_size: int) -> bool:
    """Validate file upload security"""
    if file_size > settings.MAX_FILE_SIZE:
        raise SecurityError(f"File too large (max {settings.MAX_FILE_SIZE} bytes)")
    
    # Check file extension
    if not any(filename.lower().endswith(ext) for ext in settings.ALLOWED_EXTENSIONS):
        raise SecurityError("File type not allowed")
    
    # Check for dangerous filenames
    dangerous_patterns = ['..', '/', '\\', '\x00']
    for pattern in dangerous_patterns:
        if pattern in filename:
            raise SecurityError("Invalid filename")
    
    return True