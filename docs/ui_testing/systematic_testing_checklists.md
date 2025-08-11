# Systematic UI Testing Checklists - NIA Sales Assistant

## Overview
This document provides comprehensive, step-by-step testing checklists for every page and component in the NIA Sales Assistant application. Each checklist includes detailed procedures, expected outcomes, and systematic testing approaches.

## How to Use These Checklists

### Testing Symbols
- ⏳ = **Pending Test** (Not yet tested)
- ✅ = **Test Passed** (Works as expected)
- ❌ = **Test Failed** (Bug found, needs fixing)
- ⚠️ = **Test Needs Review** (Unclear behavior, needs clarification)
- 🔄 = **Retest Required** (Fixed, needs retesting)

### Testing Priority Levels
- **🔴 Critical** - Core functionality that must work
- **🟡 High** - Important features that impact user experience
- **🟢 Medium** - Nice-to-have features
- **🔵 Low** - Minor enhancements or edge cases

## Critical Path Testing Checklists

### 1. Authentication Flow Testing Checklist

#### Pre-Test Setup
- [ ] Clear browser cache and cookies
- [ ] Ensure test user accounts are available
- [ ] Verify server is running and accessible

#### Login Page Testing (`/login/`)
| Step | Action | Expected Result | Priority | Status | Notes |
|------|--------|-----------------|----------|--------|-------|
| 1.1 | Navigate to `/login/` | Login page loads within 2 seconds | 🔴 | ⏳ | |
| 1.2 | Check page title | Title shows "Login - NIA Sales Assistant" | 🟡 | ⏳ | |
| 1.3 | Verify form elements | Username field, password field, login button visible | 🔴 | ⏳ | |
| 1.4 | Check placeholder text | Username shows "Enter username", password shows "Enter password" | 🟢 | ⏳ | |
| 1.5 | Test empty form submission | Click login without entering data | 🔴 | ⏳ | Should show validation errors |
| 1.6 | Test invalid credentials | Enter wrong username/password | 🔴 | ⏳ | Should show "Invalid credentials" error |
| 1.7 | Test valid login | Enter correct credentials | 🔴 | ⏳ | Should redirect to dashboard |
| 1.8 | Check remember me | Toggle remember me checkbox | 🟡 | ⏳ | Should persist login longer |
| 1.9 | Test forgot password link | Click "Forgot Password" | 🟡 | ⏳ | Should navigate to password reset |
| 1.10 | Test responsive design | Resize browser to mobile width | 🟡 | ⏳ | Form should remain usable |

#### Session Management Testing
| Step | Action | Expected Result | Priority | Status | Notes |
|------|--------|-----------------|----------|--------|-------|
| 2.1 | Login successfully | User is authenticated | 🔴 | ⏳ | |
| 2.2 | Navigate to protected page | Page loads without redirect | 🔴 | ⏳ | |
| 2.3 | Wait for session timeout | Session expires after configured time | 🟡 | ⏳ | Should redirect to login |
| 2.4 | Test logout functionality | Click logout button | 🔴 | ⏳ | Should clear session and redirect |
| 2.5 | Try accessing protected page after logout | Navigate to dashboard | 🔴 | ⏳ | Should redirect to login |

### 2. Dashboard Functionality Testing Checklist

#### Pre-Test Setup
- [ ] Login with valid user account
- [ ] Ensure sample data exists (leads, meetings, etc.)
- [ ] Clear any existing filters or search terms

#### Dashboard Loading and Layout
| Step | Action | Expected Result | Priority | Status | Notes |
|------|--------|-----------------|----------|--------|-------|
| 3.1 | Navigate to dashboard | Dashboard loads within 3 seconds | 🔴 | ⏳ | |
| 3.2 | Check header navigation | Logo, menu items, user profile visible | 🔴 | ⏳ | |
| 3.3 | Verify welcome section | Welcome message and description display | 🟢 | ⏳ | |
| 3.4 | Check widget loading | All dashboard widgets load data | 🔴 | ⏳ | |
| 3.5 | Test navigation menu | Click each menu item (Leads, Create Lead, Analytics, Chat) | 🔴 | ⏳ | Should switch views |
| 3.6 | Verify active state | Active menu item highlighted | 🟡 | ⏳ | |
| 3.7 | Test responsive layout | Resize to tablet/mobile | 🟡 | ⏳ | Layout should adapt |

