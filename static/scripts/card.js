
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

function addFiles(files) {
    for (let file of files) {
        if (file.type === "application/pdf") {
            selectedFiles.push(file);
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
        <button type="button" class="remove-btn" onclick="removeFile(${index})">✕</button>
      `;

        fileListUI.appendChild(li);
    });
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    renderFileList();
}

function clearAll() {
    selectedFiles = [];
    renderFileList();
}

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
