# API Endpoint Testing - Complete UI Integration Guide

## Overview
This document provides comprehensive testing specifications for all API endpoints and their integration with the UI components of the NIA Sales Assistant application.

## Authentication API Testing

### Login Endpoint (`POST /api/auth/login/`)

#### UI Integration Points
| UI Element | API Call | Expected Response | UI Behavior | Test Status |
|------------|----------|-------------------|-------------|-------------|
| **Login Form Submit** | POST with credentials | 200 + auth token | Redirect to dashboard | ⏳ |
| **Invalid Credentials** | POST with wrong data | 401 error | Show error message | ⏳ |
| **Network Error** | POST request fails | Network timeout | Show connection error | ⏳ |
| **Remember Me** | POST with remember flag | 200 + extended token | Set longer session | ⏳ |

#### Test Scenarios
| Scenario | Request Body | Expected Response | UI Expected Behavior | Test Status |
|----------|--------------|-------------------|---------------------|-------------|
| **Valid Login** | `{"username": "user", "password": "pass"}` | `{"token": "...", "user": {...}}` | Redirect to dashboard, show welcome | ⏳ |
| **Invalid Username** | `{"username": "wrong", "password": "pass"}` | `{"error": "Invalid credentials"}` | Show error below form | ⏳ |
| **Invalid Password** | `{"username": "user", "password": "wrong"}` | `{"error": "Invalid credentials"}` | Show error below form | ⏳ |
| **Empty Fields** | `{"username": "", "password": ""}` | `{"error": "Required fields missing"}` | Show field validation errors | ⏳ |

### Logout Endpoint (`POST /api/auth/logout/`)

#### UI Integration Points
| UI Element | API Call | Expected Response | UI Behavior | Test Status |
|------------|----------|-------------------|-------------|-------------|
| **Logout Button** | POST with auth token | 200 success | Clear session, redirect to login | ⏳ |
| **Session Expired** | Auto-logout trigger | 401 unauthorized | Show session expired message | ⏳ |

## User Management API Testing

### User List Endpoint (`GET /api/users/`)

#### UI Integration Points
| UI Element | API Call | Expected Response | UI Behavior | Test Status |
|------------|----------|-------------------|-------------|-------------|
| **User List Page Load** | GET /api/users/ | Array of user objects | Populate user table | ⏳ |
| **Search Users** | GET /api/users/?search=query | Filtered user array | Update table with results | ⏳ |
| **Filter by Role** | GET /api/users/?role=admin | Filtered user array | Show only matching users | ⏳ |
| **Pagination** | GET /api/users/?page=2 | Paginated response | Load next page of users | ⏳ |

#### Test Scenarios
| Scenario | Request | Expected Response | UI Expected Behavior | Test Status |
|----------|---------|-------------------|---------------------|-------------|
| **Load All Users** | `GET /api/users/` | `{"results": [...], "count": 50}` | Show user table with 50 users | ⏳ |
| **Search by Name** | `GET /api/users/?search=john` | `{"results": [users with "john"]}` | Filter table to matching users | ⏳ |
| **Empty Results** | `GET /api/users/?search=xyz` | `{"results": [], "count": 0}` | Show "No users found" message | ⏳ |
| **Server Error** | `GET /api/users/` | `500 Internal Server Error` | Show error message, retry button | ⏳ |

### User Creation Endpoint (`POST /api/users/`)

#### UI Integration Points
| UI Element | API Call | Expected Response | UI Behavior | Test Status |
|------------|----------|-------------------|-------------|-------------|
| **Create User Form** | POST with user data | 201 + created user | Show success, redirect to user list | ⏳ |
| **Validation Errors** | POST with invalid data | 400 + error details | Show field-specific errors | ⏳ |
| **Duplicate Email** | POST with existing email | 400 + duplicate error | Show email already exists error | ⏳ |

