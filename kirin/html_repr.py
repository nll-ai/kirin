"""HTML representation utilities for Dataset, Commit, and Catalog classes."""

import html
from pathlib import Path
from typing import Optional


def escape_html(text: str) -> str:
    """Escape HTML special characters.

    Args:
        text: Text to escape

    Returns:
        Escaped HTML string
    """
    return html.escape(str(text))


def format_file_size(size: int) -> str:
    """Format file size in bytes to human-readable format.

    Args:
        size: Size in bytes

    Returns:
        Formatted size string (e.g., "1.5 KB", "2.3 MB")
    """
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.1f} GB"


def get_file_icon_html(filename: str, content_type: Optional[str] = None) -> str:
    """Generate file icon SVG based on file type.

    Args:
        filename: Name of the file
        content_type: Optional content type

    Returns:
        SVG icon HTML string
    """
    # Determine file type from extension or content type
    ext = Path(filename).suffix.lower()
    file_type = "file"  # default

    # Map extensions to file types
    if ext in [".txt", ".md", ".rst", ".log"]:
        file_type = "text"
    elif ext in [".csv", ".tsv"]:
        file_type = "csv"
    elif ext in [".json"]:
        file_type = "json"
    elif ext in [".py", ".js", ".ts", ".java", ".cpp", ".c", ".h"]:
        file_type = "code"
    elif ext in [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"]:
        file_type = "image"
    elif ext in [".pdf"]:
        file_type = "pdf"
    elif ext in [".zip", ".tar", ".gz", ".rar"]:
        file_type = "archive"
    elif ext in [".xlsx", ".xls"]:
        file_type = "excel"
    elif ext in [".ipynb"]:
        file_type = "notebook"

    # SVG icons (16x16px) - simple colored rectangles with file type indicators
    # Long SVG strings are kept on single lines for readability
    icons = {
        "text": '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="16" height="16" fill="#3B82F6" opacity="0.1" rx="2"/><path d="M4 4h8M4 6h8M4 8h6M4 10h4" stroke="#3B82F6" stroke-width="1.5" stroke-linecap="round"/></svg>',  # noqa: E501
        "csv": '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="16" height="16" fill="#10B981" opacity="0.1" rx="2"/><path d="M4 4h8v8H4z" stroke="#10B981" stroke-width="1.5" fill="none"/><path d="M4 6h8M6 4v8M8 4v8" stroke="#10B981" stroke-width="1" stroke-linecap="round"/></svg>',  # noqa: E501
        "json": '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="16" height="16" fill="#F59E0B" opacity="0.1" rx="2"/><path d="M4 4l4 4-4 4M12 4l-4 4 4 4" stroke="#F59E0B" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',  # noqa: E501
        "code": '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="16" height="16" fill="#8B5CF6" opacity="0.1" rx="2"/><path d="M6 4l-2 4 2 4M10 4l2 4-2 4" stroke="#8B5CF6" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',  # noqa: E501
        "image": '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="16" height="16" fill="#EC4899" opacity="0.1" rx="2"/><rect x="3" y="4" width="10" height="8" rx="1" stroke="#EC4899" stroke-width="1.5" fill="none"/><circle cx="6" cy="7" r="1" fill="#EC4899"/><path d="M3 11l3-2 2 2 4-3 2 3" stroke="#EC4899" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',  # noqa: E501
        "pdf": '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="16" height="16" fill="#EF4444" opacity="0.1" rx="2"/><path d="M4 4h8v8H4z" stroke="#EF4444" stroke-width="1.5" fill="none"/><path d="M6 6h4M6 8h4M6 10h2" stroke="#EF4444" stroke-width="1" stroke-linecap="round"/></svg>',  # noqa: E501
        "archive": '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="16" height="16" fill="#6B7280" opacity="0.1" rx="2"/><path d="M4 5h8M4 5v6h8V5M6 7h4" stroke="#6B7280" stroke-width="1.5" stroke-linecap="round"/></svg>',  # noqa: E501
        "excel": '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="16" height="16" fill="#10B981" opacity="0.1" rx="2"/><path d="M4 4h8v8H4z" stroke="#10B981" stroke-width="1.5" fill="none"/><path d="M4 6h8M6 4v8" stroke="#10B981" stroke-width="1" stroke-linecap="round"/></svg>',  # noqa: E501
        "notebook": '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="16" height="16" fill="#F59E0B" opacity="0.1" rx="2"/><path d="M5 4h6v8H5z" stroke="#F59E0B" stroke-width="1.5" fill="none"/><path d="M7 4v8" stroke="#F59E0B" stroke-width="1"/></svg>',  # noqa: E501
        "file": '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="16" height="16" fill="#6B7280" opacity="0.1" rx="2"/><path d="M5 4h6l2 2v6H5V4z" stroke="#6B7280" stroke-width="1.5" fill="none" stroke-linejoin="round"/><path d="M7 4v2h2" stroke="#6B7280" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"/></svg>',  # noqa: E501
    }

    return icons.get(file_type, icons["file"])


def get_inline_css() -> str:
    """Extract and return relevant CSS from web UI stylesheet for standalone rendering.

    Returns:
        CSS string with relevant styles
    """
    return """
/* Kirin HTML Representation Styles - Extracted from web UI */
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --card: 0 0% 100%;
  --card-foreground: 222.2 84% 4.9%;
  --primary: 221.2 83.2% 53.3%;
  --primary-foreground: 210 40% 98%;
  --secondary: 210 40% 96%;
  --secondary-foreground: 222.2 84% 4.9%;
  --muted: 210 40% 96%;
  --muted-foreground: 215.4 16.3% 46.9%;
  --accent: 210 40% 96%;
  --accent-foreground: 222.2 84% 4.9%;
  --border: 214.3 31.8% 91.4%;
  --input: 214.3 31.8% 91.4%;
  --ring: 221.2 83.2% 53.3%;
  --radius: 0.5rem;
}

* {
  border-color: hsl(var(--border));
  box-sizing: border-box;
}

body {
  background-color: hsl(var(--background));
  color: hsl(var(--foreground));
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
    "Helvetica Neue", Arial, sans-serif;
  line-height: 1.5;
  margin: 0;
  padding: 0;
}

/* Layout */
.flex {
  display: flex;
}

.flex-col {
  flex-direction: column;
}

.items-center {
  align-items: center;
}

.justify-between {
  justify-content: space-between;
}

.gap-2 {
  gap: 0.5rem;
}

.gap-4 {
  gap: 1rem;
}

.mb-2 {
  margin-bottom: 0.5rem;
}

.mb-4 {
  margin-bottom: 1rem;
}

.mt-4 {
  margin-top: 1rem;
}

.p-4 {
  padding: 1rem;
}

/* Typography */
.text-sm {
  font-size: 0.875rem;
}

.text-lg {
  font-size: 1.125rem;
}

.font-medium {
  font-weight: 500;
}

.font-semibold {
  font-weight: 600;
}

.text-muted-foreground {
  color: hsl(var(--muted-foreground));
}

.text-primary {
  color: hsl(var(--primary));
}

/* Components */
.panel {
  background: hsl(var(--card));
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  overflow: hidden;
  margin-bottom: 1rem;
}

.panel-header {
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid hsl(var(--border));
  background: hsl(var(--muted));
}

.panel-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
}

.panel-content {
  padding: 1.5rem;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  background: hsl(var(--card));
  transition: all 0.2s;
  margin-bottom: 0.5rem;
}

.file-item:hover {
  border-color: hsl(var(--ring));
  background: hsl(var(--accent));
}

.file-item .copy-code-btn {
  margin-left: auto;
  margin-right: 0.5rem;
}

.file-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  color: hsl(var(--muted-foreground));
  opacity: 0.6;
}

.file-name {
  flex: 1;
  font-size: 0.875rem;
  font-weight: 500;
  color: hsl(var(--foreground));
}

.file-size {
  font-size: 0.75rem;
  color: hsl(var(--muted-foreground));
}

.commit-item {
  padding: 0.75rem;
  border: 1px solid hsl(var(--border));
  border-radius: var(--radius);
  background: hsl(var(--card));
  margin-bottom: 0.5rem;
}

.commit-hash {
  font-family: monospace;
  font-size: 0.75rem;
  color: hsl(var(--primary));
}

.commit-message {
  font-weight: 500;
  margin: 0.25rem 0;
}

.commit-timestamp {
  font-size: 0.75rem;
  color: hsl(var(--muted-foreground));
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  font-weight: 500;
  border-radius: calc(var(--radius) / 2);
  background: hsl(var(--secondary));
  color: hsl(var(--secondary-foreground));
}

.space-y-4 > * + * {
  margin-top: 1rem;
}

.hidden {
  display: none;
}

/* Buttons - matching web UI */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  margin: 0;
  font-size: 0.875rem;
  font-weight: 500;
  border-radius: var(--radius);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
  box-sizing: border-box;
  line-height: 1.5;
  height: 2.5rem;
  vertical-align: top;
  -webkit-appearance: none;
  appearance: none;
  font-family: inherit;
  background: transparent;
  color: hsl(var(--foreground));
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: hsl(var(--primary));
  color: hsl(var(--primary-foreground));
  border-color: hsl(var(--primary));
}

.btn-primary:hover:not(:disabled) {
  background: hsl(var(--primary) / 0.9);
}

.btn-secondary {
  background: hsl(var(--secondary));
  color: hsl(var(--secondary-foreground));
  border-color: hsl(var(--border));
}

.btn-secondary:hover:not(:disabled) {
  background: hsl(var(--secondary) / 0.8);
}

.btn-ghost {
  background: transparent;
  color: hsl(var(--foreground));
  border-color: transparent;
  height: auto;
  padding: 0.375rem 0.75rem;
  font-size: 0.75rem;
}

.btn-ghost:hover:not(:disabled) {
  background: hsl(var(--accent));
}

.btn-sm {
  padding: 0.25rem 0.75rem;
  font-size: 0.75rem;
  height: auto;
}

/* Copy button styles */
.copy-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 500;
  color: hsl(var(--muted-foreground));
  background-color: transparent;
  border: 1px solid hsl(var(--border));
  border-radius: calc(var(--radius) - 2px);
  cursor: pointer;
  transition: all 0.2s ease;
  height: auto;
}

.copy-btn:hover {
  color: hsl(var(--foreground));
  background-color: hsl(var(--muted));
  border-color: hsl(var(--border));
}

.copy-btn:active {
  transform: translateY(1px);
}

.copy-btn.copied {
  color: hsl(var(--primary));
  background-color: hsl(var(--primary) / 0.1);
  border-color: hsl(var(--primary));
}

/* Better commit hash styling */
.commit-hash {
  font-family: monospace;
  font-size: 0.875rem;
  background: hsl(var(--muted));
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  color: hsl(var(--muted-foreground));
  display: inline-block;
}

/* Code snippet styles */
.code-snippet {
  position: relative;
  background-color: transparent;
  border: none;
  overflow: hidden;
  margin-top: 0.5rem;
  margin-bottom: 0.5rem;
}

.code-snippet-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background-color: hsl(var(--muted));
  border-bottom: 1px solid hsl(var(--border));
}

.code-snippet-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: hsl(var(--foreground));
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.code-snippet-content {
  padding: 0;
  background-color: transparent;
}

.code-snippet pre {
  margin: 0;
  padding: 0.75rem 1rem;
  background-color: transparent;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.875rem;
  line-height: 1.5;
  color: hsl(var(--foreground));
  overflow-x: auto;
  white-space: pre;
}

.code-snippet code {
  font-family: inherit;
  font-size: inherit;
  color: inherit;
}

/* Copy button styles */
.copy-code-btn {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  height: auto;
  min-height: 1.75rem;
}

.copy-code-btn.copied {
  background: hsl(var(--primary));
  color: hsl(var(--primary-foreground));
}

/* File actions */
.file-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}
"""


def generate_file_access_code(
    code_id: str, filename: str, variable_name: str = "dataset"
) -> str:
    """Generate Python code snippet for accessing a file.

    Args:
        code_id: Unique ID for the code snippet element
        filename: Name of the file to access
        variable_name: Name of the dataset variable to use in the code snippet.
                      Defaults to "dataset".

    Returns:
        HTML string with code snippet (hidden by default)
    """
    code = f"""# Get path to local clone of file
with {escape_html(variable_name)}.local_files() as files:
    file_path = files["{escape_html(filename)}"]"""
    escaped_code = escape_html(code)
    return (
        f'<div id="{code_id}" class="code-snippet hidden">'
        f'<div class="code-snippet-content">'
        f"<pre><code>{escaped_code}</code></pre>"
        f"</div></div>"
    )


def get_inline_javascript() -> str:
    """Return inline JavaScript for interactivity.

    Returns:
        JavaScript string for toggling code snippets and copying code
    """
    return """
<script>
(function() {
  // Toggle code snippet visibility when file item is clicked
  function toggleCodeSnippet(event) {
    // Don't toggle if clicking on the copy button
    if (event.target.closest('.copy-code-btn')) {
      return;
    }

    const fileItem = event.target.closest('.file-item[data-code-id]');
    if (!fileItem) return;

    const codeId = fileItem.getAttribute('data-code-id');
    if (!codeId) return;

    const codeSnippet = document.getElementById(codeId);
    if (!codeSnippet) return;

    codeSnippet.classList.toggle('hidden');
  }

  // Copy code to clipboard
  function copyCodeToClipboard(button) {
    // Get code directly from button's data-code attribute
    let code = button.getAttribute('data-code');

    // Fallback: try to get from code snippet if data-code is not available
    if (!code) {
      const codeId = button.getAttribute('data-code-id');
      if (codeId) {
        const codeSnippet = document.getElementById(codeId);
        if (codeSnippet) {
          const codeElement = codeSnippet.querySelector('code');
          if (codeElement) {
            code = codeElement.textContent;
          }
        }
      }
    }

    if (!code) {
      console.error('No code found to copy');
      return;
    }

    // Decode HTML entities (like &#10; for newlines, &quot; for quotes, etc.)
    const decodeHtml = function(html) {
      const txt = document.createElement('textarea');
      txt.innerHTML = html;
      return txt.value;
    };
    code = decodeHtml(code);

    // Trim whitespace
    code = code.trim();

    // Try modern clipboard API first
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(code).then(function() {
        // Show feedback
        const originalText = button.textContent;
        button.textContent = 'Copied!';
        button.classList.add('copied');
        setTimeout(function() {
          button.textContent = originalText;
          button.classList.remove('copied');
        }, 2000);
      }).catch(function(err) {
        console.error('Failed to copy:', err);
        // Fallback to old method
        fallbackCopy(code, button);
      });
    } else {
      // Fallback for older browsers
      fallbackCopy(code, button);
    }
  }

  // Fallback copy method for older browsers
  function fallbackCopy(text, button) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
      const successful = document.execCommand('copy');
      if (successful) {
        const originalText = button.textContent;
        button.textContent = 'Copied!';
        button.classList.add('copied');
        setTimeout(function() {
          button.textContent = originalText;
          button.classList.remove('copied');
        }, 2000);
      }
    } catch (err) {
      console.error('Fallback copy failed:', err);
    }

    document.body.removeChild(textArea);
  }

  // Initialize event listeners
  function init() {
    // Use event delegation for all clicks
    document.addEventListener('click', function(event) {
      // Check if the click is on or inside a copy button
      const copyButton = event.target.closest('.copy-code-btn');
      if (copyButton) {
        event.stopPropagation(); // Prevent toggling the code snippet
        event.preventDefault(); // Prevent any default behavior
        copyCodeToClipboard(copyButton);
        return false;
      }

      // Handle file item clicks (toggle code snippet)
      // But only if not clicking on the copy button or its children
      const fileItem = event.target.closest('.file-item[data-code-id]');
      if (fileItem) {
        // Make sure we're not clicking on the copy button
        const clickedCopyButton = event.target.closest('.copy-code-btn');
        if (!clickedCopyButton) {
          toggleCodeSnippet(event);
        }
      }
    });
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
</script>
"""
