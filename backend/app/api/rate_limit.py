import time
from collections import defaultdict
from fastapi import Request, HTTPException, status


class RateLimiter:
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def __call__(self, request: Request):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        self._requests[client_ip] = [
            t for t in self._requests[client_ip] if now - t < self.window_seconds
        ]

        if len(self._requests[client_ip]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="请求过于频繁，请稍后再试。",
            )

        self._requests[client_ip].append(now)
