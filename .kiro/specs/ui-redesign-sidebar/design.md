# Design Document

## Overview

This design document outlines the transformation of the CreatorFlow platform from a traditional top-navigation layout to a modern, app-like sidebar navigation interface. The redesign maintains all existing Django functionality while providing a more intuitive, visually appealing user experience inspired by modern SaaS applications.

## Architecture

### Layout Structure

The application will use a two-column layout:

```
┌─────────────────────────────────────┐
│  Sidebar  │   Main Content Area     │
│  (Fixed)  │   (Scrollable)          │
│           │                          │
│  Logo     │   View Content           │
│  Nav      │   - Dashboard            │
│  Items    │   - Analytics            │
│           │   - A/B Testing          │
│  User     │   - etc.                 │
│  Profile  │                          │
└─────────────────────────────────────┘
```

### View Management

The system will use a single-page application (SPA) approach for view switching:
- All view sections exist in the DOM simultaneously
- Only one view is visible at a time (controlled by CSS classes)
- JavaScript handles view switching and navigation state
- Django still handles server-side routing for initial page loads and data fetching

### Template Hierarchy

```
base_sidebar.html (new)
├── CSS Variables & Global Styles
├── Sidebar Navigation Component
└── Main Content Wrapper
    ├── dashboard.html (updated)
    ├── analytics views (updated)
    ├── abtesting views (updated)
    └── other views (updated)
```

## Components and Interfaces

### 1. Sidebar Navigation Component

**Purpose**: Provide persistent navigation and branding

**Structure**:
```html
<div class="sidebar">
  <div class="logo">CREATOR<span>FLOW</span></div>
  
  <nav class="nav-section">
    <div class="nav-group-label">Growth</div>
    <div class="nav-link" data-target="analytics">
      <i class="fas fa-chart-pie"></i> AI Analytics
    </div>
    <!-- More nav items -->
  </nav>
  
  <div class="sidebar-footer">
    <div class="user-profile">
      <!-- Avatar, name, plan -->
    </div>
  </div>
</div>
```

