# UI Component Test Templates - NIA Sales Assistant

## Overview
This document provides reusable test templates for common UI components and patterns. These templates can be applied to any similar component throughout the application to ensure consistent testing coverage.

## Template Usage Instructions

### How to Use These Templates
1. **Copy the relevant template** for the component type you're testing
2. **Fill in the specific details** for your component (IDs, text, expected behaviors)
3. **Execute each test step** systematically
4. **Document results** using the provided status indicators
5. **Report any deviations** from expected behavior

### Status Indicators
- ⏳ = **Pending Test** (Not yet tested)
- ✅ = **Test Passed** (Works as expected)
- ❌ = **Test Failed** (Bug found, needs fixing)
- ⚠️ = **Test Needs Review** (Unclear behavior, needs clarification)
- 🔄 = **Retest Required** (Fixed, needs retesting)

## Button Component Test Template

### Basic Button Testing Template
Use this template for any clickable button in the application.

#### Component Information
- **Component Type**: Button
- **Component ID**: `[BUTTON_ID]`
- **Button Text**: `[BUTTON_TEXT]`
- **Button Type**: `[primary|secondary|outline|danger]`
- **Location**: `[PAGE/SECTION]`

#### Visual Testing
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Display** | Load page containing button | Button visible with correct text | ⏳ | |
| **Styling** | Check button appearance | Correct colors, fonts, sizing | ⏳ | |
| **Hover State** | Hover mouse over button | Hover effect displays | ⏳ | |
| **Focus State** | Tab to button | Focus indicator visible | ⏳ | |
| **Disabled State** | If applicable, test disabled state | Button appears disabled and non-clickable | ⏳ | |

#### Functional Testing
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Click Action** | Click button | `[EXPECTED_ACTION]` | ⏳ | |
| **Keyboard Activation** | Press Enter/Space when focused | Same action as click | ⏳ | |
| **Double Click** | Double-click button | No unintended side effects | ⏳ | |
| **Loading State** | If applicable, test during loading | Loading indicator shows, button disabled | ⏳ | |

#### Responsive Testing
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Mobile View** | Resize to mobile width | Button remains usable and properly sized | ⏳ | |
| **Tablet View** | Resize to tablet width | Button displays appropriately | ⏳ | |
| **Touch Interaction** | On touch device, tap button | Button responds to touch | ⏳ | |

#### Accessibility Testing
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **ARIA Labels** | Check button attributes | Proper ARIA labels if needed | ⏳ | |
| **Screen Reader** | Test with screen reader | Button purpose clearly announced | ⏳ | |
| **Color Contrast** | Check text/background contrast | Meets WCAG AA standards | ⏳ | |

---

## Form Component Test Template

### Form Field Testing Template
Use this template for any form input field.

#### Component Information
- **Component Type**: Form Field
- **Field Type**: `[text|email|password|number|textarea|select]`
- **Field ID**: `[FIELD_ID]`
- **Field Label**: `[FIELD_LABEL]`
- **Required**: `[Yes/No]`
- **Location**: `[FORM_NAME/PAGE]`

#### Visual Testing
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Label Display** | Load form | Label text displays correctly | ⏳ | |
| **Placeholder Text** | Check input field | Placeholder text shows if applicable | ⏳ | |
| **Field Styling** | Check field appearance | Correct borders, fonts, sizing | ⏳ | |
| **Focus State** | Click or tab to field | Focus indicator visible | ⏳ | |
| **Error State** | Trigger validation error | Error styling applied | ⏳ | |

#### Functional Testing
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Text Input** | Type in field | Text appears correctly | ⏳ | |
| **Character Limits** | If applicable, test max length | Input stops at limit or shows warning | ⏳ | |
| **Clear Field** | Clear all text | Field empties completely | ⏳ | |
| **Copy/Paste** | Copy and paste text | Text pastes correctly | ⏳ | |

