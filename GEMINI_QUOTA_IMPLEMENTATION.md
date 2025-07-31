# Gemini API Quota Tracking Implementation

## Overview

This implementation provides comprehensive quota tracking and management for the Gemini AI API to prevent rate limit violations and ensure optimal API usage across multiple API keys.

## Features Implemented

### 1. Quota Tracking System (`ai_service/quota_tracker.py`)

**Key Features:**
- ✅ Real-time tracking of minute, daily, and token usage
- ✅ Intelligent quota checking before API calls
- ✅ Automatic API key rotation when limits are reached
- ✅ Redis-based caching for distributed quota tracking
- ✅ Token estimation for request planning
- ✅ Comprehensive usage analytics

**Quota Limits Monitored:**
- **Minute Requests**: 15 requests per minute (Free tier)
- **Daily Requests**: 1,500 requests per day (Free tier)
- **Token Limit**: 1,000,000 tokens per minute
- **Request Size**: 32,000 tokens per request (max)

### 2. Enhanced AI Service Integration

**Updated `GeminiAIService` class:**
- ✅ Integrated quota checking in `_make_api_call()` method
- ✅ Automatic API key rotation on quota exceeded
- ✅ Exponential backoff for failed requests
- ✅ Token usage recording for accurate tracking
- ✅ Intelligent wait times based on quota status

### 3. API Endpoints

**New endpoint: `/api/ai/quota-status/`**

**GET Request - Check Quota Status:**
```json
{
  "success": true,
  "quota_status": {
    "healthy": true,
    "warnings": [],
    "errors": [],
    "usage": {
      "minute_requests": 4,
      "minute_limit": 15,
      "minute_remaining": 11,
      "daily_requests": 4,
      "daily_limit": 1500,
      "daily_remaining": 1496,
      "minute_tokens": 2000,
      "token_minute_limit": 1000000,
      "token_minute_remaining": 998000,
      "usage_percentage": {
        "minute": 26.7,
        "daily": 0.3,
        "tokens": 0.2
      }
    }
  },
  "timestamp": "2024-01-31T10:30:00Z"
}
```

**POST Request - Reset Quota (Admin only):**
```json
{
  "quota_type": "minute|daily|tokens|all"
}
```

### 4. Configuration

**Environment Variables (.env):**
```env
# Primary API Key
GEMINI_API_KEY=your-primary-gemini-api-key-here

# Backup API Key
GEMINI_API_KEY_BACKUP=your-backup-gemini-api-key-here

# Multiple API Keys (comma-separated)
GEMINI_API_KEYS=your-primary-key,your-backup-key

# Optional: Custom Quota Limits
GEMINI_MINUTE_LIMIT=15
GEMINI_DAILY_LIMIT=1500
GEMINI_TOKEN_MINUTE_LIMIT=1000000
```

**Django Settings (nia_sales_assistant/settings.py):**
```python
# Gemini AI Configuration
GEMINI_API_KEY = config('GEMINI_API_KEY')
GEMINI_API_KEY_BACKUP = config('GEMINI_API_KEY_BACKUP', default='')
GEMINI_API_KEYS = config('GEMINI_API_KEYS', default='').split(',') if config('GEMINI_API_KEYS', default='') else [GEMINI_API_KEY]

# Gemini API Quota Limits
GEMINI_MINUTE_LIMIT = config('GEMINI_MINUTE_LIMIT', default=15, cast=int)
GEMINI_DAILY_LIMIT = config('GEMINI_DAILY_LIMIT', default=1500, cast=int)
GEMINI_TOKEN_MINUTE_LIMIT = config('GEMINI_TOKEN_MINUTE_LIMIT', default=1000000, cast=int)
```

## Usage Examples

### 1. Check Quota Before Making Request

