# Django Admin Interface - Complete UI Testing Guide

## Overview
This document provides comprehensive testing specifications for every UI element in the Django Admin interface of the NIA Sales Assistant application.

## Admin Dashboard Testing

### Main Dashboard Page (`/admin/`)

#### Navigation Elements
| Element | Location | Action | Expected Behavior | Test Status |
|---------|----------|--------|-------------------|-------------|
| **NIA Logo** | Top left | Click | Navigate to admin dashboard | [X] |
| **Site Administration** | Header | Visual | Display current site name | [x] |
| **View Site** | Top right | Click | Open main site in new tab | Not opening in new tab     |
| **Change Password** | Top right | Click | Navigate to password change form | [x] |
| **Log Out** | Top right | Click | Log out and redirect to login page | [x] |

#### Application Sections
| Section | Elements | Expected Behavior | Test Status |
|---------|----------|-------------------|-------------|
| **AI Service** | Links to Lead, ConversationAnalysis, AIInsights | Click navigates to respective list views | ✅ |
| **Admin Config** | Links to ConfigurationTemplate, IntegrationConfiguration, etc. | Click navigates to respective list views | ✅ |
| **Authentication** | Links to Groups, Users, Permissions | Click navigates to respective list views | ✅ |
| **Meeting Service** | Links to Meeting, MeetingSession, MeetingQuestion, etc. | Click navigates to respective list views | ✅ |
| **Voice Service** | Links to CallSession, AudioChunk, ConversationTurn, etc. | Click navigates to respective list views | ✅ |

## User Management Testing

### User List View (`/admin/users/user/`)

#### Page Header Elements
| Element | Action | Expected Behavior | Test Status |
|---------|--------|-------------------|-------------|
| **Add User** button | Click | Navigate to user creation form | ⏳ |
| **Search box** | Type and Enter | Filter users by username/email | ⏳ |
| **Filter sidebar** | Click filter options | Filter users by role, status, etc. | ⏳ |

#### User List Table
| Column | Sortable | Action | Expected Behavior | Test Status |
|--------|----------|--------|-------------------|-------------|
| **Username** | Yes | Click header | Sort by username A-Z/Z-A | ⏳ |
| **Email** | Yes | Click header | Sort by email A-Z/Z-A | ⏳ |
| **First Name** | Yes | Click header | Sort by first name A-Z/Z-A | ⏳ |
| **Last Name** | Yes | Click header | Sort by last name A-Z/Z-A | ⏳ |
| **Role** | Yes | Click header | Sort by role | ⏳ |
| **Status** | Yes | Click header | Sort by active/inactive | ⏳ |
| **Date Joined** | Yes | Click header | Sort by join date | ⏳ |

#### Row Actions
| Element | Action | Expected Behavior | Test Status |
|---------|--------|-------------------|-------------|
| **Username link** | Click | Navigate to user edit form | ⏳ |
| **Checkbox** | Check/Uncheck | Select user for bulk actions | ⏳ |
| **Action dropdown** | Select action + Go | Execute bulk action on selected users | ⏳ |

### User Creation Form (`/admin/users/user/add/`)

#### Form Fields
| Field | Type | Validation | Expected Behavior | Test Status |
|-------|------|------------|-------------------|-------------|
| **Username** | Text | Required, unique | Show error if duplicate/empty | ⏳ |
| **Email** | Email | Required, valid email | Show error if invalid format | ⏳ |
| **First Name** | Text | Optional | Accept any text input | ⏳ |
| **Last Name** | Text | Optional | Accept any text input | ⏳ |
| **Password** | Password | Required, strength rules | Show strength indicator | ⏳ |
| **Password Confirmation** | Password | Must match password | Show error if mismatch | ⏳ |
| **Role** | Dropdown | Required | Show available roles | ⏳ |
| **Is Active** | Checkbox | Default checked | Toggle user active status | ⏳ |
| **Is Staff** | Checkbox | Default unchecked | Toggle staff access | ⏳ |
| **Is Superuser** | Checkbox | Default unchecked | Toggle superuser access | ⏳ |