#### Validation Testing
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Required Field** | If required, submit empty | Validation error shows | ⏳ | |
| **Format Validation** | Enter invalid format | Format error shows | ⏳ | |
| **Real-time Validation** | Type invalid then valid data | Validation updates in real-time | ⏳ | |
| **Error Message** | Trigger error | Clear, helpful error message | ⏳ | |

#### Accessibility Testing
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Label Association** | Check label-input association | Label properly associated with input | ⏳ | |
| **Error Announcement** | Trigger error with screen reader | Error announced to screen reader | ⏳ | |
| **Required Indication** | Check required field indication | Required status clearly indicated | ⏳ | |

---

## Navigation Component Test Template

### Navigation Menu Testing Template
Use this template for any navigation menu or link collection.

#### Component Information
- **Component Type**: Navigation Menu
- **Menu Type**: `[header|sidebar|breadcrumb|tabs]`
- **Menu ID**: `[MENU_ID]`
- **Number of Items**: `[COUNT]`
- **Location**: `[PAGE/SECTION]`

#### Visual Testing
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Menu Display** | Load page | All menu items visible | ⏳ | |
| **Active State** | Check current page indicator | Active item highlighted | ⏳ | |
| **Hover Effects** | Hover over menu items | Hover effects display | ⏳ | |
| **Menu Alignment** | Check menu layout | Items properly aligned | ⏳ | |

#### Functional Testing
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Link Navigation** | Click each menu item | Navigate to correct page/section | ⏳ | |
| **Active State Update** | Navigate between pages | Active state updates correctly | ⏳ | |
| **External Links** | If applicable, test external links | Open in new tab/window | ⏳ | |

#### Responsive Testing
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Mobile Collapse** | Resize to mobile | Menu collapses to hamburger if applicable | ⏳ | |
| **Mobile Menu** | Open mobile menu | All items accessible | ⏳ | |
| **Touch Navigation** | On touch device, tap items | Items respond to touch | ⏳ | |

#### Accessibility Testing
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Keyboard Navigation** | Tab through menu items | All items reachable by keyboard | ⏳ | |
| **ARIA Roles** | Check navigation attributes | Proper ARIA roles applied | ⏳ | |
| **Screen Reader** | Test with screen reader | Navigation structure clear | ⏳ | |

---

## Modal Dialog Test Template

### Modal Component Testing Template
Use this template for any modal dialog or popup.

#### Component Information
- **Component Type**: Modal Dialog
- **Modal ID**: `[MODAL_ID]`
- **Modal Title**: `[MODAL_TITLE]`
- **Trigger Element**: `[TRIGGER_DESCRIPTION]`
- **Modal Type**: `[confirmation|form|information|warning]`

#### Opening/Closing Testing
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Modal Open** | Click trigger element | Modal opens and displays | ⏳ | |
| **Backdrop Display** | Check modal backdrop | Backdrop covers page content | ⏳ | |
| **Focus Management** | Modal opens | Focus moves to modal | ⏳ | |
| **Close Button** | Click X or close button | Modal closes | ⏳ | |
| **Backdrop Click** | Click outside modal | Modal closes (if applicable) | ⏳ | |
| **Escape Key** | Press Escape key | Modal closes | ⏳ | |

#### Content Testing
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Title Display** | Check modal header | Title displays correctly | ⏳ | |
| **Content Display** | Check modal body | All content visible and formatted | ⏳ | |
| **Button Actions** | Click modal buttons | Buttons perform expected actions | ⏳ | |
| **Form Functionality** | If form modal, test form | Form works as expected | ⏳ | |

#### Responsive Testing
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Mobile Display** | Open modal on mobile | Modal fits screen appropriately | ⏳ | |
| **Tablet Display** | Open modal on tablet | Modal displays properly | ⏳ | |
| **Scrolling** | If content is long, test scrolling | Content scrolls within modal | ⏳ | |

#### Accessibility Testing
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Focus Trap** | Tab through modal | Focus stays within modal | ⏳ | |
| **Focus Return** | Close modal | Focus returns to trigger element | ⏳ | |
| **ARIA Attributes** | Check modal attributes | Proper ARIA attributes applied | ⏳ | |
| **Screen Reader** | Test with screen reader | Modal purpose and content clear | ⏳ | |

