"""
Custom exception hierarchy for URL Shortener application.
Provides specific exceptions for different error scenarios with proper error codes and messages.
"""

from typing import Optional, Dict, Any
from http import HTTPStatus


class URLShortenerException(Exception):
    """Base exception for all URL shortener related errors."""
    
    def __init__(
        self, 
        message: str, 
        error_code: str = "GENERAL_ERROR",
        status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(URLShortenerException):
    """Exception raised for validation errors."""
    
    def __init__(
        self, 
        message: str, 
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=HTTPStatus.BAD_REQUEST,
            details=details or {"field": field}
        )


class URLValidationException(ValidationException):
    """Exception raised for URL-specific validation errors."""
    
    def __init__(
        self, 
        message: str, 
        url: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            field="url",
            details=details or {"url": url}
        )


class DatabaseException(URLShortenerException):
    """Exception raised for database-related errors."""
    
    def __init__(
        self, 
        message: str, 
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            details=details or {"operation": operation}
        )


class ConnectionException(DatabaseException):
    """Exception raised for database connection errors."""
    
    def __init__(
        self, 
        message: str = "Database connection failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            operation="connection",
            details=details
        )


class NotFoundException(URLShortenerException):
    """Exception raised when a resource is not found."""
    
    def __init__(
        self, 
        message: str, 
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            status_code=HTTPStatus.NOT_FOUND,
            details=details or {
                "resource_type": resource_type,
                "resource_id": resource_id
            }
        )


class URLNotFoundException(NotFoundException):
    """Exception raised when a URL mapping is not found."""
    
    def __init__(
        self, 
        short_url: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"URL mapping not found for short URL: {short_url}",
            resource_type="url_mapping",
            resource_id=short_url,
            details=details
        )


class RateLimitException(URLShortenerException):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(
        self, 
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=HTTPStatus.TOO_MANY_REQUESTS,
            details=details or {"retry_after": retry_after}
        )


class AuthenticationException(URLShortenerException):
    """Exception raised for authentication errors."""
    
    def __init__(
        self, 
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=HTTPStatus.UNAUTHORIZED,
            details=details
        )


class AuthorizationException(URLShortenerException):
    """Exception raised for authorization errors."""
    
    def __init__(
        self, 
        message: str = "Access denied",
        required_permission: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=HTTPStatus.FORBIDDEN,
            details=details or {"required_permission": required_permission}
        )


class ConfigurationException(URLShortenerException):
    """Exception raised for configuration errors."""
    
    def __init__(
        self, 
        message: str, 
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            details=details or {"config_key": config_key}
        )


class SecretsManagerException(URLShortenerException):
    """Exception raised for secrets manager errors."""
    
    def __init__(
        self, 
        message: str, 
        secret_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="SECRETS_MANAGER_ERROR",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            details=details or {"secret_name": secret_name}
        )


class CacheException(URLShortenerException):
    """Exception raised for cache-related errors."""
    
    def __init__(
        self, 
        message: str, 
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            details=details or {"operation": operation}
        )


class URLExpiredException(URLShortenerException):
    """Exception raised when a URL has expired."""
    
    def __init__(
        self, 
        short_url: str,
        expired_at: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"URL has expired: {short_url}",
            error_code="URL_EXPIRED",
            status_code=HTTPStatus.GONE,
            details=details or {
                "short_url": short_url,
                "expired_at": expired_at
            }
        )


class DuplicateURLException(URLShortenerException):
    """Exception raised when trying to create a duplicate URL mapping."""
    
    def __init__(
        self, 
        original_url: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"URL already exists: {original_url}",
            error_code="DUPLICATE_URL",
            status_code=HTTPStatus.CONFLICT,
            details=details or {"original_url": original_url}
        )


class ServiceUnavailableException(URLShortenerException):
    """Exception raised when a service is temporarily unavailable."""
    
    def __init__(
        self, 
        message: str = "Service temporarily unavailable",
        service_name: Optional[str] = None,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="SERVICE_UNAVAILABLE",
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            details=details or {
                "service_name": service_name,
                "retry_after": retry_after
            }
        ) 