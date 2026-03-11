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
                } else {
                    // assume it's HTML or text; update only the <body> so head/script tags remain
                    const text = await resp.text();
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(text, "text/html");
                    if (doc && doc.body) {
                        // replace body content
                        document.body.innerHTML = doc.body.innerHTML;
                        // re-execute any scripts included in the new body
                        const scripts = doc.body.querySelectorAll("script");
                        scripts.forEach((oldScript) => {
                            const newScript = document.createElement("script");
                            if (oldScript.src) {
                                newScript.src = oldScript.src;
                                // preserve async/defer attributes if necessary
                                if (oldScript.async) newScript.async = true;
                                if (oldScript.defer) newScript.defer = true;
                            } else {
                                newScript.textContent = oldScript.textContent;
                            }
                            document.body.appendChild(newScript);
                        });
                    }
                }
            } catch (err) {
                console.error(err);
                alert("Request failed");
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