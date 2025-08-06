"""
Comprehensive URL Shortener API with enhanced features and error handling.
"""

import logging
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from fastapi import FastAPI, Request, HTTPException, Depends, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response

from domain.models import (
    URLRequest, URLResponse, URLListResponse, BulkURLRequest, BulkURLResponse,
    HealthCheckResponse, ErrorResponse, AnalyticsRequest, UserRequest, UserResponse,
    LoginRequest, LoginResponse
)
from domain.exceptions import (
    URLShortenerException, ValidationException, URLValidationException,
    URLNotFoundException, DuplicateURLException, URLExpiredException,
    DatabaseException, NotFoundException, RateLimitException,
    AuthenticationException, AuthorizationException, ServiceUnavailableException
)
from domain.url_handler import URLHandler
from domain.analytics_service import AnalyticsService
from domain.rate_limiter import RateLimiter
from bootstrap.bootstrap import injector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="URL Shortener API",
    description="A comprehensive URL shortening service with analytics, rate limiting, and user management",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8001", "https://omereliyahu2.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for handling custom exceptions."""
    
    async def dispatch(self, request: StarletteRequest, call_next):
        try:
            response = await call_next(request)
            return response
        except URLShortenerException as e:
            logger.error(f"Custom exception: {e.message}", extra=e.details)
            return JSONResponse(
                status_code=e.status_code,
                content=ErrorResponse(
                    error_code=e.error_code,
                    message=e.message,
                    details=e.details
                ).dict()
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content=ErrorResponse(
                    error_code="INTERNAL_SERVER_ERROR",
                    message="An unexpected error occurred",
                    details={"error_type": type(e).__name__}
                ).dict()
            )


app.add_middleware(ErrorHandlingMiddleware)


# Dependency injection
def get_url_handler() -> URLHandler:
    return injector.get(URLHandler)


def get_analytics_service() -> AnalyticsService:
    return injector.get(AnalyticsService)


def get_rate_limiter() -> RateLimiter:
    return injector.get(RateLimiter)


# Authentication helper
async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[str]:
    """Get current user from JWT token (placeholder for authentication)."""
    if not credentials:
        return None
    
    # TODO: Implement JWT token validation
    # For now, return a placeholder user ID
    return "user_123"