#### Widget Functionality Testing
| Step | Action | Expected Result | Priority | Status | Notes |
|------|--------|-----------------|----------|--------|-------|
| 4.1 | Check total leads widget | Displays correct lead count | 🔴 | ⏳ | |
| 4.2 | Check high quality leads | Shows count of leads with score >70% | 🔴 | ⏳ | |
| 4.3 | Check average score | Displays calculated average score | 🔴 | ⏳ | |
| 4.4 | Test widget refresh | Refresh page and verify data consistency | 🟡 | ⏳ | |
| 4.5 | Test with no data | Remove all leads and check widget display | 🟡 | ⏳ | Should show 0 or "No data" |

### 3. Lead Management Testing Checklist

#### Pre-Test Setup
- [ ] Ensure test leads exist in database
- [ ] Clear any existing search/filter states
- [ ] Prepare test conversation text for lead creation

#### Leads List View Testing
| Step | Action | Expected Result | Priority | Status | Notes |
|------|--------|-----------------|----------|--------|-------|
| 5.1 | Navigate to Leads view | Leads list loads within 3 seconds | 🔴 | ⏳ | |
| 5.2 | Verify lead cards display | All leads show with correct information | 🔴 | ⏳ | |
| 5.3 | Check search functionality | Type in search box | 🔴 | ⏳ | Should filter leads in real-time |
| 5.4 | Test status filter | Select different status options | 🔴 | ⏳ | Should filter by status |
| 5.5 | Test score filter | Select score ranges | 🔴 | ⏳ | Should filter by score |
| 5.6 | Test sorting | Change sort options | 🔴 | ⏳ | Should reorder leads |
| 5.7 | Test view mode toggle | Switch between list and grid view | 🟡 | ⏳ | Layout should change |
| 5.8 | Test refresh button | Click refresh | 🟡 | ⏳ | Should reload leads |
| 5.9 | Test export button | Click export | 🟡 | ⏳ | Should download CSV |
| 5.10 | Test lead detail view | Click on lead card | 🔴 | ⏳ | Should show lead details |

#### Lead Creation Testing
| Step | Action | Expected Result | Priority | Status | Notes |
|------|--------|-----------------|----------|--------|-------|
| 6.1 | Click "Create New Lead" | Create form displays | 🔴 | ⏳ | |
| 6.2 | Test empty form submission | Submit without conversation text | 🔴 | ⏳ | Should show validation error |
| 6.3 | Enter conversation text | Paste sample conversation | 🔴 | ⏳ | Text should be accepted |
| 6.4 | Select lead source | Choose from dropdown | 🟡 | ⏳ | Should accept selection |
| 6.5 | Select urgency level | Choose urgency | 🟡 | ⏳ | Should accept selection |
| 6.6 | Click "Analyze & Create Lead" | Analysis starts | 🔴 | ⏳ | Should show loading indicator |
| 6.7 | Wait for analysis completion | Results display | 🔴 | ⏳ | Should show extracted information |
| 6.8 | Review analysis results | Information is accurate | 🔴 | ⏳ | Should match conversation content |
| 6.9 | Confirm lead creation | Click "Create Lead" | 🔴 | ⏳ | Should create lead and redirect |
| 6.10 | Verify lead in list | New lead appears in leads list | 🔴 | ⏳ | |

