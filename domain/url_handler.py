"""
Enhanced URL handler with comprehensive features and custom exception handling.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from injector import inject
import shortuuid
import hashlib

from domain.db_manager_interface import DBManagerInterface
from domain.models import URLRequest, URLResponse, URLListResponse, BulkURLRequest, BulkURLResponse
from domain.exceptions import (
    URLValidationException,
    URLNotFoundException,
    DuplicateURLException,
    URLExpiredException,
    DatabaseException,
    ValidationException,
    NotFoundException,
    RateLimitException,
    ServiceUnavailableException
)
from domain.url_validator import URLValidator
from domain.rate_limiter import RateLimiter
from domain.analytics_service import AnalyticsService
from infrastructure.models import URLMapping, User
from fastapi import Request


class URLHandler:
    """Enhanced URL handler with comprehensive features and exception handling."""
    
    @inject
    def __init__(
        self, 
        db: DBManagerInterface,
        url_validator: URLValidator,
        rate_limiter: RateLimiter,
        analytics_service: AnalyticsService
    ):
        self.db = db
        self.url_validator = url_validator
        self.rate_limiter = rate_limiter
        self.analytics_service = analytics_service
    
    def shorten_url(
        self, 
        url_request: URLRequest, 
        fastapi_request: Request,
        user_id: Optional[str] = None
    ) -> URLResponse:
        """
        Create a short URL with comprehensive validation and features.
        
        Args:
            url_request: URL request containing original URL and optional parameters
            fastapi_request: FastAPI request object for getting client info
            user_id: Optional user ID for authenticated users
            
        Returns:
            URLResponse with short URL information
            
        Raises:
            URLValidationException: If URL validation fails
            DuplicateURLException: If URL already exists
            DatabaseException: If database operation fails
            RateLimitException: If rate limit is exceeded
        """
        try:
            # Get client IP for rate limiting
            client_ip = self._get_client_ip(fastapi_request)
            
            # Check rate limit
            self.rate_limiter.check_rate_limit(
                identifier=client_ip,
                endpoint="/shorten/",
                user_id=user_id
            )
            
            # Validate URL
            validation_result = self.url_validator.validate_url(str(url_request.url))
            
            # Check for custom alias
            short_url = url_request.custom_alias
            if short_url:
                # Validate custom alias
                self.url_validator.validate_custom_alias(short_url)
                
                # Check if custom alias already exists
                existing_mapping = self.db.filter_query(
                    URLMapping,
                    URLMapping.custom_alias,
                    short_url
                )
                
                if existing_mapping:
                    raise DuplicateURLException(
                        original_url=str(url_request.url),
                        details={"custom_alias": short_url}
                    )
            else:
                # Generate unique short URL
                short_url = self._generate_unique_short_url()
            
            # Check for duplicate original URL (optional - you might want to allow this)
            existing_mapping = self.db.filter_query(
                URLMapping,
                URLMapping.original_url,
                str(url_request.url)
            )
            
            if existing_mapping:
                # Return existing URL instead of creating duplicate
                return URLResponse(
                    short_url=existing_mapping.short_url,
                    original_url=existing_mapping.original_url,
                    expires_at=existing_mapping.expires_at,
                    created_at=existing_mapping.created_at,
                    click_count=existing_mapping.total_clicks
                )
            
            # Create URL mapping
            url_mapping = URLMapping(
                short_url=short_url,
                original_url=str(url_request.url),
                user_id=user_id,
                custom_alias=url_request.custom_alias,
                expires_at=url_request.expires_at,
                created_at=datetime.utcnow()
            )
            
            self.db.add(url_mapping)
            self.db.commit()
            self.db.refresh(url_mapping)
            
            # Build response URL
            base_url = f"{fastapi_request.url.scheme}://{fastapi_request.url.netloc}"
            full_short_url = f"{base_url}/{short_url}"
            
            return URLResponse(
                short_url=full_short_url,
                original_url=str(url_request.url),
                expires_at=url_mapping.expires_at,
                created_at=url_mapping.created_at,
                click_count=url_mapping.total_clicks
            )
            
        except (URLValidationException, DuplicateURLException, RateLimitException):
            raise
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to create short URL: {str(e)}",
                operation="shorten_url",
                details={"original_url": str(url_request.url)}
            )
    
    def get_original_url(self, short_url: str, fastapi_request: Request) -> str:
        """
        Get original URL with analytics tracking.
        
        Args:
            short_url: The short URL to resolve
            fastapi_request: FastAPI request object for tracking
            
        Returns:
            Original URL string
            
        Raises:
            URLNotFoundException: If URL mapping not found
            URLExpiredException: If URL has expired
            DatabaseException: If database operation fails
        """
        try:
            # Get URL mapping
            url_mapping = self.db.filter_query(
                URLMapping, 
                URLMapping.short_url, 
                short_url
            )
            
            if not url_mapping:
                raise URLNotFoundException(short_url=short_url)
            
            # Check if URL has expired
            if url_mapping.expires_at and url_mapping.expires_at < datetime.utcnow():
                raise URLExpiredException(
                    short_url=short_url,
                    expired_at=url_mapping.expires_at.isoformat()
                )
            
            # Track click analytics
            try:
                client_ip = self._get_client_ip(fastapi_request)
                user_agent = fastapi_request.headers.get("user-agent")
                referrer = fastapi_request.headers.get("referer")
                
                self.analytics_service.track_click(
                    short_url=short_url,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    referrer=referrer
                )
            except Exception as e:
                # Don't fail the redirect if analytics tracking fails
                print(f"Analytics tracking failed: {str(e)}")
            
            return url_mapping.original_url
            
        except (URLNotFoundException, URLExpiredException):
            raise
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to get original URL: {str(e)}",
                operation="get_original_url",
                details={"short_url": short_url}
            )
    
    def bulk_shorten_urls(
        self, 
        bulk_request: BulkURLRequest, 
        fastapi_request: Request,
        user_id: Optional[str] = None
    ) -> BulkURLResponse:
        """
        Create multiple short URLs in bulk.
        
        Args:
            bulk_request: Bulk URL request containing multiple URLs
            fastapi_request: FastAPI request object
            user_id: Optional user ID for authenticated users
            
        Returns:
            BulkURLResponse with results
            
        Raises:
            RateLimitException: If rate limit is exceeded
            ValidationException: If request validation fails
        """
        try:
            # Check rate limit for bulk operation
            client_ip = self._get_client_ip(fastapi_request)
            self.rate_limiter.check_rate_limit(
                identifier=client_ip,
                endpoint="/bulk-shorten/",
                user_id=user_id
            )
            
            created_urls = []
            failed_urls = []
            
            for url in bulk_request.urls:
                try:
                    # Create individual URL request
                    url_request = URLRequest(
                        url=url,
                        expires_at=bulk_request.expires_at,
                        user_id=user_id
                    )
                    
                    # Create short URL
                    response = self.shorten_url(url_request, fastapi_request, user_id)
                    created_urls.append(response)
                    
                except Exception as e:
                    failed_urls.append({
                        "url": str(url),
                        "error": str(e),
                        "error_type": type(e).__name__
                    })
            
            return BulkURLResponse(
                created_urls=created_urls,
                failed_urls=failed_urls,
                total_requested=len(bulk_request.urls),
                total_created=len(created_urls),
                total_failed=len(failed_urls)
            )
            
        except RateLimitException:
            raise
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to bulk shorten URLs: {str(e)}",
                operation="bulk_shorten_urls"
            )
    
    def get_user_urls(
        self, 
        user_id: str, 
        page: int = 1, 
        page_size: int = 20
    ) -> URLListResponse:
        """
        Get all URLs created by a user with pagination.
        
        Args:
            user_id: User ID to get URLs for
            page: Page number (1-based)
            page_size: Number of URLs per page
            
        Returns:
            URLListResponse with paginated URLs
            
        Raises:
            ValidationException: If pagination parameters are invalid
            DatabaseException: If database operation fails
        """
        try:
            if page < 1:
                raise ValidationException(
                    message="Page number must be positive",
                    field="page"
                )
            
            if page_size < 1 or page_size > 100:
                raise ValidationException(
                    message="Page size must be between 1 and 100",
                    field="page_size"
                )
            
            # Calculate offset
            offset = (page - 1) * page_size
            
            # Get total count
            total_count = self.db.query(URLMapping).filter(
                URLMapping.user_id == user_id
            ).count()
            
            # Get paginated URLs
            url_mappings = self.db.query(URLMapping).filter(
                URLMapping.user_id == user_id
            ).offset(offset).limit(page_size).all()
            
            # Convert to response models
            urls = []
            for mapping in url_mappings:
                urls.append(URLResponse(
                    short_url=mapping.short_url,
                    original_url=mapping.original_url,
                    expires_at=mapping.expires_at,
                    created_at=mapping.created_at,
                    click_count=mapping.total_clicks
                ))
            
            return URLListResponse(
                urls=urls,
                total_count=total_count,
                page=page,
                page_size=page_size,
                has_next=offset + page_size < total_count,
                has_previous=page > 1
            )
            
        except ValidationException:
            raise
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to get user URLs: {str(e)}",
                operation="get_user_urls",
                details={"user_id": user_id}
            )
    
    def delete_url(self, short_url: str, user_id: str) -> bool:
        """
        Delete a URL mapping (only by the user who created it).
        
        Args:
            short_url: The short URL to delete
            user_id: User ID who owns the URL
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundException: If URL not found
            AuthorizationException: If user doesn't own the URL
        """
        try:
            url_mapping = self.db.filter_query(
                URLMapping,
                URLMapping.short_url,
                short_url
            )
            
            if not url_mapping:
                raise NotFoundException(
                    message=f"URL mapping not found: {short_url}",
                    resource_type="url_mapping",
                    resource_id=short_url
                )
            
            # Check ownership
            if url_mapping.user_id != user_id:
                raise AuthorizationException(
                    message="You can only delete your own URLs",
                    required_permission="url_owner",
                    details={"url_owner": url_mapping.user_id}
                )
            
            # Delete the URL mapping
            self.db.delete(url_mapping)
            self.db.commit()
            
            return True
            
        except (NotFoundException, AuthorizationException):
            raise
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to delete URL: {str(e)}",
                operation="delete_url",
                details={"short_url": short_url}
            )
    
    def update_url_expiration(
        self, 
        short_url: str, 
        expires_at: datetime, 
        user_id: str
    ) -> URLResponse:
        """
        Update URL expiration date.
        
        Args:
            short_url: The short URL to update
            expires_at: New expiration date
            user_id: User ID who owns the URL
            
        Returns:
            Updated URLResponse
            
        Raises:
            NotFoundException: If URL not found
            AuthorizationException: If user doesn't own the URL
            ValidationException: If expiration date is invalid
        """
        try:
            # Validate expiration date
            if expires_at <= datetime.utcnow():
                raise ValidationException(
                    message="Expiration date must be in the future",
                    field="expires_at"
                )
            
            url_mapping = self.db.filter_query(
                URLMapping,
                URLMapping.short_url,
                short_url
            )
            
            if not url_mapping:
                raise NotFoundException(
                    message=f"URL mapping not found: {short_url}",
                    resource_type="url_mapping",
                    resource_id=short_url
                )
            
            # Check ownership
            if url_mapping.user_id != user_id:
                raise AuthorizationException(
                    message="You can only update your own URLs",
                    required_permission="url_owner",
                    details={"url_owner": url_mapping.user_id}
                )
            
            # Update expiration
            url_mapping.expires_at = expires_at
            url_mapping.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(url_mapping)
            
            return URLResponse(
                short_url=url_mapping.short_url,
                original_url=url_mapping.original_url,
                expires_at=url_mapping.expires_at,
                created_at=url_mapping.created_at,
                click_count=url_mapping.total_clicks
            )
            
        except (NotFoundException, AuthorizationException, ValidationException):
            raise
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to update URL expiration: {str(e)}",
                operation="update_url_expiration",
                details={"short_url": short_url}
            )
    
    def _generate_unique_short_url(self) -> str:
        """Generate a unique short URL."""
        max_attempts = 10
        for _ in range(max_attempts):
            short_url = shortuuid.uuid()[:6]
            
            # Check if it already exists
            existing = self.db.filter_query(
                URLMapping,
                URLMapping.short_url,
                short_url
            )
            
            if not existing:
                return short_url
        
        raise ServiceUnavailableException(
            message="Unable to generate unique short URL after maximum attempts",
            service_name="url_generation"
        )
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct IP
        return request.client.host if request.client else "unknown"