#### Test Scenarios
| Scenario | Request Body | Expected Response | UI Expected Behavior | Test Status |
|----------|--------------|-------------------|---------------------|-------------|
| **Valid User** | `{"username": "newuser", "email": "new@test.com", ...}` | `201 {"id": 123, "username": "newuser", ...}` | Show success message, clear form | ⏳ |
| **Missing Required** | `{"username": "", "email": "test@test.com"}` | `400 {"username": ["This field is required"]}` | Highlight username field error | ⏳ |
| **Invalid Email** | `{"username": "user", "email": "invalid-email"}` | `400 {"email": ["Enter a valid email"]}` | Show email format error | ⏳ |
| **Duplicate Username** | `{"username": "existing", ...}` | `400 {"username": ["Username already exists"]}` | Show username taken error | ⏳ |

## Meeting Management API Testing

### Meeting List Endpoint (`GET /api/meetings/`)

#### UI Integration Points
| UI Element | API Call | Expected Response | UI Behavior | Test Status |
|------------|----------|-------------------|-------------|-------------|
| **Meeting Dashboard** | GET /api/meetings/ | Array of meetings | Populate meeting cards | ⏳ |
| **Filter by Date** | GET /api/meetings/?date=2024-01-01 | Filtered meetings | Show meetings for selected date | ⏳ |
| **Filter by Status** | GET /api/meetings/?status=upcoming | Status-filtered meetings | Show only upcoming meetings | ⏳ |
| **Calendar View** | GET /api/meetings/?start=date&end=date | Date range meetings | Populate calendar with meetings | ⏳ |

#### Test Scenarios
| Scenario | Request | Expected Response | UI Expected Behavior | Test Status |
|----------|---------|-------------------|---------------------|-------------|
| **Load Meetings** | `GET /api/meetings/` | `[{"id": 1, "title": "Meeting 1", ...}]` | Display meeting cards with details | ⏳ |
| **Today's Meetings** | `GET /api/meetings/?date=today` | Today's meetings array | Show today's meetings highlighted | ⏳ |
| **No Meetings** | `GET /api/meetings/?date=future` | `[]` | Show "No meetings scheduled" message | ⏳ |
| **Loading Error** | `GET /api/meetings/` | `500 Server Error` | Show error message with retry option | ⏳ |

### Meeting Creation Endpoint (`POST /api/meetings/`)

#### UI Integration Points
| UI Element | API Call | Expected Response | UI Behavior | Test Status |
|------------|----------|-------------------|-------------|-------------|
| **Create Meeting Form** | POST with meeting data | 201 + created meeting | Show success, add to meeting list | ⏳ |
| **Schedule Conflict** | POST with conflicting time | 409 + conflict details | Show scheduling conflict warning | ⏳ |
| **Invalid Participants** | POST with invalid emails | 400 + validation errors | Highlight invalid participant fields | ⏳ |

#### Test Scenarios
| Scenario | Request Body | Expected Response | UI Expected Behavior | Test Status |
|----------|--------------|-------------------|---------------------|-------------|
| **Valid Meeting** | `{"title": "Team Meeting", "start_time": "...", ...}` | `201 {"id": 456, "title": "Team Meeting", ...}` | Show success, refresh meeting list | ⏳ |
| **Missing Title** | `{"title": "", "start_time": "...", ...}` | `400 {"title": ["This field is required"]}` | Highlight title field with error | ⏳ |
| **Past Date** | `{"title": "Meeting", "start_time": "2020-01-01", ...}` | `400 {"start_time": ["Cannot schedule in past"]}` | Show date validation error | ⏳ |
| **Time Conflict** | `{"title": "Meeting", "start_time": "existing-time", ...}` | `409 {"error": "Scheduling conflict with Meeting X"}` | Show conflict dialog with options | ⏳ |

### Meeting Update Endpoint (`PUT /api/meetings/{id}/`)

#### UI Integration Points
| UI Element | API Call | Expected Response | UI Behavior | Test Status |
|------------|----------|-------------------|-------------|-------------|
| **Edit Meeting Form** | PUT with updated data | 200 + updated meeting | Show success, update meeting display | ⏳ |
| **Reschedule Meeting** | PUT with new time | 200 + updated meeting | Update calendar, notify participants | ⏳ |
| **Cancel Meeting** | PUT with cancelled status | 200 + cancelled meeting | Show cancelled status, send notifications | ⏳ |

### Meeting Deletion Endpoint (`DELETE /api/meetings/{id}/`)

