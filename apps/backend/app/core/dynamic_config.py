"""
Dynamic Configuration Module
Provides dynamic server configuration for image URLs and other dynamic settings
"""

import os
from typing import Dict, Any
from .config import settings

def get_server_config() -> Dict[str, Any]:
    """Get current server configuration for dynamic URL generation"""

    # Get host IP from environment or use default
    host_ip = os.environ.get('HOST_IP', '143.110.195.148')

    return {
        "host_ip": host_ip,
        "api_url": f"http://{host_ip}:4000",
        "frontend_url": f"http://{host_ip}:4001",
        "websocket_url": f"ws://{host_ip}:4002",
        "image_base_url": f"http://{host_ip}:4000/dynamic-images",
        "environment": getattr(settings, 'ENVIRONMENT', 'development'),
        "debug": getattr(settings, 'DEBUG', True)
    }

def get_dynamic_image_url(relative_path: str) -> str:
    """Generate dynamic image URL for a given relative path"""
    if not relative_path:
        return ""

    # Clean the path
    relative_path = relative_path.strip().lstrip('/')

    # Get server config
    config = get_server_config()

    return f"{config['image_base_url']}/{relative_path}"