**Styling**:
- Width: 260px (fixed)
- Background: `var(--ink)` (#0a0a0a)
- Color: white
- Full viewport height
- Flex column layout with footer pushed to bottom

### 2. Main Content Area

**Purpose**: Display active view content

**Structure**:
```html
<div class="main-content">
  <div id="view-dashboard" class="view-section active">
    <!-- Dashboard content -->
  </div>
  <div id="view-analytics" class="view-section">
    <!-- Analytics content -->
  </div>
  <!-- More views -->
</div>
```

**Styling**:
- Flex: 1 (takes remaining space)
- Padding: 30px
- Overflow-y: auto
- Background: `var(--bg-wash)` (#f0f2f5)

### 3. Card Component

**Purpose**: Container for grouped content

**Styling**:
```css
.card {
  background: white;
  border: 2px solid var(--ink);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 4px 4px 0 rgba(0,0,0,0.15);
  margin-bottom: 20px;
  transition: transform 0.3s ease;
}

.card:hover {
  transform: translate(-2px, -2px);
  box-shadow: 6px 6px 0 rgba(0,0,0,0.2);
}
```

### 4. Button Component

**Purpose**: Interactive actions

**Variants**:
- `.btn` - Base button
- `.btn-primary` - Black background, white text
- `.btn-purple` - Purple accent for marketplace
- `.btn-green` - Green accent for ROI/success

**Styling**:
```css
.btn {
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  border: 2px solid var(--ink);
  transition: 0.2s;
}

.btn:hover {
  transform: translate(-2px, -2px);
  box-shadow: 4px 4px 0 var(--ink);
}
```

### 5. Navigation Link Component

**Purpose**: Sidebar navigation items

**States**:
- Default: Gray text, transparent background
- Hover: White text, semi-transparent white background
- Active: Black text, white background, red shadow

**Styling**:
```css
.nav-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  color: #aaa;
  transition: 0.2s;
}

.nav-link.active {
  background: white;
  color: var(--ink);
  font-weight: 700;
  box-shadow: 4px 4px 0 var(--accent-red);
}
```

### 6. Toast Notification Component

**Purpose**: Display Django messages as non-intrusive toast notifications

**Structure**:
```html
<div class="toast-container">
  <div class="toast toast-success">
    <i class="fas fa-check-circle"></i>
    <span>Operation completed successfully</span>
    <button class="toast-close">&times;</button>
  </div>
</div>
```

**Variants**:
- `.toast-success` - Green background for success messages
- `.toast-error` - Red background for error messages
- `.toast-warning` - Orange background for warning messages
- `.toast-info` - Blue background for info messages

**Styling**:
```css
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.toast {
  background: white;
  border: 2px solid var(--ink);
  border-radius: 12px;
  padding: 16px 20px;
  min-width: 300px;
  max-width: 400px;
  box-shadow: 4px 4px 0 rgba(0,0,0,0.15);
  display: flex;
  align-items: center;
  gap: 12px;
  animation: slideInRight 0.3s ease;
}

.toast-success {
  border-left: 4px solid #10B981;
}

.toast-error {
  border-left: 4px solid var(--accent-red);
}

@keyframes slideInRight {
  from {
    transform: translateX(400px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
```

**Behavior**:
- Auto-dismiss after 5 seconds
- Manual dismiss via close button
- Stack multiple toasts vertically
- Slide in from right with animation
- Fade out on dismiss

## Data Models

No new data models are required. This is a pure UI/UX transformation that works with existing Django models and views.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Single Active View

*For any* navigation action, exactly one view section should have the "active" class at any given time.

**Validates: Requirements 2.1, 2.2**

### Property 2: Navigation State Consistency

*For any* active view, the corresponding navigation link should have the "active" class applied.

**Validates: Requirements 1.4, 2.3**

### Property 3: CSS Variable Consistency

*For any* color value in the stylesheet, it should reference a CSS custom property defined in `:root` rather than using hardcoded hex values.

**Validates: Requirements 6.1**

### Property 4: Responsive Breakpoint Behavior

*For any* viewport width below 768px, the sidebar should either be hidden or transformed into a mobile-friendly navigation pattern.

**Validates: Requirements 7.1**

### Property 5: Django Template Preservation

*For any* updated template file, all original Django template tags ({% %}) and variables ({{ }}) should remain functional and produce the same output.

**Validates: Requirements 8.1, 8.2, 8.3**

### Property 6: Button Hover State

*For any* button element, hovering should apply a transform and shadow effect within the specified transition duration.

**Validates: Requirements 4.2**

### Property 7: Card Hover Feedback

*For any* interactive card, hovering should translate the card position and increase shadow depth.

**Validates: Requirements 3.3**

### Property 8: Toast Auto-Dismiss

*For any* toast notification, it should automatically dismiss after 5 seconds unless manually closed earlier.

**Validates: Requirements 8.4**

## Error Handling

### JavaScript Navigation Errors

**Scenario**: User clicks navigation link but target view doesn't exist

**Handling**:
- Check if target element exists before attempting to show it
- Log error to console
- Fall back to dashboard view
- Display user-friendly toast message

```javascript
function navTo(target) {
  const targetView = document.getElementById(`view-${target}`);
  if (!targetView) {
    console.error(`View not found: ${target}`);
    showToast('View not found', 'error');
    navTo('dashboard');
    return;
  }
  // Proceed with navigation
}
```

### Toast Notification Errors

**Scenario**: Multiple toasts stack and overflow viewport

**Handling**:
- Limit maximum visible toasts to 5
- Auto-dismiss oldest toast when limit reached
- Ensure toasts remain within viewport bounds
- Handle rapid successive toast creation

```javascript
function showToast(message, type = 'info') {
  const container = document.querySelector('.toast-container');
  const toasts = container.querySelectorAll('.toast');
  
  // Limit to 5 toasts
  if (toasts.length >= 5) {
    toasts[0].remove();
  }
  
  // Create and show new toast
  const toast = createToastElement(message, type);
  container.appendChild(toast);
  
  // Auto-dismiss after 5 seconds
  setTimeout(() => dismissToast(toast), 5000);
}
```

### CSS Loading Failures

**Scenario**: Custom CSS fails to load

**Handling**:
- Ensure critical styles are inlined in `<head>`
- Provide fallback to Bootstrap classes
- Use `@supports` queries for advanced CSS features

### Mobile Viewport Issues

**Scenario**: Layout breaks on small screens

**Handling**:
- Use CSS Grid and Flexbox with fallbacks
- Test breakpoints at 320px, 768px, 1024px
- Implement mobile-first approach
- Hide sidebar by default on mobile, show via toggle

## Testing Strategy

### Unit Testing

**CSS Unit Tests** (using a tool like Jest + jsdom):
- Test that CSS variables are properly defined
- Verify button hover states apply correct transforms
- Check card shadow calculations
- Validate responsive breakpoint behavior

**JavaScript Unit Tests**:
- Test `navTo()` function with valid and invalid targets
- Test active class toggling logic
- Test sidebar toggle functionality
- Test view visibility management

**Example Test**:
```javascript
describe('Navigation', () => {
  test('navTo() should activate correct view', () => {
    navTo('analytics');
    const analyticsView = document.getElementById('view-analytics');
    expect(analyticsView.classList.contains('active')).toBe(true);
  });
  
  test('navTo() should deactivate other views', () => {
    navTo('analytics');
    const dashboardView = document.getElementById('view-dashboard');
    expect(dashboardView.classList.contains('active')).toBe(false);
  });
});
```

### Property-Based Testing

We will use **Hypothesis** (Python) for property-based testing of template rendering and **fast-check** (JavaScript) for frontend property tests.

**Property Test Configuration**:
- Minimum 100 iterations per property test
- Each test tagged with format: `**Feature: ui-redesign-sidebar, Property {number}: {property_text}**`

**Property Test Examples**:

**Test 1: Single Active View Property**
```javascript
// **Feature: ui-redesign-sidebar, Property 1: Single Active View**
fc.assert(
  fc.property(
    fc.constantFrom('dashboard', 'analytics', 'marketplace', 'crm', 'media'),
    (targetView) => {
      navTo(targetView);
      const activeViews = document.querySelectorAll('.view-section.active');
      return activeViews.length === 1;
    }
  ),
  { numRuns: 100 }
);
```

**Test 2: Navigation State Consistency**
```javascript
// **Feature: ui-redesign-sidebar, Property 2: Navigation State Consistency**
fc.assert(
  fc.property(
    fc.constantFrom('dashboard', 'analytics', 'marketplace', 'crm', 'media'),
    (targetView) => {
      navTo(targetView);
      const activeView = document.querySelector('.view-section.active');
      const activeLink = document.querySelector('.nav-link.active');
      return activeLink.dataset.target === activeView.id.replace('view-', '');
    }
  ),
  { numRuns: 100 }
);
```

**Test 3: CSS Variable Consistency**
```python
# **Feature: ui-redesign-sidebar, Property 3: CSS Variable Consistency**
from hypothesis import given, strategies as st
import re

@given(st.text(min_size=1))
def test_css_uses_variables(css_content):
    """All color values should use CSS variables"""
    # Find all color declarations
    hex_colors = re.findall(r':\s*#[0-9a-fA-F]{3,6}', css_content)
    # Exclude :root definitions
    root_section = re.search(r':root\s*{[^}]+}', css_content)
    if root_section:
        hex_colors = [c for c in hex_colors if c not in root_section.group()]
    # Should have no hardcoded colors outside :root
    assert len(hex_colors) == 0
```

**Test 4: Django Template Preservation**
```python
# **Feature: ui-redesign-sidebar, Property 5: Django Template Preservation**
from hypothesis import given, strategies as st
from django.template import Template, Context

@given(st.dictionaries(st.text(), st.text()))
def test_template_variables_preserved(context_data):
    """Template variables should render correctly"""
    template = Template("{{ user.username }}")
    context = Context({'user': type('User', (), context_data)()})
    # Should not raise exception
    result = template.render(context)
    assert isinstance(result, str)
```

**Test 5: Toast Auto-Dismiss**
```javascript
// **Feature: ui-redesign-sidebar, Property 8: Toast Auto-Dismiss**
fc.assert(
  fc.property(
    fc.constantFrom('success', 'error', 'warning', 'info'),
    fc.string(),
    async (type, message) => {
      const startTime = Date.now();
      showToast(message, type);
      
      // Wait for auto-dismiss
      await new Promise(resolve => setTimeout(resolve, 5100));
      
      const toasts = document.querySelectorAll('.toast');
      const elapsed = Date.now() - startTime;
      
      // Should be dismissed after ~5 seconds
      return toasts.length === 0 && elapsed >= 5000 && elapsed <= 5500;
    }
  ),
  { numRuns: 100 }
);
```

### Integration Testing

**Browser Testing**:
- Test in Chrome, Firefox, Safari, Edge
- Test on iOS Safari and Android Chrome
- Verify animations and transitions
- Check accessibility with screen readers

**Django Integration**:
- Test all views render with new templates
- Verify authentication flows work
- Check permission-based navigation visibility
- Test message framework integration

### Visual Regression Testing

Use a tool like Percy or BackstopJS to:
- Capture screenshots of all views
- Compare against baseline
- Flag unexpected visual changes
- Test responsive breakpoints

## Implementation Notes

### Font Loading

Use Google Fonts for Oswald and Inter:
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Oswald:wght@500;700&display=swap" rel="stylesheet">
```

### Icon Library

Continue using Font Awesome 6.4.0 for consistency with existing implementation.

### Animation Performance

Use CSS transforms and opacity for animations (GPU-accelerated):
- Avoid animating `width`, `height`, `top`, `left`
- Use `transform: translate()` instead
- Use `will-change` sparingly for critical animations

### Accessibility Considerations

- Maintain keyboard navigation support
- Ensure sufficient color contrast (WCAG AA minimum)
- Add ARIA labels to navigation elements
- Support reduced motion preferences:

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Browser Support

Target modern browsers:
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- iOS Safari 14+
- Android Chrome 90+

Use autoprefixer for vendor prefixes.

## Migration Strategy

### Phase 1: Create New Base Template
- Create `base_sidebar.html` alongside existing `base.html`
- Implement sidebar navigation structure
- Add CSS variables and new styles

### Phase 2: Update Individual Views
- Convert one view at a time (start with dashboard)
- Test each view thoroughly before moving to next
- Maintain backward compatibility during transition

### Phase 3: JavaScript Integration
- Implement view switching logic
- Add navigation state management
- Test all navigation flows

### Phase 4: Mobile Optimization
- Implement responsive breakpoints
- Add mobile menu toggle
- Test on real devices

### Phase 5: Cleanup
- Remove old `base.html` once all views migrated
- Remove unused CSS from `style.css`
- Optimize and minify assets