#### Form Buttons
| Button | Action | Expected Behavior | Test Status |
|--------|--------|-------------------|-------------|
| **Save** | Click | Validate and create user, redirect to user list | ⏳ |
| **Save and Add Another** | Click | Create user and reload blank form | ⏳ |
| **Save and Continue Editing** | Click | Create user and stay on edit form | ⏳ |
| **Cancel** | Click | Discard changes and return to user list | ⏳ |

## Meeting Management Testing

### Meeting List View (`/admin/meeting_service/meeting/`)

#### Page Header Elements
| Element | Action | Expected Behavior | Test Status |
|---------|--------|-------------------|-------------|
| **Add Meeting** button | Click | Navigate to meeting creation form | ⏳ |
| **Search box** | Type and Enter | Filter meetings by title/participant | ⏳ |
| **Date filter** | Select date range | Filter meetings by date | ⏳ |
| **Status filter** | Select status | Filter by meeting status | ⏳ |

#### Meeting List Table
| Column | Sortable | Action | Expected Behavior | Test Status |
|--------|----------|--------|-------------------|-------------|
| **Title** | Yes | Click header | Sort by meeting title | ⏳ |
| **Organizer** | Yes | Click header | Sort by organizer name | ⏳ |
| **Scheduled Time** | Yes | Click header | Sort by meeting time | ⏳ |
| **Status** | Yes | Click header | Sort by status | ⏳ |
| **Participants** | No | Display | Show participant count | ⏳ |
| **Lead Context** | No | Display | Show associated lead info | ⏳ |

#### Meeting Actions
| Element | Action | Expected Behavior | Test Status |
|---------|--------|-------------------|-------------|
| **Meeting title link** | Click | Navigate to meeting edit form | ⏳ |
| **View Details** button | Click | Open meeting details modal | ⏳ |
| **Generate Questions** button | Click | Trigger AI question generation | ⏳ |
| **Export** button | Click | Download meeting data as CSV/PDF | ⏳ |

### Meeting Creation Form (`/admin/meeting_service/meeting/add/`)

#### Basic Information Section
| Field | Type | Validation | Expected Behavior | Test Status |
|-------|------|------------|-------------------|-------------|
| **Title** | Text | Required | Show error if empty | ⏳ |
| **Description** | Textarea | Optional | Accept long text input | ⏳ |
| **Meeting Type** | Dropdown | Required | Show available types | ⏳ |
| **Scheduled Start** | DateTime | Required | Show date/time picker | ⏳ |
| **Scheduled End** | DateTime | Required | Validate end > start | ⏳ |
| **Timezone** | Dropdown | Required | Show timezone options | ⏳ |

#### Participants Section
| Element | Action | Expected Behavior | Test Status |
|---------|--------|-------------------|-------------|
| **Add Participant** button | Click | Add new participant row | ⏳ |
| **Participant Name** field | Type | Accept text input | ⏳ |
| **Participant Email** field | Type | Validate email format | ⏳ |
| **Participant Role** dropdown | Select | Show role options | ⏳ |
| **Remove Participant** button | Click | Remove participant row | ⏳ |

#### Lead Context Section
| Field | Type | Expected Behavior | Test Status |
|-------|------|-------------------|-------------|
| **Associated Lead** | Dropdown | Show available leads | ⏳ |
| **Lead Priority** | Dropdown | Show priority levels | ⏳ |
| **Expected Outcome** | Textarea | Accept text input | ⏳ |

#### Integration Settings
| Field | Type | Expected Behavior | Test Status |
|-------|------|-------------------|-------------|
| **Google Meet Integration** | Checkbox | Toggle Google Meet features | ⏳ |
| **Teams Integration** | Checkbox | Toggle Teams features | ⏳ |
| **Auto-generate Questions** | Checkbox | Toggle AI question generation | ⏳ |
| **Record Meeting** | Checkbox | Toggle meeting recording | ⏳ |

## AI Service Testing

### Lead Management (`/admin/ai_service/lead/`)