#### Lead Detail View Testing
| Step | Action | Expected Result | Priority | Status | Notes |
|------|--------|-----------------|----------|--------|-------|
| 7.1 | Open lead detail view | Detail view loads | 🔴 | ⏳ | |
| 7.2 | Check header information | Company name, status badge display | 🔴 | ⏳ | |
| 7.3 | Verify overview cards | Score, last contact, source, next action | 🔴 | ⏳ | |
| 7.4 | Test tab navigation | Click each tab | 🔴 | ⏳ | Should switch content |
| 7.5 | Check lead information tab | Contact info, requirements display | 🔴 | ⏳ | |
| 7.6 | Check conversation history | Conversation timeline shows | 🔴 | ⏳ | |
| 7.7 | Check AI insights tab | Insights load and display | 🔴 | ⏳ | |
| 7.8 | Check activity timeline | Activities show chronologically | 🟡 | ⏳ | |
| 7.9 | Test edit button | Click edit | 🟡 | ⏳ | Should open edit modal |
| 7.10 | Test back button | Click back | 🔴 | ⏳ | Should return to leads list |

### 4. Meeting Management Testing Checklist

#### Pre-Test Setup
- [ ] Login as user with meeting permissions
- [ ] Ensure test meetings exist
- [ ] Verify calendar integrations are configured

#### Meeting List Testing
| Step | Action | Expected Result | Priority | Status | Notes |
|------|--------|-----------------|----------|--------|-------|
| 8.1 | Navigate to meetings page | Meeting list loads | 🔴 | ⏳ | |
| 8.2 | Check meeting cards | All meetings display correctly | 🔴 | ⏳ | |
| 8.3 | Test search functionality | Search by meeting title | 🔴 | ⏳ | Should filter meetings |
| 8.4 | Test date filter | Filter by date range | 🔴 | ⏳ | Should show meetings in range |
| 8.5 | Test status filter | Filter by meeting status | 🔴 | ⏳ | Should filter by status |
| 8.6 | Test calendar view | Switch to calendar view | 🟡 | ⏳ | Should show calendar layout |
| 8.7 | Test meeting actions | Click join, edit, delete buttons | 🔴 | ⏳ | Should perform respective actions |

#### Meeting Creation Testing
| Step | Action | Expected Result | Priority | Status | Notes |
|------|--------|-----------------|----------|--------|-------|
| 9.1 | Click "New Meeting" | Creation modal opens | 🔴 | ⏳ | |
| 9.2 | Test required fields | Submit empty form | 🔴 | ⏳ | Should show validation errors |
| 9.3 | Enter meeting title | Type meeting title | 🔴 | ⏳ | Should accept input |
| 9.4 | Enter description | Type description | 🟡 | ⏳ | Should accept input |
| 9.5 | Select date and time | Use date/time pickers | 🔴 | ⏳ | Should accept valid date/time |
| 9.6 | Test time validation | Set end time before start | 🔴 | ⏳ | Should show validation error |
| 9.7 | Add participants | Add participant emails | 🔴 | ⏳ | Should accept valid emails |
| 9.8 | Select meeting type | Choose platform | 🟡 | ⏳ | Should accept selection |
| 9.9 | Submit form | Click create button | 🔴 | ⏳ | Should create meeting |
| 9.10 | Verify in list | New meeting appears | 🔴 | ⏳ | |

### 5. Voice Service Testing Checklist

#### Pre-Test Setup
- [ ] Ensure microphone permissions are granted
- [ ] Test audio input/output devices
- [ ] Verify WebRTC support in browser

#### Voice Interface Testing
| Step | Action | Expected Result | Priority | Status | Notes |
|------|--------|-----------------|----------|--------|-------|
| 10.1 | Navigate to voice service | Voice page loads | 🔴 | ⏳ | |
| 10.2 | Check microphone permissions | Permission prompt appears | 🔴 | ⏳ | |
| 10.3 | Test microphone test | Click test microphone | 🔴 | ⏳ | Should show audio levels |
| 10.4 | Start voice call | Click start call | 🔴 | ⏳ | Should initialize call |
| 10.5 | Test mute/unmute | Toggle mute button | 🔴 | ⏳ | Should mute/unmute audio |
| 10.6 | Test volume control | Adjust volume slider | 🟡 | ⏳ | Should change volume |
| 10.7 | Test call recording | Start/stop recording | 🟡 | ⏳ | Should record audio |
| 10.8 | End call | Click end call | 🔴 | ⏳ | Should terminate call |
| 10.9 | Check call history | View previous calls | 🟡 | ⏳ | Should show call list |
| 10.10 | Play recording | Click play on recording | 🟡 | ⏳ | Should play audio |

