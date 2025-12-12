"""Dataset widget for interactive HTML representation."""

import anywidget
import traitlets


class DatasetWidget(anywidget.AnyWidget):
    """Interactive dataset widget with files and commit history."""

    _esm = """
    function render({ model, el }) {
      const data = model.get("data");
      if (!data) return;

      el.innerHTML = "";
      el.className = "kirin-dataset-view";

      // Header panel
      const headerPanel = createPanel(
        data.name,
        createHeaderContent(data)
      );
      el.appendChild(headerPanel);

      // Files panel (if files exist)
      if (data.files && data.files.length > 0) {
        const filesPanel = createFilesPanel(data.files, data.name);
        el.appendChild(filesPanel);
      } else if (data.has_commit) {
        const emptyPanel = createPanel(
          "Files",
          '<p class="text-muted-foreground">No files in current commit</p>'
        );
        el.appendChild(emptyPanel);
      }

      // Commit history panel
      if (data.history && data.history.length > 0) {
        const historyPanel = createHistoryPanel(data.history);
        el.appendChild(historyPanel);
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

      if (data.description) {
        html += `<p class="text-muted-foreground">${escapeHtml(data.description)}</p>`;
      }

      html += '<div class="flex items-center gap-4">';
      html += `<span class="text-sm text-muted-foreground">` +
        `Commits: ${data.commit_count}</span>`;

      if (data.total_size) {
        html += `<span class="text-sm text-muted-foreground">` +
          `Size: ${escapeHtml(data.total_size)}</span>`;
      }
      html += "</div>";

      if (data.current_commit) {
        html += '<div>';
        html += '<span class="text-sm text-muted-foreground">' +
          "Current Commit:</span> ";
        html += `<span class="commit-hash">` +
          `${escapeHtml(data.current_commit.hash)}</span> `;
        html += `<span class="text-sm">` +
          `${escapeHtml(data.current_commit.message)}</span>`;
        html += "</div>";
      } else {
        html += '<p class="text-muted-foreground">No commits yet</p>';
      }

      html += "</div>";
      return html;
    }

    function createFilesPanel(files, datasetName) {
      const panel = createPanel("Files", "");
      const content = panel.querySelector(".panel-content");

      const fileList = document.createElement("div");
      fileList.className = "kirin-file-list";

      files.forEach((file, index) => {
        const fileItem = createFileItem(file, datasetName, index, model);
        fileList.appendChild(fileItem);
      });

      content.appendChild(fileList);
      return panel;
    }

    function createFileItem(file, datasetName, index, model) {
      const item = document.createElement("div");
      item.className = "file-item";
      item.dataset.index = index;
      item.style.cursor = "pointer";

      // File icon
      const icon = document.createElement("div");
      icon.className = "file-icon";
      icon.innerHTML = file.icon_html || "";

      // File name
      const name = document.createElement("div");
      name.className = "file-name";
      name.textContent = file.name || "";

      // File size
      const size = document.createElement("div");
      size.className = "file-size";
      size.textContent = file.size || "";

      // Click handler
      item.addEventListener("click", () => {
        const expanded = (model.get("expanded_files") || []).map(String);
        const indexStr = String(index);

        if (expanded.includes(indexStr)) {
          model.set(
            "expanded_files",
            expanded.filter((i) => i !== indexStr)
          );
        } else {
          model.set("expanded_files", [...expanded, indexStr]);
        }
        model.save_changes();
      });

      item.appendChild(icon);
      item.appendChild(name);
      item.appendChild(size);

      // Code snippet (initially hidden)
      const codeSnippet = createCodeSnippet(file.name || "", datasetName);
      const expandedFiles = new Set(
        (model.get("expanded_files") || []).map(String)
      );
      codeSnippet.className = expandedFiles.has(String(index))
        ? "code-snippet"
        : "code-snippet hidden";
      item.appendChild(codeSnippet);

      // Listen for expansion changes
      model.on("change:expanded_files", () => {
        const newExpanded = new Set(
          (model.get("expanded_files") || []).map(String)
        );
        if (newExpanded.has(String(index))) {
          codeSnippet.classList.remove("hidden");
        } else {
          codeSnippet.classList.add("hidden");
        }
      });

      return item;
    }

    function createCodeSnippet(filename, datasetName) {
      const snippet = document.createElement("div");
      snippet.className = "code-snippet";

      const escapedFilename = escapeHtml(filename);
      const code = `# Get path to local clone of file
with dataset.local_files() as files:
    file_path = files["${escapedFilename}"]`;

      const pre = document.createElement("pre");
      const codeEl = document.createElement("code");
      codeEl.textContent = code;
      pre.appendChild(codeEl);
      snippet.appendChild(pre);

      return snippet;
    }

    function createHistoryPanel(history) {
      const panel = createPanel("Recent Commits", "");
      const content = panel.querySelector(".panel-content");

      history.forEach((commit) => {
        const item = document.createElement("div");
        item.className = "commit-item";

        const header = document.createElement("div");
        header.className = "flex items-center justify-between gap-4";
        header.innerHTML = `
          <div>
            <span class="commit-hash">${escapeHtml(commit.hash)}</span>
            <span class="commit-message">${escapeHtml(commit.message)}</span>
          </div>
          <span class="commit-timestamp">${escapeHtml(commit.timestamp)}</span>
        `;

        const stats = document.createElement("div");
        stats.className = "text-sm text-muted-foreground mt-2";
        stats.textContent = `${commit.file_count} files, ${escapeHtml(commit.size)}`;

        item.appendChild(header);
        item.appendChild(stats);
        content.appendChild(item);
      });

      return panel;
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

    .kirin-dataset-view {
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

    .justify-between {
      justify-content: space-between;
    }

    .gap-4 {
      gap: 1rem;
    }

    .mt-2 {
      margin-top: 0.5rem;
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

    .commit-item {
      padding: 0.75rem 0;
      border-bottom: 1px solid hsl(var(--border));
    }

    .commit-item:last-child {
      border-bottom: none;
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
      transition: background-color 0.2s;
    }

    .file-item:hover {
      background-color: hsl(var(--muted) / 0.5);
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

    /* Code snippet styles */
    .code-snippet {
      width: 100%;
      margin-top: 0.5rem;
      padding-left: 1.75rem;
    }

    .code-snippet.hidden {
      display: none;
    }

    .code-snippet pre {
      margin: 0;
      padding: 0.75rem 1rem;
      font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
      font-size: 0.875rem;
      line-height: 1.5;
      color: hsl(var(--foreground));
      overflow-x: auto;
      white-space: pre;
      background-color: transparent;
    }
    """

    # Python state synchronized with JavaScript
    data = traitlets.Dict(default_value={}).tag(sync=True)
    expanded_files = traitlets.List(default_value=[]).tag(sync=True)

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
        # The widget will be rendered by the notebook frontend, but we also
        # include static HTML as a fallback and for testing
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

        # This is a fallback/static representation
        # The actual interactive widget will be rendered by the frontend
        html_parts = ['<div class="kirin-dataset-view-static" style="display:none;">']

        # Include CSS from widget
        html_parts.append(f"<style>{self._css}</style>")

        # Header panel
        html_parts.append('<div class="panel">')
        html_parts.append('<div class="panel-header">')
        html_parts.append(
            f'<h2 class="panel-title">{html_module.escape(data.get("name", ""))}</h2>'
        )
        html_parts.append("</div>")
        html_parts.append('<div class="panel-content">')

        # Metadata
        html_parts.append('<div class="space-y-4">')
        if data.get("description"):
            html_parts.append(
                f'<p class="text-muted-foreground">'
                f"{html_module.escape(data['description'])}</p>"
            )

        html_parts.append('<div class="flex items-center gap-4">')
        html_parts.append(
            f'<span class="text-sm text-muted-foreground">'
            f"Commits: {data.get('commit_count', 0)}</span>"
        )
        if data.get("total_size"):
            html_parts.append(
                f'<span class="text-sm text-muted-foreground">'
                f"Size: {html_module.escape(data['total_size'])}</span>"
            )
        html_parts.append("</div>")

        if data.get("current_commit"):
            commit = data["current_commit"]
            html_parts.append("<div>")
            html_parts.append('<span class="text-sm text-muted-foreground">')
            html_parts.append("Current Commit:</span> ")
            html_parts.append(
                f'<span class="commit-hash">'
                f"{html_module.escape(commit['hash'])}</span> "
            )
            html_parts.append(
                f'<span class="text-sm">{html_module.escape(commit["message"])}</span>'
            )
            html_parts.append("</div>")
        else:
            html_parts.append('<p class="text-muted-foreground">No commits yet</p>')

        html_parts.append("</div>")  # space-y-4
        html_parts.append("</div>")  # panel-content
        html_parts.append("</div>")  # panel

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

                # Add code snippet for file access
                filename = file_info.get("name", "")
                code_snippet = f"""# Get path to local clone of file
with dataset.local_files() as files:
    file_path = files["{html_module.escape(filename)}"]"""
                html_parts.append('<div class="code-snippet">')
                html_parts.append("<pre><code>")
                html_parts.append(html_module.escape(code_snippet))
                html_parts.append("</code></pre>")
                html_parts.append("</div>")

            html_parts.append("</div>")
            html_parts.append("</div>")
        elif data.get("has_commit"):
            html_parts.append('<div class="panel">')
            html_parts.append('<div class="panel-content">')
            html_parts.append(
                '<p class="text-muted-foreground">No files in current commit</p>'
            )
            html_parts.append("</div>")
            html_parts.append("</div>")

        # History
        if data.get("history"):
            html_parts.append('<div class="panel">')
            html_parts.append('<div class="panel-header">')
            html_parts.append('<h3 class="panel-title">Recent Commits</h3>')
            html_parts.append("</div>")
            html_parts.append('<div class="panel-content">')
            for commit in data["history"]:
                html_parts.append('<div class="commit-item">')
                html_parts.append(
                    '<div class="flex items-center justify-between gap-4">'
                )
                html_parts.append("<div>")
                html_parts.append(
                    f'<span class="commit-hash">'
                    f"{html_module.escape(commit['hash'])}</span> "
                )
                html_parts.append(
                    f'<span class="commit-message">'
                    f"{html_module.escape(commit['message'])}</span>"
                )
                html_parts.append("</div>")
                html_parts.append(
                    f'<span class="commit-timestamp">'
                    f"{html_module.escape(commit['timestamp'])}</span>"
                )
                html_parts.append("</div>")
                html_parts.append(
                    f'<div class="text-sm text-muted-foreground mt-2">'
                    f"{commit['file_count']} files, "
                    f"{html_module.escape(commit['size'])}"
                    f"</div>"
                )
                html_parts.append("</div>")
            html_parts.append("</div>")
            html_parts.append("</div>")

        html_parts.append("</div>")  # kirin-dataset-view-static
        return "".join(html_parts)
