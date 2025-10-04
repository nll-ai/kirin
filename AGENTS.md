# GitData - Agent Guidelines

This document provides guidelines for AI agents working on the GitData project.

## Design System

### UI Framework: shadcn/ui

This project uses **shadcn/ui** as the design system for all user interface components. When working on the web UI:

- **Use shadcn/ui components and styling patterns** - All UI elements should follow shadcn/ui design principles
- **CSS Variables** - The project uses CSS custom properties defined in the `:root` selector for consistent theming:
  - `--background`, `--foreground` for text and backgrounds
  - `--card`, `--card-foreground` for panel backgrounds
  - `--primary`, `--primary-foreground` for primary actions
  - `--secondary`, `--secondary-foreground` for secondary elements
  - `--muted`, `--muted-foreground` for subtle text and backgrounds
  - `--border`, `--input` for form elements
  - `--destructive`, `--destructive-foreground` for destructive actions
  - `--radius` for border radius consistency

- **Component Classes** - Use the established component classes:
  - `.btn` with variants: `.btn-primary`, `.btn-secondary`, `.btn-ghost`, `.btn-destructive`
  - `.input` for form inputs
  - `.panel` for card-like containers
  - `.panel-header` and `.panel-title` for panel headers
  - `.panel-content` for panel body content
  - `.file-item` for file list items

- **Layout Patterns** - Follow established layout patterns:
  - Use `.container` for main content areas
  - Use `.header` for page headers with titles and descriptions
  - Use grid layouts with `.grid` and responsive breakpoints
  - Use `.space-y-*` for consistent vertical spacing

### Styling Guidelines

1. **Always use the CSS custom properties** instead of hardcoded colors
2. **Follow the established component patterns** from existing templates
3. **Use semantic class names** that match shadcn/ui conventions
4. **Maintain consistency** with the existing design system
5. **Test responsive behavior** on different screen sizes

### Examples

```html
<!-- Good: Using shadcn/ui patterns -->
<div class="panel">
    <div class="panel-header">
        <h2 class="panel-title">Title</h2>
    </div>
    <div class="panel-content">
        <button class="btn btn-primary">Action</button>
    </div>
</div>

<!-- Avoid: Custom styling that doesn't follow the system -->
<div class="bg-white rounded-lg shadow-md p-6">
    <h2 class="text-xl font-semibold mb-4">Title</h2>
    <button class="bg-blue-600 text-white px-4 py-2 rounded-md">Action</button>
</div>
```

## Development Guidelines

- Always maintain consistency with the existing shadcn/ui design system
- Use the established component classes and CSS variables
- Follow the responsive design patterns used throughout the application
- Test UI changes to ensure they match the overall design language
