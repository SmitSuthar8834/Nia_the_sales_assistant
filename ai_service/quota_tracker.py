import logging
import time

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class GeminiQuotaTracker:
    """
    Track Gemini API quota usage to prevent rate limit violations

    Gemini API Free Tier Limits:
    - 15 requests per minute
    - 1,500 requests per day
    - 1 million tokens per minute
    - 32,000 tokens per request
    """

    def __init__(self):
        self.cache_prefix = "gemini_quota"
        self.minute_limit = getattr(settings, "GEMINI_MINUTE_LIMIT", 15)
        self.daily_limit = getattr(settings, "GEMINI_DAILY_LIMIT", 1500)
        self.token_per_minute_limit = getattr(
            settings, "GEMINI_TOKEN_MINUTE_LIMIT", 1000000
        )

    def _get_cache_key(self, key_type):
        """Generate cache key for different quota types"""
        return f"{self.cache_prefix}_{key_type}"

    def _get_current_minute_key(self):
        """Get current minute as cache key"""
        return int(time.time() // 60)

    def _get_current_day_key(self):
        """Get current day as cache key"""
        return int(time.time() // 86400)

    def get_current_usage(self):
        """Get current quota usage statistics"""
        current_minute = self._get_current_minute_key()
        current_day = self._get_current_day_key()

        minute_key = f"{self.cache_prefix}_minute_{current_minute}"
        day_key = f"{self.cache_prefix}_day_{current_day}"
        token_minute_key = f"{self.cache_prefix}_tokens_{current_minute}"

        minute_requests = cache.get(minute_key, 0)
        daily_requests = cache.get(day_key, 0)
        minute_tokens = cache.get(token_minute_key, 0)

        return {
            "minute_requests": minute_requests,
            "minute_limit": self.minute_limit,
            "minute_remaining": max(0, self.minute_limit - minute_requests),
            "daily_requests": daily_requests,
            "daily_limit": self.daily_limit,
            "daily_remaining": max(0, self.daily_limit - daily_requests),
            "minute_tokens": minute_tokens,
            "token_minute_limit": self.token_per_minute_limit,
            "token_minute_remaining": max(
                0, self.token_per_minute_limit - minute_tokens
            ),
            "usage_percentage": {
                "minute": (minute_requests / self.minute_limit) * 100,
                "daily": (daily_requests / self.daily_limit) * 100,
                "tokens": (minute_tokens / self.token_per_minute_limit) * 100,
            },
        }

    def can_make_request(self, estimated_tokens=1000):
        """
        Check if we can make a request without exceeding limits

        Args:
            estimated_tokens (int): Estimated tokens for the request

        Returns:
            dict: Status and details about quota availability
        """
        usage = self.get_current_usage()

        # Check minute request limit
        if usage["minute_remaining"] <= 0:
            return {
                "can_request": False,
                "reason": "minute_request_limit_exceeded",
                "wait_seconds": 60 - (time.time() % 60),
                "usage": usage,
            }

        # Check daily request limit
        if usage["daily_remaining"] <= 0:
            return {
                "can_request": False,
                "reason": "daily_request_limit_exceeded",
                "wait_seconds": 86400 - (time.time() % 86400),
                "usage": usage,
            }

        # Check token limit
        if usage["token_minute_remaining"] < estimated_tokens:
            return {
                "can_request": False,
                "reason": "token_limit_exceeded",
                "wait_seconds": 60 - (time.time() % 60),
                "usage": usage,
            }

        return {"can_request": True, "usage": usage}

    def record_request(self, tokens_used=1000):
        """
        Record a successful API request

        Args:
            tokens_used (int): Number of tokens used in the request
        """
        current_minute = self._get_current_minute_key()
        current_day = self._get_current_day_key()

        minute_key = f"{self.cache_prefix}_minute_{current_minute}"
        day_key = f"{self.cache_prefix}_day_{current_day}"
        token_minute_key = f"{self.cache_prefix}_tokens_{current_minute}"

        # Increment counters with expiration
        cache.set(minute_key, cache.get(minute_key, 0) + 1, timeout=120)  # 2 minutes
        cache.set(day_key, cache.get(day_key, 0) + 1, timeout=86400 + 3600)  # 25 hours
        cache.set(
            token_minute_key, cache.get(token_minute_key, 0) + tokens_used, timeout=120
        )

        logger.info(f"Recorded Gemini API request: {tokens_used} tokens used")

    def get_quota_status(self):
        """Get detailed quota status for monitoring"""
        usage = self.get_current_usage()

        status = {"healthy": True, "warnings": [], "errors": [], "usage": usage}

        # Check for warnings (>80% usage)
        if usage["usage_percentage"]["minute"] > 80:
            status["warnings"].append("High minute request usage")

        if usage["usage_percentage"]["daily"] > 80:
            status["warnings"].append("High daily request usage")

        if usage["usage_percentage"]["tokens"] > 80:
            status["warnings"].append("High token usage")

        # Check for errors (>95% usage)
        if usage["usage_percentage"]["minute"] > 95:
            status["errors"].append("Critical minute request usage")
            status["healthy"] = False

        if usage["usage_percentage"]["daily"] > 95:
            status["errors"].append("Critical daily request usage")
            status["healthy"] = False

        if usage["usage_percentage"]["tokens"] > 95:
            status["errors"].append("Critical token usage")
            status["healthy"] = False

        return status

    def reset_quota(self, quota_type="all"):
        """
        Reset quota counters (for testing or manual reset)

        Args:
            quota_type (str): 'minute', 'daily', 'tokens', or 'all'
        """
        current_minute = self._get_current_minute_key()
        current_day = self._get_current_day_key()

        if quota_type in ["minute", "all"]:
            minute_key = f"{self.cache_prefix}_minute_{current_minute}"
            cache.delete(minute_key)

        if quota_type in ["daily", "all"]:
            day_key = f"{self.cache_prefix}_day_{current_day}"
            cache.delete(day_key)

        if quota_type in ["tokens", "all"]:
            token_minute_key = f"{self.cache_prefix}_tokens_{current_minute}"
            cache.delete(token_minute_key)

        logger.info(f"Reset Gemini quota counters: {quota_type}")

    def estimate_tokens(self, text):
        """
        Estimate token count for text (rough approximation)

        Args:
            text (str): Text to estimate tokens for

        Returns:
            int: Estimated token count
        """
        # Rough estimation: 1 token ≈ 4 characters for English text
        # This is a conservative estimate
        return max(100, len(text) // 3)  # Minimum 100 tokens

    def get_wait_time(self):
        """Get recommended wait time before next request"""
        usage = self.get_current_usage()

        if usage["minute_remaining"] <= 0:
            return 60 - (time.time() % 60)
        elif usage["daily_remaining"] <= 0:
            return 86400 - (time.time() % 86400)
        elif usage["usage_percentage"]["minute"] > 90:
            return 10  # Wait 10 seconds if close to limit
        else:
            return 0  # No wait needed


# Global quota tracker instance
quota_tracker = GeminiQuotaTracker()