#### UI Integration Points
| UI Element | API Call | Expected Response | UI Behavior | Test Status |
|------------|----------|-------------------|-------------|-------------|
| **Delete Button** | DELETE /api/meetings/123/ | 204 No Content | Remove from list, show confirmation | ⏳ |
| **Delete Confirmation** | DELETE after confirmation | 204 No Content | Remove meeting, show success message | ⏳ |
| **Delete Error** | DELETE request fails | 500 Server Error | Show error, keep meeting in list | ⏳ |

## Lead Management API Testing

### Lead List Endpoint (`GET /api/leads/`)

#### UI Integration Points
| UI Element | API Call | Expected Response | UI Behavior | Test Status |
|------------|----------|-------------------|-------------|-------------|
| **Lead Dashboard** | GET /api/leads/ | Array of leads | Populate lead cards | ⏳ |
| **Search Leads** | GET /api/leads/?search=company | Filtered leads | Show matching leads | ⏳ |
| **Filter by Status** | GET /api/leads/?status=hot | Status-filtered leads | Show leads with selected status | ⏳ |
| **Sort Leads** | GET /api/leads/?ordering=-created | Sorted leads | Display leads in specified order | ⏳ |

#### Test Scenarios
| Scenario | Request | Expected Response | UI Expected Behavior | Test Status |
|----------|---------|-------------------|---------------------|-------------|
| **Load All Leads** | `GET /api/leads/` | `[{"id": 1, "name": "John Doe", ...}]` | Display lead cards with contact info | ⏳ |
| **Search by Company** | `GET /api/leads/?search=acme` | Leads from Acme Corp | Filter to show only Acme leads | ⏳ |
| **High Priority** | `GET /api/leads/?priority=high` | High priority leads | Show leads with red priority indicator | ⏳ |
| **Empty Results** | `GET /api/leads/?search=nonexistent` | `[]` | Show "No leads found" with add lead button | ⏳ |

### Lead Creation Endpoint (`POST /api/leads/`)

#### UI Integration Points
| UI Element | API Call | Expected Response | UI Behavior | Test Status |
|------------|----------|-------------------|-------------|-------------|
| **Add Lead Form** | POST with lead data | 201 + created lead | Show success, add to lead list | ⏳ |
| **Duplicate Email** | POST with existing email | 400 + duplicate error | Show "Lead already exists" with link | ⏳ |
| **Invalid Data** | POST with invalid fields | 400 + validation errors | Highlight invalid fields | ⏳ |

#### Test Scenarios
| Scenario | Request Body | Expected Response | UI Expected Behavior | Test Status |
|----------|--------------|-------------------|---------------------|-------------|
| **Valid Lead** | `{"name": "Jane Doe", "email": "jane@company.com", ...}` | `201 {"id": 789, "name": "Jane Doe", ...}` | Show success, refresh lead list | ⏳ |
| **Missing Name** | `{"name": "", "email": "test@test.com", ...}` | `400 {"name": ["This field is required"]}` | Highlight name field error | ⏳ |
| **Invalid Email** | `{"name": "John", "email": "invalid", ...}` | `400 {"email": ["Enter a valid email"]}` | Show email format error | ⏳ |
| **Duplicate Lead** | `{"name": "John", "email": "existing@test.com", ...}` | `400 {"email": ["Lead with this email exists"]}` | Show duplicate warning with view option | ⏳ |

### Lead Details Endpoint (`GET /api/leads/{id}/`)

#### UI Integration Points
| UI Element | API Call | Expected Response | UI Behavior | Test Status |
|------------|----------|-------------------|-------------|-------------|
| **Lead Details Page** | GET /api/leads/123/ | Complete lead object | Populate all lead information | ⏳ |
| **Lead Not Found** | GET /api/leads/999/ | 404 Not Found | Show "Lead not found" error page | ⏳ |
| **Load Lead for Edit** | GET /api/leads/123/ | Lead object | Pre-populate edit form | ⏳ |

## AI Service API Testing

### AI Insights Endpoint (`GET /api/ai/insights/{lead_id}/`)

