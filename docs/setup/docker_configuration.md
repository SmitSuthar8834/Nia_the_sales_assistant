# Docker Configuration Guide

This document explains the Docker setup for the NIA Sales Assistant application.

## Overview

The Docker configuration provides the following services:

- **PostgreSQL**: Primary database for production use
- **Redis**: Message broker for Celery and channel layer for Django Channels
- **Web Application**: Django application server (optional, commented out)
- **Celery Worker**: Background task processor (optional, commented out)

## Quick Start

### Development Setup (Database Services Only)

For development, you typically only need the database services:

```bash
# Start PostgreSQL and Redis services
docker-compose up -d postgres redis

# Run Django application locally
python manage.py runserver
```

### Full Containerized Setup

To run the entire application in containers:

1. Uncomment the `web` and `celery` services in `docker-compose.yml`
2. Create a `Dockerfile` in the project root
3. Start all services:

```bash
docker-compose up -d
```

## Service Configuration

### PostgreSQL Database

- **Image**: `postgres:15`
- **Port**: 5432 (configurable via `DB_PORT` environment variable)
- **Default Database**: `nia_sales_assistant`
- **Health Check**: Automatic readiness check
- **Data Persistence**: Named volume `postgres_data`

**Environment Variables:**
- `DB_NAME`: Database name (default: `nia_sales_assistant`)
- `DB_USER`: Database user (default: `postgres`)
- `DB_PASSWORD`: Database password (default: `password`)
- `DB_PORT`: Host port mapping (default: `5432`)

### Redis Service

- **Image**: `redis:7-alpine`
- **Port**: 6380 (mapped from container port 6379)
- **Persistence**: Enabled with AOF (Append Only File)
- **Health Check**: Redis ping command
- **Data Persistence**: Named volume `redis_data`

### Network Configuration

All services communicate through a custom bridge network (`nia_network`) for better isolation and service discovery.

## Environment Variables

The Docker configuration supports environment variables from your `.env` file:

```bash
# Copy and customize environment variables
cp .env.example .env
```

Key variables for Docker:
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`: Database configuration
- `SECRET_KEY`: Django secret key
- `DEBUG`: Debug mode setting
- `GEMINI_API_KEY`: AI service API key

## Data Persistence

### Volumes

- `postgres_data`: PostgreSQL database files
- `redis_data`: Redis persistence files

### Backup and Restore

**Database Backup:**
```bash
# Create backup
docker-compose exec postgres pg_dump -U postgres nia_sales_assistant > backup.sql

# Restore backup
docker-compose exec -T postgres psql -U postgres nia_sales_assistant < backup.sql
```

**Redis Backup:**
```bash
# Redis automatically persists data with AOF
# Backup files are stored in the redis_data volume
```

## Development Workflow

### Starting Services

```bash
# Start only database services for local development
docker-compose up -d postgres redis

# Check service status
docker-compose ps

# View logs
docker-compose logs postgres redis
```

### Stopping Services

```bash
# Stop services
docker-compose down

# Stop and remove volumes (WARNING: This deletes all data)
docker-compose down -v
```

### Database Management

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d nia_sales_assistant

# Run Django migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

## Production Considerations

### Security

1. **Change Default Passwords**: Never use default passwords in production
2. **Environment Variables**: Use secure environment variable management
3. **Network Security**: Configure proper firewall rules
4. **SSL/TLS**: Enable encryption for database connections

### Performance

1. **Resource Limits**: Set appropriate CPU and memory limits
2. **Connection Pooling**: Configure PostgreSQL connection pooling
3. **Redis Memory**: Set appropriate Redis memory limits
4. **Monitoring**: Implement health checks and monitoring

### Example Production Override

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    environment:
      POSTGRES_PASSWORD: ${SECURE_DB_PASSWORD}
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
  
  redis:
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '0.25'
```

Use with: `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d`

## Troubleshooting

### Common Issues

1. **Port Conflicts**: Change port mappings if 5432 or 6380 are in use
2. **Permission Issues**: Ensure Docker has proper permissions
3. **Memory Issues**: Increase Docker memory allocation
4. **Connection Refused**: Check if services are healthy with `docker-compose ps`

### Health Checks

Both PostgreSQL and Redis include health checks:

```bash
# Check service health
docker-compose ps

# View detailed health status
docker inspect $(docker-compose ps -q postgres) | grep Health -A 10
```

### Logs

```bash
# View all logs
docker-compose logs

# Follow logs for specific service
docker-compose logs -f postgres

# View last 100 lines
docker-compose logs --tail=100 redis
```

## Integration with Django

The Django application is configured to automatically detect and use the Docker services:

1. **Database**: Automatically uses PostgreSQL when `DB_NAME` is set
2. **Redis**: Configured for both Celery and Django Channels
3. **Environment**: Reads configuration from environment variables

This allows seamless switching between local development and containerized services.