## Complex Workflow Testing Checklists

### 6. End-to-End Lead Conversion Workflow

#### Complete Lead Journey Testing
| Step | Action | Expected Result | Priority | Status | Notes |
|------|--------|-----------------|----------|--------|-------|
| 11.1 | Create new lead from conversation | Lead created successfully | 🔴 | ⏳ | |
| 11.2 | Review AI-generated insights | Insights are relevant and accurate | 🔴 | ⏳ | |
| 11.3 | Schedule follow-up meeting | Meeting created and linked to lead | 🔴 | ⏳ | |
| 11.4 | Update lead status to "Contacted" | Status changes and timeline updates | 🔴 | ⏳ | |
| 11.5 | Add conversation notes | Notes saved and visible in history | 🔴 | ⏳ | |
| 11.6 | Generate new AI insights | Updated insights reflect new information | 🔴 | ⏳ | |
| 11.7 | Convert lead to opportunity | Conversion process completes | 🔴 | ⏳ | |
| 11.8 | Verify data consistency | All related data remains intact | 🔴 | ⏳ | |

### 7. Multi-User Collaboration Testing

#### Concurrent User Testing
| Step | Action | Expected Result | Priority | Status | Notes |
|------|--------|-----------------|----------|--------|-------|
| 12.1 | Login with User A | User A authenticated | 🔴 | ⏳ | |
| 12.2 | Login with User B (different browser) | User B authenticated | 🔴 | ⏳ | |
| 12.3 | User A creates lead | Lead appears in User A's list | 🔴 | ⏳ | |
| 12.4 | User B refreshes leads | New lead appears in User B's list | 🔴 | ⏳ | |
| 12.5 | User A edits lead | Changes saved successfully | 🔴 | ⏳ | |
| 12.6 | User B views same lead | Updated information displays | 🔴 | ⏳ | |
| 12.7 | Both users edit simultaneously | Conflict resolution works | 🟡 | ⏳ | |

### 8. Integration Testing Checklist

#### Third-Party Integration Testing
| Step | Action | Expected Result | Priority | Status | Notes |
|------|--------|-----------------|----------|--------|-------|
| 13.1 | Create Google Meet meeting | Meeting link generated | 🔴 | ⏳ | |
| 13.2 | Create Teams meeting | Teams meeting created | 🔴 | ⏳ | |
| 13.3 | Sync with calendar | Events appear in calendar | 🟡 | ⏳ | |
| 13.4 | Send email notifications | Emails delivered successfully | 🟡 | ⏳ | |
| 13.5 | Test webhook callbacks | Webhooks trigger correctly | 🟡 | ⏳ | |

## Error Scenario Testing Checklists

### 9. Network Error Handling

#### Connection Issues Testing
| Step | Action | Expected Result | Priority | Status | Notes |
|------|--------|-----------------|----------|--------|-------|
| 14.1 | Disconnect internet | "Connection lost" message appears | 🔴 | ⏳ | |
| 14.2 | Reconnect internet | "Connection restored" message appears | 🔴 | ⏳ | |
| 14.3 | Submit form while offline | Form queued for submission | 🟡 | ⏳ | |
| 14.4 | Slow network simulation | Loading indicators show appropriately | 🟡 | ⏳ | |
| 14.5 | Server timeout | Timeout error with retry option | 🟡 | ⏳ | |

### 10. Form Validation Testing

#### Comprehensive Form Validation
| Step | Action | Expected Result | Priority | Status | Notes |
|------|--------|-----------------|----------|--------|-------|
| 15.1 | Submit empty required fields | Field-specific error messages | 🔴 | ⏳ | |
| 15.2 | Enter invalid email format | Email format error message | 🔴 | ⏳ | |
| 15.3 | Enter duplicate username | Uniqueness error message | 🔴 | ⏳ | |
| 15.4 | Enter weak password | Password strength error | 🔴 | ⏳ | |
| 15.5 | Enter mismatched passwords | Password mismatch error | 🔴 | ⏳ | |
| 15.6 | Enter invalid date range | Date validation error | 🔴 | ⏳ | |
| 15.7 | Enter text in number field | Input type validation error | 🔴 | ⏳ | |
| 15.8 | Exceed character limits | Character limit error | 🟡 | ⏳ | |

