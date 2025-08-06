"""
Tests for custom exception hierarchy and error handling.
"""

import pytest
from datetime import datetime, timedelta

from domain.exceptions import (
    URLShortenerException,
    ValidationException,
    URLValidationException,
    URLNotFoundException,
    DuplicateURLException,
    URLExpiredException,
    DatabaseException,
    NotFoundException,
    RateLimitException,
    AuthenticationException,
    AuthorizationException,
    ConnectionException,
    ConfigurationException,
    ServiceUnavailableException
)


class TestCustomExceptions:
    """Test cases for custom exception hierarchy."""
    
    def test_url_shortener_exception_base(self):
        """Test base URL shortener exception."""
        exc = URLShortenerException(
            message="Test error",
            error_code="TEST_ERROR",
            status_code=400,
            details={"test": "value"}
        )
        
        assert exc.message == "Test error"
        assert exc.error_code == "TEST_ERROR"
        assert exc.status_code == 400
        assert exc.details == {"test": "value"}
        assert str(exc) == "Test error"
    
    def test_validation_exception(self):
        """Test validation exception."""
        exc = ValidationException(
            message="Invalid input",
            field="url",
            details={"invalid_value": "test"}
        )
        
        assert exc.message == "Invalid input"
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.status_code == 400
        assert exc.details["field"] == "url"
        assert exc.details["invalid_value"] == "test"
    
    def test_url_validation_exception(self):
        """Test URL validation exception."""
        exc = URLValidationException(
            message="Invalid URL format",
            url="invalid-url",
            details={"expected_format": "http(s)://domain.com"}
        )
        
        assert exc.message == "Invalid URL format"
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.status_code == 400
        assert exc.details["url"] == "invalid-url"
        assert exc.details["expected_format"] == "http(s)://domain.com"
    
    def test_url_not_found_exception(self):
        """Test URL not found exception."""
        exc = URLNotFoundException(
            short_url="abc123",
            details={"searched_at": datetime.utcnow().isoformat()}
        )
        
        assert "abc123" in exc.message
        assert exc.error_code == "NOT_FOUND"
        assert exc.status_code == 404
        assert exc.details["resource_type"] == "url_mapping"
        assert exc.details["resource_id"] == "abc123"
    
    def test_duplicate_url_exception(self):
        """Test duplicate URL exception."""
        exc = DuplicateURLException(
            original_url="https://example.com",
            details={"existing_short_url": "xyz789"}
        )
        
        assert "https://example.com" in exc.message
        assert exc.error_code == "DUPLICATE_URL"
        assert exc.status_code == 409
        assert exc.details["original_url"] == "https://example.com"
    
    def test_url_expired_exception(self):
        """Test URL expired exception."""
        expired_at = datetime.utcnow() - timedelta(days=1)
        exc = URLExpiredException(
            short_url="expired123",
            expired_at=expired_at.isoformat()
        )
        
        assert "expired123" in exc.message
        assert exc.error_code == "URL_EXPIRED"
        assert exc.status_code == 410
        assert exc.details["short_url"] == "expired123"
        assert exc.details["expired_at"] == expired_at.isoformat()
    
    def test_database_exception(self):
        """Test database exception."""
        exc = DatabaseException(
            message="Connection failed",
            operation="query",
            details={"sql": "SELECT * FROM users"}
        )
        
        assert exc.message == "Connection failed"
        assert exc.error_code == "DATABASE_ERROR"
        assert exc.status_code == 500
        assert exc.details["operation"] == "query"
        assert exc.details["sql"] == "SELECT * FROM users"
    
    def test_connection_exception(self):
        """Test connection exception."""
        exc = ConnectionException(
            message="Database connection failed",
            details={"host": "localhost", "port": 5432}
        )
        
        assert exc.message == "Database connection failed"
        assert exc.error_code == "DATABASE_ERROR"
        assert exc.status_code == 500
        assert exc.details["operation"] == "connection"
        assert exc.details["host"] == "localhost"
    
    def test_not_found_exception(self):
        """Test not found exception."""
        exc = NotFoundException(
            message="User not found",
            resource_type="user",
            resource_id="user123"
        )
        
        assert exc.message == "User not found"
        assert exc.error_code == "NOT_FOUND"
        assert exc.status_code == 404
        assert exc.details["resource_type"] == "user"
        assert exc.details["resource_id"] == "user123"
    
    def test_rate_limit_exception(self):
        """Test rate limit exception."""
        exc = RateLimitException(
            message="Rate limit exceeded",
            retry_after=60,
            details={"endpoint": "/shorten/", "limit": 10}
        )
        
        assert exc.message == "Rate limit exceeded"
        assert exc.error_code == "RATE_LIMIT_EXCEEDED"
        assert exc.status_code == 429
        assert exc.details["retry_after"] == 60
        assert exc.details["endpoint"] == "/shorten/"
    
    def test_authentication_exception(self):
        """Test authentication exception."""
        exc = AuthenticationException(
            message="Invalid credentials",
            details={"username": "testuser"}
        )
        
        assert exc.message == "Invalid credentials"
        assert exc.error_code == "AUTHENTICATION_ERROR"
        assert exc.status_code == 401
        assert exc.details["username"] == "testuser"
    
    def test_authorization_exception(self):
        """Test authorization exception."""
        exc = AuthorizationException(
            message="Access denied",
            required_permission="admin",
            details={"user_role": "user"}
        )
        
        assert exc.message == "Access denied"
        assert exc.error_code == "AUTHORIZATION_ERROR"
        assert exc.status_code == 403
        assert exc.details["required_permission"] == "admin"
        assert exc.details["user_role"] == "user"
    
    def test_configuration_exception(self):
        """Test configuration exception."""
        exc = ConfigurationException(
            message="Missing database configuration",
            config_key="database_url",
            details={"missing_keys": ["host", "port"]}
        )
        
        assert exc.message == "Missing database configuration"
        assert exc.error_code == "CONFIGURATION_ERROR"
        assert exc.status_code == 500
        assert exc.details["config_key"] == "database_url"
        assert exc.details["missing_keys"] == ["host", "port"]
    
    def test_service_unavailable_exception(self):
        """Test service unavailable exception."""
        exc = ServiceUnavailableException(
            message="Service temporarily unavailable",
            service_name="database",
            retry_after=300,
            details={"maintenance_window": "2 hours"}
        )
        
        assert exc.message == "Service temporarily unavailable"
        assert exc.error_code == "SERVICE_UNAVAILABLE"
        assert exc.status_code == 503
        assert exc.details["service_name"] == "database"
        assert exc.details["retry_after"] == 300
        assert exc.details["maintenance_window"] == "2 hours"
    
    def test_exception_inheritance(self):
        """Test exception inheritance hierarchy."""
        # Test that specific exceptions inherit from base
        assert issubclass(ValidationException, URLShortenerException)
        assert issubclass(URLValidationException, ValidationException)
        assert issubclass(DatabaseException, URLShortenerException)
        assert issubclass(ConnectionException, DatabaseException)
        assert issubclass(NotFoundException, URLShortenerException)
        assert issubclass(URLNotFoundException, NotFoundException)
    
    def test_exception_with_minimal_params(self):
        """Test exceptions with minimal parameters."""
        # Test with default values
        exc = URLShortenerException("Simple error")
        assert exc.message == "Simple error"
        assert exc.error_code == "GENERAL_ERROR"
        assert exc.status_code == 500
        assert exc.details == {}
        
        # Test validation exception with minimal params
        val_exc = ValidationException("Field required", field="email")
        assert val_exc.message == "Field required"
        assert val_exc.details["field"] == "email"
    
    def test_exception_details_immutability(self):
        """Test that exception details are properly handled."""
        details = {"key": "value"}
        exc = URLShortenerException("Test", details=details)
        
        # Modify the original details dict
        details["key"] = "modified"
        
        # Exception details should not be affected
        assert exc.details["key"] == "value"
    
    def test_exception_string_representation(self):
        """Test exception string representation."""
        exc = URLShortenerException("Test error message")
        assert str(exc) == "Test error message"
        assert repr(exc) == "URLShortenerException('Test error message')"


if __name__ == "__main__":
    pytest.main([__file__]) 