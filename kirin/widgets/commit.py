"""Commit widget for interactive HTML representation."""

import anywidget
import traitlets


class CommitWidget(anywidget.AnyWidget):
    """Interactive commit widget with file list."""

    _esm = """
    function render({ model, el }) {
      const data = model.get("data");
      if (!data) return;

      el.innerHTML = "";
      el.className = "kirin-commit-view";

      // Header panel
      const headerPanel = createPanel(
        "Commit",
        createHeaderContent(data)
      );
      el.appendChild(headerPanel);

      // Files panel
      if (data.files && data.files.length > 0) {
        const filesPanel = createFilesPanel(data.files);
        el.appendChild(filesPanel);
      } else {
        const emptyPanel = createPanel(
          "Files",
          '<p class="text-muted-foreground">No files in this commit</p>'
        );
        el.appendChild(emptyPanel);
      }
    }

    function createPanel(title, content) {
      const panel = document.createElement("div");
      panel.className = "panel";

      const header = document.createElement("div");
      header.className = "panel-header";
      const titleEl = document.createElement("h2");
      titleEl.className = "panel-title";
      titleEl.textContent = title;
      header.appendChild(titleEl);
      panel.appendChild(header);

      const body = document.createElement("div");
      body.className = "panel-content";
      body.innerHTML = content;
      panel.appendChild(body);

      return panel;
    }

    function createHeaderContent(data) {
      let html = '<div class="space-y-4">';

      html += '<div>';
      html += '<span class="text-sm text-muted-foreground">Hash:</span> ';
      html += `<span class="commit-hash">${escapeHtml(data.hash)}</span>`;
      html += "</div>";

      html += '<div>';
      html += '<span class="text-sm text-muted-foreground">Message:</span> ';
      html += `<span class="commit-message">${escapeHtml(data.message)}</span>`;
      html += "</div>";

      html += '<div>';
      html += '<span class="text-sm text-muted-foreground">Timestamp:</span> ';
      html += `<span class="commit-timestamp">${escapeHtml(data.timestamp)}</span>`;
      html += "</div>";

      if (data.parent_hash) {
        html += '<div>';
        html += '<span class="text-sm text-muted-foreground">Parent:</span> ';
        html += `<span class="commit-hash">${escapeHtml(data.parent_hash)}</span>`;
        html += "</div>";
      } else {
        html += '<div><span class="badge">Initial Commit</span></div>';
      }

      html += '<div class="flex items-center gap-4">';
      html += `<span class="text-sm text-muted-foreground">` +
        `Files: ${data.file_count}</span>`;
      html += `<span class="text-sm text-muted-foreground">` +
        `Size: ${escapeHtml(data.size)}</span>`;
      html += "</div>";

      html += "</div>";
      return html;
    }

    function createFilesPanel(files) {
      const panel = createPanel("Files", "");
      const content = panel.querySelector(".panel-content");

      const fileList = document.createElement("div");
      fileList.className = "kirin-file-list";

      files.forEach((file) => {
        const fileItem = createFileItem(file);
        fileList.appendChild(fileItem);
      });

      content.appendChild(fileList);
      return panel;
    }

    function createFileItem(file) {
      const item = document.createElement("div");
      item.className = "file-item";

      const icon = document.createElement("div");
      icon.className = "file-icon";
      icon.innerHTML = file.icon_html || "";

      const name = document.createElement("div");
      name.className = "file-name";
      name.textContent = file.name || "";

      const size = document.createElement("div");
      size.className = "file-size";
      size.textContent = file.size || "";

      item.appendChild(icon);
      item.appendChild(name);
      item.appendChild(size);

      return item;
    }

    function escapeHtml(text) {
      const div = document.createElement("div");
      div.textContent = text;
      return div.innerHTML;
    }

    export default { render };
    """

    _css = """
    /* CSS Variables */
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

    .kirin-commit-view {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
        "Helvetica Neue", Arial, sans-serif;
      line-height: 1.5;
      color: hsl(var(--foreground));
    }

    /* Panel styles */
    .panel {
      background-color: hsl(var(--card));
      border: 1px solid hsl(var(--border));
      border-radius: calc(var(--radius));
      margin-bottom: 1rem;
      overflow: hidden;
    }

    .panel-header {
      padding: 1.25rem 1.5rem;
      border-bottom: 1px solid hsl(var(--border));
    }

    .panel-title {
      font-size: 1.125rem;
      font-weight: 600;
      margin: 0;
      color: hsl(var(--foreground));
    }

    .panel-content {
      padding: 1.5rem;
    }

    /* Spacing utilities */
    .space-y-4 > * + * {
      margin-top: 1rem;
    }

    .flex {
      display: flex;
    }

    .items-center {
      align-items: center;
    }

    .gap-4 {
      gap: 1rem;
    }

    /* Text styles */
    .text-sm {
      font-size: 0.875rem;
    }

    .text-muted-foreground {
      color: hsl(var(--muted-foreground));
    }

    /* Commit styles */
    .commit-hash {
      font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
      font-size: 0.875rem;
      color: hsl(var(--primary));
    }

    .commit-message {
      color: hsl(var(--foreground));
    }

    .commit-timestamp {
      font-size: 0.875rem;
      color: hsl(var(--muted-foreground));
    }

    .badge {
      display: inline-flex;
      align-items: center;
      padding: 0.25rem 0.5rem;
      font-size: 0.75rem;
      font-weight: 500;
      background-color: hsl(var(--primary));
      color: hsl(var(--primary-foreground));
      border-radius: calc(var(--radius) - 2px);
    }

    /* File list styles */
    .kirin-file-list {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .file-item {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.5rem;
      border-radius: 4px;
    }

    .file-icon {
      width: 16px;
      height: 16px;
      flex-shrink: 0;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .file-name {
      flex: 1;
      font-size: 0.875rem;
      color: hsl(var(--foreground));
    }

    .file-size {
      font-size: 0.75rem;
      color: hsl(var(--muted-foreground));
    }
    """

    # Python state synchronized with JavaScript
    data = traitlets.Dict(default_value={}).tag(sync=True)

    def _repr_html_(self) -> str:
        """Generate HTML representation of the widget.

        Returns:
            HTML string with widget embedded and static fallback
        """
        # Get the widget's mimebundle to extract model_id
        bundle = self._repr_mimebundle_()
        if isinstance(bundle, tuple):
            widget_data = bundle[0]
        else:
            widget_data = bundle

        # Extract model_id from widget view JSON
        widget_view = widget_data.get("application/vnd.jupyter.widget-view+json", {})
        model_id = widget_view.get("model_id", "")

        # Generate HTML that includes both the widget container and static content
        data = self.data
        static_html = self._generate_static_html(data)

        return f'<div data-anywidget-id="{model_id}">{static_html}</div>'

    def _generate_static_html(self, data: dict) -> str:
        """Generate static HTML representation from data.

        Args:
            data: Widget data dictionary

        Returns:
            Static HTML string
        """
        import html as html_module

        html_parts = ['<div class="kirin-commit-view-static" style="display:none;">']

        # Include CSS from widget
        html_parts.append(f"<style>{self._css}</style>")

        # Header panel
        html_parts.append('<div class="panel">')
        html_parts.append('<div class="panel-header">')
        html_parts.append('<h2 class="panel-title">Commit</h2>')
        html_parts.append("</div>")
        html_parts.append('<div class="panel-content">')

        html_parts.append('<div class="space-y-4">')
        html_parts.append("<div>")
        html_parts.append('<span class="text-sm text-muted-foreground">Hash:</span> ')
        html_parts.append(
            f'<span class="commit-hash">'
            f"{html_module.escape(data.get('hash', ''))}</span>"
        )
        html_parts.append("</div>")

        html_parts.append("<div>")
        html_parts.append(
            '<span class="text-sm text-muted-foreground">Message:</span> '
        )
        html_parts.append(
            f'<span class="commit-message">'
            f"{html_module.escape(data.get('message', ''))}</span>"
        )
        html_parts.append("</div>")

        html_parts.append("<div>")
        html_parts.append(
            '<span class="text-sm text-muted-foreground">Timestamp:</span> '
        )
        html_parts.append(
            f'<span class="commit-timestamp">'
            f"{html_module.escape(data.get('timestamp', ''))}</span>"
        )
        html_parts.append("</div>")

        if data.get("parent_hash"):
            html_parts.append("<div>")
            html_parts.append(
                '<span class="text-sm text-muted-foreground">Parent:</span> '
            )
            html_parts.append(
                f'<span class="commit-hash">'
                f"{html_module.escape(data['parent_hash'])}</span>"
            )
            html_parts.append("</div>")
        else:
            html_parts.append('<div><span class="badge">Initial Commit</span></div>')

        html_parts.append('<div class="flex items-center gap-4">')
        html_parts.append(
            f'<span class="text-sm text-muted-foreground">'
            f"Files: {data.get('file_count', 0)}</span>"
        )
        html_parts.append(
            f'<span class="text-sm text-muted-foreground">'
            f"Size: {html_module.escape(data.get('size', ''))}</span>"
        )
        html_parts.append("</div>")
        html_parts.append("</div>")
        html_parts.append("</div>")
        html_parts.append("</div>")

        # Files
        if data.get("files"):
            html_parts.append('<div class="panel">')
            html_parts.append('<div class="panel-header">')
            html_parts.append('<h3 class="panel-title">Files</h3>')
            html_parts.append("</div>")
            html_parts.append('<div class="panel-content">')
            for file_info in data["files"]:
                html_parts.append('<div class="file-item">')
                html_parts.append(
                    f'<div class="file-icon">{file_info.get("icon_html", "")}</div>'
                )
                html_parts.append(
                    f'<div class="file-name">'
                    f"{html_module.escape(file_info.get('name', ''))}</div>"
                )
                html_parts.append(
                    f'<div class="file-size">'
                    f"{html_module.escape(file_info.get('size', ''))}</div>"
                )
                html_parts.append("</div>")
            html_parts.append("</div>")
            html_parts.append("</div>")
        else:
            html_parts.append('<div class="panel">')
            html_parts.append('<div class="panel-content">')
            html_parts.append(
                '<p class="text-muted-foreground">No files in this commit</p>'
            )
            html_parts.append("</div>")
            html_parts.append("</div>")

        html_parts.append("</div>")
        return "".join(html_parts)
