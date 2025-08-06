from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"
    
    user_id = Column(String(50), primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    url_mappings = relationship("URLMapping", back_populates="user")
    click_events = relationship("ClickEvent", back_populates="user")
    
    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_username', 'username'),
        Index('idx_users_role', 'role'),
    )


class URLMapping(Base):
    """Enhanced URL mapping model with expiration and analytics."""
    __tablename__ = "url_mappings"
    
    short_url = Column(String(256), primary_key=True, index=True)
    original_url = Column(String(2048), nullable=False, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=True, index=True)
    custom_alias = Column(String(20), unique=True, nullable=True, index=True)
    expires_at = Column(DateTime, nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Analytics fields
    total_clicks = Column(Integer, default=0)
    unique_clicks = Column(Integer, default=0)
    last_clicked_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="url_mappings")
    click_events = relationship("ClickEvent", back_populates="url_mapping")
    
    __table_args__ = (
        Index('idx_url_mappings_original_url', 'original_url'),
        Index('idx_url_mappings_user_id', 'user_id'),
        Index('idx_url_mappings_expires_at', 'expires_at'),
        Index('idx_url_mappings_created_at', 'created_at'),
        Index('idx_url_mappings_total_clicks', 'total_clicks'),
    )


class ClickEvent(Base):
    """Model for tracking URL click events."""
    __tablename__ = "click_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    short_url = Column(String(256), ForeignKey("url_mappings.short_url"), nullable=False, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    referrer = Column(String(2048), nullable=True)
    timestamp = Column(DateTime, default=func.now(), index=True)
    
    # Relationships
    url_mapping = relationship("URLMapping", back_populates="click_events")
    user = relationship("User", back_populates="click_events")
    
    __table_args__ = (
        Index('idx_click_events_short_url', 'short_url'),
        Index('idx_click_events_timestamp', 'timestamp'),
        Index('idx_click_events_user_id', 'user_id'),
        Index('idx_click_events_ip_address', 'ip_address'),
    )


class RateLimit(Base):
    """Model for tracking rate limits."""
    __tablename__ = "rate_limits"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    identifier = Column(String(255), nullable=False, index=True)  # IP or user_id
    endpoint = Column(String(100), nullable=False)
    request_count = Column(Integer, default=1)
    window_start = Column(DateTime, nullable=False, index=True)
    window_end = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_rate_limits_identifier', 'identifier'),
        Index('idx_rate_limits_endpoint', 'endpoint'),
        Index('idx_rate_limits_window', 'window_start', 'window_end'),
    )


class APIKey(Base):
    """Model for API key management."""
    __tablename__ = "api_keys"
    
    key_id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False, index=True)
    api_key = Column(String(255), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('idx_api_keys_user_id', 'user_id'),
        Index('idx_api_keys_api_key', 'api_key'),
        Index('idx_api_keys_expires_at', 'expires_at'),
    )


class SystemLog(Base):
    """Model for system logging."""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String(20), nullable=False, index=True)
    message = Column(Text, nullable=False)
    module = Column(String(100), nullable=True)
    function = Column(String(100), nullable=True)
    line_number = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=func.now(), index=True)
    user_id = Column(String(50), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    additional_data = Column(Text, nullable=True)  # JSON string
    
    __table_args__ = (
        Index('idx_system_logs_level', 'level'),
        Index('idx_system_logs_timestamp', 'timestamp'),
        Index('idx_system_logs_user_id', 'user_id'),
    )