---

## Table/List Component Test Template

### Data Table Testing Template
Use this template for any data table or list component.

#### Component Information
- **Component Type**: Data Table/List
- **Table ID**: `[TABLE_ID]`
- **Data Type**: `[DATA_DESCRIPTION]`
- **Number of Columns**: `[COUNT]`
- **Sortable**: `[Yes/No]`
- **Filterable**: `[Yes/No]`

#### Display Testing
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Table Load** | Load page with table | Table displays with data | ⏳ | |
| **Column Headers** | Check table headers | All headers display correctly | ⏳ | |
| **Data Display** | Check table rows | Data displays in correct columns | ⏳ | |
| **Empty State** | If no data, check display | "No data" message shows | ⏳ | |
| **Loading State** | During data load, check display | Loading indicator shows | ⏳ | |

#### Sorting Testing (if applicable)
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Sort Indicators** | Check sortable columns | Sort indicators visible | ⏳ | |
| **Ascending Sort** | Click column header | Data sorts ascending | ⏳ | |
| **Descending Sort** | Click header again | Data sorts descending | ⏳ | |
| **Sort Persistence** | Navigate away and back | Sort order maintained | ⏳ | |

#### Filtering Testing (if applicable)
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Filter Controls** | Check filter elements | Filters display correctly | ⏳ | |
| **Apply Filter** | Use filter controls | Data filters correctly | ⏳ | |
| **Clear Filter** | Clear filter | All data shows again | ⏳ | |
| **Multiple Filters** | Apply multiple filters | Filters work together | ⏳ | |

#### Pagination Testing (if applicable)
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Page Controls** | Check pagination controls | Controls display correctly | ⏳ | |
| **Next Page** | Click next page | Next set of data loads | ⏳ | |
| **Previous Page** | Click previous page | Previous data loads | ⏳ | |
| **Page Numbers** | Click specific page number | Correct page loads | ⏳ | |
| **Items Per Page** | Change items per page | Display updates correctly | ⏳ | |

#### Responsive Testing
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Mobile View** | Resize to mobile | Table adapts (scroll/stack/cards) | ⏳ | |
| **Tablet View** | Resize to tablet | Table displays appropriately | ⏳ | |
| **Horizontal Scroll** | If needed, test scrolling | Horizontal scroll works | ⏳ | |

#### Accessibility Testing
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Table Headers** | Check header markup | Proper th elements used | ⏳ | |
| **Row Navigation** | Tab through table | Logical tab order | ⏳ | |
| **Screen Reader** | Test with screen reader | Table structure announced | ⏳ | |
| **Sort Announcement** | Sort with screen reader | Sort changes announced | ⏳ | |

---

## Search Component Test Template

### Search Interface Testing Template
Use this template for any search functionality.

#### Component Information
- **Component Type**: Search Interface
- **Search ID**: `[SEARCH_ID]`
- **Search Type**: `[real-time|submit-based]`
- **Search Scope**: `[WHAT_IS_SEARCHED]`
- **Location**: `[PAGE/SECTION]`

#### Visual Testing
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Search Box Display** | Load page | Search box visible with placeholder | ⏳ | |
| **Search Icon** | Check search icon | Icon displays correctly | ⏳ | |
| **Clear Button** | If applicable, check clear button | Clear button shows when text entered | ⏳ | |

#### Functional Testing
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Text Input** | Type in search box | Text appears correctly | ⏳ | |
| **Search Execution** | Execute search | Search results display | ⏳ | |
| **Empty Search** | Search with empty query | Appropriate handling (all results or error) | ⏳ | |
| **No Results** | Search for non-existent item | "No results" message shows | ⏳ | |
| **Clear Search** | Clear search query | Results reset to default | ⏳ | |

#### Real-time Search Testing (if applicable)
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Typing Response** | Type characters | Results update as you type | ⏳ | |
| **Debouncing** | Type rapidly | Search waits for pause before executing | ⏳ | |
| **Loading Indicator** | During search | Loading indicator shows | ⏳ | |

