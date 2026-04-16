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

    let hideTimer = null;

    const clearHideTimer = () => {
        if (hideTimer) {
            clearTimeout(hideTimer);
            hideTimer = null;
        }
    };

    form.addEventListener("submit", () => {
        if (typeof showLoader === "function") {
            showLoader();
        }

        clearHideTimer();

        // A file download does not trigger a page navigation, so hide the loader
        // after a reasonable delay instead of leaving the overlay stuck forever.
        hideTimer = setTimeout(() => {
            if (typeof hideLoader === "function") {
                hideLoader();
            }
        }, 12000);
    });

    window.addEventListener("focus", () => {
        clearHideTimer();
        if (typeof hideLoader === "function") {
            hideLoader();
        }
    });

    window.addEventListener("pageshow", () => {
        clearHideTimer();
        if (typeof hideLoader === "function") {
            hideLoader();
        }
    });
});
