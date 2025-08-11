# Environment Variables Documentation

This document describes all environment variables used in the NIA Sales Assistant application.

## Required Environment Variables

### Django Core Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | Django secret key for cryptographic signing | None | Yes |
| `DEBUG` | Enable/disable debug mode | `True` | No |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `localhost,127.0.0.1,testserver` | No |

### AI Service Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GEMINI_API_KEY` | Primary Gemini API key | None | Yes |
| `GEMINI_API_KEY_BACKUP` | Backup Gemini API key | Empty | No |
| `GEMINI_API_KEYS` | Comma-separated list of API keys | Uses `GEMINI_API_KEY` | No |
| `GEMINI_MINUTE_LIMIT` | API calls per minute limit | `15` | No |
| `GEMINI_DAILY_LIMIT` | API calls per day limit | `1500` | No |
| `GEMINI_TOKEN_MINUTE_LIMIT` | Token limit per minute | `1000000` | No |

### Database Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DB_NAME` | PostgreSQL database name | `nia_sales_assistant` | No* |
| `DB_USER` | PostgreSQL username | `postgres` | No* |
| `DB_PASSWORD` | PostgreSQL password | `password` | No* |
| `DB_HOST` | PostgreSQL host | `localhost` | No* |
| `DB_PORT` | PostgreSQL port | `5432` | No* |

*Note: Database variables are only required when using PostgreSQL. The application defaults to SQLite for development.

### Redis Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `REDIS_URL` | Redis connection URL for Celery and Channels | `redis://localhost:6379/0` | Yes |

## Optional Environment Variables

### Google Cloud Integration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GOOGLE_CLOUD_PROJECT` | Google Cloud project ID | Empty | No |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account key file | Empty | No |

### Google Meet Integration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GOOGLE_MEET_CLIENT_ID` | Google OAuth2 client ID | Empty | No |
| `GOOGLE_MEET_CLIENT_SECRET` | Google OAuth2 client secret | Empty | No |
| `GOOGLE_MEET_REDIRECT_URI` | OAuth2 redirect URI | `http://localhost:8000/meeting/oauth/callback/` | No |

### Microsoft Teams Integration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MICROSOFT_CLIENT_ID` | Microsoft OAuth2 client ID | Empty | No |
| `MICROSOFT_CLIENT_SECRET` | Microsoft OAuth2 client secret | Empty | No |
| `MICROSOFT_TENANT_ID` | Microsoft tenant ID | `common` | No |
| `MICROSOFT_REDIRECT_URI` | OAuth2 redirect URI | `http://localhost:8000/meeting/oauth/outlook/callback/` | No |

## Environment Setup

### Development Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Update the required variables in `.env`:
   - Set your `SECRET_KEY` (generate a new one for production)
   - Add your `GEMINI_API_KEY`
   - Configure Redis URL if different from default

3. Optional: Configure database settings if using PostgreSQL instead of SQLite

### Production Setup

1. Generate a secure `SECRET_KEY`:
   ```python
   from django.core.management.utils import get_random_secret_key
   print(get_random_secret_key())
   ```

2. Set `DEBUG=False`

3. Configure `ALLOWED_HOSTS` with your domain names

4. Use environment-specific values for database and Redis connections

5. Set up proper OAuth2 credentials for calendar integrations if needed

## Security Considerations

- Never commit `.env` files to version control
- Use strong, unique secret keys in production
- Rotate API keys regularly
- Use environment-specific Redis and database credentials
- Enable proper authentication for external services

## Validation

The application will validate required environment variables on startup. Missing required variables will cause the application to fail to start with appropriate error messages.

To validate your environment configuration:

```bash
python manage.py check
```

## Troubleshooting

### Common Issues

1. **Missing GEMINI_API_KEY**: The AI service requires a valid Gemini API key
2. **Redis Connection Failed**: Ensure Redis is running and accessible at the configured URL
3. **Database Connection Issues**: Verify database credentials and connectivity
4. **OAuth2 Errors**: Check client IDs, secrets, and redirect URIs for calendar integrations

### Environment Variable Precedence

1. Environment variables set in the system
2. Variables defined in `.env` file
3. Default values defined in `settings.py`