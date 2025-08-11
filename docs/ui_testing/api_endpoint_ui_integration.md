# API Endpoint UI Integration Testing Documentation

## Overview

This document provides comprehensive testing specifications for how each API endpoint integrates with UI components in the NIA Sales Assistant application. It covers expected responses, error handling, loading states, and real-time features.

## Base API Configuration

### API Service Configuration
- **Base URL**: `/api/ai/`
- **Authentication**: Django session-based authentication
- **CSRF Protection**: Required for all POST/PUT/PATCH/DELETE requests
- **Content Type**: `application/json`
- **Error Format**: JSON with `error` field

### Global Error Handling
- **Network Errors**: Show "Connection error" alert, provide retry option
- **Authentication Errors**: Redirect to login page
- **Server Errors (5xx)**: Show "Server error occurred" alert
- **Validation Errors (4xx)**: Show specific field errors

## Lead Management API Integration

### GET /api/ai/leads/ - Load Leads List

#### UI Integration Points
- **Trigger**: Page load, refresh button click, filter changes
- **Loading State**: Shows `#leads-loading` spinner
- **Success Response**:
  ```json
  {
    "results": [
      {
        "id": "uuid",
        "company_name": "string",
        "contact_info": {
          "name": "string",
          "email": "string",
          "phone": "string"
        },
        "status": "new|contacted|qualified|converted|lost",
        "industry": "string",
        "created_at": "ISO datetime",
        "lead_score": "number (0-100)",
        "source": "string"
      }
    ],
    "count": "number",
    "next": "url|null",
    "previous": "url|null"
  }
  ```

#### UI Response Handling
- **Success**: 
  - Hides loading spinner
  - Populates `#leads-list` with lead cards
  - Updates filter counts
  - Shows "No leads found" if empty results
- **Error**: 
  - Hides loading spinner
  - Shows error alert: "Error loading leads: {error message}"
  - Keeps previous data if available

#### Query Parameters
- `search`: Text search across company, contact, email
- `status`: Filter by lead status
- `industry`: Filter by industry
- `ordering`: Sort field (created_at, company_name, lead_score)
- `limit`: Pagination limit
- `offset`: Pagination offset

### POST /api/ai/leads/ - Create New Lead

#### UI Integration Points
- **Trigger**: Create lead form submission
- **Loading State**: Shows `#create-loading` with "Creating lead..." text
- **Request Body**:
  ```json
  {
    "company_name": "string",
    "contact_info": {
      "name": "string",
      "email": "string",
      "phone": "string"
    },
    "industry": "string",
    "notes": "string",
    "conversation_text": "string",
    "source": "string",
    "urgency": "high|medium|low",
    "ai_analysis": "object",
    "extracted_info": "object"
  }
  ```

#### UI Response Handling
- **Success (201)**:
  - Hides loading spinner
  - Shows success alert: "Lead created successfully!"
  - Adds new lead to leads list
  - Resets form after 3 seconds
  - Returns to leads view
- **Validation Error (400)**:
  - Hides loading spinner
  - Shows field-specific errors
  - Highlights invalid form fields
- **Server Error (500)**:
  - Hides loading spinner
  - Shows error alert: "Error creating lead: {error message}"

### GET /api/ai/leads/{id}/ - Get Lead Details

#### UI Integration Points
- **Trigger**: Lead card click, direct navigation
- **Loading State**: Shows loading in detail view sections
- **Success Response**: Full lead object with additional fields:
  ```json
  {
    "id": "uuid",
    "company_name": "string",
    "contact_info": "object",
    "status": "string",
    "industry": "string",
    "notes": "string",
    "conversation_history": "array",
    "ai_insights": "object",
    "activity_timeline": "array",
    "lead_score": "number",
    "scoring_factors": "object",
    "next_actions": "array",
    "created_at": "datetime",
    "updated_at": "datetime"
  }
  ```

#### UI Response Handling
- **Success**: 
  - Populates all detail view sections
  - Updates overview cards
  - Loads conversation history
  - Shows AI insights tab content
