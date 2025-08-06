"""
Enhanced bootstrap configuration with comprehensive dependency injection.
"""

import uvicorn
from injector import Injector, Module, singleton

from domain.db_manager_interface import DBManagerInterface
from domain.secrets_manager_interface import SecretsManagerInterface
from domain.url_handler import URLHandler
from domain.url_validator import URLValidator
from domain.rate_limiter import RateLimiter
from domain.analytics_service import AnalyticsService
from infrastructure.db_manager import DBManager
from infrastructure.secrets_manager import SecretsManager


class AppModule(Module):
    """Application module for dependency injection configuration."""
    
    def configure(self, binder):
        # Core infrastructure services
        binder.bind(SecretsManagerInterface, to=SecretsManager, scope=singleton)
        binder.bind(DBManagerInterface, to=DBManager, scope=singleton)
        
        # Domain services
        binder.bind(URLValidator, to=URLValidator, scope=singleton)
        binder.bind(RateLimiter, to=RateLimiter, scope=singleton)
        binder.bind(AnalyticsService, to=AnalyticsService, scope=singleton)
        
        # Business logic services
        binder.bind(URLHandler, to=URLHandler, scope=singleton)


# Create injector instance
injector = Injector([AppModule()])


def run_server(port: int = 8080, host: str = "localhost", reload: bool = False):
    """
    Run the FastAPI server with enhanced configuration.
    
    Args:
        port: Server port number
        host: Server host address
        reload: Whether to enable auto-reload for development
    """
    uvicorn.run(
        "web_api.api:app", 
        host=host, 
        port=port, 
        reload=reload,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    run_server(port=8080, host="localhost", reload=False)
