# Interactive Element Specifications

## Overview

This document provides detailed specifications for all interactive elements in the NIA Sales Assistant application, including form validation behaviors, hover effects, disabled states, loading animations, modal dialogs, popup interactions, and notification systems.

## Form Validation Behaviors

### Input Field Validation

#### Text Input Fields
- **Element**: `.form-input`
- **Focus State**:
  - Border color changes to `--primary-color` (#2563eb)
  - Box shadow: `0 0 0 3px rgba(37, 99, 235, 0.1)`
  - Outline removed
  - Transition duration: 0.2s
- **Invalid State**:
  - Border color: `--danger-color` (#dc2626)
  - Background: light red tint
  - Error message appears below field
- **Valid State**:
  - Border color: `--success-color` (#059669)
  - Checkmark icon may appear
- **Disabled State**:
  - Background: `#f3f4f6`
  - Border color: `#d1d5db`
  - Text color: `#9ca3af`
  - Cursor: `not-allowed`

#### Email Field Validation
- **Element**: Email input fields
- **Real-time Validation**: Validates on blur event
- **Invalid Email Format**:
  - Shows error: "Enter a valid email address"
  - Red border and error styling
- **Valid Email**:
  - Green border confirmation
  - No error message

#### Phone Field Validation
- **Element**: Phone input fields
- **Auto-formatting**: Formats as user types
- **Pattern**: (XXX) XXX-XXXX format
- **Invalid Format**:
  - Shows error: "Enter a valid phone number"
  - Red border styling

#### Required Field Validation
- **Visual Indicator**: Red asterisk (*) next to label
- **Empty Required Field**:
  - Red border on form submission attempt
  - Error message: "This field is required"
  - Focus automatically moves to first invalid field
- **Form Submission Blocking**: Prevents submission until all required fields are valid

### Textarea Validation

#### Conversation Text Area
- **Element**: `#conversation-text`
- **Focus Behavior**:
  - Expands from 120px to 150px minimum height
  - Border and shadow effects same as input fields
- **Character Limit**: If implemented, shows counter
- **Required Validation**: Shows error if empty on submission

### Select Dropdown Validation
- **Element**: `.form-select`
- **Focus State**: Same border and shadow effects as inputs
- **Invalid Selection**: Red border if required and not selected
- **Placeholder Option**: Grayed out and not selectable after initial selection

## Button States and Interactions

### Primary Buttons
- **Element**: `.btn-primary`
- **Default State**:
  - Background: `--primary-color` (#2563eb)
  - Color: white
  - Padding: 0.75rem 1.5rem
  - Border radius: 6px
- **Hover State**:
  - Background: `--primary-hover` (#1d4ed8)
  - Cursor: pointer
  - Transition: all 0.2s
  - Slight shadow increase
- **Active State**:
  - Background: darker blue
  - Transform: translateY(1px)
- **Disabled State**:
  - Background: `#9ca3af`
  - Cursor: not-allowed
  - No hover effects
  - Opacity: 0.6

### Secondary Buttons
- **Element**: `.btn-secondary`
- **Default State**: Background: `--secondary-color` (#64748b)
- **Hover State**: Background: darker gray
- **States**: Same pattern as primary buttons

### Outline Buttons
- **Element**: `.btn-outline`
- **Default State**:
  - Background: transparent
  - Border: 1px solid `--border-color`
  - Color: `--text-primary`
- **Hover State**:
  - Background: `--light-bg` (#f8fafc)
  - Border color: `--primary-color`
- **Active State**: Slight background darkening

### Button Sizes
- **Small**: `.btn-sm` - Padding: 0.5rem 1rem, Font: 0.75rem
- **Regular**: Default sizing
- **Large**: `.btn-lg` - Padding: 1rem 2rem, Font: 1rem

### Icon Buttons
- **Chat Actions**: Emoji, attach, send buttons
- **Hover State**: Background color change
- **Active State**: Slight scale transform
- **Disabled State**: Grayed out, no interactions

## Loading States and Animations

### Global Loading Spinner
- **Element**: `.spinner`
- **Animation**: Continuous rotation (360deg in 1s)
- **Size**: 20px diameter
- **Colors**: Border: `--border-color`, Top: `--primary-color`
- **Minimum Display**: 300ms to prevent flashing
- **Maximum Display**: 30s before timeout

### Component-Specific Loading States

#### Leads Loading
- **Element**: `#leads-loading`
- **Display**: Flex center alignment
- **Content**: Spinner + "Loading leads..." text
- **Behavior**: Blocks interaction with leads list
- **Height**: Minimum 200px

#### Create Lead Loading
- **Element**: `#create-loading`
- **Text**: "Analyzing conversation and creating lead..."
- **Behavior**: 
  - Disables form submission button
  - Shows progress indication
  - Prevents form interaction

#### Analysis Loading
- **Element**: `#insights-loading`
- **Text**: "Generating AI insights..."
- **Location**: AI insights tab
- **Behavior**: Shows during AI processing

#### Chat Typing Indicator
- **Element**: `#typing-indicator`
- **Animation**: Pulse effect (opacity 0.5 to 1)
- **Text**: "NIA is typing..."
- **Duration**: Shows during bot response generation

### Loading Animation Specifications
```css
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

@keyframes pulse {
    0%, 100% { opacity: 0.5; }
    50% { opacity: 1; }
}
```

## Hover Effects

### Card Hover Effects

#### Lead Cards
- **Element**: `.lead-card`
- **Default State**: Box shadow: `--shadow`
- **Hover State**:
  - Transform: `translateY(-4px)`
  - Box shadow: `--shadow-lg`
  - Border color: `--primary-color`
  - Transition: all 0.2s
- **Cursor**: pointer

#### Lead List Items
- **Element**: `.lead-item`
- **Hover State**:
  - Transform: `translateY(-2px)`
  - Box shadow increase
  - Border color change to primary

### Navigation Hover Effects

#### Nav Links
- **Element**: `.nav-link`
- **Default State**: Color: `--text-secondary`
- **Hover State**: Color: `--primary-color`
- **Active State**: Color: `--primary-color` (persistent)
- **Transition**: color 0.2s

#### Tab Buttons
- **Element**: `.tab-button`
- **Default State**: Color: `--text-secondary`
- **Hover State**:
  - Color: `--primary-color`
  - Background: `--light-bg`
- **Active State**:
  - Color: `--primary-color`
  - Border bottom: 2px solid `--primary-color`
  - Background: `--light-bg`

### Interactive Element Hover Effects

#### Form Elements
- **Inputs/Textareas**: No hover effect, focus effect only
- **Select Dropdowns**: Slight border color change on hover
- **Buttons**: Background color changes as specified above

#### Search Results
- **Element**: `.search-result`
- **Hover State**:
  - Background: `--light-bg`
  - Border color: `--primary-color`
  - Cursor: pointer

## Disabled States

### Form Element Disabled States

#### Disabled Inputs
- **Visual**: 
  - Background: `#f3f4f6`
  - Border: `#d1d5db`
  - Text color: `#9ca3af`
  - Cursor: `not-allowed`
- **Behavior**: No focus, no interaction, no validation

#### Disabled Buttons
- **Visual**:
  - Background: `#9ca3af`
  - Color: white with reduced opacity
  - Cursor: `not-allowed`
  - Opacity: 0.6
- **Behavior**: No click events, no hover effects

#### Disabled Select Dropdowns
- **Visual**: Same as disabled inputs
- **Behavior**: Cannot open dropdown, no selection possible

### Conditional Disabled States

#### Form Submission During Loading
- **Trigger**: When form is being submitted
- **Effect**: All form elements become disabled
- **Visual**: Loading spinner replaces submit button text
- **Duration**: Until response received or timeout

#### Chat Input During Connection Issues
- **Trigger**: When WebSocket disconnected
- **Effect**: Chat input and send button disabled
- **Visual**: Grayed out with "Reconnecting..." placeholder
- **Recovery**: Re-enabled when connection restored

## Modal Dialog Behaviors

### Modal Structure
- **Container**: `.modal` - Full screen overlay
- **Content**: `.modal-content` - Centered dialog box
- **Backdrop**: Semi-transparent black (rgba(0, 0, 0, 0.5))

### Modal Opening Animation
- **Effect**: Fade in backdrop, scale in content
- **Duration**: 0.3s ease-out
- **Initial State**: opacity: 0, transform: scale(0.9)
- **Final State**: opacity: 1, transform: scale(1)

### Modal Closing Behaviors
- **Close Button**: X button in top-right corner
- **Backdrop Click**: Clicking outside content area closes modal
- **Escape Key**: ESC key closes modal
- **Form Submission**: Modal closes on successful form submission

### Modal Types

#### Lead Edit Modal
- **Element**: `#edit-modal`
- **Content**: Lead editing form
- **Size**: Max-width 600px, 90% viewport width
- **Scrolling**: Vertical scroll if content exceeds viewport height

#### Voice Transition Modal
- **Element**: `#voice-transition-modal`
- **Content**: Voice call preparation interface
- **Actions**: Join call button, cancel button
- **Auto-close**: Closes when voice call initiated

### Modal Accessibility
- **Focus Management**: Focus moves to modal when opened
- **Tab Trapping**: Tab key cycles within modal content
- **Screen Reader**: Proper ARIA labels and roles
- **Focus Return**: Focus returns to trigger element when closed

## Popup Interactions

### Dropdown Menus
- **Trigger**: Click on dropdown button/select
- **Animation**: Slide down with fade in
- **Positioning**: Below trigger element, adjusts if near viewport edge
- **Closing**: Click outside, select option, or ESC key

### Tooltip Behaviors
- **Trigger**: Hover over elements with title attributes
- **Delay**: 500ms hover delay before showing
- **Positioning**: Above element, adjusts for viewport constraints
- **Content**: Title attribute text or custom content
- **Styling**: Dark background, white text, small arrow pointer

### Context Menus
- **Trigger**: Right-click on applicable elements
- **Content**: Contextual actions (Edit, Delete, etc.)
- **Positioning**: At cursor position
- **Closing**: Click outside, select action, or ESC key

## Notification Systems

### Alert Container
- **Element**: `#alert-container`
- **Position**: Fixed or absolute positioning for visibility
- **Stacking**: Multiple alerts stack vertically
- **Z-index**: High value to appear above other content

### Alert Types and Styling

#### Success Alerts
- **Class**: `.alert-success`
- **Background**: `#dcfce7` (light green)
- **Text Color**: `#166534` (dark green)
- **Border**: `1px solid #bbf7d0`
- **Icon**: ✓ checkmark (optional)

#### Error Alerts
- **Class**: `.alert-error`
- **Background**: `#fee2e2` (light red)
- **Text Color**: `#991b1b` (dark red)
- **Border**: `1px solid #fecaca`
- **Icon**: ❌ X mark (optional)

#### Warning Alerts
- **Class**: `.alert-warning`
- **Background**: `#fef3c7` (light yellow)
- **Text Color**: `#92400e` (dark orange)
- **Border**: `1px solid #fed7aa`
- **Icon**: ⚠️ warning triangle (optional)

#### Info Alerts
- **Class**: `.alert-info`
- **Background**: Light blue
- **Text Color**: Dark blue
- **Border**: Blue border
- **Icon**: ℹ️ info circle (optional)

### Alert Behaviors

#### Auto-Dismiss
- **Duration**: 5 seconds for most alerts
- **Exception**: Error alerts may persist longer
- **Visual**: Progress bar or fade-out animation

#### Manual Dismiss
- **Close Button**: X button in top-right corner
- **Click to Dismiss**: Entire alert clickable to dismiss
- **Keyboard**: ESC key dismisses focused alert

#### Alert Animation
- **Entry**: Slide in from right with fade
- **Exit**: Fade out with slide up
- **Duration**: 0.3s ease-out

```css
@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}
```

### Toast Notifications
- **Position**: Top-right corner of viewport
- **Stacking**: New toasts appear above existing ones
- **Max Count**: Limit to 5 visible toasts
- **Overflow**: Oldest toasts auto-dismiss when limit reached

## Real-time Update Animations

### Live Data Updates

#### New Lead Animation
- **Trigger**: New lead received via WebSocket/SSE
- **Effect**: Slide in from top of leads list
- **Highlight**: Brief background color flash
- **Duration**: 0.5s animation

#### Lead Status Change
- **Trigger**: Lead status updated
- **Effect**: Status badge color change with pulse animation
- **Duration**: 0.3s transition

#### Message Arrival Animation
- **Trigger**: New chat message received
- **Effect**: Slide in from bottom with fade
- **Sound**: Optional notification sound
- **Scroll**: Auto-scroll to new message

### Connection Status Indicators

#### WebSocket Connection
- **Connected**: Green dot with "Connected" text
- **Disconnected**: Red dot with "Disconnected" text
- **Connecting**: Yellow dot with pulse animation
- **Animation**: Smooth color transitions

#### Real-time Data Sync
- **Syncing**: Rotating sync icon
- **Synced**: Checkmark with brief flash
- **Error**: Warning icon with error color

## Responsive Interaction Behaviors

### Mobile Touch Interactions

#### Touch Targets
- **Minimum Size**: 44px x 44px for touch elements
- **Spacing**: 8px minimum between touch targets
- **Feedback**: Brief highlight on touch

#### Swipe Gestures
- **Lead Cards**: Swipe left for actions menu
- **Chat Messages**: Swipe for reply/react options
- **Modal Dismiss**: Swipe down to close

#### Long Press Actions
- **Lead Items**: Long press for context menu
- **Chat Messages**: Long press for message options
- **Duration**: 500ms press duration

### Tablet Interactions
- **Hover Simulation**: Touch and hold for hover effects
- **Right Click**: Two-finger tap for context menus
- **Drag and Drop**: Touch drag for reordering items

### Desktop Keyboard Interactions

#### Tab Navigation
- **Order**: Logical tab sequence through interactive elements
- **Visual**: Clear focus indicators on all elements
- **Skip Links**: Skip to main content option

#### Keyboard Shortcuts
- **Form Submission**: Enter key submits forms
- **Modal Close**: ESC key closes modals
- **Search**: Ctrl+F for search functionality
- **Navigation**: Arrow keys for tab navigation

## Performance Considerations

### Animation Performance
- **Hardware Acceleration**: Use transform and opacity for animations
- **Frame Rate**: Target 60fps for smooth animations
- **Reduced Motion**: Respect user's reduced motion preferences

### Interaction Debouncing
- **Search Input**: 300ms debounce on keyup
- **Resize Events**: 100ms debounce on window resize
- **Scroll Events**: RequestAnimationFrame for scroll handlers

### Memory Management
- **Event Listeners**: Proper cleanup on component unmount
- **Timers**: Clear timeouts and intervals
- **WebSocket**: Close connections when not needed

## Testing Checklist

### Form Validation Testing
- [ ] All required fields show validation errors
- [ ] Email fields validate format correctly
- [ ] Phone fields format automatically
- [ ] Form submission blocked with invalid data
- [ ] Success states show after valid submission
- [ ] Error messages are clear and helpful

### Interactive State Testing
- [ ] All buttons show hover effects
- [ ] Disabled states prevent interaction
- [ ] Loading states show during operations
- [ ] Focus states are visible and logical
- [ ] Keyboard navigation works properly

### Animation Testing
- [ ] Loading spinners animate smoothly
- [ ] Modal open/close animations work
- [ ] Card hover effects are smooth
- [ ] Real-time updates animate properly
- [ ] Reduced motion preferences respected

### Responsive Testing
- [ ] Touch targets are appropriately sized
- [ ] Hover effects work on touch devices
- [ ] Keyboard navigation works on all devices
- [ ] Animations perform well on all devices
- [ ] Interactive elements scale properly

### Accessibility Testing
- [ ] All interactive elements have focus indicators
- [ ] Screen readers can access all functionality
- [ ] Color contrast meets WCAG standards
- [ ] Keyboard-only navigation is possible
- [ ] Error messages are announced properly

This comprehensive specification ensures all interactive elements in the NIA Sales Assistant provide consistent, accessible, and performant user experiences across all devices and interaction methods.