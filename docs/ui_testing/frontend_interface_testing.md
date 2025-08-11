# Frontend Interface Testing Documentation

## Overview

This document provides comprehensive testing specifications for all frontend interface components of the NIA Sales Assistant application. It covers every page, button, form, and interactive element with detailed expected behaviors and test scenarios.

## Main Application Views

### 1. Header Navigation

#### Logo Section
- **Element**: Logo image and text
- **Location**: Top-left of header
- **Expected Behavior**: 
  - Logo image displays NIA logo (40px height, rounded corners)
  - Logo text displays "NIA" in primary blue color
  - No click action defined (static display)

#### Navigation Menu
- **Elements**: Four navigation links
- **Location**: Top-right of header
- **Links**:
  1. **Leads** (`data-view="leads"`)
     - **Click Action**: Shows leads view, adds 'active' class
     - **Visual State**: Blue text when active, gray when inactive
  2. **Create Lead** (`data-view="create"`)
     - **Click Action**: Shows create lead form view
     - **Visual State**: Blue text when active, gray when inactive
  3. **Analytics** (`data-view="analytics"`)
     - **Click Action**: Shows analytics dashboard view
     - **Visual State**: Blue text when active, gray when inactive
  4. **Smart Chat** (`data-view="chat"`)
     - **Click Action**: Shows chat interface view
     - **Visual State**: Blue text when active, gray when inactive

### 2. Welcome Section

#### Welcome Content
- **Element**: Welcome banner with logo and text
- **Location**: Top of main container
- **Content**:
  - Large NIA logo image
  - "Welcome to NIA" heading
  - "Neural Intelligence Assistant - Your AI-Powered Sales Companion" subtitle
  - "Transform your sales conversations into actionable insights with advanced AI analysis" description
- **Expected Behavior**: Static display, no interactive elements

## Leads View (`#leads-view`)

### Search and Filter Controls

#### Search Box
- **Element**: Text input with search icon
- **ID**: `lead-search`
- **Placeholder**: "Search leads by company, contact, or email..."
- **Event**: `onkeyup="handleLeadSearch()"`
- **Expected Behavior**:
  - Real-time search as user types
  - Filters leads by company name, contact name, or email
  - Search icon (🔍) displays on right side
  - Case-insensitive search

#### Filter Controls
1. **Status Filter**
   - **Element**: Select dropdown
   - **ID**: `status-filter`
   - **Event**: `onchange="handleFilterChange()"`
   - **Options**: All Statuses, New, Contacted, Qualified, Converted, Lost
   - **Expected Behavior**: Filters leads by selected status

2. **Score Filter**
   - **Element**: Select dropdown
   - **ID**: `score-filter`
   - **Event**: `onchange="handleFilterChange()"`
   - **Options**: All Scores, High Score (70%+), Medium Score (40-69%), Low Score (<40%)
   - **Expected Behavior**: Filters leads by score range

3. **Sort By**
   - **Element**: Select dropdown
   - **ID**: `sort-by`
   - **Event**: `onchange="handleSortChange()"`
   - **Options**: Sort by Date, Sort by Score, Sort by Company, Sort by Status
   - **Expected Behavior**: Sorts leads by selected criteria

### Action Buttons

#### Create New Lead Button
- **Element**: Primary button with plus icon
- **Text**: "+ Create New Lead"
- **Event**: `onclick="showCreateForm()"`
- **Expected Behavior**: 
  - Switches to create lead view
  - Hides leads view, shows create view
  - Updates navigation state

#### Refresh Button
- **Element**: Outline button with refresh icon
- **Text**: "↻ Refresh"
- **Event**: `onclick="refreshLeads()"`
- **Expected Behavior**:
  - Reloads leads from API
  - Shows loading indicator during refresh
  - Updates leads list with fresh data

#### Export Button
- **Element**: Outline button with chart icon
- **Text**: "📊 Export"
- **Event**: `onclick="exportLeads()"`
- **Expected Behavior**:
  - Generates CSV file of current filtered leads
  - Downloads file named "leads-export.csv"
  - Shows warning if no leads to export

#### View Mode Toggle Button
- **Element**: Outline button with dynamic icon/text
- **ID**: `view-mode-icon` and `view-mode-text`
- **Event**: `onclick="toggleViewMode()"`
- **Expected Behavior**:
  - Toggles between "List View" and "Grid View"
  - Icon changes between 📋 and 📊
  - Updates leads display layout

### Leads List Display