#### Lead List View
| Element | Action | Expected Behavior | Test Status |
|---------|--------|-------------------|-------------|
| **Add Lead** button | Click | Navigate to lead creation form | ⏳ |
| **Search** field | Type | Filter leads by name/company | ⏳ |
| **Status filter** | Select | Filter by lead status | ⏳ |
| **Priority filter** | Select | Filter by priority level | ⏳ |
| **Export** button | Click | Download leads as CSV | ⏳ |

#### Lead Table Columns
| Column | Sortable | Action | Expected Behavior | Test Status |
|--------|----------|--------|-------------------|-------------|
| **Name** | Yes | Click | Navigate to lead edit form | ⏳ |
| **Company** | Yes | Click header | Sort by company name | ⏳ |
| **Email** | Yes | Click header | Sort by email | ⏳ |
| **Status** | Yes | Click header | Sort by status | ⏳ |
| **Priority** | Yes | Click header | Sort by priority | ⏳ |
| **Created** | Yes | Click header | Sort by creation date | ⏳ |
| **Last Contact** | Yes | Click header | Sort by last contact date | ⏳ |

#### Lead Actions
| Element | Action | Expected Behavior | Test Status |
|---------|--------|-------------------|-------------|
| **View** button | Click | Open lead details modal | ⏳ |
| **Edit** button | Click | Navigate to lead edit form | ⏳ |
| **Generate Insights** button | Click | Trigger AI insights generation | ⏳ |
| **Schedule Meeting** button | Click | Open meeting scheduling modal | ⏳ |

### AI Insights Dashboard (`/admin/ai_service/aiinsights/`)

#### Dashboard Widgets
| Widget | Elements | Expected Behavior | Test Status |
|--------|----------|-------------------|-------------|
| **Conversion Probability** | Progress bar, percentage | Display lead conversion likelihood | ⏳ |
| **Engagement Score** | Gauge chart | Show engagement level | ⏳ |
| **Next Best Action** | Action cards | Display recommended actions | ⏳ |
| **Risk Factors** | Alert badges | Show potential risks | ⏳ |

#### Interactive Elements
| Element | Action | Expected Behavior | Test Status |
|---------|--------|-------------------|-------------|
| **Refresh Insights** button | Click | Regenerate AI insights | ⏳ |
| **Export Report** button | Click | Download insights as PDF | ⏳ |
| **Schedule Follow-up** button | Click | Open follow-up scheduling modal | ⏳ |
| **Update Status** dropdown | Select | Change lead status | ⏳ |

## Voice Service Testing

### Call Session Management (`/admin/voice_service/callsession/`)

#### Call Session List
| Element | Action | Expected Behavior | Test Status |
|---------|--------|-------------------|-------------|
| **Session ID** link | Click | Navigate to session details | ⏳ |
| **Play Recording** button | Click | Play audio recording | ⏳ |
| **View Transcript** button | Click | Open transcript modal | ⏳ |
| **Download** button | Click | Download session data | ⏳ |

#### Audio Controls
| Control | Action | Expected Behavior | Test Status |
|---------|--------|-------------------|-------------|
| **Play/Pause** button | Click | Start/stop audio playback | ⏳ |
| **Volume slider** | Drag | Adjust playback volume | ⏳ |
| **Progress bar** | Click | Seek to specific time | ⏳ |
| **Speed control** | Select | Change playback speed | ⏳ |

## Configuration Management Testing

### Configuration Templates (`/admin/admin_config/configurationtemplate/`)

#### Template Management
| Element | Action | Expected Behavior | Test Status |
|---------|--------|-------------------|-------------|
| **Create Template** button | Click | Open template creation form | ⏳ |
| **Import Template** button | Click | Open file upload dialog | ⏳ |
| **Export Template** button | Click | Download template as JSON | ⏳ |
| **Clone Template** button | Click | Create copy of template | ⏳ |

#### Template Editor
| Field | Type | Expected Behavior | Test Status |
|-------|------|-------------------|-------------|
| **Template Name** | Text | Required field validation | ⏳ |
| **Description** | Textarea | Optional long text | ⏳ |
| **Configuration JSON** | Code editor | JSON syntax validation | ⏳ |
| **Is Active** | Checkbox | Toggle template status | ⏳ |

