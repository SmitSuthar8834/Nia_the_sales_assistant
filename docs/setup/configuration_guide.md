# Configuration Guide

This document provides a comprehensive guide to configuring the NIA Sales Assistant application.

## Configuration Files Overview

### Core Configuration Files

| File | Purpose | Environment |
|------|---------|-------------|
| `nia_sales_assistant/settings.py` | Django application settings | All |
| `.env` | Environment variables (local) | Development |
| `.env.example` | Environment variable template | All |
| `docker-compose.yml` | Docker services configuration | Development/Production |
| `pyproject.toml` | Python project and tool configuration | Development |

### Documentation Files

| File | Purpose |
|------|---------|
| `docs/setup/environment_variables.md` | Environment variables reference |
| `docs/setup/docker_configuration.md` | Docker setup and usage guide |
| `docs/setup/configuration_guide.md` | This comprehensive guide |

## Configuration Sections

### 1. Django Core Settings

**Location**: `nia_sales_assistant/settings.py`

Key configurations:
- **SECRET_KEY**: Cryptographic signing key (required)
- **DEBUG**: Debug mode toggle (default: True for development)
- **ALLOWED_HOSTS**: Permitted host/domain names
- **INSTALLED_APPS**: Django applications and third-party packages
- **MIDDLEWARE**: Request/response processing pipeline

### 2. Database Configuration

**Auto-detection**: The application automatically chooses database backend:
- **SQLite**: Used when `DB_NAME` environment variable is not set (development)
- **PostgreSQL**: Used when `DB_NAME` is set (production)

**PostgreSQL Settings**:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='password'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}
```

### 3. AI Service Configuration

**Gemini API Settings**:
- Primary and backup API keys for redundancy
- Quota limits to prevent API overuse
- Multiple key support for load balancing

**Configuration Variables**:
- `GEMINI_API_KEY`: Primary API key (required)
- `GEMINI_API_KEY_BACKUP`: Backup API key (optional)
- `GEMINI_MINUTE_LIMIT`: Requests per minute (default: 15)
- `GEMINI_DAILY_LIMIT`: Requests per day (default: 1500)

### 4. Background Tasks (Celery)

**Redis Configuration**:
- Broker and result backend using Redis
- JSON serialization for task data
- Timezone-aware task scheduling

### 5. Real-time Features (Django Channels)

**WebSocket Support**:
- Redis channel layer for WebSocket connections
- ASGI application configuration
- Real-time voice and chat features

### 6. External Integrations

**Google Meet Integration**:
- OAuth2 configuration for calendar access
- Meeting creation and management
- Required scopes for calendar operations

**Microsoft Teams Integration**:
- OAuth2 configuration for Outlook/Teams
- Calendar synchronization
- Meeting scheduling capabilities

## Environment-Specific Configuration

### Development Environment

**Characteristics**:
- SQLite database (no setup required)
- Debug mode enabled
- Local Redis instance
- Relaxed security settings

**Setup**:
```bash
# Copy environment template
cp .env.example .env

# Edit required variables
# - Set GEMINI_API_KEY
# - Configure Redis URL if needed
```

### Production Environment

**Characteristics**:
- PostgreSQL database
- Debug mode disabled
- Secure secret key
- Proper allowed hosts
- Environment-specific credentials

**Setup**:
```bash
# Set required environment variables
export SECRET_KEY="your-secure-secret-key"
export DEBUG=False
export ALLOWED_HOSTS="yourdomain.com,www.yourdomain.com"
export DB_NAME="nia_sales_assistant"
export DB_USER="your_db_user"
export DB_PASSWORD="secure_password"
export GEMINI_API_KEY="your_api_key"
```

## Configuration Validation

### Startup Checks

The application performs validation on startup:

1. **Required Environment Variables**: Checks for essential variables
2. **Database Connectivity**: Validates database connection
3. **Redis Connectivity**: Verifies Redis connection for Celery/Channels
4. **API Key Validation**: Basic validation of AI service credentials

### Manual Validation

```bash
# Django system check
python manage.py check

# Database migration status
python manage.py showmigrations

# Test Redis connection
python manage.py shell -c "from django.core.cache import cache; print(cache.get('test', 'Redis OK'))"
```

## Security Best Practices

### Environment Variables

1. **Never commit `.env` files** to version control
2. **Use strong secret keys** in production
3. **Rotate API keys** regularly
4. **Use environment-specific credentials**

### Database Security

1. **Use strong passwords** for database users
2. **Limit database user permissions** to required operations only
3. **Enable SSL/TLS** for database connections in production
4. **Regular backups** with encryption

### API Security

1. **Secure API key storage** using environment variables
2. **Monitor API usage** to detect unusual patterns
3. **Implement rate limiting** to prevent abuse
4. **Use HTTPS** for all external API calls

## Performance Optimization

### Database Optimization

1. **Connection Pooling**: Configure PostgreSQL connection pooling
2. **Query Optimization**: Use Django ORM efficiently
3. **Database Indexing**: Add indexes for frequently queried fields
4. **Migration Management**: Keep migrations clean and efficient

### Redis Optimization

1. **Memory Management**: Configure appropriate memory limits
2. **Persistence**: Enable AOF for data durability
3. **Connection Limits**: Set appropriate connection limits
4. **Monitoring**: Monitor Redis performance metrics

### Application Optimization

1. **Static Files**: Use CDN for static file serving in production
2. **Caching**: Implement appropriate caching strategies
3. **Background Tasks**: Use Celery for long-running operations
4. **Monitoring**: Implement application performance monitoring

## Troubleshooting

### Common Configuration Issues

1. **Missing Environment Variables**:
   - Check `.env` file exists and is readable
   - Verify all required variables are set
   - Check for typos in variable names

2. **Database Connection Issues**:
   - Verify database server is running
   - Check connection credentials
   - Ensure database exists and is accessible

3. **Redis Connection Issues**:
   - Verify Redis server is running
   - Check Redis URL format
   - Test connection manually

4. **API Integration Issues**:
   - Verify API keys are valid and active
   - Check API quota limits
   - Verify network connectivity to external APIs

### Debug Mode

Enable debug mode for troubleshooting:

```bash
# Temporarily enable debug mode
export DEBUG=True

# Run with verbose output
python manage.py runserver --verbosity=2
```

### Logging Configuration

Add logging configuration to `settings.py` for better debugging:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'nia_sales_assistant.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## Configuration Maintenance

### Regular Tasks

1. **Update Dependencies**: Keep packages up to date
2. **Rotate Secrets**: Regularly rotate API keys and passwords
3. **Review Settings**: Periodically review configuration for optimization
4. **Monitor Usage**: Track API usage and performance metrics

### Version Control

1. **Track Configuration Changes**: Document configuration changes in commits
2. **Environment Parity**: Keep development and production configurations in sync
3. **Backup Configurations**: Maintain backups of working configurations
4. **Documentation Updates**: Keep configuration documentation current

This guide should be updated whenever configuration changes are made to ensure it remains accurate and helpful for developers and system administrators.