```python
from ai_service.quota_tracker import quota_tracker

# Check if we can make a request
quota_check = quota_tracker.can_make_request(estimated_tokens=1000)

if quota_check['can_request']:
    # Safe to make API call
    response = ai_service.extract_lead_info(conversation_text)
else:
    # Handle quota exceeded
    print(f"Quota exceeded: {quota_check['reason']}")
    wait_time = quota_check.get('wait_seconds', 60)
    print(f"Wait {wait_time} seconds before retry")
```

### 2. Get Current Usage Statistics

```python
from ai_service.quota_tracker import quota_tracker

usage = quota_tracker.get_current_usage()
print(f"Minute requests: {usage['minute_requests']}/{usage['minute_limit']}")
print(f"Daily requests: {usage['daily_requests']}/{usage['daily_limit']}")
print(f"Usage percentage: {usage['usage_percentage']['daily']:.1f}%")
```

### 3. Monitor Quota Health

```python
from ai_service.quota_tracker import quota_tracker

status = quota_tracker.get_quota_status()
if not status['healthy']:
    print("⚠️ Quota issues detected:")
    for error in status['errors']:
        print(f"  - {error}")
```

## API Key Rotation Strategy

The system implements intelligent API key rotation:

1. **Primary Key Usage**: Starts with the first API key
2. **Quota Detection**: Monitors for quota exceeded errors
3. **Automatic Rotation**: Switches to next available key
4. **Fallback Handling**: Waits for quota reset if all keys exhausted
5. **Seamless Operation**: No interruption to application functionality

## Monitoring and Alerts

### Health Status Indicators

- **🟢 Healthy**: < 80% quota usage
- **🟡 Warning**: 80-95% quota usage  
- **🔴 Critical**: > 95% quota usage

### Alert Conditions

- High minute request usage (>80%)
- High daily request usage (>80%)
- High token usage (>80%)
- All API keys quota exceeded
- Consecutive API failures

## Testing Results

### ✅ Quota Tracking Test Results:
- Minute requests: Properly tracked (4/15 after test)
- Daily requests: Accurately counted (4/1500 after test)
- Token usage: Estimated and recorded
- API key rotation: Successfully switched keys on quota exceeded

### ✅ API Endpoint Test Results:
- GET `/api/ai/quota-status/`: ✅ Returns detailed quota information
- POST `/api/ai/quota-status/`: ✅ Admin reset functionality works
- Authentication: ✅ Properly blocks unauthorized access

### ✅ Integration Test Results:
- AI service integration: ✅ Seamless quota checking
- Automatic key rotation: ✅ Switches keys on quota exceeded
- Error handling: ✅ Graceful degradation on quota limits
- Performance: ✅ Minimal overhead on API calls

## Benefits

1. **Prevents API Quota Violations**: Proactive checking prevents 429 errors
2. **Maximizes API Usage**: Intelligent rotation across multiple keys
3. **Real-time Monitoring**: Live quota status and usage analytics
4. **Automatic Recovery**: Self-healing on quota exceeded scenarios
5. **Cost Optimization**: Efficient usage of free tier quotas
6. **Production Ready**: Robust error handling and fallback mechanisms

## Recommendations

1. **Monitor Daily Usage**: Set up alerts at 80% daily quota usage
2. **API Key Management**: Rotate API keys regularly for security
3. **Scaling Strategy**: Add more API keys as usage grows
4. **Caching Strategy**: Implement response caching to reduce API calls
5. **Usage Analytics**: Track patterns to optimize request timing

## Next Steps

1. **Dashboard Integration**: Add quota metrics to admin dashboard
2. **Automated Alerts**: Email/Slack notifications on quota issues
3. **Usage Prediction**: ML-based quota usage forecasting
4. **Cost Tracking**: Monitor API costs across multiple keys
5. **Performance Optimization**: Batch requests where possible

---

**Implementation Status**: ✅ **COMPLETE AND TESTED**

The Gemini API quota tracking system is fully implemented, tested, and ready for production use. It provides comprehensive quota management with automatic failover and detailed monitoring capabilities.