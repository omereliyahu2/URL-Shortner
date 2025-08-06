"""
Enhanced database manager with comprehensive error handling and custom exceptions.
"""

from typing import Any, Optional, List
from datetime import datetime
import logging

from injector import inject
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import (
    SQLAlchemyError, 
    IntegrityError, 
    OperationalError, 
    DisconnectionError,
    TimeoutError as SQLTimeoutError
)

from domain.db_manager_interface import DBManagerInterface
from domain.secrets_manager_interface import SecretsManagerInterface
from domain.exceptions import (
    DatabaseException,
    ConnectionException,
    ConfigurationException,
    SecretsManagerException
)
from infrastructure.models import Base

# Configure logging
logger = logging.getLogger(__name__)


class DBManager(DBManagerInterface):
    """Enhanced database manager with comprehensive error handling."""
    
    @inject
    def __init__(self, secrets_manager: SecretsManagerInterface):
        try:
            # Get database configuration from secrets manager
            secret = secrets_manager.get_secret("url_database-1")
            
            if not secret:
                raise ConfigurationException(
                    message="Database configuration not found in secrets",
                    config_key="url_database-1"
                )
            
            # Validate required database configuration
            required_keys = ['engine', 'username', 'password', 'host', 'port', 'dbname']
            missing_keys = [key for key in required_keys if key not in secret]
            
            if missing_keys:
                raise ConfigurationException(
                    message=f"Missing required database configuration keys: {missing_keys}",
                    config_key="database_config",
                    details={"missing_keys": missing_keys}
                )
            
            # Build database URL
            database_url = (
                f"{secret['engine']}://{secret['username']}:{secret['password']}"
                f"@{secret['host']}:{secret['port']}/{secret['dbname']}"
            )
            
            # Create engine with enhanced configuration
            self.engine = create_engine(
                database_url,
                connect_args={
                    "connect_timeout": 20,
                    "application_name": "url_shortener"
                },
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False  # Set to True for SQL debugging
            )
            
            # Create session factory
            self.session_local = sessionmaker(
                autocommit=False, 
                autoflush=False, 
                bind=self.engine
            )
            
            # Create database tables
            self._create_tables()
            
            # Initialize session
            self.db: Session = self.session_local()
            
            # Test connection
            self._test_connection()
            
            logger.info("Database manager initialized successfully")
            
        except SecretsManagerException as e:
            logger.error(f"Secrets manager error: {str(e)}")
            raise
        except ConfigurationException as e:
            logger.error(f"Configuration error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            raise ConnectionException(
                message=f"Failed to initialize database: {str(e)}",
                details={"error_type": type(e).__name__}
            )
    
    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created/verified successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {str(e)}")
            raise DatabaseException(
                message=f"Failed to create database tables: {str(e)}",
                operation="create_tables"
            )
    
    def _test_connection(self) -> None:
        """Test database connection."""
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            raise ConnectionException(
                message=f"Database connection test failed: {str(e)}",
                details={"error_type": type(e).__name__}
            )
    
    def add(self, obj: Any) -> None:
        """
        Add an object to the database session.
        
        Args:
            obj: SQLAlchemy model object to add
            
        Raises:
            DatabaseException: If database operation fails
        """
        try:
            self.db.add(obj)
            logger.debug(f"Added object to session: {type(obj).__name__}")
        except Exception as e:
            logger.error(f"Failed to add object to session: {str(e)}")
            raise DatabaseException(
                message=f"Failed to add object to database: {str(e)}",
                operation="add",
                details={"object_type": type(obj).__name__}
            )
    
    def commit(self) -> None:
        """
        Commit the current database transaction.
        
        Raises:
            DatabaseException: If commit operation fails
        """
        try:
            self.db.commit()
            logger.debug("Database transaction committed successfully")
        except IntegrityError as e:
            logger.error(f"Integrity error during commit: {str(e)}")
            self.db.rollback()
            raise DatabaseException(
                message=f"Database integrity error: {str(e)}",
                operation="commit",
                details={"error_type": "integrity_error"}
            )
        except OperationalError as e:
            logger.error(f"Operational error during commit: {str(e)}")
            self.db.rollback()
            raise DatabaseException(
                message=f"Database operational error: {str(e)}",
                operation="commit",
                details={"error_type": "operational_error"}
            )
        except Exception as e:
            logger.error(f"Unexpected error during commit: {str(e)}")
            self.db.rollback()
            raise DatabaseException(
                message=f"Failed to commit database transaction: {str(e)}",
                operation="commit",
                details={"error_type": type(e).__name__}
            )
    
    def rollback(self) -> None:
        """Rollback the current database transaction."""
        try:
            self.db.rollback()
            logger.debug("Database transaction rolled back")
        except Exception as e:
            logger.error(f"Failed to rollback transaction: {str(e)}")
            # Don't raise exception for rollback failures
    
    def refresh(self, obj: Any) -> None:
        """
        Refresh an object from the database.
        
        Args:
            obj: SQLAlchemy model object to refresh
            
        Raises:
            DatabaseException: If refresh operation fails
        """
        try:
            self.db.refresh(obj)
            logger.debug(f"Refreshed object: {type(obj).__name__}")
        except Exception as e:
            logger.error(f"Failed to refresh object: {str(e)}")
            raise DatabaseException(
                message=f"Failed to refresh object: {str(e)}",
                operation="refresh",
                details={"object_type": type(obj).__name__}
            )
    
    def filter_query(self, model: Any, field: Any, value: Any) -> Optional[Any]:
        """
        Filter query with enhanced error handling.
        
        Args:
            model: SQLAlchemy model class
            field: Model field to filter on
            value: Value to filter by
            
        Returns:
            First matching object or None
            
        Raises:
            DatabaseException: If query operation fails
        """
        try:
            result = self.db.query(model).filter(field == value).first()
            logger.debug(f"Filter query executed: {model.__name__} where {field} = {value}")
            return result
        except Exception as e:
            logger.error(f"Failed to execute filter query: {str(e)}")
            raise DatabaseException(
                message=f"Failed to execute database query: {str(e)}",
                operation="filter_query",
                details={
                    "model": model.__name__,
                    "field": str(field),
                    "value": str(value)
                }
            )
    
    def query(self, model: Any):
        """
        Get a query object for a model.
        
        Args:
            model: SQLAlchemy model class
            
        Returns:
            SQLAlchemy query object
            
        Raises:
            DatabaseException: If query creation fails
        """
        try:
            return self.db.query(model)
        except Exception as e:
            logger.error(f"Failed to create query: {str(e)}")
            raise DatabaseException(
                message=f"Failed to create database query: {str(e)}",
                operation="query",
                details={"model": model.__name__}
            )
    
    def delete(self, obj: Any) -> None:
        """
        Delete an object from the database.
        
        Args:
            obj: SQLAlchemy model object to delete
            
        Raises:
            DatabaseException: If delete operation fails
        """
        try:
            self.db.delete(obj)
            logger.debug(f"Deleted object: {type(obj).__name__}")
        except Exception as e:
            logger.error(f"Failed to delete object: {str(e)}")
            raise DatabaseException(
                message=f"Failed to delete object: {str(e)}",
                operation="delete",
                details={"object_type": type(obj).__name__}
            )
    
    def get_by_id(self, model: Any, id_value: Any) -> Optional[Any]:
        """
        Get an object by its primary key.
        
        Args:
            model: SQLAlchemy model class
            id_value: Primary key value
            
        Returns:
            Object if found, None otherwise
            
        Raises:
            DatabaseException: If query operation fails
        """
        try:
            result = self.db.query(model).filter(model.__table__.primary_key.columns[0] == id_value).first()
            logger.debug(f"Get by ID query executed: {model.__name__} with ID {id_value}")
            return result
        except Exception as e:
            logger.error(f"Failed to get object by ID: {str(e)}")
            raise DatabaseException(
                message=f"Failed to get object by ID: {str(e)}",
                operation="get_by_id",
                details={
                    "model": model.__name__,
                    "id_value": str(id_value)
                }
            )
    
    def get_all(self, model: Any, limit: Optional[int] = None) -> List[Any]:
        """
        Get all objects of a model type.
        
        Args:
            model: SQLAlchemy model class
            limit: Optional limit on number of results
            
        Returns:
            List of model objects
            
        Raises:
            DatabaseException: If query operation fails
        """
        try:
            query = self.db.query(model)
            if limit:
                query = query.limit(limit)
            result = query.all()
            logger.debug(f"Get all query executed: {model.__name__}, returned {len(result)} results")
            return result
        except Exception as e:
            logger.error(f"Failed to get all objects: {str(e)}")
            raise DatabaseException(
                message=f"Failed to get all objects: {str(e)}",
                operation="get_all",
                details={"model": model.__name__}
            )
    
    def count(self, model: Any) -> int:
        """
        Get count of objects for a model.
        
        Args:
            model: SQLAlchemy model class
            
        Returns:
            Count of objects
            
        Raises:
            DatabaseException: If count operation fails
        """
        try:
            result = self.db.query(model).count()
            logger.debug(f"Count query executed: {model.__name__}, count: {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to count objects: {str(e)}")
            raise DatabaseException(
                message=f"Failed to count objects: {str(e)}",
                operation="count",
                details={"model": model.__name__}
            )
    
    def execute_raw_sql(self, sql: str, params: Optional[dict] = None) -> Any:
        """
        Execute raw SQL query.
        
        Args:
            sql: SQL query string
            params: Optional parameters for the query
            
        Returns:
            Query result
            
        Raises:
            DatabaseException: If SQL execution fails
        """
        try:
            result = self.db.execute(text(sql), params or {})
            logger.debug(f"Raw SQL executed: {sql[:100]}...")
            return result
        except Exception as e:
            logger.error(f"Failed to execute raw SQL: {str(e)}")
            raise DatabaseException(
                message=f"Failed to execute raw SQL: {str(e)}",
                operation="execute_raw_sql",
                details={"sql": sql[:100] + "..." if len(sql) > 100 else sql}
            )
    
    def health_check(self) -> dict:
        """
        Perform database health check.
        
        Returns:
            Health check status dictionary
        """
        try:
            # Test connection
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1 as health_check"))
                row = result.fetchone()
                
                # Get database info
                db_info = connection.execute(text("SELECT version()")).fetchone()
                
                return {
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "database_version": db_info[0] if db_info else "unknown",
                    "connection_pool_size": self.engine.pool.size(),
                    "connection_pool_checked_in": self.engine.pool.checkedin(),
                    "connection_pool_checked_out": self.engine.pool.checkedout()
                }
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def __del__(self):
        """Cleanup database session on destruction."""
        try:
            if hasattr(self, 'db') and self.db:
                self.db.close()
                logger.debug("Database session closed")
        except Exception as e:
            logger.error(f"Failed to close database session: {str(e)}")