## Performance Testing Checklists

### 11. Page Load Performance

#### Load Time Testing
| Step | Action | Target Time | Priority | Status | Actual Time |
|------|--------|-------------|----------|--------|-------------|
| 16.1 | Load login page | < 1 second | 🔴 | ⏳ | |
| 16.2 | Load dashboard | < 2 seconds | 🔴 | ⏳ | |
| 16.3 | Load leads list (100 leads) | < 3 seconds | 🔴 | ⏳ | |
| 16.4 | Load lead detail view | < 2 seconds | 🔴 | ⏳ | |
| 16.5 | Load meeting list | < 3 seconds | 🔴 | ⏳ | |
| 16.6 | Load analytics page | < 4 seconds | 🟡 | ⏳ | |

### 12. Interactive Performance

#### Response Time Testing
| Step | Action | Target Time | Priority | Status | Actual Time |
|------|--------|-------------|----------|--------|-------------|
| 17.1 | Form submission | < 1 second | 🔴 | ⏳ | |
| 17.2 | Search/filter | < 0.5 seconds | 🔴 | ⏳ | |
| 17.3 | Modal opening | < 0.3 seconds | 🟡 | ⏳ | |
| 17.4 | Page navigation | < 1 second | 🔴 | ⏳ | |
| 17.5 | AI insight generation | < 10 seconds | 🔴 | ⏳ | |

## Accessibility Testing Checklists

### 13. Keyboard Navigation

#### Keyboard Accessibility Testing
| Step | Action | Expected Result | Priority | Status | Notes |
|------|--------|-----------------|----------|--------|-------|
| 18.1 | Tab through all elements | Logical tab order | 🔴 | ⏳ | |
| 18.2 | Check focus indicators | Visible focus on all elements | 🔴 | ⏳ | |
| 18.3 | Use Enter key on buttons | Buttons activate | 🔴 | ⏳ | |
| 18.4 | Use Escape key on modals | Modals close | 🔴 | ⏳ | |
| 18.5 | Navigate dropdowns with arrows | Arrow keys work | 🔴 | ⏳ | |
| 18.6 | Test skip links | Skip to main content works | 🟡 | ⏳ | |

### 14. Screen Reader Support

#### Screen Reader Testing
| Step | Action | Expected Result | Priority | Status | Notes |
|------|--------|-----------------|----------|--------|-------|
| 19.1 | Check form labels | All inputs have labels | 🔴 | ⏳ | |
| 19.2 | Check button descriptions | Clear action descriptions | 🔴 | ⏳ | |
| 19.3 | Check error announcements | Errors announced when shown | 🔴 | ⏳ | |
| 19.4 | Check status updates | Live regions announce changes | 🔴 | ⏳ | |
| 19.5 | Check image alt text | Descriptive alt text present | 🔴 | ⏳ | |

## Browser Compatibility Testing Checklists

### 15. Cross-Browser Testing

#### Chrome Testing
| Step | Feature | Expected Result | Status | Notes |
|------|---------|-----------------|--------|-------|
| 20.1 | Page loading | All pages load correctly | ⏳ | |
| 20.2 | Form submission | All forms work | ⏳ | |
| 20.3 | JavaScript functionality | All interactions work | ⏳ | |
| 20.4 | CSS styling | Correct appearance | ⏳ | |
| 20.5 | WebRTC features | Voice features work | ⏳ | |

#### Firefox Testing
| Step | Feature | Expected Result | Status | Notes |
|------|---------|-----------------|--------|-------|
| 21.1 | Page loading | All pages load correctly | ⏳ | |
| 21.2 | Form submission | All forms work | ⏳ | |
| 21.3 | JavaScript functionality | All interactions work | ⏳ | |
| 21.4 | CSS styling | Correct appearance | ⏳ | |
| 21.5 | WebRTC features | Voice features work | ⏳ | |

