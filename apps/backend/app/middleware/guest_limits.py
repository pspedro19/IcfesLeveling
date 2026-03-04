from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Any, Callable
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

GUEST_LIMITS = {
    "daily_questions": 10,
    "daily_tests": 2,
    "dungeon_floors": 1,
    "ai_requests": 3
}

class GuestLimitsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.limits = GUEST_LIMITS
        self._guest_usage = {}

    async def dispatch(self, request: Request, call_next: Callable):
        is_guest = await self._is_guest_request(request)
        
        if is_guest:
            limit_check = await self._check_guest_limits(request)
            if not limit_check["allowed"]:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Guest limit exceeded",
                        "message": limit_check["message"]
                    }
                )
        
        response = await call_next(request)
        
        if is_guest and response.status_code < 400:
            await self._update_guest_usage(request)
        
        return response
    
    async def _is_guest_request(self, request: Request) -> bool:
        return request.query_params.get("mode") == "guest"
    
    async def _check_guest_limits(self, request: Request) -> Dict[str, Any]:
        guest_id = await self._get_guest_id(request)
        current_usage = self._guest_usage.get(guest_id, {})
        today = datetime.now().date().isoformat()
        
        if request.url.path.startswith("/api/v1/questions"):
            daily_questions = current_usage.get("daily_questions", {}).get(today, 0)
            if daily_questions >= self.limits["daily_questions"]:
                return {
                    "allowed": False,
                    "message": "Daily question limit exceeded"
                }
        
        return {"allowed": True}
    
    async def _get_guest_id(self, request: Request) -> str:
        return request.query_params.get("guest_id", "default")
    
    async def _update_guest_usage(self, request: Request):
        guest_id = await self._get_guest_id(request)
        current_usage = self._guest_usage.get(guest_id, {})
        today = datetime.now().date().isoformat()
        
        if request.url.path.startswith("/api/v1/questions"):
            if "daily_questions" not in current_usage:
                current_usage["daily_questions"] = {}
            current_usage["daily_questions"][today] = current_usage["daily_questions"].get(today, 0) + 1
        
        self._guest_usage[guest_id] = current_usage 