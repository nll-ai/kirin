import { escapeHtml } from "./ui_utils.js";

function render({ model, el }) {
  const data = model.get("data");
  if (!data) return;

  el.innerHTML = "";
  el.className = "kirin-dataset-view";

  // Header panel
  const headerPanel = createPanel(data.name, createHeaderContent(data));
  el.appendChild(headerPanel);

  // Files panel (if files exist)
  if (data.files && data.files.length > 0) {
    const filesPanel = createFilesPanel(data.files, data.name, model);
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
  html +=
    `<span class="text-sm text-muted-foreground">` +
    `Commits: ${data.commit_count}</span>`;

  if (data.total_size) {
    html +=
      `<span class="text-sm text-muted-foreground">` +
      `Size: ${escapeHtml(data.total_size)}</span>`;
  }
  html += "</div>";

  if (data.current_commit) {
    html += '<div>';
    html +=
      '<span class="text-sm text-muted-foreground">' +
      "Current Commit:</span> ";
    html +=
      `<span class="commit-hash">` +
      `${escapeHtml(data.current_commit.hash)}</span> `;
    html +=
      `<span class="text-sm">` +
      `${escapeHtml(data.current_commit.message)}</span>`;
    html += "</div>";
  } else {
    html += '<p class="text-muted-foreground">No commits yet</p>';
  }

  html += "</div>";
  return html;
}

function createFilesPanel(files, datasetName, model) {
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

export default { render };
