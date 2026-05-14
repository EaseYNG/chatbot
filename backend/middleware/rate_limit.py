from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import Depends, HTTPException, status

from backend.auth.middleware import optional_user
from backend.config import RATE_LIMIT_PER_MINUTE

_window: dict[int | str, deque[float]] = defaultdict(deque)


async def rate_limit(
    user: dict | None = Depends(optional_user),
) -> None:
    """Sliding-window per-user rate limiter for /api/chat."""
    key = user["id"] if user else "anonymous"
    now = time.time()
    window = _window[key]

    while window and window[0] < now - 60:
        window.popleft()

    if len(window) >= RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded ({RATE_LIMIT_PER_MINUTE} requests per minute)",
        )

    window.append(now)