#### Safari Testing
| Step | Feature | Expected Result | Status | Notes |
|------|---------|-----------------|--------|-------|
| 22.1 | Page loading | All pages load correctly | ⏳ | |
| 22.2 | Form submission | All forms work | ⏳ | |
| 22.3 | JavaScript functionality | All interactions work | ⏳ | |
| 22.4 | CSS styling | Correct appearance | ⏳ | |
| 22.5 | WebRTC features | Voice features work | ⏳ | |

#### Edge Testing
| Step | Feature | Expected Result | Status | Notes |
|------|---------|-----------------|--------|-------|
| 23.1 | Page loading | All pages load correctly | ⏳ | |
| 23.2 | Form submission | All forms work | ⏳ | |
| 23.3 | JavaScript functionality | All interactions work | ⏳ | |
| 23.4 | CSS styling | Correct appearance | ⏳ | |
| 23.5 | WebRTC features | Voice features work | ⏳ | |

## Mobile and Responsive Testing Checklists

### 16. Mobile Device Testing

#### Mobile Functionality Testing
| Step | Action | Expected Result | Priority | Status | Notes |
|------|--------|-----------------|----------|--------|-------|
| 24.1 | Load on mobile device | All pages load correctly | 🔴 | ⏳ | |
| 24.2 | Test touch interactions | All buttons respond to touch | 🔴 | ⏳ | |
| 24.3 | Test form input | Virtual keyboard works properly | 🔴 | ⏳ | |
| 24.4 | Test navigation | Mobile menu works | 🔴 | ⏳ | |
| 24.5 | Test scrolling | Smooth scrolling on all pages | 🔴 | ⏳ | |
| 24.6 | Test orientation change | Layout adapts to rotation | 🟡 | ⏳ | |

### 17. Tablet Testing

#### Tablet Functionality Testing
| Step | Action | Expected Result | Priority | Status | Notes |
|------|--------|-----------------|----------|--------|-------|
| 25.1 | Load on tablet | Optimized layout displays | 🔴 | ⏳ | |
| 25.2 | Test touch targets | Buttons are appropriately sized | 🔴 | ⏳ | |
| 25.3 | Test two-column layouts | Content displays properly | 🟡 | ⏳ | |
| 25.4 | Test modal sizing | Modals are appropriately sized | 🟡 | ⏳ | |

## Security Testing Checklists

### 18. Authentication Security

#### Security Testing
| Step | Action | Expected Result | Priority | Status | Notes |
|------|--------|-----------------|----------|--------|-------|
| 26.1 | Test password strength | Weak passwords rejected | 🔴 | ⏳ | |
| 26.2 | Test session management | Sessions expire appropriately | 🔴 | ⏳ | |
| 26.3 | Test auto logout | Logout after inactivity | 🟡 | ⏳ | |
| 26.4 | Test CSRF protection | Forms protected from CSRF | 🔴 | ⏳ | |
| 26.5 | Test input sanitization | XSS attacks prevented | 🔴 | ⏳ | |
| 26.6 | Test SQL injection | SQL injection prevented | 🔴 | ⏳ | |

## Testing Completion Checklist

### Final Validation
- [ ] All critical path tests completed
- [ ] All high priority tests completed
- [ ] All medium priority tests completed
- [ ] All bugs documented and tracked
- [ ] Performance requirements met
- [ ] Accessibility standards met
- [ ] Browser compatibility verified
- [ ] Mobile responsiveness confirmed
- [ ] Security measures validated
- [ ] Integration points tested

### Sign-off Requirements
- [ ] Test execution completed
- [ ] Bug reports filed
- [ ] Test results documented
- [ ] Stakeholder approval obtained
- [ ] Production deployment approved

---

**Note**: This checklist should be used systematically, with each test step completed before moving to the next. Update the status column as tests are completed, and document any issues in the notes column.