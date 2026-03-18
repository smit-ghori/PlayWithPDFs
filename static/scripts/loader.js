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
    if (disposition && disposition.indexOf("filename=") !== -1) {
        filename = disposition
            .split("filename=")[1]
            .replace(/"/g, "");
    }

    const downloadUrl = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = downloadUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(downloadUrl);
}

// function resetUploader() {
//     const form = document.getElementById("mergeForm");
//     if (form) form.reset();

//     const fileList = document.getElementById("fileList");
//     if (fileList) fileList.innerHTML = "";

//     const input = document.getElementById("pdfInput");
//     if (input) input.value = "";

//     // if card.js has a selectedFiles array, clear it
//     if (window.selectedFiles && Array.isArray(window.selectedFiles)) {
//         window.selectedFiles.length = 0;
//     }

//     // also call the helper from card.js if available
//     if (typeof window.resetUploadForm === "function") {
//         window.resetUploadForm();
//     }
// }

// when DOM ready, wire up interactions
document.addEventListener("DOMContentLoaded", () => {
    // show loader on any form submit so user sees something while server works
    // regular forms just show a loader while the browser processes the request
    document.querySelectorAll("form:not(.ajax-upload-form)").forEach((form) => {
        form.addEventListener("submit", (e) => {
            showLoader();
        });
    });

    // intercept file-upload forms and perform the request via fetch so we can
    // hide the loader once the response is handled (downloaded or HTML returned).
    document.querySelectorAll("form.ajax-upload-form").forEach((form) => {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();

            const fileInput = form.querySelector('input[type="file"]');

            // ✅ VALIDATION FIRST
            if (!window.selectedFiles || window.selectedFiles.length === 0) {
                return;
            }

            // ✅ NOW show loader
            showLoader();

            const url = form.action;
            const method = form.method || "POST";
            const formData = new FormData(form);

            try {
                const resp = await fetch(url, {
                    method,
                    body: formData,
                    credentials: "same-origin",
                });

                if (!resp.ok) throw new Error("Network response was not ok");

                const contentType = resp.headers.get("Content-Type") || "";

                if (
                    contentType.includes("application/pdf") ||
                    contentType.includes("application/zip") ||
                    contentType.includes("application/octet-stream")
                ) {
                    await downloadFromResponse(resp);
                    resetUploader();
                } else {
                    resetUploader();
                    const text = await resp.text();
                    console.log("Upload response:", text);
                }
            } catch (err) {
                console.error(err);
            } finally {
                hideLoader();
            }
        });
    });

    // hide loader when the page finishes loading (handles normal navigations)
    window.addEventListener("load", () => {
        hideLoader();
    });

    // intercept download links so we can hide loader when the file has been fetched
    document.querySelectorAll("a.download-link").forEach((link) => {
        link.addEventListener("click", async function (e) {
            e.preventDefault();
            const url = this.href;
            showLoader();
            try {
                const resp = await fetch(url, { credentials: 'same-origin' });
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