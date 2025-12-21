/**
 * Shared utility functions for Kirin widgets.
 * Provides clipboard handling and HTML escaping helpers.
 */

/**
 * Escape HTML special characters to prevent XSS attacks.
 * @param {string} text - Text to escape
 * @returns {string} Escaped HTML string
 */
export function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Decode HTML entities (like &#10; for newlines, &quot; for quotes, etc.)
 * @param {string} html - HTML string with entities
 * @returns {string} Decoded string
 */
export function decodeHtml(html) {
  const txt = document.createElement("textarea");
  txt.innerHTML = html;
  return txt.value;
}

/**
 * Copy text to clipboard with fallback for older browsers.
 * @param {string} text - Text to copy
 * @returns {Promise<void>} Promise that resolves when copy is complete
 */
export function copyToClipboard(text) {
  // Try modern clipboard API first
  if (navigator.clipboard && navigator.clipboard.writeText) {
    return navigator.clipboard.writeText(text).catch((err) => {
      console.error("Failed to copy with clipboard API:", err);
      // Fallback to old method
      return fallbackCopy(text);
    });
  } else {
    // Fallback for older browsers
    return Promise.resolve(fallbackCopy(text));
  }
}

/**
 * Fallback copy method for older browsers using execCommand.
 * @param {string} text - Text to copy
 * @returns {boolean} True if copy was successful
 */
function fallbackCopy(text) {
  const textArea = document.createElement("textarea");
  textArea.value = text;
  textArea.style.position = "fixed";
  textArea.style.left = "-999999px";
  textArea.style.top = "-999999px";
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();

  try {
    const successful = document.execCommand("copy");
    document.body.removeChild(textArea);
    return successful;
  } catch (err) {
    console.error("Fallback copy failed:", err);
    document.body.removeChild(textArea);
    return false;
  }
}

/**
 * Show copy feedback on a button element.
 * Updates button text and adds 'copied' class temporarily.
 * @param {HTMLElement} button - Button element to update
 * @param {string} originalText - Original button text to restore
 * @param {number} duration - Duration in milliseconds (default: 2000)
 */
export function showCopyFeedback(button, originalText, duration = 2000) {
  button.textContent = "Copied!";
  button.classList.add("copied");
  setTimeout(() => {
    button.textContent = originalText;
    button.classList.remove("copied");
  }, duration);
}

/**
 * Copy code to clipboard from a button element.
 * Handles HTML entity decoding and shows feedback.
 * @param {HTMLElement} button - Button element with data-code or data-code-id attribute
 * @returns {Promise<void>} Promise that resolves when copy is complete
 */
export function copyCodeFromButton(button) {
  // Get code directly from button's data-code attribute
  let code = button.getAttribute("data-code");

  // Fallback: try to get from code snippet if data-code is not available
  if (!code) {
    const codeId = button.getAttribute("data-code-id");
    if (codeId) {
      const codeSnippet = document.getElementById(codeId);
      if (codeSnippet) {
        const codeElement = codeSnippet.querySelector("code");
        if (codeElement) {
          code = codeElement.textContent;
        }
      }
    }
  }

  if (!code) {
    console.error("No code found to copy");
    return Promise.reject(new Error("No code found to copy"));
  }

  // Decode HTML entities
  code = decodeHtml(code);

  // Trim whitespace
  code = code.trim();

  const originalText = button.textContent;

  return copyToClipboard(code)
    .then(() => {
      showCopyFeedback(button, originalText);
    })
    .catch((err) => {
      console.error("Failed to copy code:", err);
      throw err;
    });
}
