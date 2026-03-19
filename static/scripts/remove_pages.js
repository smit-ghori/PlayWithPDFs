/* =========================================
   GLOBAL VARIABLES
========================================= */
const dropZone = document.getElementById("dropZone");
const input = document.getElementById("pdfInput");
const fileListUI = document.getElementById("fileList");
const form = document.getElementById("mergeForm");

let selectedFiles = [];

/* =========================================
   FILE HANDLING
========================================= */

// Click → open file picker
if (dropZone) {
    dropZone.addEventListener("click", () => input.click());
}

// File select
if (input) {
    input.addEventListener("change", (e) => {
        handleFiles(e.target.files);
    });
}

// Drag & Drop
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
        handleFiles(e.dataTransfer.files);
    });
}

/* =========================================
   HANDLE FILES
========================================= */
function handleFiles(files) {
    for (let file of files) {
        if (file.type === "application/pdf") {
            selectedFiles = [file]; // 🔥 single file for remove pages
            renderPDFPreview(file); // preview
        }
    }
    renderFileList();
}

/* =========================================
   FILE LIST UI
========================================= */
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
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    renderFileList();

    // clear preview
    const preview = document.getElementById("preview_section");
    if (preview) preview.innerHTML = "";
}

function clearAll() {
    selectedFiles = [];
    renderFileList();
    if (input) input.value = "";

    const preview = document.getElementById("preview_section");
    if (preview) preview.innerHTML = "";
}

/* =========================================
   PDF PREVIEW + PAGE SELECT
========================================= */
function renderPDFPreview(file) {
    const previewContainer = document.getElementById("preview_section");
    previewContainer.innerHTML = "";

    const fileURL = URL.createObjectURL(file);
    const loadingTask = pdfjsLib.getDocument(fileURL);

    loadingTask.promise.then(pdf => {

        for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {

            pdf.getPage(pageNum).then(page => {

                const desiredWidth = 120;
                const viewport = page.getViewport({ scale: 1 });
                const scale = desiredWidth / viewport.width;
                const scaledViewport = page.getViewport({ scale });

                const pageDiv = document.createElement("div");
                pageDiv.classList.add("pdf-page");

                const canvas = document.createElement("canvas");
                const context = canvas.getContext("2d");

                canvas.height = scaledViewport.height;
                canvas.width = scaledViewport.width;

                const checkbox = document.createElement("input");
                checkbox.type = "checkbox";
                checkbox.value = pageNum;
                checkbox.classList.add("page-checkbox");

                const label = document.createElement("p");
                label.innerText = "Page " + pageNum;

                // toggle selection
                checkbox.addEventListener("change", () => {
                    pageDiv.classList.toggle("selected", checkbox.checked);
                });

                // click anywhere
                pageDiv.addEventListener("click", (e) => {
                    if (e.target !== checkbox) {
                        checkbox.checked = !checkbox.checked;
                        checkbox.dispatchEvent(new Event("change"));
                    }
                });

                pageDiv.appendChild(canvas);
                pageDiv.appendChild(checkbox);
                pageDiv.appendChild(label);

                previewContainer.appendChild(pageDiv);

                page.render({
                    canvasContext: context,
                    viewport: scaledViewport
                });
            });
        }
    });
}

/* =========================================
   GET SELECTED PAGES
========================================= */
function getSelectedPages() {
    const checked = document.querySelectorAll(".page-checkbox:checked");
    return Array.from(checked).map(cb => cb.value);
}

/* =========================================
   FORM SUBMIT
========================================= */
if (form) {
    form.addEventListener("submit", (e) => {

        if (selectedFiles.length === 0) {
            e.preventDefault();
            alert("Please select a PDF file.");
            return;
        }

        // rebuild file input
        const dataTransfer = new DataTransfer();
        selectedFiles.forEach(file => dataTransfer.items.add(file));
        input.files = dataTransfer.files;

        // add selected pages
        const selected = getSelectedPages();

        const old = document.getElementById("pages_input");
        if (old) old.remove();

        const hidden = document.createElement("input");
        hidden.type = "hidden";
        hidden.name = "pages_to_remove";
        hidden.id = "pages_input";
        hidden.value = selected.join(",");

        form.appendChild(hidden);

        console.log("Pages to remove:", hidden.value);
    });
}