#### Loading State
- **Element**: Loading spinner with text
- **ID**: `leads-loading`
- **Class**: `loading hidden` (initially hidden)
- **Expected Behavior**:
  - Shows during API calls
  - Displays spinner animation
  - Text: "Loading leads..."

#### Leads Container
- **Element**: Container for lead cards/list items
- **ID**: `leads-list`
- **Expected Behavior**:
  - Displays filtered and sorted leads
  - Shows "No leads found" message when empty
  - Responsive grid/list layout based on view mode

## Create Lead View (`#create-view`)

### Main Form

#### Conversation Text Area
- **Element**: Large textarea
- **ID**: `conversation-text`
- **Placeholder**: "Paste your conversation transcript or notes here. NIA will analyze this to extract lead information and provide recommendations..."
- **Attributes**: `rows="8"`, `required`
- **Expected Behavior**:
  - Required field validation
  - Accepts multi-line text input
  - Used for AI analysis

#### Lead Source Dropdown
- **Element**: Select dropdown
- **ID**: `lead-source`
- **Options**: Select source..., Phone Call, Email, Meeting, Website, Referral, Other
- **Expected Behavior**:
  - Optional field
  - Used to categorize lead origin

#### Urgency Level Dropdown
- **Element**: Select dropdown
- **ID**: `urgency`
- **Options**: Auto-detect, High, Medium, Low
- **Expected Behavior**:
  - Optional field
  - Defaults to "Auto-detect" for AI determination

### Action Buttons

#### Analyze & Create Lead Button
- **Element**: Primary submit button
- **Text**: "🤖 Analyze & Create Lead"
- **Type**: `submit`
- **Expected Behavior**:
  - Validates required fields
  - Shows loading indicator
  - Calls AI analysis API
  - Creates lead if successful
  - Shows analysis results

#### Test API Button
- **Element**: Secondary button
- **Text**: "🔧 Test API"
- **Event**: `onclick="testAPIConnection()"`
- **Expected Behavior**:
  - Tests API connectivity
  - Shows success/error alert
  - Logs results to console

#### Cancel Button
- **Element**: Outline button
- **Text**: "Cancel"
- **Event**: `onclick="showLeadsView()"`
- **Expected Behavior**:
  - Returns to leads view without saving
  - Clears form data

### Loading Indicator
- **Element**: Loading spinner with text
- **ID**: `create-loading`
- **Style**: `display: none` (initially hidden)
- **Expected Behavior**:
  - Shows during form submission
  - Text: "Analyzing conversation and creating lead..."

### Analysis Results Section
- **Element**: Collapsible results card
- **ID**: `analysis-results`
- **Class**: `hidden mt-4` (initially hidden)
- **Expected Behavior**:
  - Shows after successful analysis
  - Displays extracted lead information
  - Shows AI analysis summary
  - Provides confirmation buttons

#### Analysis Results Buttons
1. **Create Lead Button**
   - **Text**: "✓ Create Lead"
   - **Event**: `onclick="confirmCreateLead()"`
   - **Expected Behavior**: Confirms lead creation with analyzed data

2. **Edit Conversation Button**
   - **Text**: "Edit Conversation"
   - **Event**: `onclick="hideAnalysisResults()"`
   - **Expected Behavior**: Hides results, allows editing conversation text

## Lead Detail View (`#detail-view`)

### Header Section

#### Lead Title and Status
- **Element**: Company name heading with status badge
- **ID**: `detail-company-name`, `detail-status-badge`
- **Expected Behavior**:
  - Displays lead company name
  - Shows colored status badge (new, contacted, qualified, etc.)

#### Action Buttons
1. **Edit Button**
   - **Text**: "✏️ Edit"
   - **Event**: `onclick="editLead()"`
   - **Expected Behavior**: Opens edit modal for lead

2. **Convert Button**
   - **Text**: "🎯 Convert"
   - **Event**: `onclick="convertToOpportunity()"`
   - **Expected Behavior**: Converts lead to opportunity

3. **Refresh AI Button**
   - **Text**: "🔄 Refresh AI"
   - **Event**: `onclick="refreshInsights()"`
   - **Expected Behavior**: Regenerates AI insights

4. **Back Button**
   - **Text**: "← Back"
   - **Event**: `onclick="showLeadsView()"`
   - **Expected Behavior**: Returns to leads list view

