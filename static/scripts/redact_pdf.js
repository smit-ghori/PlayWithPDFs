// =========================================
// WORKER
// =========================================
pdfjsLib.GlobalWorkerOptions.workerSrc =
  "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";

// =========================================
// ELEMENT REFS
// =========================================
const dropZone = document.getElementById("dropZone");
const input = document.getElementById("pdfInput");
const fileListUI = document.getElementById("fileList");
const uploadCard = dropZone?.closest(".merge-card");
const uploadForm = input?.closest("form");

const pdfPages = document.getElementById("pdfPages");
const selectedCount = document.getElementById("selectedCount");
const redactData = document.getElementById("redactData");
const pageNumber = document.getElementById("pageNumber");
const markToolBtn = document.getElementById("markToolBtn");
const eraseToolBtn = document.getElementById("eraseToolBtn");
const zoomValue = document.getElementById("zoomValue");
const zoomOutBtn = document.getElementById("zoomOutBtn");
const zoomInBtn = document.getElementById("zoomInBtn");

// =========================================
// STATE
// =========================================
let selectedFiles = [];
let selectedTexts = []; // { id, text, page, bbox[] }
let textItems = []; // word-level hit boxes + metadata
let pdfDoc = null;

let isDragging = false;
let dragStart = { x: 0, y: 0 };
let dragRectEl = null;
let activeLayer = null;
let activeTool = "mark";
let pdfScale = 1;
let isRendering = false;

const MIN_ZOOM = 0.65;
const MAX_ZOOM = 1.75;

