
const dropZone = document.getElementById("dropZone");
const input = document.getElementById("pdfInput");
const fileListUI = document.getElementById("fileList");

let selectedFiles = [];

// Open file picker when clicking drop zone
dropZone.addEventListener("click", () => input.click());

// Handle file selection
input.addEventListener("change", (e) => {
    addFiles(e.target.files);
});

// Drag events
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

// Allow scrolling in file list without triggering drop zone
fileListUI.addEventListener("wheel", (e) => {
    e.stopPropagation();
});

fileListUI.addEventListener("touchstart", (e) => {
    // Allow touch scrolling
});

fileListUI.addEventListener("touchmove", (e) => {
    // Allow touch scrolling
});

const fileTypes = {
    pdf: ["application/pdf"],
    word: [
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
};

function addFiles(files) {
    const type = dropZone.dataset.type;
    const allowed = fileTypes[type] || [];

    for (let file of files) {
        if (allowed.includes(file.type)) {
            selectedFiles.push(file);
        } else {
            alert(`Invalid file type! Allowed: ${type}`);
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
        <button type="button" class="remove-btn" onclick="removeFile(event, ${index})">✕</button>
      `;

        fileListUI.appendChild(li);
    });
}

function removeFile(event, index) {
    event.stopPropagation(); // Prevent click from bubbling to drop zone
    selectedFiles.splice(index, 1);
    renderFileList();
}

function clearAll() {
    selectedFiles = [];
    renderFileList();
    // if (input) input.value = "";
}

// // Allow external scripts (like the AJAX loader) to reset the form state after an upload
// window.resetUploadForm = function () {
//     clearAll();
// };

// Before submit, rebuild input files
document.getElementById("mergeForm").addEventListener("submit", function (e) {
    if (selectedFiles.length === 0) {
        e.preventDefault();
        alert("Please select at least one PDF file.");
        return;
    }

    const dataTransfer = new DataTransfer();
    selectedFiles.forEach((file) => dataTransfer.items.add(file));
    input.files = dataTransfer.files;
});