### Overview Cards
- **Elements**: Four overview cards displaying key metrics
- **IDs**: `detail-lead-score`, `detail-last-contact`, `detail-source`, `detail-next-action`
- **Expected Behavior**: Display lead score, last contact date, source, and recommended next action

### Tabbed Content

#### Tab Navigation
- **Elements**: Four tab buttons
- **Expected Behavior**:
  - Only one tab active at a time
  - Active tab has 'active' class
  - Clicking tab shows corresponding content

1. **Lead Information Tab**
   - **Text**: "📋 Lead Information"
   - **Event**: `onclick="showDetailTab('info')"`
   - **Content**: Company info, contact info, requirements, budget/timeline

2. **Conversation History Tab**
   - **Text**: "💬 Conversation History"
   - **Event**: `onclick="showDetailTab('conversation')"`
   - **Content**: Conversation timeline with add note button

3. **AI Insights Tab**
   - **Text**: "🤖 AI Insights"
   - **Event**: `onclick="showDetailTab('insights')"`
   - **Content**: AI-generated insights with loading state

4. **Activity Timeline Tab**
   - **Text**: "📈 Activity Timeline"
   - **Event**: `onclick="showDetailTab('activity')"`
   - **Content**: Chronological activity history

## Analytics View (`#analytics-view`)

### Analytics Cards
- **Elements**: Three metric cards in grid layout
- **Expected Behavior**: Display key performance indicators

1. **Total Leads Card**
   - **ID**: `total-leads`
   - **Display**: Large number in primary color
   - **Expected Behavior**: Shows total lead count

2. **High Quality Leads Card**
   - **ID**: `high-quality-leads`
   - **Display**: Large number in success color
   - **Expected Behavior**: Shows count of high-scoring leads

3. **Average Lead Score Card**
   - **ID**: `avg-lead-score`
   - **Display**: Large number in warning color
   - **Expected Behavior**: Shows average lead score percentage

## Smart Chat View (`#chat-view`)

### Chat Header

#### Chat Title and Status
- **Element**: Title with connection status
- **Expected Behavior**:
  - Shows "Smart Chat with NIA" title
  - Displays connection status (Connected/Disconnected)
  - Shows availability toggle for voice calls

#### Availability Control
- **Element**: Toggle switch with label
- **ID**: `availability-toggle`
- **Expected Behavior**:
  - Toggles between "Available for voice calls" and "Chat only"
  - Updates server availability status
  - Changes visual indicator

#### Chat Action Buttons
1. **Voice Call Button**
   - **ID**: `voice-transition-btn`
   - **Text**: "🎤 Voice Call"
   - **Expected Behavior**: Initiates voice call transition

2. **Search Button**
   - **ID**: `search-toggle-btn`
   - **Text**: "🔍 Search"
   - **Expected Behavior**: Toggles search panel visibility

3. **End Chat Button**
   - **ID**: `end-chat-btn`
   - **Text**: "❌ End Chat"
   - **Expected Behavior**: Ends current chat session

### Chat Messages Area

#### Messages Container
- **Element**: Scrollable messages container
- **ID**: `chat-messages`
- **Expected Behavior**:
  - Displays chat messages chronologically
  - Auto-scrolls to bottom on new messages
  - Shows message status indicators

#### Typing Indicator
- **Element**: Typing status display
- **ID**: `typing-indicator`
- **Style**: `display: none` (initially hidden)
- **Expected Behavior**:
  - Shows "NIA is typing..." when bot is responding
  - Hides when typing stops

### Chat Sidebar

#### Search Panel
- **Element**: Collapsible search panel
- **ID**: `search-panel`
- **Class**: `sidebar-panel hidden` (initially hidden)
- **Components**:
  - Search input field
  - Search button
  - Results container
- **Expected Behavior**:
  - Searches chat history
  - Displays results with highlighting
  - Allows navigation to specific messages

#### Quick Commands Panel
- **Element**: Bot commands reference
- **ID**: `command-suggestions`
- **Expected Behavior**:
  - Shows available bot commands
  - Displays command help and usage
  - Allows clicking to insert commands

#### File Sharing Panel
- **Element**: File upload interface
- **Components**:
  - File input (hidden)
  - Upload label/button
  - Uploaded files display
- **Expected Behavior**:
  - Accepts file uploads up to 10MB
  - Shows upload progress
  - Displays uploaded files list

### Chat Input

#### Message Input Area
- **Element**: Expandable textarea
- **ID**: `chat-input`
- **Placeholder**: "Type your message... (Use / for commands)"
- **Attributes**: `rows="1"`
- **Expected Behavior**:
  - Expands as user types
  - Supports Enter to send (Shift+Enter for new line)
  - Shows command suggestions when typing "/"