#### UI Integration Points
| UI Element | API Call | Expected Response | UI Behavior | Test Status |
|------------|----------|-------------------|-------------|-------------|
| **Insights Widget** | GET /api/ai/insights/123/ | AI insights object | Display conversion probability, scores | ⏳ |
| **Generate Insights** | POST /api/ai/insights/123/generate/ | 202 Accepted | Show loading, poll for completion | ⏳ |
| **Insights Loading** | GET during generation | 202 Processing | Show progress indicator | ⏳ |
| **Insights Complete** | GET after generation | 200 + insights | Display generated insights | ⏳ |

#### Test Scenarios
| Scenario | Request | Expected Response | UI Expected Behavior | Test Status |
|----------|---------|-------------------|---------------------|-------------|
| **Load Insights** | `GET /api/ai/insights/123/` | `{"conversion_probability": 0.75, ...}` | Show 75% conversion probability | ⏳ |
| **No Insights** | `GET /api/ai/insights/456/` | `{"message": "No insights available"}` | Show "Generate insights" button | ⏳ |
| **Generate Request** | `POST /api/ai/insights/123/generate/` | `202 {"task_id": "abc123"}` | Show "Generating..." with progress | ⏳ |
| **Generation Error** | `GET /api/ai/insights/123/` | `500 Generation failed` | Show error with retry option | ⏳ |

### Question Generation Endpoint (`POST /api/ai/questions/`)

#### UI Integration Points
| UI Element | API Call | Expected Response | UI Behavior | Test Status |
|------------|----------|-------------------|-------------|-------------|
| **Generate Questions** | POST with meeting context | 200 + questions array | Display generated questions | ⏳ |
| **Question Loading** | POST request in progress | Processing | Show loading spinner | ⏳ |
| **Generation Failed** | POST returns error | 500 Error | Show error message with retry | ⏳ |

## Voice Service API Testing

### Voice Session Endpoint (`POST /api/voice/sessions/`)

#### UI Integration Points
| UI Element | API Call | Expected Response | UI Behavior | Test Status |
|------------|----------|-------------------|-------------|-------------|
| **Start Call Button** | POST /api/voice/sessions/ | 201 + session object | Initialize voice interface | ⏳ |
| **Session Creation Failed** | POST returns error | 500 Error | Show "Unable to start call" error | ⏳ |

### Voice Recording Endpoint (`POST /api/voice/sessions/{id}/audio/`)

#### UI Integration Points
| UI Element | API Call | Expected Response | UI Behavior | Test Status |
|------------|----------|-------------------|-------------|-------------|
| **Audio Upload** | POST with audio data | 200 + transcript | Display real-time transcript | ⏳ |
| **Upload Failed** | POST returns error | 500 Error | Show recording error indicator | ⏳ |

## WebSocket API Testing

### Real-time Updates (`ws://localhost:8000/ws/updates/`)

#### UI Integration Points
| WebSocket Event | Message Type | Expected Data | UI Behavior | Test Status |
|-----------------|--------------|---------------|-------------|-------------|
| **Meeting Update** | meeting_updated | Meeting object | Update meeting display | ⏳ |
| **New Lead** | lead_created | Lead object | Add lead to list | ⏳ |
| **AI Insights Ready** | insights_ready | Insights object | Update insights widget | ⏳ |
| **Connection Lost** | connection_error | Error message | Show offline indicator | ⏳ |

#### Test Scenarios
| Scenario | WebSocket Message | UI Expected Behavior | Test Status |
|----------|-------------------|---------------------|-------------|
| **Meeting Reminder** | `{"type": "meeting_reminder", "meeting_id": 123}` | Show notification popup | ⏳ |
| **Lead Status Change** | `{"type": "lead_updated", "lead": {...}}` | Update lead card status | ⏳ |
| **System Notification** | `{"type": "system_message", "message": "..."}` | Show system notification | ⏳ |
| **Connection Restored** | `{"type": "connection_restored"}` | Hide offline indicator | ⏳ |

## Error Handling Testing

### HTTP Error Responses

#### 400 Bad Request
| Scenario | API Response | UI Expected Behavior | Test Status |
|----------|--------------|---------------------|-------------|
| **Form Validation** | `{"field": ["Error message"]}` | Highlight field with error message | ⏳ |
| **Invalid JSON** | `{"error": "Invalid JSON"}` | Show generic form error | ⏳ |
| **Missing Required** | `{"field": ["This field is required"]}` | Show required field indicator | ⏳ |

