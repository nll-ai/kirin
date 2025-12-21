import { escapeHtml } from "./ui_utils.js";
import { createPanel } from "./panel_utils.js";

function render({ model, el }) {
  const data = model.get("data");
  if (!data) return;

  el.innerHTML = "";
  el.className = "kirin-catalog-view";

  // Header panel
  const headerPanel = createPanel("Catalog", createHeaderContent(data));
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

function createHeaderContent(data) {
  let html = '<div class="space-y-4">';

  html += '<div>';
  html += '<span class="text-sm text-muted-foreground">Root Directory:</span> ';
  html += `<span class="text-sm">${escapeHtml(data.root_dir)}</span>`;
  html += "</div>";

  html += '<div>';
  html +=
    `<span class="text-sm text-muted-foreground">` +
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
      stats.textContent =
        `${dataset.commit.file_count} files, ` +
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

  if (totalSize) {
    const statsDiv = document.createElement("div");
    statsDiv.className = "mt-4 pt-4 border-t";
    const statsText = document.createElement("div");
    statsText.className = "text-sm text-muted-foreground";
    statsText.textContent =
      `Total size across all datasets: ` + `${escapeHtml(totalSize)}`;
    statsDiv.appendChild(statsText);
    content.appendChild(statsDiv);
  }

  return panel;
}

export default { render };
