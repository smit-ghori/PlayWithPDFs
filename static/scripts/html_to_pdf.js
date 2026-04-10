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