#### Search Results Testing
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Results Display** | Execute search | Results display in expected format | ⏳ | |
| **Result Highlighting** | Check search term highlighting | Search terms highlighted in results | ⏳ | |
| **Result Actions** | Click on result | Appropriate action taken | ⏳ | |
| **Results Count** | Check results count | Accurate count displayed | ⏳ | |

#### Advanced Search Testing (if applicable)
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Filter Options** | Use search filters | Filters apply correctly | ⏳ | |
| **Sort Options** | Change result sorting | Results re-sort correctly | ⏳ | |
| **Search History** | Check search history | Previous searches available | ⏳ | |

#### Accessibility Testing
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Label Association** | Check search input label | Proper label association | ⏳ | |
| **Keyboard Navigation** | Navigate with keyboard | All search features accessible | ⏳ | |
| **Screen Reader** | Test with screen reader | Search functionality clear | ⏳ | |
| **Results Announcement** | Search with screen reader | Results changes announced | ⏳ | |

---

## File Upload Component Test Template

### File Upload Testing Template
Use this template for any file upload functionality.

#### Component Information
- **Component Type**: File Upload
- **Upload ID**: `[UPLOAD_ID]`
- **Accepted File Types**: `[FILE_TYPES]`
- **Max File Size**: `[SIZE_LIMIT]`
- **Multiple Files**: `[Yes/No]`

#### Visual Testing
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Upload Area Display** | Load page | Upload area visible | ⏳ | |
| **Upload Instructions** | Check instructions | Clear instructions displayed | ⏳ | |
| **Drag Zone** | If applicable, check drag zone | Drag zone clearly indicated | ⏳ | |

#### File Selection Testing
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **File Browser** | Click upload button | File browser opens | ⏳ | |
| **File Selection** | Select valid file | File selected and displayed | ⏳ | |
| **Multiple Selection** | If applicable, select multiple files | All files selected | ⏳ | |
| **File Type Validation** | Select invalid file type | Error message shows | ⏳ | |
| **File Size Validation** | Select oversized file | Size error message shows | ⏳ | |

#### Drag and Drop Testing (if applicable)
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Drag Over** | Drag file over upload area | Visual feedback shows | ⏳ | |
| **Drop File** | Drop file in upload area | File accepted and processed | ⏳ | |
| **Invalid Drop** | Drop invalid file | Error message shows | ⏳ | |
| **Multiple Drop** | Drop multiple files | All valid files accepted | ⏳ | |

#### Upload Process Testing
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Upload Progress** | Start upload | Progress indicator shows | ⏳ | |
| **Upload Completion** | Wait for upload | Success message shows | ⏳ | |
| **Upload Cancellation** | Cancel during upload | Upload stops and cleans up | ⏳ | |
| **Upload Error** | Simulate upload error | Error message shows with retry option | ⏳ | |

#### File Management Testing
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **File List** | After selection, check list | Selected files listed | ⏳ | |
| **Remove File** | Remove file from list | File removed from upload queue | ⏳ | |
| **File Preview** | If applicable, check preview | File preview displays | ⏳ | |

#### Accessibility Testing
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Keyboard Access** | Navigate with keyboard | Upload accessible via keyboard | ⏳ | |
| **Screen Reader** | Test with screen reader | Upload purpose and status clear | ⏳ | |
| **Focus Management** | During upload process | Focus managed appropriately | ⏳ | |

---

## Browser Compatibility Test Template

### Cross-Browser Testing Template
Use this template to test any component across different browsers.

#### Browser Test Matrix
| Browser | Version | Component Loads | Functionality Works | Styling Correct | Performance OK | Status | Notes |
|---------|---------|-----------------|-------------------|-----------------|----------------|--------|-------|
| **Chrome** | Latest | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | |
| **Firefox** | Latest | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | |
| **Safari** | Latest | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | |
| **Edge** | Latest | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | |
| **Chrome Mobile** | Latest | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | |
| **Safari Mobile** | Latest | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | |

