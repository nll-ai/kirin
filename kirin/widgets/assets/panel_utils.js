/**
 * Shared utility functions for creating panel UI components.
 */

import { escapeHtml } from "./ui_utils.js";

/**
 * Create a panel element with header and content.
 *
 * @param {string} title - Panel title
 * @param {string} content - Panel content HTML
 * @returns {HTMLElement} Panel element
 */
export function createPanel(title, content) {
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

/**
 * Create a code snippet element for file access.
 *
 * @param {string} filename - File name
 * @param {string} datasetName - Dataset name (for code generation)
 * @returns {HTMLElement} Code snippet element
 */
export function createCodeSnippet(filename, datasetName) {
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