- **Not Found (404)**:
  - Shows "Lead not found" alert
  - Returns to leads list
- **Error**: 
  - Shows error alert
  - Disables detail view actions

## AI Analysis API Integration

### POST /api/ai/analyze/ - Analyze Conversation

#### UI Integration Points
- **Trigger**: "Analyze & Create Lead" button click
- **Loading State**: Shows analysis loading with "Analyzing conversation..." text
- **Request Body**:
  ```json
  {
    "conversation_text": "string",
    "context": {
      "source": "string",
      "urgency": "string"
    },
    "extract_entities": true,
    "generate_recommendations": true
  }
  ```

#### UI Response Handling
- **Success (200)**:
  ```json
  {
    "summary": "string",
    "recommendations": "string",
    "entities": {
      "company_name": "string",
      "contact_name": "string",
      "contact_email": "string",
      "contact_phone": "string",
      "industry": "string",
      "pain_points": "array",
      "requirements": "array",
      "budget_info": "string",
      "timeline": "string"
    },
    "sentiment": "positive|neutral|negative",
    "urgency_level": "high|medium|low",
    "quality_score": "number (0-100)"
  }
  ```
- **UI Updates**:
  - Shows `#analysis-results` section
  - Populates extracted information
  - Displays AI recommendations
  - Shows confirmation buttons

### POST /api/ai/extract-lead/ - Extract Lead Information

#### UI Integration Points
- **Trigger**: Called automatically during lead creation
- **Loading State**: Part of create lead loading process
- **Request Body**:
  ```json
  {
    "conversation_text": "string",
    "context": {
      "source": "string",
      "urgency": "string"
    }
  }
  ```

#### UI Response Handling
- **Success**: Extracted data used to pre-populate lead creation form
- **Error**: Shows warning, allows manual entry

### POST /api/ai/comprehensive-recommendations/ - Get AI Recommendations

#### UI Integration Points
- **Trigger**: "Refresh AI" button in lead detail view
- **Loading State**: Shows `#insights-loading` in AI insights tab
- **Request Body**:
  ```json
  {
    "lead_data": "object",
    "include_quality_score": true,
    "include_sales_strategy": true,
    "include_industry_insights": true,
    "include_next_steps": true
  }
  ```

#### UI Response Handling
- **Success**: 
  - Populates `#insights-content` with recommendations
  - Updates lead score display
  - Shows next action suggestions
- **Error**: Shows "Failed to generate insights" message

## Analytics API Integration

### GET /api/ai/analytics/ - Get Lead Analytics

#### UI Integration Points
- **Trigger**: Analytics view navigation
- **Loading State**: Shows loading in analytics cards
- **Success Response**:
  ```json
  {
    "total_leads": "number",
    "high_quality_leads": "number",
    "average_lead_score": "number",
    "conversion_rate": "number",
    "leads_by_status": "object",
    "leads_by_source": "object",
    "monthly_trends": "array"
  }
  ```

#### UI Response Handling
- **Success**:
  - Updates `#total-leads` display
  - Updates `#high-quality-leads` display  
  - Updates `#avg-lead-score` display
  - Renders charts if available
- **Error**: Shows "Analytics unavailable" message

## Voice Service API Integration

### POST /api/voice/chat/create/ - Create Chat Session

#### UI Integration Points
- **Trigger**: "New Chat Session" button click
- **Loading State**: Shows "Creating chat session..." alert
- **Request Body**:
  ```json
  {
    "priority": "high|medium|low",
    "initial_message": "string"
  }
  ```

#### UI Response Handling
- **Success (201)**:
  ```json
  {
    "session_id": "uuid",
    "status": "active",
    "created_at": "datetime",
    "voice_available": "boolean"
  }
  ```
- **UI Updates**:
  - Establishes WebSocket connection
  - Updates connection status to "Connected"
  - Enables chat input
  - Shows success alert