#### Input Action Buttons
1. **Emoji Button**
   - **ID**: `emoji-btn`
   - **Text**: "😊"
   - **Expected Behavior**: Opens emoji picker (not implemented)

2. **Attach Button**
   - **ID**: `attach-btn`
   - **Text**: "📎"
   - **Event**: `onclick="document.getElementById('file-input').click()"`
   - **Expected Behavior**: Opens file picker

3. **Send Button**
   - **ID**: `send-button`
   - **Text**: "Send"
   - **Expected Behavior**: Sends message, clears input

### Chat Session Controls
- **Elements**: Three control buttons below chat
- **Expected Behavior**:
  1. **New Chat Session**: Creates new chat session
  2. **Chat History**: Shows previous chat sessions
  3. **Chat Analytics**: Shows chat usage analytics

## Modal Dialogs

### Voice Transition Modal
- **Element**: Modal dialog for voice call transition
- **ID**: `voice-transition-modal`
- **Class**: `voice-transition-modal hidden` (initially hidden)
- **Components**:
  - Title: "Voice Call Ready"
  - Description text
  - Join Voice Call button
  - Cancel button
- **Expected Behavior**:
  - Shows when voice call is ready
  - Join button opens voice call in new window
  - Cancel button closes modal

### Lead Edit Modal
- **Element**: Modal dialog for editing leads
- **ID**: `edit-modal`
- **Class**: `modal hidden` (initially hidden)
- **Components**:
  - Modal header with title and close button
  - Edit form with lead fields
  - Save and cancel buttons
- **Expected Behavior**:
  - Populates form with current lead data
  - Validates form on submission
  - Updates lead and closes modal on success

## Global UI Elements

### Alert Container
- **Element**: Container for system alerts
- **ID**: `alert-container`
- **Expected Behavior**:
  - Shows success, error, warning, and info messages
  - Auto-dismisses after 5 seconds
  - Allows manual dismissal with close button

### Loading States
- **Elements**: Various loading indicators throughout app
- **Expected Behavior**:
  - Shows spinner animation
  - Displays relevant loading text
  - Blocks user interaction during loading

## Responsive Design Behavior

### Mobile Breakpoints
- **Small screens (< 768px)**:
  - Navigation collapses to hamburger menu
  - Cards stack vertically
  - Reduced padding and margins
  - Touch-friendly button sizes

### Tablet Breakpoints
- **Medium screens (768px - 1024px)**:
  - Two-column grid layouts
  - Adjusted sidebar widths
  - Optimized touch targets

### Desktop Breakpoints
- **Large screens (> 1024px)**:
  - Full multi-column layouts
  - Hover effects enabled
  - Maximum content width of 1200px

## Form Validation Behaviors

### Required Field Validation
- **Visual Indicators**: Red border on invalid fields
- **Error Messages**: Display below invalid fields
- **Submission Blocking**: Prevents form submission until valid

### Real-time Validation
- **Email Fields**: Validates email format on blur
- **Phone Fields**: Formats phone numbers automatically
- **Text Fields**: Shows character count for limited fields

## Error Handling

### Network Errors
- **Behavior**: Shows "Connection error" alert
- **Retry**: Provides retry button for failed requests
- **Offline**: Shows offline indicator when disconnected

### Validation Errors
- **Behavior**: Highlights invalid fields
- **Messages**: Shows specific error messages
- **Focus**: Focuses first invalid field

### Server Errors
- **Behavior**: Shows user-friendly error messages
- **Logging**: Logs detailed errors to console
- **Recovery**: Provides recovery options when possible

## Accessibility Features

### Keyboard Navigation
- **Tab Order**: Logical tab sequence through interactive elements
- **Focus Indicators**: Visible focus outlines on all interactive elements
- **Keyboard Shortcuts**: Enter to submit forms, Escape to close modals

### Screen Reader Support
- **ARIA Labels**: Descriptive labels for all interactive elements
- **Role Attributes**: Proper semantic roles for complex widgets
- **Live Regions**: Announcements for dynamic content changes

### Color and Contrast
- **High Contrast**: Meets WCAG AA contrast requirements
- **Color Independence**: Information not conveyed by color alone
- **Focus Indicators**: High contrast focus outlines

This documentation provides comprehensive testing specifications for every frontend interface component in the NIA Sales Assistant application.