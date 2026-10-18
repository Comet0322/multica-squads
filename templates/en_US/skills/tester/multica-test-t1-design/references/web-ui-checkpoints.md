# Web UI Design-to-Case Mapping (turning UI designs into test points)

## ⚠️ UI check scope principle (important)

**The Figma comparison check only covers page element styles discernible to the naked eye; it does not check pixel-level exact values.** Test cases focus on functional correctness and obvious UI state defects; pixel-level details (exact sizes, color values, corner radii, fine spacing tweaks, etc.) are left to the UI walkthrough stage where designers sign off.

- **Check**: element presence, layout structure, copy text, interaction states (default/hover/disabled/empty/error), overall visual style
- **Skip**: exact position/size (px values), exact color values, corner radius / border thickness / shadow amount, exact pixels of responsive breakpoints, exact font size and line height, cross-browser rendering differences

---

## Extracting test points from Figma designs

When the user provides a Figma design (screenshot or description), extract test points along the following dimensions:

### 1. Page element inventory

For each page element in the design, build the following inventory:

```
□ Input
  - placeholder text
  - Prefix/suffix icons
  - Border style (normal/focus/error)
  - Input format hint
  - Clear button

□ Button
  - Label text
  - Color style (normal/hover/click/disabled — qualitative, not quantitative)
  - Loading indicator

□ Select/Dropdown
  - Option list
  - Multi-select/single-select
  - Search/filter function
  - Empty-option display

□ Table/List
  - Column definitions and order
  - Sorting function
  - Pager configuration
  - Row action buttons
  - Empty-data state
  - Selected-state style

□ Modal/Dialog
  - Trigger method
  - Mask layer style
  - Close methods (click mask / close button / ESC)
  - Title and content
  - Button layout

□ Navigation/Menu
  - Menu hierarchy
  - Active-state style
  - Breadcrumb navigation
  - Tab switching
```

### 2. Interaction-state test dimensions

For each interactive element, check the following states (qualitative description is enough):

| State | Check point |
|------|--------|
| Default | Element displays normally, the state with no interaction |
| Hover | Visual feedback on mouse hover (color change / underline / shadow) |
| Focus | Outline style on keyboard/Tab focus |
| Active | Visual feedback at the moment of click |
| Disabled | Grayed out when not operable, with the reason indicated |
| Loading | Animation or progress indicator while waiting |
| Error | Red border and error message are visible when validation fails |
| Empty | Placeholder content is reasonable when there is no data |
| Selected | The selected item has a highlight style |

### 3. Common Web page checklists

> **Note**: In the items below, quantitative checks (such as "1920 resolution") are only indicative references; during execution, judge by eye — no precise measurement is needed.

#### Form pages
- [ ] All labels are associated with the correct input fields
- [ ] Required fields are marked (* or "required" text)
- [ ] Error messages appear in the correct place (usually below the field)
- [ ] The submit button is disabled while the form is incomplete
- [ ] Tab key focuses fields in the correct order
- [ ] Enter key triggers submission
- [ ] Inputs have an appropriate input type

#### List/table pages
- [ ] The pagination component shows the correct total pages and current page
- [ ] Data reloads after switching the page size
- [ ] Sort indicators (ascending/descending icons) are correct
- [ ] Select-all / invert-selection works during multi-select
- [ ] Bulk action buttons are disabled when nothing is selected
- [ ] Adjusting column widths does not break the layout

#### Search/filter pages
- [ ] The search box shows a keyword input hint
- [ ] Filter conditions support combined queries
- [ ] The result count after filtering is correct
- [ ] An empty search result shows a message and suggestions
- [ ] Clearing the filters restores all data

#### Detail/display pages
- [ ] All information fields are displayed completely
- [ ] Long text has expand/collapse
- [ ] Image/file preview works
- [ ] Related recommendations / navigation links are correct
- [ ] Loading order (skeleton screen / loading animation)

#### Responsive/cross-browser
- [ ] Desktop layout is complete with no breakage
- [ ] Small-screen layout has no breakage
- [ ] Key interactions work in mainstream browsers

### 4. Expected-result wording conventions

- Use **qualitative descriptions** rather than quantitative ones
- Correct example: "The Save button text is correct, its color is prominent, and it gives feedback on hover"
- Correct example: "The error message is shown in red text below the input box"
- Wrong example: "Button size 120x40px, corner radius 4px, color #1890FF"
- Wrong example: "Input width 320px, height 36px"
