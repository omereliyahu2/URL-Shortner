"""
Rate limiting service with comprehensive rate limiting rules and custom exceptions.
"""

import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from domain.exceptions import RateLimitException, ValidationException
from domain.db_manager_interface import DBManagerInterface
from infrastructure.models import RateLimit


class RateLimitType(str, Enum):
    """Rate limit types."""
    IP_BASED = "ip_based"
    USER_BASED = "user_based"
    GLOBAL = "global"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_window: int
    window_seconds: int
    rate_limit_type: RateLimitType
    endpoint: str


class RateLimiter:
    """Comprehensive rate limiting service."""
    
    def __init__(self, db_manager: DBManagerInterface):
        self.db = db_manager
        self._rate_limit_configs = self._initialize_rate_limit_configs()
    
    def _initialize_rate_limit_configs(self) -> Dict[str, RateLimitConfig]:
        """Initialize rate limit configurations for different endpoints."""
        return {
            "/shorten/": RateLimitConfig(
                requests_per_window=10,
                window_seconds=60,
                rate_limit_type=RateLimitType.IP_BASED,
                endpoint="/shorten/"
            ),
            "/bulk-shorten/": RateLimitConfig(
                requests_per_window=5,
                window_seconds=300,
                rate_limit_type=RateLimitType.IP_BASED,
                endpoint="/bulk-shorten/"
            ),
            "/analytics/": RateLimitConfig(
                requests_per_window=20,
                window_seconds=60,
                rate_limit_type=RateLimitType.USER_BASED,
                endpoint="/analytics/"
            ),
            "/users/": RateLimitConfig(
                requests_per_window=5,
                window_seconds=300,
                rate_limit_type=RateLimitType.IP_BASED,
                endpoint="/users/"
            ),
            "/auth/login": RateLimitConfig(
                requests_per_window=3,
                window_seconds=300,
                rate_limit_type=RateLimitType.IP_BASED,
                endpoint="/auth/login"
            ),
            "/auth/register": RateLimitConfig(
                requests_per_window=2,
                window_seconds=600,
                rate_limit_type=RateLimitType.IP_BASED,
                endpoint="/auth/register"
            ),
            "default": RateLimitConfig(
                requests_per_window=100,
                window_seconds=60,
                rate_limit_type=RateLimitType.IP_BASED,
                endpoint="default"
            )
        }
    
    def check_rate_limit(
        self, 
        identifier: str, 
        endpoint: str,
        user_id: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if request is within rate limits.
        
        Args:
            identifier: IP address or user identifier
            endpoint: API endpoint being accessed
            user_id: Optional user ID for user-based rate limiting
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
            
        Raises:
            RateLimitException: When rate limit is exceeded
        """
        try:
            config = self._get_rate_limit_config(endpoint)
            current_time = datetime.utcnow()
            
            # Clean up old rate limit records
            self._cleanup_expired_rate_limits(current_time)
            
            # Get current rate limit record
            rate_limit_record = self._get_rate_limit_record(
                identifier, endpoint, config, current_time
            )
            
            if rate_limit_record is None:
                # Create new rate limit record
                self._create_rate_limit_record(
                    identifier, endpoint, config, current_time
                )
                return True, self._get_rate_limit_info(config, 1, current_time)
            
            # Check if within rate limit
            if rate_limit_record.request_count >= config.requests_per_window:
                # Rate limit exceeded
                reset_time = rate_limit_record.window_end
                retry_after = int((reset_time - current_time).total_seconds())
                
                raise RateLimitException(
                    message=f"Rate limit exceeded for {endpoint}",
                    retry_after=max(0, retry_after),
                    details={
                        "endpoint": endpoint,
                        "identifier": identifier,
                        "limit": config.requests_per_window,
                        "window_seconds": config.window_seconds,
                        "reset_time": reset_time.isoformat()
                    }
                )
            
            # Increment request count
            rate_limit_record.request_count += 1
            self.db.commit()
            
            return True, self._get_rate_limit_info(
                config, 
                rate_limit_record.request_count, 
                current_time,
                rate_limit_record.window_end
            )
            
        except RateLimitException:
            raise
        except Exception as e:
            # Log the error but don't block the request
            print(f"Rate limiting error: {str(e)}")
            return True, None
    
    def _get_rate_limit_config(self, endpoint: str) -> RateLimitConfig:
        """Get rate limit configuration for endpoint."""
        return self._rate_limit_configs.get(endpoint, self._rate_limit_configs["default"])
    
    def _cleanup_expired_rate_limits(self, current_time: datetime) -> None:
        """Clean up expired rate limit records."""
        try:
            expired_records = self.db.filter_query(
                RateLimit,
                RateLimit.window_end < current_time
            )
            
            if expired_records:
                self.db.delete(expired_records)
                self.db.commit()
        except Exception as e:
            print(f"Error cleaning up expired rate limits: {str(e)}")
    
    def _get_rate_limit_record(
        self, 
        identifier: str, 
        endpoint: str, 
        config: RateLimitConfig,
        current_time: datetime
    ) -> Optional[RateLimit]:
        """Get current rate limit record."""
        try:
            return self.db.filter_query(
                RateLimit,
                RateLimit.identifier == identifier,
                RateLimit.endpoint == endpoint,
                RateLimit.window_start <= current_time,
                RateLimit.window_end > current_time
            )
        except Exception as e:
            print(f"Error getting rate limit record: {str(e)}")
            return None
    
    def _create_rate_limit_record(
        self, 
        identifier: str, 
        endpoint: str, 
        config: RateLimitConfig,
        current_time: datetime
    ) -> None:
        """Create new rate limit record."""
        try:
            window_start = current_time
            window_end = current_time + timedelta(seconds=config.window_seconds)
            
            rate_limit_record = RateLimit(
                identifier=identifier,
                endpoint=endpoint,
                request_count=1,
                window_start=window_start,
                window_end=window_end
            )
            
            self.db.add(rate_limit_record)
            self.db.commit()
        except Exception as e:
            print(f"Error creating rate limit record: {str(e)}")
    
    def _get_rate_limit_info(
        self, 
        config: RateLimitConfig, 
        current_count: int,
        current_time: datetime,
        window_end: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get rate limit information."""
        if window_end is None:
            window_end = current_time + timedelta(seconds=config.window_seconds)
        
        return {
            "remaining_requests": max(0, config.requests_per_window - current_count),
            "reset_time": window_end,
            "limit": config.requests_per_window,
            "window_seconds": config.window_seconds,
            "current_count": current_count
        }
    
    def get_rate_limit_status(
        self, 
        identifier: str, 
        endpoint: str
    ) -> Dict[str, Any]:
        """Get current rate limit status for an identifier."""
        try:
            config = self._get_rate_limit_config(endpoint)
            current_time = datetime.utcnow()
            
            rate_limit_record = self._get_rate_limit_record(
                identifier, endpoint, config, current_time
            )
            
            if rate_limit_record is None:
                return {
                    "remaining_requests": config.requests_per_window,
                    "reset_time": current_time + timedelta(seconds=config.window_seconds),
                    "limit": config.requests_per_window,
                    "current_count": 0
                }
            
            return self._get_rate_limit_info(
                config,
                rate_limit_record.request_count,
                current_time,
                rate_limit_record.window_end
            )
            
        except Exception as e:
            print(f"Error getting rate limit status: {str(e)}")
            return {
                "remaining_requests": 0,
                "reset_time": current_time,
                "limit": 0,
                "current_count": 0,
                "error": str(e)
            }
    
    def reset_rate_limit(self, identifier: str, endpoint: str) -> bool:
        """Reset rate limit for an identifier and endpoint."""
        try:
            rate_limit_records = self.db.filter_query(
                RateLimit,
                RateLimit.identifier == identifier,
                RateLimit.endpoint == endpoint
            )
            
            if rate_limit_records:
                self.db.delete(rate_limit_records)
                self.db.commit()
                return True
            
            return False
        except Exception as e:
            print(f"Error resetting rate limit: {str(e)}")
            return False
    
    def update_rate_limit_config(
        self, 
        endpoint: str, 
        requests_per_window: int,
        window_seconds: int,
        rate_limit_type: RateLimitType
    ) -> None:
        """Update rate limit configuration for an endpoint."""
        if requests_per_window <= 0:
            raise ValidationException(
                message="Requests per window must be positive",
                field="requests_per_window"
            )
        
        if window_seconds <= 0:
            raise ValidationException(
                message="Window seconds must be positive",
                field="window_seconds"
            )
        
        self._rate_limit_configs[endpoint] = RateLimitConfig(
            requests_per_window=requests_per_window,
            window_seconds=window_seconds,
            rate_limit_type=rate_limit_type,
            endpoint=endpoint
        )
    
    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get all rate limit configurations."""
        return {
            endpoint: {
                "requests_per_window": config.requests_per_window,
                "window_seconds": config.window_seconds,
                "rate_limit_type": config.rate_limit_type.value,
                "endpoint": config.endpoint
            }
            for endpoint, config in self._rate_limit_configs.items()
        } 