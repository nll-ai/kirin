"""Interactive file list widget using anywidget.

This widget displays a list of files with clickable items that expand to show
code snippets for accessing files via dataset.local_files().
"""

import anywidget
import traitlets


class FileListWidget(anywidget.AnyWidget):
    """Interactive file list widget with expandable code snippets.

    Displays a list of files with icons, names, and sizes. Clicking a file
    item toggles the visibility of a code snippet showing how to access that
    file using dataset.local_files().

    Attributes:
        files: List of file dictionaries with name, size, and icon_html
        dataset_name: Name of the dataset (used in code snippet)
        expanded_files: List of file indices that are currently expanded
    """

    _esm = """
    function render({ model, el }) {
      const files = model.get("files") || [];
      const datasetName = model.get("dataset_name") || "";
      const expandedFiles = new Set(
        (model.get("expanded_files") || []).map(String)
      );

      // Clear existing content
      el.innerHTML = "";
      el.className = "kirin-file-list";

      // Render each file
      files.forEach((file, index) => {
        const fileItem = createFileItem(
          file,
          datasetName,
          index,
          expandedFiles,
          model
        );
        el.appendChild(fileItem);
      });

      // Listen for expansion changes
      model.on("change:expanded_files", () => {
        const newExpanded = new Set(
          (model.get("expanded_files") || []).map(String)
        );
        updateExpandedState(el, newExpanded);
      });
    }

    function createFileItem(file, datasetName, index, expandedFiles, model) {
      const item = document.createElement("div");
      item.className = "file-item";
      item.dataset.index = index;

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
      codeSnippet.className = expandedFiles.has(String(index))
        ? "code-snippet"
        : "code-snippet hidden";
      item.appendChild(codeSnippet);

      return item;
    }

    function createCodeSnippet(filename, datasetName) {
      const snippet = document.createElement("div");
      snippet.className = "code-snippet";

      // Escape HTML to prevent XSS
      const escapedFilename = filename
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");

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

    function updateExpandedState(container, expandedFiles) {
      container.querySelectorAll(".file-item").forEach((item, index) => {
        const snippet = item.querySelector(".code-snippet");
        if (snippet) {
          if (expandedFiles.has(String(index))) {
            snippet.classList.remove("hidden");
          } else {
            snippet.classList.add("hidden");
          }
        }
      });
    }

    export default { render };
    """

    _css = """
    /* File list container */
    .kirin-file-list {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    /* File item */
    .file-item {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.5rem;
      border-radius: 4px;
      cursor: pointer;
      transition: background-color 0.2s;
    }

    .file-item:hover {
      background-color: hsl(0 0% 96.1%);
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
      color: hsl(222.2 84% 4.9%);
    }

    .file-size {
      font-size: 0.75rem;
      color: hsl(215.4 16.3% 46.9%);
    }

    /* Code snippet */
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
      color: hsl(222.2 84% 4.9%);
      overflow-x: auto;
      white-space: pre;
      background-color: transparent;
    }
    """

    # Python state synchronized with JavaScript
    files = traitlets.List(default_value=[]).tag(sync=True)
    dataset_name = traitlets.Unicode(default_value="").tag(sync=True)
    expanded_files = traitlets.List(default_value=[]).tag(sync=True)
