// ===============================
// FILE UPLOAD (from card.js)
// ===============================

const dropZone = document.getElementById("dropZone");
const inputFile = document.getElementById("pdfInput");
const fileListUI = document.getElementById("fileList");
const uploadCard = dropZone.closest(".merge-card");

let selectedFiles = [];

function updateUploadState() {
    uploadCard.classList.toggle("uploaded", selectedFiles.length > 0);
}

// Open file picker
if (dropZone && inputFile) {
    dropZone.addEventListener("click", () => inputFile.click());
}

// File select
if (inputFile) {
    inputFile.addEventListener("change", (e) => {
        addFiles(e.target.files);
    });
}

// Drag & drop
if (dropZone) {
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
}

// Scroll fix
if (fileListUI) {
    fileListUI.addEventListener("wheel", (e) => e.stopPropagation());
}

// Add files
function addFiles(files) {
    for (let file of files) {
        if (file.type === "application/pdf") {
            selectedFiles.push(file);
        }
    }
    renderFileList();
}

// Render list
function renderFileList() {
    if (!fileListUI) return;

    fileListUI.innerHTML = "";

    selectedFiles.forEach((file, index) => {
        const li = document.createElement("li");

        li.innerHTML = `
      <span class="file-name">${file.name}</span>
      <button type="button" class="remove-btn" onclick="removeFile(event, ${index})">✕</button>
    `;

        fileListUI.appendChild(li);
    });

    updateUploadState();
}

// Remove file
function removeFile(event, index) {
    event.stopPropagation();
    selectedFiles.splice(index, 1);
    renderFileList();
}

// Clear all
function clearAll() {
    selectedFiles = [];
    renderFileList();
}

// Submit handler
const form = document.getElementById("mergeForm");

if (form) {
    form.addEventListener("submit", function (e) {
        if (selectedFiles.length === 0) {
            e.preventDefault();
            alert("Please select at least one PDF file.");
            return;
        }

        const dataTransfer = new DataTransfer();
        selectedFiles.forEach((file) => dataTransfer.items.add(file));
        inputFile.files = dataTransfer.files;
    });
}


// ===============================
// TRANSLATE DROPDOWN
// ===============================

document.addEventListener("DOMContentLoaded", function () {
    const input = document.getElementById("searchLang");
    const list = document.getElementById("langList");
    const form = document.getElementById("mergeForm");

    if (!input || !list || !form) return; // prevent error on other pages

    const items = list.getElementsByTagName("li");

    // Show dropdown
    input.addEventListener("focus", () => {
        list.style.display = "block";
    });

    input.addEventListener("click", () => {
        list.style.display = "block";
    });

    // Filter
    input.addEventListener("keyup", () => {
        const filter = input.value.toLowerCase();

        for (let i = 0; i < items.length; i++) {
            const txt = items[i].textContent.toLowerCase();
            items[i].style.display = txt.includes(filter) ? "" : "none";
        }
    });

    // Select item
    for (let item of items) {
        item.addEventListener("click", () => {
            input.value = item.textContent;
            list.style.display = "none";

            // hidden input for form
            let hidden = document.getElementById("selectedLang");

            if (!hidden) {
                hidden = document.createElement("input");
                hidden.type = "hidden";
                hidden.name = "lang";
                hidden.id = "selectedLang";
                form.appendChild(hidden);
            }

            hidden.value = item.getAttribute("data-value");
        });
    }

    // Click outside
    document.addEventListener("click", (e) => {
        if (!e.target.closest(".custom-dropdown")) {
            list.style.display = "none";
        }
    });

    // Form submit validation
    form.addEventListener("submit", function (e) {
        const selected = document.getElementById("selectedLang");

        if (!selected || !selected.value) {
            e.preventDefault();
            alert("Please select a language from the list.");
        }
    });
});