### WebSocket /ws/chat/{session_id}/ - Real-time Chat

#### UI Integration Points
- **Connection**: Automatic after session creation
- **Connection Status**: Updates `#connection-status` indicator

#### Message Types and UI Handling

##### connection_established
```json
{
  "type": "connection_established",
  "voice_available": "boolean",
  "session_info": "object"
}
```
- **UI Response**: Updates availability toggle, shows connected status

##### chat_message
```json
{
  "type": "chat_message",
  "message": {
    "id": "uuid",
    "sender": "user|nia",
    "content": "string",
    "timestamp": "datetime",
    "status": "sent|delivered|read",
    "attachments": "array"
  }
}
```
- **UI Response**: Adds message to `#chat-messages`, scrolls to bottom

##### typing_indicator
```json
{
  "type": "typing_indicator",
  "typing": "boolean",
  "username": "string"
}
```
- **UI Response**: Shows/hides `#typing-indicator`

##### voice_transition_ready
```json
{
  "type": "voice_transition_ready",
  "webrtc_url": "string",
  "message": "string"
}
```
- **UI Response**: Shows `#voice-transition-modal` with join button

##### error
```json
{
  "type": "error",
  "message": "string",
  "code": "string"
}
```
- **UI Response**: Shows error alert, may disconnect if critical

## Meeting Service API Integration

### GET /api/meeting/api/meetings/ - Get Meetings List

#### UI Integration Points
- **Trigger**: Meeting dashboard load
- **Loading State**: Shows meeting list loading spinner
- **Success Response**:
  ```json
  {
    "results": [
      {
        "id": "uuid",
        "title": "string",
        "scheduled_time": "datetime",
        "status": "scheduled|in_progress|completed|cancelled",
        "participants": "array",
        "meeting_type": "string",
        "platform": "google_meet|teams|zoom",
        "meeting_url": "string"
      }
    ]
  }
  ```

#### UI Response Handling
- **Success**: Populates meeting list/calendar view
- **Error**: Shows "Failed to load meetings" alert

### POST /api/meeting/api/meetings/ - Create Meeting

#### UI Integration Points
- **Trigger**: Meeting creation form submission
- **Loading State**: Shows "Creating meeting..." spinner
- **Request Body**:
  ```json
  {
    "title": "string",
    "scheduled_time": "datetime",
    "duration_minutes": "number",
    "participants": "array",
    "meeting_type": "string",
    "platform": "string",
    "agenda": "string"
  }
  ```

#### UI Response Handling
- **Success (201)**: 
  - Shows success alert
  - Adds meeting to calendar
  - Resets form
- **Validation Error (400)**: Shows field errors
- **Conflict Error (409)**: Shows scheduling conflict warning

## Real-time Features Integration

### Server-Sent Events (SSE) - /api/ai/leads/updates/

#### UI Integration Points
- **Connection**: Established on leads view load
- **Event Types**:
  - `lead_created`: Adds new lead to list
  - `lead_updated`: Updates existing lead card
  - `lead_deleted`: Removes lead from list
  - `lead_status_changed`: Updates status badge

#### UI Response Handling
```javascript
eventSource.onmessage = function(event) {
  const data = JSON.parse(event.data);
  switch(data.type) {
    case 'lead_created':
      // Add new lead card to top of list
      break;
    case 'lead_updated':
      // Update existing lead card
      break;
    case 'lead_deleted':
      // Remove lead card with animation
      break;
  }
};
```

### WebSocket - /ws/leads/ - Lead Updates

#### UI Integration Points
- **Connection**: Alternative to SSE for real-time updates
- **Reconnection**: Automatic retry every 5 seconds on disconnect
- **Message Format**: Same as SSE events

## Error State Testing Scenarios

### Network Connectivity Issues
1. **Offline State**:
   - Show offline indicator
   - Queue messages for later sending
   - Disable real-time features
   - Show cached data when available

2. **Slow Connection**:
   - Show loading states for longer periods
   - Implement request timeouts (30 seconds)
   - Show "Taking longer than expected" messages

