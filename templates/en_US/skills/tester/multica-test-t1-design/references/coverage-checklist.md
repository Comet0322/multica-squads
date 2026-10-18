# Coverage Checklist — T1 Pre-generation Self-check

> **Purpose**: check item by item that the T1 cases are complete (see `multica-test-t1-design` Step 4).  
> Use `multica-test-t2-coverage` for **T2 gap assessment**; do not use this checklist as a substitute for the T2 report.

When generating cases for each module, you must check item by item that all three dimensions are covered.

---

## Dimension 1: Full-scenario coverage

### Normal flow (Happy Path)
- [ ] The core business main path runs through completely
- [ ] Each positive branch path is run once
- [ ] Pages/states transition normally

### Branch flow
- [ ] Every if branch of each conditional is covered
- [ ] Every else/else-if branch of each conditional is covered
- [ ] Every option value of each dropdown/radio/multi-select is selected

### Exception flow
- [ ] Network timeout / connection drop
- [ ] Server returns a system error (500)
- [ ] Data does not exist (404)
- [ ] No permission (403/401)
- [ ] Request throttled / rate limited
- [ ] Third-party service unavailable

### State transitions
- [ ] Forward state transitions (A -> B -> C -> D)
- [ ] Reverse/rollback state transitions (D -> C -> A)
- [ ] State transitions that skip intermediate states
- [ ] Operating again on a finished state

### Permission scenarios
- [ ] Administrator operation
- [ ] Regular user operation
- [ ] Anonymous (not logged in) visitor operation
- [ ] Read-only user operation
- [ ] Cross-department/cross-role data visibility

### Data linkage
- [ ] List updates after add/create
- [ ] Related fields refresh after edit
- [ ] Related data changes after delete
- [ ] Cascade effect of parent-table operations on child tables

### Combination scenarios
- [ ] Multiple filter conditions combined
- [ ] Sort + pagination + filter
- [ ] Bulk operation + selected items
- [ ] Data consistency across tabs/pages

### Concurrency scenarios
- [ ] Rapid consecutive clicks on submit
- [ ] Operating after browser back
- [ ] Operating on the same page opened in multiple tabs
- [ ] Submitting the same data repeatedly

---

## Dimension 2: Boundary-scenario coverage

### Numeric input
- [ ] Minimum value
- [ ] Maximum value
- [ ] Minimum - 1
- [ ] Maximum + 1
- [ ] 0
- [ ] Negative number
- [ ] Decimal precision (truncation/rounding beyond precision)
- [ ] Scientific notation input

