import * as pdfjsLib from "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.4.168/pdf.min.mjs";

pdfjsLib.GlobalWorkerOptions.workerSrc =
  "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.4.168/pdf.worker.min.mjs";

const dropZone = document.getElementById("dropZone");
const input = document.getElementById("pdfInput");
const fileListUI = document.getElementById("fileList");
const uploadCard = dropZone?.closest(".merge-card");
const uploadForm = input?.closest("form");
const previewWrapper = document.querySelector(".pdf-preview-wrapper");
const pdfPageStage = document.getElementById("pdfPageStage");
const canvas = document.getElementById("pdfCanvas");
const cropBox = document.getElementById("cropBox");
const prevPageBtn = document.getElementById("prevPageBtn");
const nextPageBtn = document.getElementById("nextPageBtn");
const resetCropBtn = document.getElementById("resetCropBtn");
const currentPageText = document.getElementById("currentPage");
const totalPagesText = document.getElementById("totalPages");
const cropXText = document.getElementById("cropX");
const cropYText = document.getElementById("cropY");
const cropWidthText = document.getElementById("cropWidth");
const cropHeightText = document.getElementById("cropHeight");
const cropXInput = document.getElementById("cropXInput");
const cropYInput = document.getElementById("cropYInput");
const cropWidthInput = document.getElementById("cropWidthInput");
const cropHeightInput = document.getElementById("cropHeightInput");
const currentPageInput = document.getElementById("currentPageInput");
const cropDataInput = document.getElementById("cropDataInput");
const cropModeInputs = document.querySelectorAll('input[name="crop_mode"]');

let selectedFiles = [];
let pdfDoc = null;
let currentPage = 1;
let renderToken = 0;
let activeCropAction = null;
let activeCropMode = "all";
let allPagesCrop = null;
const pageCrops = new Map();

