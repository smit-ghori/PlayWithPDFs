function showLoader() {
    const overlay = document.getElementById("loader-overlay");
    if (overlay) overlay.style.display = "flex";
}

function hideLoader() {
    const overlay = document.getElementById("loader-overlay");
    if (overlay) overlay.style.display = "none";
}

/**
 * Convert a fetch response containing a file into a downloaded link.
 * Grabs filename from Content-Disposition header if available.
 */
async function downloadFromResponse(resp) {
    const blob = await resp.blob();
    let filename = "download";
    const disposition = resp.headers.get("Content-Disposition");
    if (disposition) {
        const utf8Match = disposition.match(/filename\*=UTF-8''([^;]+)/i);
        const asciiMatch = disposition.match(/filename="?([^";]+)"?/i);
        if (utf8Match) {
            filename = decodeURIComponent(utf8Match[1]);
        } else if (asciiMatch) {
            filename = asciiMatch[1];
        }
    }

    const downloadUrl = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = downloadUrl;
    a.download = filename;
    a.style.display = "none";
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(downloadUrl), 1000);
}

function resetUploader(form) {
    if (form) form.reset();

    const fileList = document.getElementById("fileList");
    if (fileList) fileList.innerHTML = "";

    const pdfInput = document.getElementById("pdfInput");
    if (pdfInput) pdfInput.value = "";

    if (window.selectedFiles && Array.isArray(window.selectedFiles)) {
        window.selectedFiles.length = 0;
    }

    if (typeof window.resetUploadForm === "function") {
        window.resetUploadForm();
    }
}

function showFlashMessage(message, category = "error") {
    let container = document.getElementById("flash-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "flash-container";
        container.className = "flash-wrapper";
        const main = document.querySelector(".main_content") || document.body;
        main.parentNode.insertBefore(container, main);
    }
    const flashDiv = document.createElement("div");
    flashDiv.className = `flash-message ${category}`;
    flashDiv.innerHTML = `
        <span>${message}</span>
        <button type="button" class="flash-close" aria-label="Close notification" onclick="closeFlashMessage(this)">✕</button>
    `;
    container.innerHTML = "";
    container.appendChild(flashDiv);
    container.scrollIntoView({ behavior: "smooth", block: "start" });

    if (typeof window.autoDismissFlashMessage === "function") {
        window.autoDismissFlashMessage(flashDiv, 10000);
    }
}
window.showFlashMessage = showFlashMessage;

function showFlashMessagesFromHtml(html) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");
    const nextFlash = doc.getElementById("flash-container");
    const currentFlash = document.getElementById("flash-container");

    if (!nextFlash || !currentFlash || !nextFlash.innerHTML.trim()) {
        return false;
    }

    currentFlash.innerHTML = nextFlash.innerHTML;
    currentFlash.scrollIntoView({ behavior: "smooth", block: "start" });

    if (typeof window.autoDismissFlashMessage === "function") {
        currentFlash.querySelectorAll(".flash-message").forEach((el) => {
            window.autoDismissFlashMessage(el, 10000);
        });
    }
    return true;
}

// when DOM ready, wire up interactions
document.addEventListener("DOMContentLoaded", () => {
    // show loader on regular form submit and validate file limits
    document.querySelectorAll("form:not(.ajax-upload-form)").forEach((form) => {
        if (form.dataset.noLoader === "true") {
            return;
        }
        form.addEventListener("submit", (e) => {
            const maxFiles = window.TOOL_CONFIG?.max_files;
            if (maxFiles) {
                let totalFiles = 0;
                form.querySelectorAll('input[type="file"]').forEach((inp) => {
                    if (inp.files) {
                        for (let f of inp.files) {
                            if (f && f.name) totalFiles++;
                        }
                    }
                });
                if (totalFiles > maxFiles) {
                    e.preventDefault();
                    showFlashMessage(`Maximum file limit is ${maxFiles}. You selected ${totalFiles} files. Please upload up to ${maxFiles} files only.`, "error");
                    return;
                }
            }
            showLoader();
        });
    });

    // intercept file-upload forms and perform the request via fetch so we can
    // hide the loader once the response is handled (downloaded or HTML returned).
    document.querySelectorAll("form.ajax-upload-form").forEach((form) => {
        form.addEventListener("submit", async (e) => {
            if (e.defaultPrevented) return;
            e.preventDefault();

            const maxFiles = window.TOOL_CONFIG?.max_files;
            const formData = new FormData(form);

            // Count selected files
            let totalFiles = 0;
            for (let [key, val] of formData.entries()) {
                if (val instanceof File && val.name) {
                    totalFiles++;
                }
            }

            if (maxFiles && totalFiles > maxFiles) {
                showFlashMessage(`Maximum file limit is ${maxFiles}. You selected ${totalFiles} files. Please upload up to ${maxFiles} files only.`, "error");
                return;
            }

            showLoader();
            const url = form.action;
            const method = form.method || "POST";
            try {
                const resp = await fetch(url, {
                    method,
                    body: formData,
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                        "Accept": "application/json, text/html, */*"
                    },
                    credentials: "same-origin",
                });

                if (!resp.ok) {
                    const contentType = resp.headers.get("Content-Type") || "";
                    if (contentType.includes("application/json")) {
                        const data = await resp.json();
                        showFlashMessage(data.error || `Upload failed (Status ${resp.status})`, "error");
                    } else {
                        const text = await resp.text();
                        const showedFlash = showFlashMessagesFromHtml(text);
                        if (!showedFlash) {
                            const parser = new DOMParser();
                            const doc = parser.parseFromString(text, "text/html");
                            const msg = doc.querySelector(".flash-message")?.textContent ||
                                        doc.querySelector(".sub")?.textContent ||
                                        doc.querySelector("h2")?.textContent ||
                                        `Upload limit exceeded (Status ${resp.status})`;
                            showFlashMessage(msg.trim(), "error");
                        }
                    }
                    return;
                }

                const contentType = resp.headers.get("Content-Type") || "";
                const disposition = resp.headers.get("Content-Disposition") || "";
                if (
                    disposition ||
                    contentType.includes("application/pdf") ||
                    contentType.includes("application/zip") ||
                    contentType.includes("application/octet-stream")
                ) {
                    await downloadFromResponse(resp);
                    resetUploader(form);
                } else {
                    const text = await resp.text();
                    const showedFlash = showFlashMessagesFromHtml(text);

                    if (!showedFlash && resp.redirected && resp.url) {
                        window.location.href = resp.url;
                        return;
                    }

                    resetUploader(form);
                }
            } catch (err) {
                console.error("Upload failed", err);
                showFlashMessage("Upload failed. Please try again.", "error");
            } finally {
                hideLoader();
            }
        });
    });

    // intercept download links so we can hide loader when the file has been fetched
    document.querySelectorAll("a.download-link").forEach((link) => {
        link.addEventListener("click", async function (e) {
            e.preventDefault();
            const url = this.href;
            showLoader();
            try {
                const resp = await fetch(url, { credentials: "same-origin" });
                if (!resp.ok) throw new Error("Network response was not ok");
                await downloadFromResponse(resp);
            } catch (err) {
                console.error("Download failed", err);
                alert("Download failed");
            } finally {
                hideLoader();
            }
        });
    });
});