### String input
- [ ] Empty string
- [ ] 1 character
- [ ] Maximum length
- [ ] Maximum length + 1
- [ ] Overlong text (10x the maximum length)
- [ ] Spaces only
- [ ] Special characters (!@#$%^&*()_+)
- [ ] HTML tags (<script>, <div>, <img onerror>)
- [ ] SQL injection statements (' OR 1=1--)
- [ ] Unicode characters (emoji, Chinese, Japanese, Arabic)
- [ ] Line breaks

### List/array
- [ ] Empty list
- [ ] 1 element
- [ ] Maximum count
- [ ] Maximum count + 1
- [ ] Large number of elements (performance boundary)

### Enum/options
- [ ] Each enum value once
- [ ] Non-existent enum value
- [ ] Enum value is null/undefined
- [ ] Enum value as number/string (type boundary)

### Date and time
- [ ] Current time
- [ ] Past time (1970-01-01)
- [ ] Future time (2099-12-31)
- [ ] Leap-year February 29
- [ ] Across time zones (UTC+8, UTC+0, UTC-5)
- [ ] Malformed time (2026/13/01, 2026-02-30)
- [ ] 0 timestamp
- [ ] Empty time field

### File upload
- [ ] Empty file (0 bytes)
- [ ] File at the size limit (exactly equal to the limit)
- [ ] Oversized file (exceeds the size limit)
- [ ] Unsupported format
- [ ] File name containing special characters
- [ ] Corrupted/unreadable file
- [ ] Uploading multiple files at once

### Pagination
- [ ] page = 1 (first page)
- [ ] page = total pages (last page)
- [ ] page = 0 or negative
- [ ] page > total pages
- [ ] pageSize = 1
- [ ] pageSize = maximum
- [ ] pageSize = 0 or negative
- [ ] pageSize > maximum

### Required-field boundaries
- [ ] All required fields empty
- [ ] Only some required fields filled
- [ ] Required field filled with spaces only
- [ ] No fields sent at all

### Uniqueness constraints
- [ ] Submit the same data repeatedly
- [ ] Create the same data concurrently
- [ ] Modify to an already existing unique value

---

## Dimension 3: Page-check coverage

### Element completeness
- [ ] All buttons exist with correct text
- [ ] All input boxes exist with correct placeholders
- [ ] All text/labels exist with correct content
- [ ] All icons/images exist and display normally
- [ ] All links/navigation exist and jump correctly
- [ ] No redundant/leftover elements

### Layout consistency (against the Figma design)
- [ ] Horizontal alignment of elements is correct
- [ ] Vertical alignment of elements is correct
- [ ] Element spacing (margin/padding) matches the design
- [ ] Element width/height matches the design
- [ ] Grid system / responsive breakpoints are correct
- [ ] List/table column widths match the design

### Style conventions
- [ ] Fonts (font-family, font-size, font-weight) follow the design spec
- [ ] Text color follows the design spec
- [ ] Background/border color follows the design spec
- [ ] Corner radius (border-radius) follows the design spec
- [ ] Shadow (box-shadow) follows the design spec
- [ ] Spacing (white space) follows the design spec

### Interaction states (element level)
- [ ] Default state style is correct
- [ ] Hover state (:hover) style is correct
- [ ] Focus state (:focus) style is correct
- [ ] Active state (:active) style is correct
- [ ] Disabled state (:disabled) style is correct
- [ ] Selected state (:checked/:selected) style is correct
- [ ] Loading state style is correct
- [ ] Error state (input validation failure) style is correct

### Page states
- [ ] Initial state (default state of each element right after page load)
- [ ] Loading state (loading indicator, action buttons disabled)
- [ ] Empty-data state (placeholder image + hint text)
- [ ] Error state (error message + retry button)
- [ ] Normal data display state
- [ ] Whether the footer/bottom fits properly

### Responsive adaptation
- [ ] 1920 x 1080 displays fully
- [ ] 1440 x 900 displays fully
- [ ] 1366 x 768 displays fully (no scrollbar, or scrolls normally)
- [ ] 768 x 1024 (tablet) layout adapts correctly
- [ ] 375 x 667 (phone) layout adapts correctly
- [ ] At 150% / 200% zoom the page is not badly broken

### Copy text check
- [ ] No typos
- [ ] Terminology matches the product docs/requirement
- [ ] Consistent punctuation (full-width/half-width unified)
- [ ] Consistent date and number formats
- [ ] Error messages are clearly worded and contain no technical jargon (such as "404", "Internal Server Error")

### Extreme content
- [ ] Overlong text is truncated with an ellipsis or expand/collapse
- [ ] Overlong lists scroll smoothly (no lag)
- [ ] Loading many images does not lag
- [ ] Tables with too many columns scroll horizontally
- [ ] Long text in dialogs does not break the layout

### Keyboard and accessibility
- [ ] Tab key focuses in the correct order
- [ ] Enter key triggers the primary action (form submit, etc.)
- [ ] All main operations can be completed with the keyboard
- [ ] Images have alt text
- [ ] Form labels are associated with the correct inputs

### Browser compatibility
- [ ] Latest Chrome
- [ ] Latest Firefox
- [ ] Latest Edge
- [ ] Latest Safari
- [ ] Core features work in all browsers

---

## API test coverage points (supplement)

Organized by the three dimensions:

### Full scenario
- [ ] A successful request returns correct data and business code
- [ ] Resource not found returns 404 + error code
- [ ] No permission returns 403 + error code
- [ ] Not logged in returns 401 + error code
- [ ] Request parameter validation failure returns 400 + error message
- [ ] Server exception returns 500
- [ ] Rate limiting returns 429

### Boundary scenario (parameter level)
- [ ] Required parameter omitted
- [ ] Wrong parameter type
- [ ] Wrong parameter format
- [ ] Parameter value empty/null
- [ ] Parameter exceeds maximum length
- [ ] Parameter at minimum/maximum boundary
- [ ] Parameter is a non-existent enum value
- [ ] Extra undefined parameters sent
- [ ] Request header missing/wrong

### Field validation (response level)
- [ ] Field completeness: none missing, none extra
- [ ] Field types correct
- [ ] Field formats correct (date, amount, URL)
- [ ] Nested structure correct
- [ ] Null handling (null, "", [])
- [ ] Array boundaries (empty, single element, multiple elements)
- [ ] Pagination fields (page, total, pageSize) correct
- [ ] Business status-code enum values complete
