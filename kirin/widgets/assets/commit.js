import { escapeHtml } from "./ui_utils.js";

function render({ model, el }) {
  const data = model.get("data");
  if (!data) return;

  el.innerHTML = "";
  el.className = "kirin-commit-view";

  // Header panel
  const headerPanel = createPanel("Commit", createHeaderContent(data));
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
  html +=
    `<span class="text-sm text-muted-foreground">` +
    `Files: ${data.file_count}</span>`;
  html +=
    `<span class="text-sm text-muted-foreground">` +
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

export default { render };
