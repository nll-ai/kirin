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

## Template Consistency Rules

### Critical: Follow Existing Template Patterns

When creating new templates, **ALWAYS** copy the exact styling patterns from existing templates like `dataset_view.html`:

1. **Use `{% block extra_styles %}`** - Include the exact CSS classes and patterns from existing templates
2. **Copy Panel Structure** - Use the same `.panel`, `.panel-header`, `.panel-title`, `.panel-content` structure
3. **File Item Styling** - For file lists, use the exact `.file-item`, `.file-icon`, `.file-name` classes from `dataset_view.html`
4. **Navigation Patterns** - Include breadcrumb navigation with `.nav-bar` and `.breadcrumb` classes
5. **Empty States** - Use proper empty state styling with icons and consistent spacing

### Template Structure Checklist

Every new template should follow this pattern:

```html
{% extends "base.html" %}
{% block title %}Page Title{% endblock %}

{% block extra_styles %}
<style>
    /* Copy exact CSS patterns from dataset_view.html */
    .panel { /* ... */ }
    .panel-header { /* ... */ }
    .panel-title { /* ... */ }
    .panel-content { /* ... */ }
    .file-item { /* ... */ }
    .file-icon { /* ... */ }
    .file-name { /* ... */ }
    /* etc. */
</style>
{% endblock %}

{% block content %}
<div class="container">
    <div class="nav-bar">
        <!-- Breadcrumb navigation -->
    </div>
    <div class="header">
        <!-- Page title and description -->
    </div>
    <div class="content-container">
        <div class="panel">
            <div class="panel-header">
                <h2 class="panel-title">Title</h2>
            </div>
            <div class="panel-content">
                <!-- Content -->
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### Common Mistakes to Avoid

❌ **DON'T** use generic CSS classes like `bg-white`, `rounded-lg`, `shadow-md`
❌ **DON'T** create custom styling that doesn't match existing patterns
❌ **DON'T** use huge icons or inconsistent sizing
❌ **DON'T** skip the `{% block extra_styles %}` section

✅ **DO** copy exact CSS from `dataset_view.html`
✅ **DO** use the established component classes
✅ **DO** maintain consistent spacing and typography
✅ **DO** test that new templates look identical to existing ones

### File Icon Standards

- **Size**: Always 16px x 16px (`width: 16px; height: 16px`)
- **Class**: Use `.file-icon` class
- **SVG**: Use the exact SVG path from `files_list.html`
- **Styling**: `color: hsl(var(--muted-foreground)); opacity: 0.6;`

### Panel Standards

- **Structure**: Always use `.panel` > `.panel-header` > `.panel-content`
- **Spacing**: `padding: 1.25rem 1.5rem` for headers, `padding: 1.5rem` for content
- **Borders**: `border: 1px solid hsl(var(--border))`
- **Shadows**: `box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)`
