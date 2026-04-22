function clearAll() {
    const urlInput = document.getElementById("urlInput");

    urlInput.value = "";
    urlInput.focus(); // cursor back to input

    // Optional: small animation effect
    urlInput.style.transition = "0.3s";
    urlInput.style.boxShadow = "0 0 10px rgba(255,0,0,0.5)";

    setTimeout(() => {
        urlInput.style.boxShadow = "none";
    }, 300);
}

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("mergeForm");
    if (!form) return;
    const urlInput = document.getElementById("urlInput");
    const messageBox = document.getElementById("htmlToPdfMessage");

    const showMessage = (message, type = "error") => {
        if (!messageBox) return;
        messageBox.textContent = message;
        messageBox.hidden = false;
        messageBox.classList.toggle("success", type === "success");
    };

    const clearMessage = () => {
        if (!messageBox) return;
        messageBox.textContent = "";
        messageBox.hidden = true;
        messageBox.classList.remove("success");
    };

    const downloadFileFromResponse = async (resp) => {
        if (typeof downloadFromResponse === "function") {
            await downloadFromResponse(resp);
            return;
        }

        const blob = await resp.blob();
        const disposition = resp.headers.get("Content-Disposition") || "";
        const filenameMatch =
            disposition.match(/filename\*=UTF-8''([^;]+)/i) ||
            disposition.match(/filename="?([^";]+)"?/i);
        const filename = filenameMatch ? decodeURIComponent(filenameMatch[1]) : "download.pdf";

        const downloadUrl = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = downloadUrl;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(downloadUrl), 1000);
    };

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        event.stopImmediatePropagation();
        clearMessage();

        if (typeof showLoader === "function") {
            showLoader();
        }

        try {
            const resp = await fetch(form.action, {
                method: form.method || "POST",
                body: new FormData(form),
                credentials: "same-origin",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    Accept: "application/pdf, application/json",
                },
            });

            const contentType = resp.headers.get("Content-Type") || "";
            if (resp.ok && contentType.includes("application/pdf")) {
                await downloadFileFromResponse(resp);
                form.reset();
                if (urlInput) urlInput.focus();
                return;
            }

            if (contentType.includes("application/json")) {
                const data = await resp.json();
                showMessage(data.error || "PDF generation failed.");
                return;
            }

            showMessage("PDF generation failed. Please try a different URL.");
        } catch (error) {
            console.error("HTML to PDF download failed", error);
            showMessage("Download failed. Please check the URL and try again.");
        } finally {
            if (typeof hideLoader === "function") {
                hideLoader();
            }
        }
    });

    form.addEventListener("reset", () => {
        if (urlInput) {
            urlInput.focus();
        }
    });
});
