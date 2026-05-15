document.addEventListener("DOMContentLoaded", () => {
    const byRange = document.getElementById("byRange");
    const bySize = document.getElementById("bySize");

    const rangeBox = document.getElementById("rangeBox");
    const sizeBox = document.getElementById("sizeBox");

    const dropZone = document.getElementById("dropZone");
    const input = document.getElementById("pdfInput");
    const fileListUI = document.getElementById("fileList");
    const form = document.getElementById("mergeForm");
    const uploadCard = dropZone.closest(".merge-card");

    let selectedFiles = [];

    function updateUploadState() {
        uploadCard.classList.toggle("uploaded", selectedFiles.length > 0);
    }

    /* =========================
       TOGGLE FUNCTION
    ========================= */
    function show(boxToShow, boxToHide) {
        boxToHide.classList.remove("visible");
        boxToHide.classList.add("hidden");

        setTimeout(() => {
            boxToShow.classList.remove("hidden");
            boxToShow.classList.add("visible");
        }, 200);
    }

    // Toggle events
    byRange.addEventListener("change", () => show(rangeBox, sizeBox));
    bySize.addEventListener("change", () => show(sizeBox, rangeBox));

    // Initial state
    if (byRange.checked) {
        rangeBox.classList.add("visible");
        sizeBox.classList.add("hidden");
    }

    /* =========================
       FILE HANDLING
    ========================= */

    // Open file picker
    dropZone.addEventListener("click", () => input.click());

    // File select
    input.addEventListener("change", (e) => {
        addFiles(e.target.files);
    });

    // Drag & Drop
    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("drag-over");
    });

    dropZone.addEventListener("dragleave", () => {
        dropZone.classList.remove("drag-over");
    });

    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("drag-over");
        addFiles(e.dataTransfer.files);
    });

    // Prevent scroll conflict
    fileListUI.addEventListener("wheel", (e) => e.stopPropagation());

    function addFiles(files) {
        for (let file of files) {
            if (file.type === "application/pdf") {
                selectedFiles = [file]; // single file only
            }
        }
        renderFileList();
    }

    function renderFileList() {
        fileListUI.innerHTML = "";

        selectedFiles.forEach((file, index) => {
            const li = document.createElement("li");

            li.innerHTML = `
                <span class="file-name">${file.name}</span>
                <button type="button" class="remove-btn">✕</button>
            `;

            li.querySelector("button").addEventListener("click", (e) => {
                e.stopPropagation();
                removeFile(index);
            });

            fileListUI.appendChild(li);
        });

        updateUploadState();
    }

    function removeFile(index) {
        selectedFiles.splice(index, 1);
        renderFileList();
    }

    window.clearAll = function () {
        selectedFiles = [];
        renderFileList();
        input.value = "";
    };

    /* =========================
       FORM VALIDATION
    ========================= */
    form.addEventListener("submit", function (e) {
        // File validation
        if (selectedFiles.length === 0) {
            e.preventDefault();
            alert("Please select a PDF file.");
            return;
        }

        // Range validation
        if (byRange.checked) {
            const start = document.querySelector('[name="start_page"]').value;
            const end = document.querySelector('[name="end_page"]').value;

            if (!start || !end) {
                e.preventDefault();
                alert("Please enter start and end page.");
                return;
            }

            if (start < 1 || end < start) {
                e.preventDefault();
                alert("Invalid page range.");
                return;
            }
        }

        // Size validation
        if (bySize.checked) {
            const size = document.querySelector('[name="max_size"]').value;

            if (!size || size <= 0) {
                e.preventDefault();
                alert("Please enter valid size.");
                return;
            }
        }

        // Rebuild file input (IMPORTANT)
        const dataTransfer = new DataTransfer();
        selectedFiles.forEach((file) => dataTransfer.items.add(file));
        input.files = dataTransfer.files;
    });
});
