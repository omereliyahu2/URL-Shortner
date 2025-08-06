# URL Shortener API v2.0

A comprehensive URL shortening service with advanced features including analytics, rate limiting, user management, and comprehensive error handling.

## 🚀 Features

### Core Functionality
- **URL Shortening**: Create short URLs with custom aliases
- **URL Validation**: Comprehensive URL validation and security checks
- **URL Expiration**: Set expiration dates for temporary URLs
- **Bulk Operations**: Create multiple URLs at once
- **Analytics**: Detailed click tracking and insights

### Advanced Features
- **Rate Limiting**: Configurable rate limits per endpoint
- **User Management**: User authentication and authorization
- **Analytics Dashboard**: Comprehensive analytics and reporting
- **Health Monitoring**: System health checks and monitoring
- **Custom Exceptions**: Comprehensive error handling system

### Security & Performance
- **Input Validation**: Robust validation with custom exceptions
- **SQL Injection Protection**: Parameterized queries
- **Rate Limiting**: Prevent abuse and ensure fair usage
- **Error Handling**: Comprehensive exception hierarchy
- **Logging**: Structured logging for debugging and monitoring

## 🏗️ Architecture

### Domain Layer
- **Custom Exceptions**: Comprehensive exception hierarchy
- **Models**: Pydantic models for request/response validation
- **Services**: Business logic services (URL handler, analytics, rate limiting)

### Infrastructure Layer
- **Database**: SQLAlchemy with enhanced error handling
- **Secrets Management**: Secure configuration management
- **Logging**: Structured logging with custom formatters

### API Layer
- **FastAPI**: Modern, fast web framework
- **Middleware**: Custom error handling middleware
- **Dependency Injection**: Clean service management

## 📁 Project Structure

```
URL-Shortner/
├── domain/                    # Domain layer
│   ├── exceptions.py         # Custom exception hierarchy
│   ├── models.py             # Pydantic models
│   ├── url_handler.py        # Enhanced URL handler
│   ├── url_validator.py      # URL validation service
│   ├── rate_limiter.py       # Rate limiting service
│   └── analytics_service.py  # Analytics service
├── infrastructure/            # Infrastructure layer
│   ├── models.py             # SQLAlchemy models
│   ├── db_manager.py         # Enhanced database manager
│   └── secrets_manager.py    # Secrets management
├── web_api/                  # API layer
│   ├── api.py               # FastAPI application
│   └── main.py              # Server entry point
├── bootstrap/                # Dependency injection
│   └── bootstrap.py         # DI configuration
└── docs/                     # Documentation
```

## 🔧 Custom Exception Hierarchy

The application implements a comprehensive exception hierarchy:

### Base Exceptions
- `URLShortenerException`: Base exception for all application errors
- `ValidationException`: Input validation errors
- `DatabaseException`: Database operation errors
- `NotFoundException`: Resource not found errors

### Specific Exceptions
- `URLValidationException`: URL-specific validation errors
- `URLNotFoundException`: URL mapping not found
- `URLExpiredException`: URL has expired
- `DuplicateURLException`: URL already exists
- `RateLimitException`: Rate limit exceeded
- `AuthenticationException`: Authentication failures
- `AuthorizationException`: Authorization failures
- `ConnectionException`: Database connection errors
- `ConfigurationException`: Configuration errors
- `ServiceUnavailableException`: Service temporarily unavailable

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- PostgreSQL/MySQL database
- Redis (optional, for caching)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd URL-Shortner
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   # Set up database configuration in your secrets manager
   # Required keys: engine, username, password, host, port, dbname
   ```

4. **Run the application**
   ```bash
   python -m web_api.main
   ```

## 📚 API Documentation

### Core Endpoints

#### Create Short URL
```http
POST /shorten/
Content-Type: application/json

{
  "url": "https://example.com/very/long/url",
  "custom_alias": "myalias",  // optional
  "expires_at": "2024-12-31T23:59:59Z",  // optional
  "user_id": "user123"  // optional
}
```

#### Bulk Create URLs
```http
POST /bulk-shorten/
Content-Type: application/json

