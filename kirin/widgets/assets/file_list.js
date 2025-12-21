import { escapeHtml } from "./ui_utils.js";
import { createCodeSnippet } from "./panel_utils.js";

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
