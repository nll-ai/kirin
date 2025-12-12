"""Catalog widget for interactive HTML representation."""

import anywidget
import traitlets


class CatalogWidget(anywidget.AnyWidget):
    """Interactive catalog widget with dataset list."""

    _esm = """
    function render({ model, el }) {
      const data = model.get("data");
      if (!data) return;

      el.innerHTML = "";
      el.className = "kirin-catalog-view";

      // Header panel
      const headerPanel = createPanel(
        "Catalog",
        createHeaderContent(data)
      );
      el.appendChild(headerPanel);

      // Datasets panel
      if (data.datasets && data.datasets.length > 0) {
        const datasetsPanel = createDatasetsPanel(data.datasets, data.total_size);
        el.appendChild(datasetsPanel);
      } else {
        const emptyPanel = createPanel(
          "Datasets",
          '<p class="text-muted-foreground">No datasets in catalog</p>'
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
      html += '<span class="text-sm text-muted-foreground">Root Directory:</span> ';
      html += `<span class="text-sm">${escapeHtml(data.root_dir)}</span>`;
      html += "</div>";

      html += '<div>';
      html += `<span class="text-sm text-muted-foreground">` +
        `Datasets: ${data.dataset_count}</span>`;
      html += "</div>";

      html += "</div>";
      return html;
    }

    function createDatasetsPanel(datasets, totalSize) {
      const panel = createPanel("Datasets", "");
      const content = panel.querySelector(".panel-content");

      datasets.forEach((dataset) => {
        const item = document.createElement("div");
        item.className = "commit-item";

        const header = document.createElement("div");
        header.className = "flex items-center justify-between gap-4";
        const nameDiv = document.createElement("div");
        nameDiv.className = "font-semibold";
        nameDiv.textContent = dataset.name;
        header.appendChild(nameDiv);
        item.appendChild(header);

        if (dataset.description) {
          const desc = document.createElement("div");
          desc.className = "text-sm text-muted-foreground";
          desc.textContent = dataset.description;
          item.appendChild(desc);
        }

        if (dataset.commit) {
          const commitInfo = document.createElement("div");
          commitInfo.className = "text-sm text-muted-foreground mt-2";
          commitInfo.innerHTML = `
            <span class="commit-hash">${escapeHtml(dataset.commit.hash)}</span>
            <span>${escapeHtml(dataset.commit.message)}</span>
          `;
          item.appendChild(commitInfo);

          const stats = document.createElement("div");
          stats.className = "text-sm text-muted-foreground";
          stats.textContent = `${dataset.commit.file_count} files, ` +
            `${escapeHtml(dataset.commit.size)}`;
          item.appendChild(stats);
        } else {
          const noCommits = document.createElement("div");
          noCommits.className = "text-sm text-muted-foreground";
          noCommits.textContent = "No commits";
          item.appendChild(noCommits);
        }

        content.appendChild(item);
      });

      if (totalSize > 0) {
        const statsDiv = document.createElement("div");
        statsDiv.className = "mt-4 pt-4 border-t";
        const statsText = document.createElement("div");
        statsText.className = "text-sm text-muted-foreground";
        statsText.textContent = `Total size across all datasets: ` +
          `${escapeHtml(totalSize)}`;
        statsDiv.appendChild(statsText);
        content.appendChild(statsDiv);
      }

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

    .kirin-catalog-view {
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

    .mt-4 {
      margin-top: 1rem;
    }

    .pt-4 {
      padding-top: 1rem;
    }

    .border-t {
      border-top: 1px solid hsl(var(--border));
    }

    /* Text styles */
    .text-sm {
      font-size: 0.875rem;
    }

    .font-semibold {
      font-weight: 600;
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

    .commit-item {
      padding: 0.75rem 0;
      border-bottom: 1px solid hsl(var(--border));
    }

    .commit-item:last-child {
      border-bottom: none;
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

        html_parts = ['<div class="kirin-catalog-view-static" style="display:none;">']

        # Include CSS from widget
        html_parts.append(f"<style>{self._css}</style>")

        # Header panel
        html_parts.append('<div class="panel">')
        html_parts.append('<div class="panel-header">')
        html_parts.append('<h2 class="panel-title">Catalog</h2>')
        html_parts.append("</div>")
        html_parts.append('<div class="panel-content">')

        html_parts.append('<div class="space-y-4">')
        html_parts.append("<div>")
        html_parts.append(
            '<span class="text-sm text-muted-foreground">Root Directory:</span> '
        )
        html_parts.append(
            f'<span class="text-sm">'
            f"{html_module.escape(data.get('root_dir', ''))}</span>"
        )
        html_parts.append("</div>")

        html_parts.append("<div>")
        html_parts.append(
            f'<span class="text-sm text-muted-foreground">'
            f"Datasets: {data.get('dataset_count', 0)}</span>"
        )
        html_parts.append("</div>")
        html_parts.append("</div>")
        html_parts.append("</div>")
        html_parts.append("</div>")

        # Datasets
        if data.get("datasets"):
            html_parts.append('<div class="panel">')
            html_parts.append('<div class="panel-header">')
            html_parts.append('<h3 class="panel-title">Datasets</h3>')
            html_parts.append("</div>")
            html_parts.append('<div class="panel-content">')

            for dataset in data["datasets"]:
                html_parts.append('<div class="commit-item">')
                html_parts.append(
                    '<div class="flex items-center justify-between gap-4">'
                )
                html_parts.append("<div>")
                html_parts.append(
                    f'<div class="font-semibold">'
                    f"{html_module.escape(dataset.get('name', ''))}</div>"
                )
                if dataset.get("description"):
                    html_parts.append(
                        f'<div class="text-sm text-muted-foreground">'
                        f"{html_module.escape(dataset['description'])}</div>"
                    )
                html_parts.append("</div>")
                html_parts.append("</div>")

                if dataset.get("commit"):
                    commit = dataset["commit"]
                    html_parts.append(
                        '<div class="text-sm text-muted-foreground mt-2">'
                    )
                    html_parts.append(
                        f'<span class="commit-hash">'
                        f"{html_module.escape(commit['hash'])}</span> "
                    )
                    html_parts.append(
                        f"<span>{html_module.escape(commit['message'])}</span>"
                    )
                    html_parts.append("</div>")
                    html_parts.append(
                        f'<div class="text-sm text-muted-foreground">'
                        f"{commit['file_count']} files, "
                        f"{html_module.escape(commit['size'])}"
                        f"</div>"
                    )
                else:
                    html_parts.append(
                        '<div class="text-sm text-muted-foreground">No commits</div>'
                    )

                html_parts.append("</div>")

            if data.get("total_size"):
                html_parts.append('<div class="mt-4 pt-4 border-t">')
                html_parts.append(
                    f'<div class="text-sm text-muted-foreground">'
                    f"Total size across all datasets: "
                    f"{html_module.escape(data['total_size'])}"
                    f"</div>"
                )
                html_parts.append("</div>")

            html_parts.append("</div>")
            html_parts.append("</div>")
        else:
            html_parts.append('<div class="panel">')
            html_parts.append('<div class="panel-content">')
            html_parts.append(
                '<p class="text-muted-foreground">No datasets in catalog</p>'
            )
            html_parts.append("</div>")
            html_parts.append("</div>")

        html_parts.append("</div>")
        return "".join(html_parts)