#### 401 Unauthorized
| Scenario | API Response | UI Expected Behavior | Test Status |
|----------|--------------|---------------------|-------------|
| **Session Expired** | `{"error": "Token expired"}` | Redirect to login with message | ⏳ |
| **Invalid Token** | `{"error": "Invalid token"}` | Clear session, redirect to login | ⏳ |

#### 403 Forbidden
| Scenario | API Response | UI Expected Behavior | Test Status |
|----------|--------------|---------------------|-------------|
| **Insufficient Permissions** | `{"error": "Permission denied"}` | Show "Access denied" message | ⏳ |
| **Resource Restricted** | `{"error": "Access restricted"}` | Hide restricted UI elements | ⏳ |

#### 404 Not Found
| Scenario | API Response | UI Expected Behavior | Test Status |
|----------|--------------|---------------------|-------------|
| **Resource Not Found** | `{"error": "Not found"}` | Show "Item not found" page | ⏳ |
| **Invalid URL** | `404 Page not found` | Show 404 error page | ⏳ |

#### 500 Internal Server Error
| Scenario | API Response | UI Expected Behavior | Test Status |
|----------|--------------|---------------------|-------------|
| **Server Error** | `{"error": "Internal server error"}` | Show error message with retry | ⏳ |
| **Database Error** | `500 Database connection failed` | Show "Service unavailable" message | ⏳ |

## Loading States Testing

### API Request Loading States
| UI Element | During API Call | Expected Behavior | Test Status |
|------------|-----------------|-------------------|-------------|
| **Form Submit Button** | POST in progress | Show spinner, disable button | ⏳ |
| **Data Table** | GET in progress | Show skeleton loading | ⏳ |
| **Search Results** | Search API call | Show search loading indicator | ⏳ |
| **Page Navigation** | Page load API | Show page loading spinner | ⏳ |

### Long-Running Operations
| Operation | Expected UI Behavior | Test Status |
|-----------|---------------------|-------------|
| **AI Insight Generation** | Progress bar with status updates | ⏳ |
| **File Upload** | Upload progress with cancel option | ⏳ |
| **Bulk Operations** | Progress indicator with item count | ⏳ |
| **Report Generation** | Loading message with estimated time | ⏳ |

## API Performance Testing

### Response Time Requirements
| Endpoint | Expected Response Time | Test Status |
|----------|----------------------|-------------|
| **GET /api/users/** | < 500ms | ⏳ |
| **POST /api/meetings/** | < 1000ms | ⏳ |
| **GET /api/leads/** | < 500ms | ⏳ |
| **POST /api/ai/insights/** | < 2000ms | ⏳ |

### Concurrent Request Handling
| Scenario | Expected Behavior | Test Status |
|----------|-------------------|-------------|
| **Multiple simultaneous searches** | All requests complete successfully | ⏳ |
| **Concurrent form submissions** | Proper validation and error handling | ⏳ |
| **Real-time updates during API calls** | UI updates don't interfere with requests | ⏳ |

## Testing Checklist Summary

### API Integration Validation
- [ ] All endpoints return expected response formats
- [ ] Error responses are handled gracefully in UI
- [ ] Loading states are shown during API calls
- [ ] Success messages are displayed appropriately
- [ ] Form validation errors are shown correctly

### Real-time Features
- [ ] WebSocket connections establish successfully
- [ ] Real-time updates appear in UI immediately
- [ ] Connection loss is handled gracefully
- [ ] Reconnection works automatically

### Error Recovery
- [ ] Network errors show retry options
- [ ] Server errors display helpful messages
- [ ] Authentication errors redirect properly
- [ ] Validation errors highlight specific fields

### Performance Requirements
- [ ] API responses meet time requirements
- [ ] UI remains responsive during API calls
- [ ] Large datasets load efficiently
- [ ] Concurrent requests don't cause issues

---

**Testing Status Legend:**
- ⏳ = Pending Test
- ✅ = Test Passed
- ❌ = Test Failed
- ⚠️ = Test Needs Review