## Error Handling and Validation Testing

### Form Validation
| Scenario | Expected Behavior | Test Status |
|----------|-------------------|-------------|
| **Submit empty required field** | Show field-specific error message | ⏳ |
| **Submit invalid email** | Show email format error | ⏳ |
| **Submit duplicate username** | Show uniqueness error | ⏳ |
| **Submit mismatched passwords** | Show password mismatch error | ⏳ |
| **Submit invalid date range** | Show date validation error | ⏳ |

### Network Error Handling
| Scenario | Expected Behavior | Test Status |
|----------|-------------------|-------------|
| **Network timeout** | Show timeout error message | ⏳ |
| **Server error (500)** | Show generic error message | ⏳ |
| **Unauthorized access (403)** | Redirect to login page | ⏳ |
| **Not found (404)** | Show not found page | ⏳ |

## Responsive Design Testing

### Mobile View (< 768px)
| Element | Expected Behavior | Test Status |
|---------|-------------------|-------------|
| **Navigation menu** | Collapse to hamburger menu | ⏳ |
| **Data tables** | Horizontal scroll or stack | ⏳ |
| **Form fields** | Full width layout | ⏳ |
| **Buttons** | Touch-friendly size | ⏳ |

### Tablet View (768px - 1024px)
| Element | Expected Behavior | Test Status |
|---------|-------------------|-------------|
| **Sidebar** | Collapsible sidebar | ⏳ |
| **Grid layout** | Responsive column adjustment | ⏳ |
| **Modal dialogs** | Appropriate sizing | ⏳ |

## Accessibility Testing

### Keyboard Navigation
| Element | Expected Behavior | Test Status |
|---------|-------------------|-------------|
| **Tab navigation** | Logical tab order through all elements | ⏳ |
| **Enter key** | Activate buttons and links | ⏳ |
| **Escape key** | Close modals and dropdowns | ⏳ |
| **Arrow keys** | Navigate through dropdown options | ⏳ |

### Screen Reader Support
| Element | Expected Behavior | Test Status |
|---------|-------------------|-------------|
| **Form labels** | Properly associated with inputs | ⏳ |
| **Button descriptions** | Clear action descriptions | ⏳ |
| **Error messages** | Announced when displayed | ⏳ |
| **Status updates** | Live region announcements | ⏳ |

## Performance Testing

### Page Load Times
| Page | Expected Load Time | Test Status |
|------|-------------------|-------------|
| **Admin dashboard** | < 2 seconds | ⏳ |
| **User list (100 users)** | < 3 seconds | ⏳ |
| **Meeting list (50 meetings)** | < 3 seconds | ⏳ |
| **Lead details with insights** | < 4 seconds | ⏳ |

### Interactive Response Times
| Action | Expected Response Time | Test Status |
|--------|----------------------|-------------|
| **Form submission** | < 1 second | ⏳ |
| **Search filtering** | < 0.5 seconds | ⏳ |
| **Modal opening** | < 0.3 seconds | ⏳ |
| **AI insight generation** | < 10 seconds | ⏳ |

## Testing Checklist Summary

### Critical Path Testing
- [ ] User login and authentication
- [ ] User creation and management
- [ ] Meeting creation and scheduling
- [ ] Lead management and insights
- [ ] Voice session playback
- [ ] Configuration management

### UI Component Testing
- [ ] All buttons clickable and functional
- [ ] All forms validate correctly
- [ ] All navigation links work
- [ ] All modals open and close properly
- [ ] All dropdowns show correct options
- [ ] All tables sort and filter correctly

### Cross-Browser Testing
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

### Device Testing
- [ ] Desktop (1920x1080)
- [ ] Laptop (1366x768)
- [ ] Tablet (768x1024)
- [ ] Mobile (375x667)

---

**Testing Status Legend:**
- ⏳ = Pending Test
- ✅ = Test Passed
- ❌ = Test Failed
- ⚠️ = Test Needs Review