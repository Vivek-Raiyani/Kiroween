---
inclusion: always
---
---
inclusion: fileMatch
fileMatchPattern: ['**/*.css', '**/*.html', '**/templates/**/*']
---

# Design System & Styling Guidelines

## CSS Variables
- Always use CSS custom properties defined in `:root` instead of hardcoded values
- Core variables: `--ink` (black), `--paper` (white), `--accent-red`, `--gray-wash`, `--glass`, `--panel-border`
- Extend existing variables rather than creating inline styles

## Typography
**Font Stack:**
- Oswald: Headlines, numbers, manga-style text (uppercase, letter-spacing: -0.02em, tight line-height)
- Inter: Body content and UI text
- Noto Sans JP: Japanese subtitling

**Heading Sizes:**
```css
h1 { font-size: clamp(3rem, 8vw, 5rem); line-height: 0.9; }
h2 { font-size: 3rem; }
h3 { font-size: 1.8rem; }
```

## Layout & Spacing
**Grid System:** 12-column CSS Grid
- `.p-large`: span 8 columns
- `.p-small`: span 4 columns
- `.p-tall`: span 4 columns + row span 2

**Standard Spacing:**
- 20px: standard gaps
- 30px: panel padding
- 50px-80px: section padding
- Avoid arbitrary values

## Panels & Cards
**Standard Panel:**
```css
background: var(--paper);
border: var(--panel-border);
box-shadow: 8px 8px 0 rgba(0,0,0,.1);
transition: transform .3s ease;
```

**Hover State:** Translate up-left, red accent shadow

## Manga Aesthetic
Maintain comic/manga visual language:
- Halftone backgrounds (radial-gradient)
- Bold borders with drop shadows
- Hollow outline numbers
- Speed-lines for motion
- Thick borders, exaggerated spacing

## Animations
**Intersection Observer Pattern:**
```css
opacity: 0 → 1;
transform: translateY(30px) → 0;
```

**Micro-animations:** Subtle, minimal motion (avoid flashy effects)

## Dark Sections
- Background: `var(--ink)` (full black)
- Foreground: white elements
- Halftone dot texture overlay
- Flat UI components within

## Buttons
**Standard Button:**
```css
.btn-black {
  background: var(--ink);
  color: var(--paper);
  border-radius: 20px;
  border: 2px solid var(--ink);
  font-weight: 600;
}
```

**Hover:** Invert colors, add shadow, translate -2px

## Icons
- FontAwesome icons throughout
- Consistent sizing per context
- Monochrome dominant with sparse red accents
- Brand colors only where meaningful (e.g., YouTube red)

## Responsive Design
**Breakpoint:** `@media (max-width: 768px)`
- Collapse panels to single column
- Center feature sections
- Reset transforms
- Stack layouts