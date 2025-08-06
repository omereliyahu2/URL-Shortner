from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel, HttpUrl, validator, Field
from enum import Enum


class URLRequest(BaseModel):
    """Request model for creating short URLs."""
    url: HttpUrl = Field(..., description="The original URL to shorten")
    custom_alias: Optional[str] = Field(None, max_length=20, description="Custom short URL alias")
    expires_at: Optional[datetime] = Field(None, description="Expiration date for the URL")
    user_id: Optional[str] = Field(None, description="User ID for the URL")
    
    @validator('custom_alias')
    def validate_custom_alias(cls, v):
        if v is not None:
            if not v.isalnum():
                raise ValueError("Custom alias must contain only alphanumeric characters")
            if len(v) < 3:
                raise ValueError("Custom alias must be at least 3 characters long")
        return v
    
    @validator('expires_at')
    def validate_expires_at(cls, v):
        if v is not None and v <= datetime.utcnow():
            raise ValueError("Expiration date must be in the future")
        return v


class URLResponse(BaseModel):
    """Response model for short URL creation."""
    short_url: str
    original_url: str
    expires_at: Optional[datetime]
    created_at: datetime
    click_count: int = 0


class URLStats(BaseModel):
    """Model for URL statistics."""
    short_url: str
    original_url: str
    total_clicks: int
    unique_clicks: int
    last_clicked_at: Optional[datetime]
    created_at: datetime
    expires_at: Optional[datetime]


class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class UserRequest(BaseModel):
    """Request model for user creation."""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    role: UserRole = Field(default=UserRole.USER, description="User role")


class UserResponse(BaseModel):
    """Response model for user data."""
    user_id: str
    username: str
    email: str
    role: UserRole
    created_at: datetime
    is_active: bool


class LoginRequest(BaseModel):
    """Request model for user login."""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")


class LoginResponse(BaseModel):
    """Response model for login."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class HealthCheckResponse(BaseModel):
    """Response model for health check."""
    status: str
    timestamp: datetime
    version: str
    services: dict


class RateLimitInfo(BaseModel):
    """Model for rate limit information."""
    remaining_requests: int
    reset_time: datetime
    limit: int


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error_code: str
    message: str
    details: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class URLListResponse(BaseModel):
    """Response model for URL list."""
    urls: List[URLResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


class AnalyticsRequest(BaseModel):
    """Request model for analytics data."""
    start_date: Optional[datetime] = Field(None, description="Start date for analytics")
    end_date: Optional[datetime] = Field(None, description="End date for analytics")
    user_id: Optional[str] = Field(None, description="Filter by user ID")


class ClickEvent(BaseModel):
    """Model for click tracking events."""
    short_url: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    referrer: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None


class BulkURLRequest(BaseModel):
    """Request model for bulk URL creation."""
    urls: List[HttpUrl] = Field(..., max_items=100, description="List of URLs to shorten")
    expires_at: Optional[datetime] = Field(None, description="Expiration date for all URLs")
    user_id: Optional[str] = Field(None, description="User ID for the URLs")


class BulkURLResponse(BaseModel):
    """Response model for bulk URL creation."""
    created_urls: List[URLResponse]
    failed_urls: List[dict]
    total_requested: int
    total_created: int
    total_failed: int