if (!dropZone || !input || !fileListUI || !uploadCard || !uploadForm || !pdfPages) {
  window.clearAll = function () {};
  window.clearSelections = function () {};
} else {
  // =========================================
  // UPLOAD STATE
  // =========================================
  function updateUploadState() {
    uploadCard.classList.toggle("uploaded", selectedFiles.length > 0);
  }

  function updateToolUI() {
    markToolBtn?.classList.toggle("active", activeTool === "mark");
    eraseToolBtn?.classList.toggle("active", activeTool === "erase");
    pdfPages.classList.toggle("eraser-active", activeTool === "erase");
  }

  function updateZoomUI() {
    const zoomPercent = Math.round((pdfScale / 1) * 100);
    if (zoomValue) zoomValue.innerText = `${zoomPercent}%`;
    if (zoomOutBtn) zoomOutBtn.disabled = pdfScale <= MIN_ZOOM;
    if (zoomInBtn) zoomInBtn.disabled = pdfScale >= MAX_ZOOM;
  }

  window.setRedactTool = function (tool) {
    activeTool = tool === "erase" ? "erase" : "mark";
    updateToolUI();
  };

  window.zoomPdf = async function (delta) {
    if (!pdfDoc || isRendering) return;

    const nextScale = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, pdfScale + delta));
    if (Math.abs(nextScale - pdfScale) < 0.01) return;

    pdfScale = Number(nextScale.toFixed(2));
    updateZoomUI();
    await renderAllPages();
  };

  updateToolUI();
  updateZoomUI();

  dropZone.addEventListener("click", () => input.click());

  input.addEventListener("change", (e) => {
    addFiles(e.target.files);
    setTimeout(() => {
      input.value = "";
    }, 0);
  });

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

  // =========================================
  // FILE HANDLING
  // =========================================
  async function addFiles(files) {
    for (const file of files) {
      if (file.type === "application/pdf") {
        selectedFiles.push(file);
      } else {
        alert("Please upload only PDF files.");
      }
    }

    renderFileList();
    updateUploadState();

    if (selectedFiles.length > 0) {
      clearSelectionsInternal();
      await loadPDF(selectedFiles[0]);
    }
  }

  function renderFileList() {
    fileListUI.innerHTML = "";

    selectedFiles.forEach((file, i) => {
      const li = document.createElement("li");
      li.innerHTML = `
        <span class="file-name">${escapeHtml(file.name)}</span>
        <button type="button" class="remove-btn" onclick="removeFile(event,${i})">&#x2715;</button>
      `;
      fileListUI.appendChild(li);
    });
  }

  window.removeFile = function (event, index) {
    event.stopPropagation();
    selectedFiles.splice(index, 1);
    renderFileList();
    clearSelectionsInternal();

    if (selectedFiles.length === 0) {
      clearPreview();
      pdfDoc = null;
    } else {
      loadPDF(selectedFiles[0]);
    }

    updateUploadState();
  };

  function clearPreview() {
    pdfPages.innerHTML = "";
    textItems = [];
    activeLayer = null;
    dragRectEl = null;
    isDragging = false;
    pageNumber.innerText = "No PDF";
  }

  // =========================================
  // LOAD PDF
  // =========================================
  async function loadPDF(file) {
    const reader = new FileReader();

    reader.onload = async function () {
      try {
        clearPreview();
        pdfDoc = await pdfjsLib.getDocument({ data: new Uint8Array(this.result) }).promise;
        pdfScale = 1;
        updateZoomUI();
        pageNumber.innerText = `${pdfDoc.numPages} page${pdfDoc.numPages !== 1 ? "s" : ""}`;
        await renderAllPages();
      } catch (err) {
        console.error("PDF load error:", err);
        alert("Failed to load PDF. Make sure the file is a valid PDF.");
      }
    };

    reader.readAsArrayBuffer(file);
  }

  // =========================================
  // RENDER ALL PAGES
  // =========================================
  async function renderAllPages() {
    if (!pdfDoc) return;

    isRendering = true;
    textItems = [];
    pdfPages.innerHTML = "";

    try {
      for (let pageNum = 1; pageNum <= pdfDoc.numPages; pageNum += 1) {
        await renderPage(pageNum);
      }
    } finally {
      isRendering = false;
    }
  }

  async function renderPage(pageNum) {
    const page = await pdfDoc.getPage(pageNum);
    const viewport = page.getViewport({ scale: pdfScale });

    const pageShell = document.createElement("section");
    pageShell.className = "pdf-page-shell";
    pageShell.dataset.page = pageNum;

    const label = document.createElement("div");
    label.className = "pdf-page-label";
    label.textContent = `Page ${pageNum}`;

    const stage = document.createElement("div");
    stage.className = "pdf-page-stage";

    const canvas = document.createElement("canvas");
    canvas.className = "pdf-canvas";
    canvas.width = viewport.width;
    canvas.height = viewport.height;

    const layer = document.createElement("div");
    layer.className = "selection-layer";
    layer.dataset.page = pageNum;

    stage.append(canvas, layer);
    pageShell.append(label, stage);
    pdfPages.appendChild(pageShell);

    await page.render({ canvasContext: canvas.getContext("2d"), viewport }).promise;

    await new Promise((resolve) => {
      requestAnimationFrame(async () => {
        const displayW = canvas.offsetWidth || viewport.width;
        const displayH = canvas.offsetHeight || viewport.height;

        layer.style.width = `${displayW}px`;
        layer.style.height = `${displayH}px`;

        attachLayerEvents(layer);

        const content = await page.getTextContent();
        buildWordHits(content.items, viewport, displayW, layer, pageNum);
        resolve();
      });
    });
  }

  // =========================================
  // COORDINATE HELPERS
  // =========================================
  function toDisplayCoords(item, viewport, cssScale) {
    const tx = pdfjsLib.Util.transform(viewport.transform, item.transform);
    const pdfH = item.height > 0 ? item.height : Math.abs(item.transform[3]);
    const canvasH = pdfH * viewport.scale;
    const canvasW = item.width * viewport.scale;

    return {
      x: tx[4] * cssScale,
      y: (tx[5] - canvasH) * cssScale,
      w: canvasW * cssScale,
      h: canvasH * cssScale,
      pdfX: item.transform[4],
      pdfY: item.transform[5],
      pdfW: item.width,
      pdfH,
    };
  }

  function textLengthValue(text) {
    return Array.from(text).reduce((total, ch) => total + (/\s/.test(ch) ? 0.45 : 1), 0);
  }

  function splitTextItemIntoWords(item, viewport, cssScale, idx) {
    const text = item.str || "";
    const display = toDisplayCoords(item, viewport, cssScale);
    const segments = [...text.matchAll(/\S+/g)];

    if (segments.length === 0) return [];

    const totalUnits = Math.max(textLengthValue(text), 1);
    const displayUnit = display.w / totalUnits;
    const pdfUnit = display.pdfW / totalUnits;

    return segments.map((match, tokenIdx) => {
      const word = match[0];
      const before = text.slice(0, match.index);
      const wordUnits = Math.max(textLengthValue(word), 0.1);
      const offsetUnits = textLengthValue(before);

      return {
        ...display,
        x: display.x + offsetUnits * displayUnit,
        w: Math.max(wordUnits * displayUnit, 2),
        pdfX: display.pdfX + offsetUnits * pdfUnit,
        pdfW: Math.max(wordUnits * pdfUnit, 0.1),
        str: word,
        idx,
        tokenIdx,
      };
    });
  }

  function groupIntoWords(rawItems, viewport, cssScale) {
    const items = rawItems
      .filter((it) => it.str.trim() !== "")
      .flatMap((it, idx) => splitTextItemIntoWords(it, viewport, cssScale, idx))
      .sort((a, b) => {
        const lineDelta = (a.y + a.h / 2) - (b.y + b.h / 2);
        if (Math.abs(lineDelta) > Math.max(a.h, b.h) * 0.5) return lineDelta;
        return a.x - b.x;
      });

    if (items.length === 0) return [];

    const words = [];
    let current = null;

    for (const item of items) {
      const midY = item.y + item.h / 2;

      if (current) {
        const curMidY = current.y + current.h / 2;
        const lineMatch = Math.abs(midY - curMidY) < current.h * 0.55;
        const gap = item.x - (current.x + current.w);
        const avgCharW = current.w / Math.max(Array.from(current.str).length, 1);
        const sameRawTextRun = current.members.some((m) => m.idx === item.idx);
        const adjacent = !sameRawTextRun && gap >= -2 && gap < Math.max(avgCharW * 0.5, 1.5);

        if (lineMatch && adjacent) {
          current.str += item.str;
          current.w = item.x + item.w - current.x;
          current.pdfW += item.pdfW;
          current.members.push(item);
          continue;
        }
      }

      if (current) words.push(current);
      current = { ...item, members: [item] };
    }

    if (current) words.push(current);
    return words;
  }

  // =========================================
  // BUILD WORD HIT BOXES
  // =========================================
  function buildWordHits(rawItems, viewport, displayW, layer, pageNum) {
    const cssScale = displayW / viewport.width;
    const words = groupIntoWords(rawItems, viewport, cssScale);

    words.forEach((word, gIdx) => {
      const id = `${pageNum}-${gIdx}`;
      const el = document.createElement("div");
      el.className = "text-hit";
      Object.assign(el.style, {
        left: `${word.x}px`,
        top: `${word.y}px`,
        width: `${word.w}px`,
        height: `${word.h}px`,
      });
      layer.appendChild(el);

      const bboxes = word.members.map((m) => ({
        x: m.pdfX,
        y: m.pdfY,
        width: m.pdfW,
        height: m.pdfH,
      }));

      textItems.push({
        id,
        el,
        layer,
        text: word.str.trim(),
        page: pageNum,
        dx: word.x,
        dy: word.y,
        dw: word.w,
        dh: word.h,
        bboxes,
      });

      if (selectedTexts.some((selected) => selected.id === id)) {
        el.classList.add("selected");
      }
    });
  }

  // =========================================
  // DRAG SELECTION
  // =========================================
  function layerPos(layer, e) {
    const r = layer.getBoundingClientRect();
    return { x: e.clientX - r.left, y: e.clientY - r.top };
  }

  function rectsOverlap(sel, item) {
    return !(
      sel.x + sel.w < item.dx ||
      item.dx + item.dw < sel.x ||
      sel.y + sel.h < item.dy ||
      item.dy + item.dh < sel.y
    );
  }

  function pointInsideItem(point, item) {
    return (
      point.x >= item.dx &&
      point.x <= item.dx + item.dw &&
      point.y >= item.dy &&
      point.y <= item.dy + item.dh
    );
  }

  function syncDragRect(cur) {
    const x = Math.min(dragStart.x, cur.x);
    const y = Math.min(dragStart.y, cur.y);
    const w = Math.abs(cur.x - dragStart.x);
    const h = Math.abs(cur.y - dragStart.y);

    Object.assign(dragRectEl.style, {
      left: `${x}px`,
      top: `${y}px`,
      width: `${w}px`,
      height: `${h}px`,
    });

    return { x, y, w, h };
  }

  function attachLayerEvents(layer) {
    layer.addEventListener("mousedown", (e) => {
      e.preventDefault();
      activeLayer = layer;
      isDragging = true;
      dragStart = layerPos(layer, e);

      if (activeTool === "erase") {
        eraseAtPoint(dragStart, layer);
        return;
      }

      dragRectEl = document.createElement("div");
      dragRectEl.className = "drag-select-rect";
      Object.assign(dragRectEl.style, {
        left: `${dragStart.x}px`,
        top: `${dragStart.y}px`,
        width: "0",
        height: "0",
      });
      layer.appendChild(dragRectEl);
    });

    layer.addEventListener("mousemove", (e) => {
      if (!isDragging || activeLayer !== layer) return;

      if (activeTool === "erase") {
        eraseAtPoint(layerPos(layer, e), layer);
        return;
      }

      if (!dragRectEl) return;
      const sel = syncDragRect(layerPos(layer, e));

      textItems.forEach((item) => {
        if (item.layer !== layer) return;
        const inside = rectsOverlap(sel, item);
        const already = selectedTexts.some((t) => t.id === item.id);
        item.el.classList.toggle("hover-preview", inside && !already);
      });
    });

    layer.addEventListener("mouseup", () => {
      finishDrag(layer);
    });

    layer.addEventListener("mouseleave", () => {
      cancelDrag(layer);
    });

    layer.addEventListener(
      "touchstart",
      (e) => {
        e.preventDefault();
        proxyMouse(layer, "mousedown", e.touches[0]);
      },
      { passive: false },
    );

    layer.addEventListener(
      "touchmove",
      (e) => {
        e.preventDefault();
        proxyMouse(layer, "mousemove", e.touches[0]);
      },
      { passive: false },
    );

    layer.addEventListener(
      "touchend",
      (e) => {
        e.preventDefault();
        proxyMouse(layer, "mouseup", e.changedTouches[0]);
      },
      { passive: false },
    );
  }

  function proxyMouse(layer, type, touch) {
    layer.dispatchEvent(
      new MouseEvent(type, {
        clientX: touch.clientX,
        clientY: touch.clientY,
        bubbles: true,
      }),
    );
  }

  function finishDrag(layer) {
    if (!isDragging || activeLayer !== layer) return;

    isDragging = false;

    if (activeTool === "erase") {
      activeLayer = null;
      textItems.forEach((t) => t.el.classList.remove("hover-preview"));
      renderSelectedTexts();
      return;
    }

    const x = parseFloat(dragRectEl.style.left);
    const y = parseFloat(dragRectEl.style.top);
    const w = parseFloat(dragRectEl.style.width);
    const h = parseFloat(dragRectEl.style.height);
    dragRectEl.remove();
    dragRectEl = null;

    textItems.forEach((t) => t.el.classList.remove("hover-preview"));
    activeLayer = null;

    if (w < 4 && h < 4) {
      toggleSelectionAtPoint({ x, y }, layer);
      return;
    }
    applySelection({ x, y, w, h }, layer);
  }

  function cancelDrag(layer) {
    if (!isDragging || activeLayer !== layer) return;
    isDragging = false;
    dragRectEl?.remove();
    dragRectEl = null;
    activeLayer = null;
    textItems.forEach((t) => t.el.classList.remove("hover-preview"));
  }

  // =========================================
  // SELECTION LIST
  // =========================================
  function applySelection(sel, layer) {
    let changed = false;

    textItems.forEach((item) => {
      if (item.layer !== layer) return;
      if (!rectsOverlap(sel, item)) return;
      if (selectedTexts.some((t) => t.id === item.id)) return;

      selectedTexts.push({
        id: item.id,
        text: item.text,
        page: item.page,
        bboxes: item.bboxes,
      });
      item.el.classList.add("selected");
      changed = true;
    });

    if (changed) renderSelectedTexts();
  }

  function removeSelectionById(id) {
    const before = selectedTexts.length;
    selectedTexts = selectedTexts.filter((item) => item.id !== id);

    if (selectedTexts.length === before) return false;

    const hit = textItems.find((t) => t.id === id);
    if (hit) hit.el.classList.remove("selected", "hover-preview");
    return true;
  }

  function eraseAtPoint(point, layer) {
    const item = [...textItems]
      .reverse()
      .find(
        (candidate) =>
          candidate.layer === layer &&
          selectedTexts.some((selected) => selected.id === candidate.id) &&
          pointInsideItem(point, candidate),
      );

    if (!item) return;

    if (removeSelectionById(item.id)) {
      renderSelectedTexts();
    }
  }

  function toggleSelectionAtPoint(point, layer) {
    const item = [...textItems]
      .reverse()
      .find((candidate) => candidate.layer === layer && pointInsideItem(point, candidate));

    if (!item) return;

    const existingIndex = selectedTexts.findIndex((selected) => selected.id === item.id);

    if (existingIndex >= 0) {
      removeSelectionById(item.id);
    } else {
      selectedTexts.push({
        id: item.id,
        text: item.text,
        page: item.page,
        bboxes: item.bboxes,
      });
      item.el.classList.add("selected");
    }

    renderSelectedTexts();
  }

  function renderSelectedTexts() {
    selectedCount.innerText = `${selectedTexts.length} item${selectedTexts.length !== 1 ? "s" : ""}`;
    redactData.value = JSON.stringify(selectedTexts);
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  window.removeSelection = function (id) {
    removeSelectionById(id);
    renderSelectedTexts();
  };

  function clearSelectionsInternal() {
    selectedTexts = [];
    textItems.forEach((t) => t.el.classList.remove("selected", "hover-preview"));
    renderSelectedTexts();
  }

  window.clearSelections = function () {
    clearSelectionsInternal();
  };

  window.clearAll = function () {
    selectedFiles = [];
    clearSelectionsInternal();
    renderFileList();
    input.value = "";
    clearPreview();
    pdfDoc = null;
    pdfScale = 1;
    updateZoomUI();
    updateUploadState();
  };

  // =========================================
  // FORM SUBMIT
  // =========================================
  uploadForm.addEventListener("submit", function (e) {
    if (selectedFiles.length === 0) {
      e.preventDefault();
      alert("Please select at least one PDF file.");
      return;
    }

    if (selectedTexts.length === 0) {
      e.preventDefault();
      alert("Please drag to select at least one text region to redact.");
      return;
    }

    const dt = new DataTransfer();
    selectedFiles.forEach((f) => dt.items.add(f));
    input.files = dt.files;
  });

  window.resetUploadForm = function () {
    clearAll();
  };
}