if (
  !dropZone ||
  !input ||
  !fileListUI ||
  !uploadCard ||
  !uploadForm ||
  !previewWrapper ||
  !pdfPageStage ||
  !canvas ||
  !cropBox ||
  !cropDataInput
) {
  window.clearAll = function () {};
} else {
  const canvasContext = canvas.getContext("2d");

  activeCropMode = getCropMode();
  cropBox.style.display = "none";

  function updateUploadState() {
    uploadCard.classList.toggle("uploaded", selectedFiles.length > 0);
  }

  function updatePageControls() {
    const totalPages = pdfDoc?.numPages || 1;

    currentPageText.textContent = String(currentPage);
    totalPagesText.textContent = String(totalPages);
    currentPageInput.value = String(currentPage);

    prevPageBtn.disabled = !pdfDoc || currentPage <= 1;
    nextPageBtn.disabled = !pdfDoc || currentPage >= totalPages;
  }

  function updateCropInfo(options = {}) {
    const shouldSave = options.save !== false;

    if (cropBox.style.display === "none") {
      cropXText.textContent = "0";
      cropYText.textContent = "0";
      cropWidthText.textContent = "0";
      cropHeightText.textContent = "0";
      cropXInput.value = "0";
      cropYInput.value = "0";
      cropWidthInput.value = "0";
      cropHeightInput.value = "0";
      syncCropData();
      return;
    }

    const x = Math.round(cropBox.offsetLeft);
    const y = Math.round(cropBox.offsetTop);
    const width = Math.round(cropBox.offsetWidth);
    const height = Math.round(cropBox.offsetHeight);

    cropXText.textContent = String(x);
    cropYText.textContent = String(y);
    cropWidthText.textContent = String(width);
    cropHeightText.textContent = String(height);

    cropXInput.value = String(x);
    cropYInput.value = String(y);
    cropWidthInput.value = String(width);
    cropHeightInput.value = String(height);

    if (shouldSave) {
      saveCurrentCrop();
    }

    syncCropData();
  }

  function getCropMode() {
    return document.querySelector('input[name="crop_mode"]:checked')?.value || "all";
  }

  function getCropRatios() {
    const stageWidth = pdfPageStage.clientWidth;
    const stageHeight = pdfPageStage.clientHeight;

    if (!stageWidth || !stageHeight || cropBox.style.display === "none") {
      return null;
    }

    return {
      x: cropBox.offsetLeft / stageWidth,
      y: cropBox.offsetTop / stageHeight,
      width: cropBox.offsetWidth / stageWidth,
      height: cropBox.offsetHeight / stageHeight,
    };
  }

  function saveCropForMode(mode) {
    const crop = getCropRatios();

    if (!crop) {
      return;
    }

    if (mode === "current") {
      pageCrops.set(currentPage, crop);
    } else {
      allPagesCrop = crop;
    }
  }

  function saveCurrentCrop() {
    saveCropForMode(activeCropMode);
  }

  function syncCropData() {
    const pageCropData = {};

    pageCrops.forEach((crop, pageNumber) => {
      pageCropData[String(pageNumber)] = crop;
    });

    cropDataInput.value = JSON.stringify({
      mode: getCropMode(),
      current_page: currentPage,
      all_pages_crop: allPagesCrop,
      page_crops: pageCropData,
    });
  }

  function applyCropRatios(crop, options = {}) {
    const stageWidth = pdfPageStage.clientWidth;
    const stageHeight = pdfPageStage.clientHeight;

    if (!crop || !stageWidth || !stageHeight) {
      return false;
    }

    const left = clamp(Math.round(crop.x * stageWidth), 0, stageWidth - 32);
    const top = clamp(Math.round(crop.y * stageHeight), 0, stageHeight - 32);
    const width = clamp(Math.round(crop.width * stageWidth), 32, stageWidth - left);
    const height = clamp(Math.round(crop.height * stageHeight), 32, stageHeight - top);

    cropBox.style.left = `${left}px`;
    cropBox.style.top = `${top}px`;
    cropBox.style.width = `${width}px`;
    cropBox.style.height = `${height}px`;
    cropBox.style.display = "block";

    updateCropInfo(options);
    return true;
  }

  function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
  }

  function placeDefaultCropBox(options = {}) {
    const stageWidth = pdfPageStage.clientWidth;
    const stageHeight = pdfPageStage.clientHeight;

    if (!stageWidth || !stageHeight) {
      cropBox.style.display = "none";
      return;
    }

    const width = Math.max(120, Math.round(stageWidth * 0.42));
    const height = Math.max(120, Math.round(stageHeight * 0.4));
    const safeWidth = Math.min(width, stageWidth);
    const safeHeight = Math.min(height, stageHeight);

    cropBox.style.width = `${safeWidth}px`;
    cropBox.style.height = `${safeHeight}px`;
    cropBox.style.left = `${Math.round((stageWidth - safeWidth) / 2)}px`;
    cropBox.style.top = `${Math.round((stageHeight - safeHeight) / 3)}px`;
    cropBox.style.display = "block";

    updateCropInfo(options);
  }

  function restoreCropBoxForPage() {
    const crop =
      activeCropMode === "current" ? pageCrops.get(currentPage) : allPagesCrop;

    if (!applyCropRatios(crop, { save: false })) {
      placeDefaultCropBox({ save: activeCropMode === "all" });
    }
  }

  async function renderPage(pageNumber) {
    if (!pdfDoc) {
      return;
    }

    const token = ++renderToken;
    const page = await pdfDoc.getPage(pageNumber);
    const viewport = page.getViewport({ scale: 1 });
    const availableWidth = Math.max(previewWrapper.clientWidth - 48, 280);
    const scale = Math.min(1.35, availableWidth / viewport.width);
    const scaledViewport = page.getViewport({ scale });

    if (token !== renderToken) {
      return;
    }

    canvas.width = Math.floor(scaledViewport.width);
    canvas.height = Math.floor(scaledViewport.height);
    canvas.style.width = `${Math.floor(scaledViewport.width)}px`;
    canvas.style.height = `${Math.floor(scaledViewport.height)}px`;

    pdfPageStage.style.width = `${Math.floor(scaledViewport.width)}px`;
    pdfPageStage.style.height = `${Math.floor(scaledViewport.height)}px`;

    await page.render({
      canvasContext,
      viewport: scaledViewport,
    }).promise;

    if (token !== renderToken) {
      return;
    }

    updatePageControls();
    restoreCropBoxForPage();
  }

  async function loadPdfPreview(file) {
    if (!file) {
      resetPreview();
      return;
    }

    try {
      const buffer = await file.arrayBuffer();
      pdfDoc = await pdfjsLib.getDocument({ data: new Uint8Array(buffer) }).promise;
      currentPage = 1;
      await renderPage(currentPage);
      setTimeout(() => {
        if (pdfDoc) {
          renderPage(currentPage);
        }
      }, 550);
    } catch (error) {
      console.error("Unable to render PDF preview:", error);
      resetPreview();
      alert("Could not preview this PDF file.");
    }
  }

  function resetPreview() {
    pdfDoc = null;
    currentPage = 1;
    renderToken++;
    allPagesCrop = null;
    pageCrops.clear();
    canvasContext.clearRect(0, 0, canvas.width, canvas.height);
    canvas.width = 0;
    canvas.height = 0;
    canvas.style.width = "";
    canvas.style.height = "";
    pdfPageStage.style.width = "";
    pdfPageStage.style.height = "";
    cropBox.style.display = "none";
    updatePageControls();
    updateCropInfo();
  }

  function addFiles(files) {
    const type = dropZone.dataset.type;
    const allowed = fileTypes[type] || [];
    const hadFiles = selectedFiles.length > 0;

    for (const file of files) {
      if (allowed.includes(file.type)) {
        selectedFiles.push(file);
      } else {
        showInvalidFileMessage(type);
      }
    }

    renderFileList();

    if (!hadFiles && selectedFiles.length > 0) {
      loadPdfPreview(selectedFiles[0]);
    }
  }

  function renderFileList() {
    fileListUI.innerHTML = "";

    selectedFiles.forEach((file, index) => {
      const li = document.createElement("li");
      const name = document.createElement("span");
      const removeButton = document.createElement("button");

      name.className = "file-name";
      name.textContent = file.name;

      removeButton.type = "button";
      removeButton.className = "remove-btn";
      removeButton.textContent = "x";
      removeButton.addEventListener("click", (event) => removeFile(event, index));

      li.append(name, removeButton);
      fileListUI.appendChild(li);
    });

    updateUploadState();
  }

  function removeFile(event, index) {
    event.stopPropagation();
    const wasPreviewedFile = index === 0;

    selectedFiles.splice(index, 1);
    renderFileList();

    if (selectedFiles.length === 0) {
      resetPreview();
      return;
    }

    if (wasPreviewedFile) {
      loadPdfPreview(selectedFiles[0]);
    }
  }

  function clearAll() {
    selectedFiles = [];
    renderFileList();
    resetPreview();
    input.value = "";
  }

  function changePage(direction) {
    if (!pdfDoc) {
      return;
    }

    const nextPage = clamp(currentPage + direction, 1, pdfDoc.numPages);

    if (nextPage !== currentPage) {
      currentPage = nextPage;
      renderPage(currentPage);
    }
  }

  function startCropAction(event) {
    if (cropBox.style.display === "none") {
      return;
    }

    event.preventDefault();
    event.stopPropagation();

    const handle = event.target.closest(".resize-handle");
    activeCropAction = {
      mode: handle ? "resize" : "move",
      handle: handle?.dataset.handle || "",
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      startLeft: cropBox.offsetLeft,
      startTop: cropBox.offsetTop,
      startWidth: cropBox.offsetWidth,
      startHeight: cropBox.offsetHeight,
    };

    cropBox.setPointerCapture(event.pointerId);
  }

  function moveCropBox(event) {
    if (!activeCropAction || event.pointerId !== activeCropAction.pointerId) {
      return;
    }

    const minSize = 32;
    const stageWidth = pdfPageStage.clientWidth;
    const stageHeight = pdfPageStage.clientHeight;
    const dx = event.clientX - activeCropAction.startX;
    const dy = event.clientY - activeCropAction.startY;

    let left = activeCropAction.startLeft;
    let top = activeCropAction.startTop;
    let width = activeCropAction.startWidth;
    let height = activeCropAction.startHeight;

    if (activeCropAction.mode === "move") {
      left = clamp(left + dx, 0, stageWidth - width);
      top = clamp(top + dy, 0, stageHeight - height);
    } else {
      if (activeCropAction.handle.includes("right")) {
        width = clamp(width + dx, minSize, stageWidth - left);
      }

      if (activeCropAction.handle.includes("bottom")) {
        height = clamp(height + dy, minSize, stageHeight - top);
      }

      if (activeCropAction.handle.includes("left")) {
        const nextLeft = clamp(left + dx, 0, left + width - minSize);
        width += left - nextLeft;
        left = nextLeft;
      }

      if (activeCropAction.handle.includes("top")) {
        const nextTop = clamp(top + dy, 0, top + height - minSize);
        height += top - nextTop;
        top = nextTop;
      }
    }

    cropBox.style.left = `${Math.round(left)}px`;
    cropBox.style.top = `${Math.round(top)}px`;
    cropBox.style.width = `${Math.round(width)}px`;
    cropBox.style.height = `${Math.round(height)}px`;

    updateCropInfo();
  }

  function stopCropAction(event) {
    if (!activeCropAction || event.pointerId !== activeCropAction.pointerId) {
      return;
    }

    cropBox.releasePointerCapture(event.pointerId);
    activeCropAction = null;
  }

  const fileTypes = {
    pdf: ["application/pdf"],
    word: [
      "application/msword",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ],
    excel: [
      "application/vnd.ms-excel",
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ],
    ppt: [
      "application/vnd.ms-powerpoint",
      "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ],
  };

  function showInvalidFileMessage(type) {
    const messages = {
      pdf: "Please upload only PDF files.",
      word: "Please upload only Word files.",
      excel: "Please upload only Excel files.",
      ppt: "Please upload only PowerPoint files.",
    };

    alert(messages[type] || "Invalid file type!");
  }

  dropZone.addEventListener("click", () => input.click());

  input.addEventListener("change", (event) => {
    addFiles(event.target.files);
    setTimeout(() => {
      input.value = "";
    }, 0);
  });

  dropZone.addEventListener("dragover", (event) => {
    event.preventDefault();
    dropZone.classList.add("drag-over");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("drag-over");
  });

  dropZone.addEventListener("drop", (event) => {
    event.preventDefault();
    dropZone.classList.remove("drag-over");
    addFiles(event.dataTransfer.files);
  });

  fileListUI.addEventListener("wheel", (event) => {
    event.stopPropagation();
  });

  prevPageBtn.addEventListener("click", () => changePage(-1));
  nextPageBtn.addEventListener("click", () => changePage(1));
  resetCropBtn.addEventListener("click", () => placeDefaultCropBox());

  cropModeInputs.forEach((input) => {
    input.addEventListener("change", () => {
      if (activeCropMode === "all") {
        saveCropForMode(activeCropMode);
      }

      activeCropMode = getCropMode();
      restoreCropBoxForPage();
      syncCropData();
    });
  });

  cropBox.addEventListener("pointerdown", startCropAction);
  cropBox.addEventListener("pointermove", moveCropBox);
  cropBox.addEventListener("pointerup", stopCropAction);
  cropBox.addEventListener("pointercancel", stopCropAction);

  window.addEventListener("resize", () => {
    if (pdfDoc) {
      renderPage(currentPage);
    }
  });

  window.resetUploadForm = function () {
    clearAll();
  };

  uploadForm.addEventListener("submit", function (event) {
    if (selectedFiles.length === 0) {
      event.preventDefault();
      alert("Please select at least one PDF file.");
      return;
    }

    if (activeCropMode === "all") {
      saveCurrentCrop();
    }

    syncCropData();

    const dataTransfer = new DataTransfer();
    selectedFiles.forEach((file) => dataTransfer.items.add(file));
    input.files = dataTransfer.files;
  });

  updatePageControls();
  updateCropInfo();
}