3. **Intermittent Connection**:
   - Retry failed requests automatically (3 attempts)
   - Show retry buttons for user-initiated retries
   - Maintain WebSocket reconnection logic

### API Error Responses

#### 400 Bad Request - Validation Errors
```json
{
  "error": "Validation failed",
  "details": {
    "company_name": ["This field is required"],
    "contact_info.email": ["Enter a valid email address"]
  }
}
```
- **UI Response**: Highlight invalid fields, show specific error messages

#### 401 Unauthorized
```json
{
  "error": "Authentication required"
}
```
- **UI Response**: Redirect to login page, show "Please log in" message

#### 403 Forbidden
```json
{
  "error": "Permission denied"
}
```
- **UI Response**: Show "Access denied" alert, disable restricted actions

#### 404 Not Found
```json
{
  "error": "Lead not found"
}
```
- **UI Response**: Show "Resource not found" alert, return to list view

#### 429 Too Many Requests
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60
}
```
- **UI Response**: Show rate limit message, disable actions temporarily

#### 500 Internal Server Error
```json
{
  "error": "Internal server error"
}
```
- **UI Response**: Show "Server error" alert, provide retry option

## Loading State Specifications

### Global Loading States
- **Minimum Display Time**: 300ms to prevent flashing
- **Maximum Display Time**: 30 seconds before timeout
- **Loading Animation**: Consistent spinner across all components
- **Loading Text**: Descriptive and action-specific

### Component-Specific Loading States

#### Leads List Loading
- **Element**: `#leads-loading`
- **Text**: "Loading leads..."
- **Behavior**: Blocks interaction with leads list

#### Create Lead Loading
- **Element**: `#create-loading`
- **Text**: "Analyzing conversation and creating lead..."
- **Behavior**: Disables form submission, shows progress

#### Chat Loading
- **Element**: Typing indicator
- **Text**: "NIA is typing..."
- **Behavior**: Shows during AI response generation

#### Analysis Loading
- **Element**: `#insights-loading`
- **Text**: "Generating AI insights..."
- **Behavior**: Shows in AI insights tab during refresh

## Performance Considerations

### API Response Caching
- **Lead List**: Cache for 5 minutes
- **Lead Details**: Cache for 2 minutes
- **Analytics**: Cache for 10 minutes
- **Chat History**: Cache indefinitely with invalidation

### Pagination Handling
- **Page Size**: 20 items per page for leads
- **Infinite Scroll**: Load next page when 5 items from bottom
- **Loading Indicator**: Show at bottom during pagination load

### Real-time Update Throttling
- **Update Frequency**: Maximum 1 update per second per lead
- **Batch Updates**: Group multiple updates within 500ms
- **UI Debouncing**: Debounce search input by 300ms

## Testing Checklist

### API Integration Tests
- [ ] All endpoints return expected response format
- [ ] Error responses include proper error messages
- [ ] Loading states show and hide correctly
- [ ] Real-time updates work without page refresh
- [ ] Pagination works correctly
- [ ] Search and filtering work as expected
- [ ] Form validation errors display properly
- [ ] Success messages appear after actions
- [ ] WebSocket connections establish and reconnect
- [ ] File uploads work with progress indication

### Error Handling Tests
- [ ] Network errors show appropriate messages
- [ ] Server errors are handled gracefully
- [ ] Validation errors highlight correct fields
- [ ] Rate limiting is handled properly
- [ ] Authentication errors redirect correctly
- [ ] 404 errors return to appropriate views
- [ ] Timeout errors show retry options

### Performance Tests
- [ ] API responses load within acceptable time
- [ ] Large datasets don't freeze the UI
- [ ] Real-time updates don't cause memory leaks
- [ ] Caching reduces unnecessary API calls
- [ ] Pagination loads smoothly
- [ ] Search results appear quickly

This documentation provides comprehensive testing specifications for all API endpoint integrations with the UI components in the NIA Sales Assistant application.