{
  "urls": [
    "https://example1.com",
    "https://example2.com"
  ],
  "expires_at": "2024-12-31T23:59:59Z",  // optional
  "user_id": "user123"  // optional
}
```

#### Redirect to Original URL
```http
GET /{short_url}
```

#### Get User URLs
```http
GET /urls/?page=1&page_size=20
Authorization: Bearer <token>
```

#### Delete URL
```http
DELETE /urls/{short_url}
Authorization: Bearer <token>
```

#### Update URL Expiration
```http
PUT /urls/{short_url}/expiration?expires_at=2024-12-31T23:59:59Z
Authorization: Bearer <token>
```

### Analytics Endpoints

#### URL Analytics
```http
GET /analytics/url/{short_url}?start_date=2024-01-01T00:00:00Z&end_date=2024-12-31T23:59:59Z
```

#### User Analytics
```http
GET /analytics/user?start_date=2024-01-01T00:00:00Z&end_date=2024-12-31T23:59:59Z
Authorization: Bearer <token>
```

#### Global Analytics (Admin)
```http
GET /analytics/global?start_date=2024-01-01T00:00:00Z&end_date=2024-12-31T23:59:59Z
Authorization: Bearer <token>
```

### System Endpoints

#### Health Check
```http
GET /health
```

#### Rate Limit Status
```http
GET /rate-limits/status?endpoint=/shorten/&identifier=192.168.1.1
```

#### Rate Limit Configurations
```http
GET /rate-limits/config
```

## 🔒 Rate Limiting

The application implements configurable rate limiting:

### Default Limits
- `/shorten/`: 10 requests per minute per IP
- `/bulk-shorten/`: 5 requests per 5 minutes per IP
- `/analytics/`: 20 requests per minute per user
- `/auth/login`: 3 requests per 5 minutes per IP
- `/auth/register`: 2 requests per 10 minutes per IP

### Rate Limit Headers
- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Window reset time
- `Retry-After`: Seconds to wait when limit exceeded

## 📊 Analytics Features

### Click Tracking
- **Total Clicks**: Overall click count
- **Unique Clicks**: Unique visitor count
- **Time Analytics**: Clicks by day, hour, week
- **Referrer Analytics**: Traffic source analysis
- **User Agent Analytics**: Browser and device information

### Analytics Data
- **IP Address Tracking**: Visitor IP addresses
- **User Agent Tracking**: Browser and device info
- **Referrer Tracking**: Traffic source URLs
- **Timestamp Tracking**: Precise click timing
- **User ID Tracking**: Authenticated user tracking

## 🛡️ Security Features

### URL Validation
- **Format Validation**: Proper URL format checking
- **Scheme Validation**: Only HTTP/HTTPS allowed
- **Domain Validation**: Valid domain name checking
- **Blocked Domains**: Protection against malicious domains
- **Length Validation**: URL length limits
- **Availability Check**: URL accessibility verification

### Input Validation
- **Pydantic Models**: Automatic request validation
- **Custom Validators**: Domain-specific validation rules
- **Error Messages**: Clear, actionable error messages
- **Field Validation**: Individual field validation

## 🔧 Configuration

### Database Configuration
```python
# Required in secrets manager
{
  "engine": "postgresql",
  "username": "db_user",
  "password": "db_password",
  "host": "localhost",
  "port": 5432,
  "dbname": "url_shortener"
}
```

### Rate Limiting Configuration
```python
# Configurable per endpoint
{
  "requests_per_window": 10,
  "window_seconds": 60,
  "rate_limit_type": "ip_based"
}
```

## 🧪 Error Handling

### Exception Response Format
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid URL format",
  "details": {
    "field": "url",
    "url": "invalid-url"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### HTTP Status Codes
- `400`: Validation errors
- `401`: Authentication required
- `403`: Authorization denied
- `404`: Resource not found
- `409`: Conflict (duplicate URL)
- `410`: Gone (expired URL)
- `429`: Rate limit exceeded
- `500`: Internal server error
- `503`: Service unavailable

## 📈 Monitoring & Health Checks

### Health Check Response
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "2.0.0",
  "services": {
    "database": {
      "status": "healthy",
      "connection_pool_size": 10,
      "connection_pool_checked_in": 8,
      "connection_pool_checked_out": 2
    },
    "rate_limiter": {
      "status": "healthy",
      "configurations": 6
    },
    "analytics": {
      "status": "healthy",
      "service": "analytics_service"
    }
  }
}
```

## 🚀 Deployment

### Production Considerations
- **Database**: Use production-grade database (PostgreSQL/MySQL)
- **Caching**: Implement Redis for caching
- **Load Balancing**: Use multiple application instances
- **Monitoring**: Implement application monitoring
- **Logging**: Configure structured logging
- **Security**: Implement proper authentication/authorization

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# Security
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# Rate Limiting
REDIS_URL=redis://localhost:6379

# Logging
LOG_LEVEL=INFO
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the health check endpoint at `/health` 