#### Specific Browser Features Testing
| Feature | Chrome | Firefox | Safari | Edge | Status | Notes |
|---------|--------|---------|--------|------|--------|-------|
| **CSS Grid/Flexbox** | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | |
| **JavaScript ES6+** | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | |
| **WebRTC** | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | |
| **Local Storage** | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | |
| **File API** | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | |

---

## Performance Test Template

### Component Performance Testing Template
Use this template to test performance of any component.

#### Performance Metrics
| Metric | Target | Chrome | Firefox | Safari | Edge | Status | Notes |
|--------|--------|--------|---------|--------|------|--------|-------|
| **Load Time** | `[TARGET_TIME]` | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | |
| **First Paint** | `[TARGET_TIME]` | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | |
| **Interactive** | `[TARGET_TIME]` | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | |
| **Memory Usage** | `[TARGET_MB]` | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | |

#### Stress Testing
| Test | Action | Expected Result | Status | Notes |
|------|--------|-----------------|--------|-------|
| **Large Dataset** | Load component with large dataset | Performance remains acceptable | ⏳ | |
| **Rapid Interactions** | Rapidly interact with component | No performance degradation | ⏳ | |
| **Memory Leaks** | Use component extensively | Memory usage remains stable | ⏳ | |
| **Concurrent Users** | Simulate multiple users | Performance scales appropriately | ⏳ | |

---

## Template Customization Guide

### Adapting Templates for Specific Components

#### Step 1: Identify Component Type
- Determine which template best matches your component
- Note any unique characteristics that need additional testing

#### Step 2: Customize Test Cases
- Replace placeholder values with actual component details
- Add component-specific test cases
- Remove irrelevant test cases

#### Step 3: Define Expected Behaviors
- Specify exact expected outcomes for each test
- Include performance targets and acceptance criteria
- Document any browser-specific behaviors

#### Step 4: Execute Tests
- Follow the test steps systematically
- Document results and any deviations
- Report bugs and issues found

#### Step 5: Maintain Templates
- Update templates based on lessons learned
- Add new test cases for common issues
- Keep templates current with application changes

---

## Common UI Patterns Testing

### Responsive Design Testing Checklist
Apply this checklist to any component for responsive testing:

| Breakpoint | Width | Test Action | Expected Result | Status |
|------------|-------|-------------|-----------------|--------|
| **Mobile** | 320px-767px | Resize browser | Component adapts to mobile layout | ⏳ |
| **Tablet** | 768px-1023px | Resize browser | Component uses tablet layout | ⏳ |
| **Desktop** | 1024px+ | Resize browser | Component uses desktop layout | ⏳ |
| **Large Desktop** | 1440px+ | Resize browser | Component scales appropriately | ⏳ |

### Loading States Testing Checklist
Apply this checklist to any component that loads data:

| State | Test Action | Expected Result | Status |
|-------|-------------|-----------------|--------|
| **Initial Load** | Load component | Loading indicator shows | ⏳ |
| **Data Loading** | Trigger data load | Loading state displays | ⏳ |
| **Load Complete** | Wait for completion | Loading state disappears | ⏳ |
| **Load Error** | Simulate error | Error state displays | ⏳ |
| **Retry** | Click retry button | Loading restarts | ⏳ |

### Error States Testing Checklist
Apply this checklist to any component that can show errors:

| Error Type | Test Action | Expected Result | Status |
|------------|-------------|-----------------|--------|
| **Validation Error** | Trigger validation | Clear error message shows | ⏳ |
| **Network Error** | Simulate network issue | Network error message shows | ⏳ |
| **Server Error** | Simulate server error | Server error message shows | ⏳ |
| **Permission Error** | Test without permissions | Permission error shows | ⏳ |
| **Error Recovery** | Fix error condition | Error clears appropriately | ⏳ |

---

**Note**: These templates provide a comprehensive foundation for testing UI components. Customize them based on your specific component requirements and add additional test cases as needed for complete coverage.