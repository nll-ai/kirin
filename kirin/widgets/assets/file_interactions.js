/**
 * Shared file interaction handlers for widget templates.
 * Handles copy button clicks and file preview toggling.
 */
(function() {
  function initFileInteractions() {
    // Use event delegation for copy buttons (works even after cloning)
    const fileList = document.querySelector(".kirin-file-list");
    if (!fileList) return;

    fileList.addEventListener("click", function (e) {
    // Check if clicked element is a copy button
    const copyButton = e.target.closest(".copy-code-btn");
    if (copyButton) {
      e.stopPropagation(); // Prevent file item click
      e.preventDefault(); // Prevent any default behavior

      const codeId = copyButton.getAttribute("data-code-id");
      const fileIndex = copyButton.getAttribute("data-file-index");
      const dataCode = copyButton.getAttribute("data-code");

      // Try data-code attribute first (pre-escaped HTML)
      let text = null;
      if (dataCode) {
        // Decode HTML entities (e.g., &#10; -> newline)
        const tempDiv = document.createElement("div");
        tempDiv.innerHTML = dataCode;
        text = tempDiv.textContent || tempDiv.innerText;
      }

      // Fallback: try to find code content by ID
      if (!text) {
        const codeContentId = "code-content-" + fileIndex;
        let codeContent = document.getElementById(codeContentId);

        // Fallback: try to find code element in code snippet div
        if (!codeContent) {
          const codeElement = document.getElementById(codeId);
          if (codeElement) {
            codeContent = codeElement.querySelector("code");
          }
        }

        if (codeContent) {
          text = codeContent.textContent || codeContent.innerText;
        }
      }

      if (!text) {
        console.error("Could not find code content to copy");
        return;
      }

      // Try modern clipboard API
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () {
          const originalText = copyButton.textContent;
          copyButton.textContent = "Copied!";
          setTimeout(function () {
            copyButton.textContent = originalText;
          }, 2000);
        }).catch(function (err) {
          console.error("Failed to copy:", err);
        });
      } else {
        // Fallback for older browsers
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "fixed";
        textArea.style.left = "-999999px";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
          document.execCommand("copy");
          const originalText = copyButton.textContent;
          copyButton.textContent = "Copied!";
          setTimeout(function () {
            copyButton.textContent = originalText;
          }, 2000);
        } catch (err) {
          console.error("Fallback copy failed:", err);
        }
        document.body.removeChild(textArea);
      }
      return; // Don't process as file item click
    }

    // Handle file item clicks - show preview (primary action)
    const fileItem = e.target.closest(".file-item");
    if (fileItem && !e.target.closest(".copy-code-btn")) {
      const index = fileItem.getAttribute("data-file-index");
      const codeId = "code-" + index;
      const previewId = "preview-" + index;

      const codeSnippet = document.getElementById(codeId);
      const preview = document.getElementById(previewId);

      console.log(
        "File clicked, index:",
        index,
        "preview exists:",
        !!preview,
        "code snippet exists:",
        !!codeSnippet
      );

      // Always hide code snippet first
      if (codeSnippet) {
        codeSnippet.classList.add("hidden");
      }

      // Show preview if it exists (primary action)
      if (preview) {
        // Toggle preview visibility
        preview.classList.toggle("hidden");
        console.log(
          "Preview toggled, now hidden:",
          preview.classList.contains("hidden")
        );
      } else {
        // If no preview exists, show code snippet as fallback
        console.log("No preview found, showing code snippet as fallback");
        if (codeSnippet) {
          codeSnippet.classList.remove("hidden");
        }
      }
    }
  });
  }

  // Auto-initialize when DOM is ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initFileInteractions);
  } else {
    initFileInteractions();
  }
})();
