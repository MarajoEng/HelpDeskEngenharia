import time
from threading import Lock


class LoginRateLimiter:
    """In-memory sliding-window rate limiter keyed by '{ip}:{email}'."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._buckets: dict[str, list[float]] = {}

    def _get_settings(self):
        from app.core.config import get_settings
        return get_settings()

    def check_and_record(self, key: str) -> bool:
        """Return True if the attempt is allowed, False if rate-limited."""
        settings = self._get_settings()
        window = settings.login_rate_limit_window_seconds
        limit = settings.login_rate_limit_attempts
        now = time.time()
        cutoff = now - window

        with self._lock:
            attempts = self._buckets.get(key, [])
            attempts = [t for t in attempts if t > cutoff]
            if len(attempts) >= limit:
                self._buckets[key] = attempts
                return False
            attempts.append(now)
            self._buckets[key] = attempts
            return True

    def clear_all(self) -> None:
        with self._lock:
            self._buckets.clear()


login_rate_limiter = LoginRateLimiter()
