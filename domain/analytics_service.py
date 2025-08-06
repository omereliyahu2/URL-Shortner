"""
Analytics service for tracking URL clicks and generating insights.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from collections import defaultdict
import json

from domain.exceptions import (
    NotFoundException,
    DatabaseException,
    ValidationException,
    ServiceUnavailableException
)
from domain.db_manager_interface import DBManagerInterface
from domain.models import ClickEvent, AnalyticsRequest
from infrastructure.models import URLMapping, ClickEvent as ClickEventModel, User


class AnalyticsService:
    """Comprehensive analytics service for URL tracking and insights."""
    
    def __init__(self, db_manager: DBManagerInterface):
        self.db = db_manager
    
    def track_click(
        self, 
        short_url: str, 
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        referrer: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Track a URL click event.
        
        Args:
            short_url: The short URL that was clicked
            ip_address: IP address of the clicker
            user_agent: User agent string
            referrer: Referrer URL
            user_id: User ID if authenticated
            
        Returns:
            Dict containing tracking information
            
        Raises:
            NotFoundException: If URL mapping not found
            DatabaseException: If database operation fails
        """
        try:
            # Verify URL mapping exists
            url_mapping = self.db.filter_query(
                URLMapping, 
                URLMapping.short_url, 
                short_url
            )
            
            if not url_mapping:
                raise NotFoundException(
                    message=f"URL mapping not found for short URL: {short_url}",
                    resource_type="url_mapping",
                    resource_id=short_url
                )
            
            # Check if URL has expired
            if url_mapping.expires_at and url_mapping.expires_at < datetime.utcnow():
                raise NotFoundException(
                    message=f"URL has expired: {short_url}",
                    resource_type="url_mapping",
                    resource_id=short_url,
                    details={"expired_at": url_mapping.expires_at.isoformat()}
                )
            
            # Create click event
            click_event = ClickEventModel(
                short_url=short_url,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                referrer=referrer,
                timestamp=datetime.utcnow()
            )
            
            self.db.add(click_event)
            
            # Update URL mapping statistics
            url_mapping.total_clicks += 1
            url_mapping.last_clicked_at = datetime.utcnow()
            
            # Update unique clicks (simplified - in production you'd use more sophisticated tracking)
            if user_id:
                existing_click = self.db.filter_query(
                    ClickEventModel,
                    ClickEventModel.short_url == short_url,
                    ClickEventModel.user_id == user_id
                )
                if not existing_click:
                    url_mapping.unique_clicks += 1
            
            self.db.commit()
            
            return {
                "short_url": short_url,
                "original_url": url_mapping.original_url,
                "total_clicks": url_mapping.total_clicks,
                "unique_clicks": url_mapping.unique_clicks,
                "timestamp": click_event.timestamp.isoformat()
            }
            
        except NotFoundException:
            raise
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to track click: {str(e)}",
                operation="track_click",
                details={"short_url": short_url}
            )
    
    def get_url_analytics(
        self, 
        short_url: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get analytics for a specific URL.
        
        Args:
            short_url: The short URL to get analytics for
            start_date: Start date for analytics period
            end_date: End date for analytics period
            
        Returns:
            Dict containing analytics data
            
        Raises:
            NotFoundException: If URL mapping not found
            ValidationException: If date range is invalid
        """
        try:
            # Validate date range
            if start_date and end_date and start_date >= end_date:
                raise ValidationException(
                    message="Start date must be before end date",
                    field="date_range"
                )
            
            # Get URL mapping
            url_mapping = self.db.filter_query(
                URLMapping, 
                URLMapping.short_url, 
                short_url
            )
            
            if not url_mapping:
                raise NotFoundException(
                    message=f"URL mapping not found for short URL: {short_url}",
                    resource_type="url_mapping",
                    resource_id=short_url
                )
            
            # Build query for click events
            query = self.db.query(ClickEventModel).filter(
                ClickEventModel.short_url == short_url
            )
            
            if start_date:
                query = query.filter(ClickEventModel.timestamp >= start_date)
            
            if end_date:
                query = query.filter(ClickEventModel.timestamp <= end_date)
            
            click_events = query.all()
            
            # Calculate analytics
            analytics = self._calculate_analytics(click_events, url_mapping)
            
            return {
                "short_url": short_url,
                "original_url": url_mapping.original_url,
                "created_at": url_mapping.created_at.isoformat(),
                "expires_at": url_mapping.expires_at.isoformat() if url_mapping.expires_at else None,
                "analytics": analytics,
                "period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                }
            }
            
        except (NotFoundException, ValidationException):
            raise
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to get analytics: {str(e)}",
                operation="get_analytics",
                details={"short_url": short_url}
            )
    
    def get_user_analytics(
        self, 
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get analytics for all URLs created by a user.
        
        Args:
            user_id: User ID to get analytics for
            start_date: Start date for analytics period
            end_date: End date for analytics period
            
        Returns:
            Dict containing user analytics data
        """
        try:
            # Validate date range
            if start_date and end_date and start_date >= end_date:
                raise ValidationException(
                    message="Start date must be before end date",
                    field="date_range"
                )
            
            # Get user's URL mappings
            query = self.db.query(URLMapping).filter(
                URLMapping.user_id == user_id
            )
            
            if start_date:
                query = query.filter(URLMapping.created_at >= start_date)
            
            if end_date:
                query = query.filter(URLMapping.created_at <= end_date)
            
            url_mappings = query.all()
            
            if not url_mappings:
                return {
                    "user_id": user_id,
                    "total_urls": 0,
                    "total_clicks": 0,
                    "unique_clicks": 0,
                    "urls": [],
                    "period": {
                        "start_date": start_date.isoformat() if start_date else None,
                        "end_date": end_date.isoformat() if end_date else None
                    }
                }
            
            # Calculate user analytics
            total_clicks = sum(url.total_clicks for url in url_mappings)
            unique_clicks = sum(url.unique_clicks for url in url_mappings)
            
            # Get detailed analytics for each URL
            urls_analytics = []
            for url_mapping in url_mappings:
                url_analytics = {
                    "short_url": url_mapping.short_url,
                    "original_url": url_mapping.original_url,
                    "created_at": url_mapping.created_at.isoformat(),
                    "expires_at": url_mapping.expires_at.isoformat() if url_mapping.expires_at else None,
                    "total_clicks": url_mapping.total_clicks,
                    "unique_clicks": url_mapping.unique_clicks,
                    "last_clicked_at": url_mapping.last_clicked_at.isoformat() if url_mapping.last_clicked_at else None
                }
                urls_analytics.append(url_analytics)
            
            return {
                "user_id": user_id,
                "total_urls": len(url_mappings),
                "total_clicks": total_clicks,
                "unique_clicks": unique_clicks,
                "urls": urls_analytics,
                "period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                }
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to get user analytics: {str(e)}",
                operation="get_user_analytics",
                details={"user_id": user_id}
            )
    
    def get_global_analytics(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get global analytics for the entire system.
        
        Args:
            start_date: Start date for analytics period
            end_date: End date for analytics period
            
        Returns:
            Dict containing global analytics data
        """
        try:
            # Validate date range
            if start_date and end_date and start_date >= end_date:
                raise ValidationException(
                    message="Start date must be before end date",
                    field="date_range"
                )
            
            # Get all URL mappings
            query = self.db.query(URLMapping)
            
            if start_date:
                query = query.filter(URLMapping.created_at >= start_date)
            
            if end_date:
                query = query.filter(URLMapping.created_at <= end_date)
            
            url_mappings = query.all()
            
            # Calculate global statistics
            total_urls = len(url_mappings)
            total_clicks = sum(url.total_clicks for url in url_mappings)
            unique_clicks = sum(url.unique_clicks for url in url_mappings)
            
            # Get click events for detailed analytics
            click_query = self.db.query(ClickEventModel)
            
            if start_date:
                click_query = click_query.filter(ClickEventModel.timestamp >= start_date)
            
            if end_date:
                click_query = click_query.filter(ClickEventModel.timestamp <= end_date)
            
            click_events = click_query.all()
            
            # Calculate time-based analytics
            time_analytics = self._calculate_time_analytics(click_events)
            
            # Calculate referrer analytics
            referrer_analytics = self._calculate_referrer_analytics(click_events)
            
            return {
                "total_urls": total_urls,
                "total_clicks": total_clicks,
                "unique_clicks": unique_clicks,
                "time_analytics": time_analytics,
                "referrer_analytics": referrer_analytics,
                "period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                }
            }
            
        except ValidationException:
            raise
        except Exception as e:
            raise DatabaseException(
                message=f"Failed to get global analytics: {str(e)}",
                operation="get_global_analytics"
            )
    
    def _calculate_analytics(
        self, 
        click_events: List[ClickEventModel], 
        url_mapping: URLMapping
    ) -> Dict[str, Any]:
        """Calculate analytics for a list of click events."""
        if not click_events:
            return {
                "total_clicks": 0,
                "unique_clicks": 0,
                "clicks_by_day": {},
                "clicks_by_hour": {},
                "top_referrers": [],
                "top_user_agents": []
            }
        
        # Calculate clicks by day
        clicks_by_day = defaultdict(int)
        clicks_by_hour = defaultdict(int)
        referrers = defaultdict(int)
        user_agents = defaultdict(int)
        
        for event in click_events:
            day = event.timestamp.strftime("%Y-%m-%d")
            hour = event.timestamp.strftime("%H")
            
            clicks_by_day[day] += 1
            clicks_by_hour[hour] += 1
            
            if event.referrer:
                referrers[event.referrer] += 1
            
            if event.user_agent:
                user_agents[event.user_agent] += 1
        
        # Get top referrers and user agents
        top_referrers = sorted(referrers.items(), key=lambda x: x[1], reverse=True)[:10]
        top_user_agents = sorted(user_agents.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_clicks": len(click_events),
            "unique_clicks": url_mapping.unique_clicks,
            "clicks_by_day": dict(clicks_by_day),
            "clicks_by_hour": dict(clicks_by_hour),
            "top_referrers": [{"referrer": ref, "count": count} for ref, count in top_referrers],
            "top_user_agents": [{"user_agent": ua, "count": count} for ua, count in top_user_agents]
        }
    
    def _calculate_time_analytics(self, click_events: List[ClickEventModel]) -> Dict[str, Any]:
        """Calculate time-based analytics."""
        if not click_events:
            return {
                "clicks_by_day": {},
                "clicks_by_hour": {},
                "clicks_by_week": {}
            }
        
        clicks_by_day = defaultdict(int)
        clicks_by_hour = defaultdict(int)
        clicks_by_week = defaultdict(int)
        
        for event in click_events:
            day = event.timestamp.strftime("%Y-%m-%d")
            hour = event.timestamp.strftime("%H")
            week = event.timestamp.strftime("%Y-W%U")
            
            clicks_by_day[day] += 1
            clicks_by_hour[hour] += 1
            clicks_by_week[week] += 1
        
        return {
            "clicks_by_day": dict(clicks_by_day),
            "clicks_by_hour": dict(clicks_by_hour),
            "clicks_by_week": dict(clicks_by_week)
        }
    
    def _calculate_referrer_analytics(self, click_events: List[ClickEventModel]) -> Dict[str, Any]:
        """Calculate referrer analytics."""
        if not click_events:
            return {
                "top_referrers": [],
                "direct_clicks": 0,
                "total_with_referrer": 0
            }
        
        referrers = defaultdict(int)
        direct_clicks = 0
        
        for event in click_events:
            if event.referrer:
                referrers[event.referrer] += 1
            else:
                direct_clicks += 1
        
        top_referrers = sorted(referrers.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "top_referrers": [{"referrer": ref, "count": count} for ref, count in top_referrers],
            "direct_clicks": direct_clicks,
            "total_with_referrer": len(click_events) - direct_clicks
        } 