@app.post("/shorten/", response_model=URLResponse, tags=["URL Management"])
async def create_short_url(
    url_request: URLRequest,
    request: Request,
    url_handler: URLHandler = Depends(get_url_handler),
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Create a short URL with comprehensive validation and features.
    
    - **URL Validation**: Validates URL format, accessibility, and security
    - **Rate Limiting**: Prevents abuse with configurable rate limits
    - **Custom Aliases**: Optional custom short URL aliases
    - **Expiration**: Optional URL expiration dates
    - **Analytics**: Automatic click tracking and analytics
    """
    try:
        return await url_handler.shorten_url(url_request, request, current_user)
    except (URLValidationException, DuplicateURLException, RateLimitException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@app.post("/bulk-shorten/", response_model=BulkURLResponse, tags=["URL Management"])
async def bulk_create_short_urls(
    bulk_request: BulkURLRequest,
    request: Request,
    url_handler: URLHandler = Depends(get_url_handler),
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Create multiple short URLs in bulk.
    
    - **Batch Processing**: Create up to 100 URLs at once
    - **Rate Limiting**: Stricter rate limits for bulk operations
    - **Error Handling**: Continues processing even if some URLs fail
    - **Shared Expiration**: Apply same expiration to all URLs
    """
    try:
        return await url_handler.bulk_shorten_urls(bulk_request, request, current_user)
    except (ValidationException, RateLimitException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@app.get("/{short_url}", tags=["URL Redirection"])
async def redirect_to_url(
    short_url: str = Path(..., description="The short URL to redirect"),
    request: Request = None,
    url_handler: URLHandler = Depends(get_url_handler)
):
    """
    Redirect to the original URL with analytics tracking.
    
    - **Analytics Tracking**: Records click events with metadata
    - **Expiration Check**: Validates URL hasn't expired
    - **User Agent Tracking**: Tracks browser and device information
    - **Referrer Tracking**: Records where clicks originated from
    """
    try:
        original_url = await url_handler.get_original_url(short_url, request)
        parsed_url = urlparse(original_url)
        
        if not parsed_url.scheme:
            # Default to http if no scheme is provided
            original_url = "http://" + original_url
            
        return RedirectResponse(url=original_url)
    except (URLNotFoundException, URLExpiredException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@app.get("/urls/", response_model=URLListResponse, tags=["URL Management"])
async def get_user_urls(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of URLs per page"),
    url_handler: URLHandler = Depends(get_url_handler),
    current_user: str = Depends(get_current_user)
):
    """
    Get all URLs created by the current user with pagination.
    
    - **Pagination**: Efficient pagination with configurable page sizes
    - **User Isolation**: Only returns URLs owned by the authenticated user
    - **Click Statistics**: Includes click counts and analytics
    - **Expiration Info**: Shows URL expiration dates
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        return await url_handler.get_user_urls(current_user, page, page_size)
    except ValidationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@app.delete("/urls/{short_url}", tags=["URL Management"])
async def delete_url(
    short_url: str = Path(..., description="The short URL to delete"),
    url_handler: URLHandler = Depends(get_url_handler),
    current_user: str = Depends(get_current_user)
):
    """
    Delete a URL mapping (only by the user who created it).
    
    - **Ownership Validation**: Only URL owners can delete their URLs
    - **Soft Delete**: Optionally implement soft delete for data retention
    - **Analytics Preservation**: Maintains historical analytics data
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        success = await url_handler.delete_url(short_url, current_user)
        return {"message": "URL deleted successfully", "short_url": short_url}
    except (NotFoundException, AuthorizationException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@app.put("/urls/{short_url}/expiration", response_model=URLResponse, tags=["URL Management"])
async def update_url_expiration(
    short_url: str = Path(..., description="The short URL to update"),
    expires_at: datetime = Query(..., description="New expiration date"),
    url_handler: URLHandler = Depends(get_url_handler),
    current_user: str = Depends(get_current_user)
):
    """
    Update URL expiration date.
    
    - **Future Validation**: Ensures expiration date is in the future
    - **Ownership Check**: Only URL owners can update expiration
    - **Flexible Expiration**: Supports various expiration timeframes
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        return await url_handler.update_url_expiration(short_url, expires_at, current_user)
    except (NotFoundException, AuthorizationException, ValidationException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@app.get("/analytics/url/{short_url}", tags=["Analytics"])
async def get_url_analytics(
    short_url: str = Path(..., description="The short URL to get analytics for"),
    start_date: Optional[datetime] = Query(None, description="Start date for analytics period"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics period"),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: Optional[str] = Depends(get_current_user)
):
    """
    Get detailed analytics for a specific URL.
    
    - **Click Tracking**: Total and unique click counts
    - **Time Analytics**: Clicks by day, hour, and week
    - **Referrer Analytics**: Top referrers and traffic sources
    - **User Agent Analytics**: Browser and device information
    - **Date Range Filtering**: Filter analytics by date range
    """
    try:
        return await analytics_service.get_url_analytics(short_url, start_date, end_date)
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@app.get("/analytics/user", tags=["Analytics"])
async def get_user_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date for analytics period"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics period"),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: str = Depends(get_current_user)
):
    """
    Get analytics for all URLs created by the current user.
    
    - **User Dashboard**: Comprehensive analytics for user's URLs
    - **Aggregate Statistics**: Total clicks, unique clicks, URL counts
    - **Individual URL Analytics**: Detailed stats for each URL
    - **Date Range Filtering**: Filter by specific time periods
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        return await analytics_service.get_user_analytics(current_user, start_date, end_date)
    except ValidationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@app.get("/analytics/global", tags=["Analytics"])
async def get_global_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date for analytics period"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics period"),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: str = Depends(get_current_user)
):
    """
    Get global analytics for the entire system (admin only).
    
    - **System Overview**: Total URLs, clicks, and user statistics
    - **Time-based Analytics**: System-wide click patterns
    - **Referrer Analysis**: Global traffic source analysis
    - **Performance Metrics**: System performance and usage statistics
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # TODO: Add admin role check
    try:
        return await analytics_service.get_global_analytics(start_date, end_date)
    except ValidationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@app.get("/health", response_model=HealthCheckResponse, tags=["System"])
async def health_check(
    url_handler: URLHandler = Depends(get_url_handler),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    rate_limiter: RateLimiter = Depends(get_rate_limiter)
):
    """
    Comprehensive system health check.
    
    - **Database Health**: Connection status and performance metrics
    - **Service Status**: All service components health status
    - **Performance Metrics**: Response times and throughput
    - **Configuration Status**: System configuration validation
    """
    try:
        # Get database health
        db_health = url_handler.db.health_check()
        
        # Get rate limiter status
        rate_limit_status = rate_limiter.get_all_configs()
        
        services = {
            "database": db_health,
            "rate_limiter": {
                "status": "healthy",
                "configurations": len(rate_limit_status)
            },
            "analytics": {
                "status": "healthy",
                "service": "analytics_service"
            }
        }
        
        return HealthCheckResponse(
            status="healthy" if db_health["status"] == "healthy" else "unhealthy",
            timestamp=datetime.utcnow(),
            version="2.0.0",
            services=services
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthCheckResponse(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            version="2.0.0",
            services={"error": str(e)}
        )


@app.get("/rate-limits/status", tags=["System"])
async def get_rate_limit_status(
    endpoint: str = Query(..., description="API endpoint to check"),
    identifier: str = Query(..., description="IP address or user identifier"),
    rate_limiter: RateLimiter = Depends(get_rate_limiter)
):
    """
    Get current rate limit status for an endpoint and identifier.
    
    - **Rate Limit Info**: Current usage and limits
    - **Reset Times**: When rate limits reset
    - **Remaining Requests**: How many requests are left
    """
    try:
        return rate_limiter.get_rate_limit_status(identifier, endpoint)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get rate limit status: {str(e)}")


@app.get("/rate-limits/config", tags=["System"])
async def get_rate_limit_configs(
    rate_limiter: RateLimiter = Depends(get_rate_limiter)
):
    """
    Get all rate limit configurations.
    
    - **Endpoint Configurations**: All configured rate limits
    - **Limit Details**: Requests per window and window duration
    - **Rate Limit Types**: IP-based, user-based, or global limits
    """
    try:
        return rate_limiter.get_all_configs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get rate limit configs: {str(e)}")


@app.get("/", tags=["System"])
async def root():
    """
    API root endpoint with service information.
    """
    return {
        "service": "URL Shortener API",
        "version": "2.0.0",
        "description": "A comprehensive URL shortening service with analytics, rate limiting, and user management",
        "docs": "/docs",
        "health": "/health"
    }


# Error handlers for specific exception types
@app.exception_handler(URLShortenerException)
async def url_shortener_exception_handler(request: Request, exc: URLShortenerException):
    """Handle custom URL shortener exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details
        ).dict()
    )


@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    """Handle validation exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details
        ).dict()
    )


@app.exception_handler(RateLimitException)
async def rate_limit_exception_handler(request: Request, exc: RateLimitException):
    """Handle rate limit exceptions."""
    headers = {}
    if exc.details and "retry_after" in exc.details:
        headers["Retry-After"] = str(exc.details["retry_after"])
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details
        ).dict(),
        headers=headers
    )
