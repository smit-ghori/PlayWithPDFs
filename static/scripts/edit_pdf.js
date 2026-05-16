/* =========================================
   FILE UPLOAD SYSTEM
   ========================================= */

document.documentElement.classList.add("edit-pdf-active");
document.body.classList.add("edit-pdf-active");

const dropZone = document.getElementById("dropZone");

const input = document.getElementById("pdfInput");

const fileListUI = document.getElementById("fileList");

const uploadCard = dropZone?.closest(".merge-card");

const uploadForm = input?.closest("form");

let selectedFiles = [];

if (
  !dropZone ||
  !input ||
  !fileListUI ||
  !uploadCard ||
  !uploadForm
) {

  window.clearAll = function () { };

} else {

  function updateUploadState() {

    uploadCard.classList.toggle(
      "uploaded",
      selectedFiles.length > 0
    );
  }

  /* =====================================
     OPEN PICKER
     ===================================== */

  dropZone.addEventListener(
    "click",
    () => input.click()
  );

  /* =====================================
     FILE CHANGE
     ===================================== */

  input.addEventListener(
    "change",
    (e) => {

      addFiles(e.target.files);

      setTimeout(() => {
        input.value = "";
      }, 0);
    }
  );

  /* =====================================
     DRAG EVENTS
     ===================================== */

  dropZone.addEventListener(
    "dragover",
    (e) => {

      e.preventDefault();

      dropZone.classList.add(
        "drag-over"
      );
    }
  );

  dropZone.addEventListener(
    "dragleave",
    () => {

      dropZone.classList.remove(
        "drag-over"
      );
    }
  );

  dropZone.addEventListener(
    "drop",
    (e) => {

      e.preventDefault();

      dropZone.classList.remove(
        "drag-over"
      );

      addFiles(e.dataTransfer.files);
    }
  );

  /* =====================================
     FILE TYPES
     ===================================== */

  const fileTypes = {

    pdf: [
      "application/pdf"
    ]
  };

  function showInvalidFileMessage(type) {

    const messages = {

      pdf:
        "Please upload only PDF files."
    };

    alert(
      messages[type] ||
      "Invalid file type!"
    );
  }

  /* =====================================
     ADD FILES
     ===================================== */

  function addFiles(files) {

    const type =
      dropZone.dataset.type;

    const allowed =
      fileTypes[type] || [];

    for (let file of files) {

      if (
        allowed.includes(file.type)
      ) {

        selectedFiles.push(file);

      } else {

        showInvalidFileMessage(type);
      }
    }

    renderFileList();

    if (selectedFiles.length > 0) {

      loadPDFPreview(
        selectedFiles[0]
      );
    }
  }

  /* =====================================
     FILE LIST
     ===================================== */

  function renderFileList() {

    fileListUI.innerHTML = "";

    selectedFiles.forEach(
      (file, index) => {

        const li =
          document.createElement("li");

        li.innerHTML = `
          <span class="file-name">
            ${file.name}
          </span>

          <button
            type="button"
            class="remove-btn"
            onclick="removeFile(event, ${index})"
          >
            ✕
          </button>
        `;

        fileListUI.appendChild(li);
      }
    );

    updateUploadState();
  }

  /* =====================================
     REMOVE FILE
     ===================================== */

  window.removeFile = function (
    event,
    index
  ) {

    event.preventDefault();

    event.stopPropagation();

    selectedFiles.splice(index, 1);

    if (selectedFiles.length === 0) {

      window.clearAll();

      return;
    }

    renderFileList();

    loadPDFPreview(
      selectedFiles[0]
    );
  };

  /* =====================================
     CLEAR ALL
     ===================================== */

  window.clearAll = function () {

    renderVersion++;

    selectedFiles = [];

    renderFileList();

    input.value = "";

    fabricCanvas.clear();

    pdfDoc = null;

    totalPages = 1;

    currentPage = 1;

    pageAnnotations = {};

    pageDimensions = {};

    if (pdfPages) {

      pdfPages.innerHTML = "";
    }

    document.getElementById(
      "currentPage"
    ).textContent = "1";

    document.getElementById(
      "currentPageInput"
    ).value = "1";

    document.getElementById(
      "totalPages"
    ).textContent = "1";
  };

  window.resetUploadForm = window.clearAll;

  /* =====================================
     SUBMIT
     ===================================== */

  uploadForm.addEventListener(
    "submit",
    function (e) {

      if (
        selectedFiles.length === 0
      ) {

        e.preventDefault();

        alert(
          "Please select at least one PDF file."
        );

        return;
      }

      const dataTransfer =
        new DataTransfer();

      selectedFiles.forEach(
        (file) =>
          dataTransfer.items.add(file)
      );

      document.getElementById(
        "annotationsData"
      ).value = JSON.stringify(
        getAnnotationPayload()
      );

      input.files =
        dataTransfer.files;
    }
  );
}

/* =========================================
   PDF.JS + FABRIC.JS EDITOR
   ========================================= */

const pdfPages =
  document.getElementById(
    "pdfPages"
  );

const fabricCanvas =
  new fabric.Canvas(
    "fabricCanvas"
  );

fabricCanvas.freeDrawingBrush.color =
  "#ff0000";

fabricCanvas.freeDrawingBrush.width =
  3;

let pdfDoc = null;

let currentPage = 1;

let totalPages = 1;

let currentTool = "text";

let pdfjsReady = null;

let pageAnnotations = {};

let pageDimensions = {};

const PDF_SCALE = 1.75;

let renderVersion = 0;

let pendingPdfSelection = null;

let nextAnnotationId = 1;

function createAnnotationId() {
  const annotationId =
    `annotation-${nextAnnotationId}`;

  nextAnnotationId += 1;

  return annotationId;
}

/* =========================================
   PDF.JS LOADER
   ========================================= */

async function getPdfjs() {

  if (!pdfjsReady) {

    pdfjsReady = window.pdfjsLib
      ? Promise.resolve(window.pdfjsLib)
      : import(
        "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.4.168/pdf.min.mjs"
      );
  }

  const pdfjs = await pdfjsReady;

  pdfjs.GlobalWorkerOptions.workerSrc =
    "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.4.168/pdf.worker.min.mjs";

  return pdfjs;
}

/* =========================================
   LOAD PDF
   ========================================= */

async function loadPDFPreview(file) {

  const activeRenderVersion =
    ++renderVersion;

  const pdfjs = await getPdfjs();

  if (activeRenderVersion !== renderVersion)
    return;

  const fileReader =
    new FileReader();

  fileReader.onload =
    async function () {

      const typedArray =
        new Uint8Array(
          this.result
        );

      pdfDoc =
        await pdfjs.getDocument(
          typedArray
        ).promise;

      if (activeRenderVersion !== renderVersion)
        return;

      totalPages =
        pdfDoc.numPages;

      currentPage = 1;

      pageAnnotations = {};

      pageDimensions = {};

      fabricCanvas.clear();

      document.getElementById(
        "totalPages"
      ).textContent = totalPages;

      renderAllPages(
        activeRenderVersion
      );
    };

  fileReader.readAsArrayBuffer(file);
}

/* =========================================
   RENDER PAGE
   ========================================= */

async function renderPage(
  pageNumber,
  activeRenderVersion
) {

  if (
    !pdfDoc ||
    activeRenderVersion !== renderVersion
  )
    return;

  const page =
    await pdfDoc.getPage(
      pageNumber
    );

  const viewport =
    page.getViewport({
      scale: PDF_SCALE
    });

  const pageEl =
    document.createElement("div");

  pageEl.className = "pdf-page";

  pageEl.dataset.pageNumber =
    pageNumber;

  pageEl.style.width =
    `${viewport.width}px`;

  pageEl.style.height =
    `${viewport.height}px`;

  pageDimensions[pageNumber] = {
    width: viewport.width,
    height: viewport.height
  };

  const canvas =
    document.createElement("canvas");

  const context =
    canvas.getContext("2d");

  canvas.width =
    viewport.width;

  canvas.height =
    viewport.height;

  const textLayer =
    document.createElement("div");

  textLayer.className =
    "text-layer";

  textLayer.style.setProperty(
    "--scale-factor",
    viewport.scale
  );

  pageEl.appendChild(canvas);

  pageEl.appendChild(textLayer);

  await page.render(
    {
      canvasContext: context,
      viewport: viewport
    }
  ).promise;

  if (activeRenderVersion !== renderVersion)
    return;

  const textContent =
    await page.getTextContent();

  const pdfjs =
    await getPdfjs();

  await pdfjs.renderTextLayer({
    textContentSource: textContent,
    container: textLayer,
    viewport: viewport
  }).promise;

  if (activeRenderVersion !== renderVersion)
    return;

  pageEl.addEventListener(
    "click",
    () => activatePage(pageNumber)
  );

  textLayer.addEventListener(
    "mouseup",
    handlePdfTextSelection
  );

  pdfPages.appendChild(pageEl);

  return pageEl;
}

/* =========================================
   RENDER ALL PAGES
   ========================================= */

async function renderAllPages(
  activeRenderVersion
) {

  pdfPages.innerHTML = "";

  for (
    let pageNumber = 1;
    pageNumber <= totalPages;
    pageNumber++
  ) {

    await renderPage(
      pageNumber,
      activeRenderVersion
    );
  }

  if (activeRenderVersion === renderVersion) {

    activatePage(currentPage);
  }
}

/* =========================================
   ACTIVE PAGE
   ========================================= */

function saveCurrentAnnotations() {

  if (!pdfDoc)
    return;

  pageAnnotations[currentPage] =
    fabricCanvas.toJSON([
      "annotationId",
      "objectRole",
      "linkedCoverId",
      "linkedTextId",
      "originalPdfText"
    ]);
}

function relinkCanvasObjects() {
  const objects =
    fabricCanvas.getObjects();

  const byId =
    new Map();

  objects.forEach((object) => {
    if (object.annotationId) {
      byId.set(
        object.annotationId,
        object
      );
    }
  });

  objects.forEach((object) => {
    if (
      object.type === "textbox" &&
      object.linkedCoverId
    ) {
      object.linkedCoverRect =
        byId.get(
          object.linkedCoverId
        ) || null;
    }
  });

  objects.forEach((object) => {
    if (object.type === "textbox") {
      syncTextboxCoverRect(object);
    }
  });
}

function getAnnotationPayload() {
  saveCurrentAnnotations();

  const payload = {
    scale: PDF_SCALE,
    pages: {}
  };

  Object.entries(pageAnnotations).forEach(
    ([pageNumber, json]) => {
      const dimensions =
        pageDimensions[pageNumber];

      if (
        !json ||
        !dimensions ||
        !Array.isArray(json.objects) ||
        json.objects.length === 0
      ) {
        return;
      }

      const exportCanvas =
        new fabric.StaticCanvas(
          null,
          {
            width: dimensions.width,
            height: dimensions.height,
            backgroundColor: null
          }
        );

      exportCanvas.loadFromJSON(
        json,
        () => {
          exportCanvas.renderAll();
        }
      );

      payload.pages[pageNumber] = {
        width: dimensions.width,
        height: dimensions.height,
        image: exportCanvas.toDataURL({
          format: "png",
          multiplier: 1
        })
      };

      exportCanvas.dispose();
    }
  );

  return payload;
}

function activatePage(pageNumber) {

  if (!pdfDoc)
    return;

  saveCurrentAnnotations();

  currentPage = pageNumber;

  document
    .querySelectorAll(".pdf-page")
    .forEach((page) =>
      page.classList.toggle(
        "active",
        Number(page.dataset.pageNumber) ===
        pageNumber
      )
    );

  const pageEl =
    document.querySelector(
      `.pdf-page[data-page-number="${pageNumber}"]`
    );

  if (!pageEl)
    return;

  const wrapperRect =
    document
      .querySelector(".pdf-canvas-wrapper")
      .getBoundingClientRect();

  const pageRect =
    pageEl.getBoundingClientRect();

  const pageLeft =
    pageRect.left -
    wrapperRect.left +
    document.querySelector(
      ".pdf-canvas-wrapper"
    ).scrollLeft;

  const pageTop =
    pageRect.top -
    wrapperRect.top +
    document.querySelector(
      ".pdf-canvas-wrapper"
    ).scrollTop;

  const canvasContainer =
    fabricCanvas.wrapperEl;

  canvasContainer.style.left =
    `${pageLeft}px`;

  canvasContainer.style.top =
    `${pageTop}px`;

  fabricCanvas.setWidth(
    pageEl.offsetWidth
  );

  fabricCanvas.setHeight(
    pageEl.offsetHeight
  );

  fabricCanvas.clear();

  if (pageAnnotations[pageNumber]) {

    fabricCanvas.loadFromJSON(
      pageAnnotations[pageNumber],
      () => {
        relinkCanvasObjects();
        fabricCanvas.renderAll();
      }
    );
  }

  document.getElementById(
    "currentPage"
  ).textContent = pageNumber;

  document.getElementById(
    "currentPageInput"
  ).value = pageNumber;

  pageEl.scrollIntoView({
    behavior: "smooth",
    block: "nearest",
    inline: "center"
  });
}

function clearBrowserSelection() {
  const selection =
    window.getSelection();

  if (selection) {
    selection.removeAllRanges();
  }
}

function buildTextboxFromSelection(
  pageEl,
  selectionRange
) {
  const selectionText =
    selectionRange.toString().trim();

  if (!selectionText) {
    return;
  }

  const pageNumber =
    Number(pageEl.dataset.pageNumber);

  if (pageNumber !== currentPage) {
    activatePage(pageNumber);
  }

  const pageRect =
    pageEl.getBoundingClientRect();

  const rangeRect =
    selectionRange.getBoundingClientRect();

  const left =
    Math.max(
      0,
      rangeRect.left - pageRect.left
    );

  const top =
    Math.max(
      0,
      rangeRect.top - pageRect.top
    );

  const width =
    Math.max(
      96,
      rangeRect.width + 12
    );

  const height =
    Math.max(
      28,
      rangeRect.height + 10
    );

  const fontSize =
    Math.max(
      12,
      Math.round(rangeRect.height * 0.78)
    );

  const fontFamily =
    document.getElementById(
      "fontFamily"
    ).value;

  const color =
    document.getElementById(
      "textColor"
    ).value;

  const textbox =
    new fabric.Textbox(
      selectionText,
      {
        left,
        top,
        width,
        fontSize,
        fill: color,
        fontFamily,
        editable: true,
        backgroundColor: "#ffffff",
        padding: 2
      }
    );

  const coverRect =
    new fabric.Rect({
      annotationId:
        createAnnotationId(),
      objectRole:
        "replacement-cover",
      left: Math.max(0, left - 2),
      top: Math.max(0, top - 2),
      width: width + 4,
      height,
      fill: "#ffffff",
      selectable: false,
      evented: false,
      excludeFromExport: false
    });

  textbox.set({
    annotationId:
      createAnnotationId(),
    objectRole:
      "replacement-text",
    originalPdfText: selectionText,
    linkedCoverId:
      coverRect.annotationId,
    linkedCoverRect: coverRect
  });

  document.getElementById(
    "editorText"
  ).value = selectionText;

  document.getElementById(
    "fontSize"
  ).value = fontSize;

  fabricCanvas.add(coverRect);

  fabricCanvas.add(textbox);

  fabricCanvas.setActiveObject(
    textbox
  );

  fabricCanvas.renderAll();

  setActiveTool(
    "select",
    null
  );

  textbox.enterEditing();
  textbox.selectAll();

  if (textbox.hiddenTextarea) {
    textbox.hiddenTextarea.focus();
  }
}

function syncTextboxCoverRect(
  textbox
) {
  if (
    !textbox ||
    textbox.type !== "textbox"
  ) {
    return;
  }

  const coverRect =
    textbox.linkedCoverRect;

  if (!coverRect) {
    return;
  }

  textbox.setCoords();

  const scaledWidth =
    (textbox.width || 0) *
    (textbox.scaleX || 1);

  const scaledHeight =
    (textbox.height || 0) *
    (textbox.scaleY || 1);

  coverRect.set({
    left: Math.max(
      0,
      (textbox.left || 0) - 3
    ),
    top: Math.max(
      0,
      (textbox.top || 0) - 3
    ),
    width: Math.max(
      24,
      scaledWidth + 6
    ),
    height: Math.max(
      24,
      scaledHeight + 6
    )
  });

  coverRect.setCoords();
  coverRect.sendToBack();
}

function handlePdfTextSelection(
  event
) {
  if (currentTool !== "pdf-text") {
    return;
  }

  const selection =
    window.getSelection();

  if (
    !selection ||
    selection.rangeCount === 0 ||
    selection.isCollapsed
  ) {
    pendingPdfSelection = null;
    return;
  }

  const range =
    selection.getRangeAt(0);

  if (!range.toString().trim()) {
    pendingPdfSelection = null;
    return;
  }

  const pageEl =
    event.currentTarget.closest(
      ".pdf-page"
    );

  if (!pageEl) {
    pendingPdfSelection = null;
    return;
  }

  pendingPdfSelection = {
    pageEl,
    range: range.cloneRange()
  };

  requestAnimationFrame(() => {
    if (!pendingPdfSelection) {
      return;
    }

    buildTextboxFromSelection(
      pendingPdfSelection.pageEl,
      pendingPdfSelection.range
    );

    pendingPdfSelection = null;
    clearBrowserSelection();
  });
}

function syncEditorControlsFromObject(
  active
) {
  if (
    !active ||
    active.type !== "textbox"
  ) {
    return;
  }

  document.getElementById(
    "editorText"
  ).value = active.text || "";

  document.getElementById(
    "fontSize"
  ).value = Math.round(
    active.fontSize || 24
  );

  document.getElementById(
    "fontFamily"
  ).value = active.fontFamily || "Arial";

  if (
    typeof active.fill === "string" &&
    active.fill.startsWith("#")
  ) {
    document.getElementById(
      "textColor"
    ).value = active.fill;
  }
}

/* =========================================
   PAGE NAVIGATION
   ========================================= */

document
  .getElementById(
    "prevPageBtn"
  )
  .addEventListener(
    "click",
    () => {

      if (currentPage <= 1)
        return;

      currentPage--;

      activatePage(currentPage);
    }
  );

document
  .getElementById(
    "nextPageBtn"
  )
  .addEventListener(
    "click",
    () => {

      if (
        currentPage >= totalPages
      )
        return;

      currentPage++;

      activatePage(currentPage);
    }
  );

/* =========================================
   TOOL BUTTONS
   ========================================= */

const addTextBtn =
  document.getElementById(
    "addTextBtn"
  );

const selectTextBtn =
  document.getElementById(
    "selectTextBtn"
  );

const drawBtn =
  document.getElementById(
    "drawBtn"
  );

const eraseBtn =
  document.getElementById(
    "eraseBtn"
  );

function setActiveTool(tool, button) {

  currentTool = tool;

  [
    selectTextBtn,
    addTextBtn,
    drawBtn,
    eraseBtn
  ].forEach((toolButton) => {

    if (toolButton) {

      toolButton.classList.toggle(
        "active",
        toolButton === button
      );
    }
  });

  fabricCanvas.isDrawingMode =
    tool === "draw";

  fabricCanvas.selection =
    tool !== "pdf-text";

  fabricCanvas.wrapperEl.classList.toggle(
    "text-selection-mode",
    tool === "pdf-text"
  );

  if (tool !== "pdf-text") {
    clearBrowserSelection();
  }
}

selectTextBtn.addEventListener(
  "click",
  () => setActiveTool(
    "pdf-text",
    selectTextBtn
  )
);

addTextBtn.addEventListener(
  "click",
  () => setActiveTool(
    "text",
    addTextBtn
  )
);

drawBtn.addEventListener(
  "click",
  () => setActiveTool(
    "draw",
    drawBtn
  )
);

eraseBtn.addEventListener(
  "click",
  () => setActiveTool(
    "erase",
    eraseBtn
  )
);

/* =========================================
   ADD TEXT
   ========================================= */

fabricCanvas.on(
  "mouse:down",
  function (options) {

    if (currentTool === "text") {

      if (options.target)
        return;

      const pointer =
        fabricCanvas.getPointer(
          options.e
        );

      const text =
        document.getElementById(
          "editorText"
        ).value || "New Text";

      const fontSize =
        parseInt(
          document.getElementById(
            "fontSize"
          ).value
        );

      const color =
        document.getElementById(
          "textColor"
        ).value;

      const fontFamily =
        document.getElementById(
          "fontFamily"
        ).value;

      const textbox =
        new fabric.Textbox(
          text,
          {
            annotationId:
              createAnnotationId(),
            objectRole:
              "text",

            left: pointer.x,

            top: pointer.y,

            fontSize:
              fontSize,

            fill: color,

            fontFamily:
              fontFamily,

            editable: true
          }
        );

      fabricCanvas.add(textbox);

      fabricCanvas.setActiveObject(
        textbox
      );

      setActiveTool(
        "select",
        null
      );
    }

    /* ===================================
       WHITEOUT TOOL
       =================================== */

    if (currentTool === "erase") {

      const pointer =
        fabricCanvas.getPointer(
          options.e
        );

      const rect =
        new fabric.Rect({
          annotationId:
            createAnnotationId(),
          objectRole:
            "whiteout",

          left: pointer.x,

          top: pointer.y,

          width: 150,

          height: 40,

          fill: "#ffffff",

          stroke: "#cccccc",

          strokeDashArray: [5, 5]
        });

      fabricCanvas.add(rect);

      fabricCanvas.setActiveObject(
        rect
      );

      setActiveTool(
        "select",
        null
      );
    }
  }
);

fabricCanvas.on(
  "text:changed",
  function (event) {
    const textbox =
      event.target;

    syncTextboxCoverRect(textbox);

    if (
      textbox &&
      textbox.type === "textbox"
    ) {
      document.getElementById(
        "editorText"
      ).value = textbox.text || "";
    }
  }
);

fabricCanvas.on(
  "object:moving",
  function (event) {
    syncTextboxCoverRect(
      event.target
    );
  }
);

fabricCanvas.on(
  "object:scaling",
  function (event) {
    syncTextboxCoverRect(
      event.target
    );
  }
);

fabricCanvas.on(
  "object:modified",
  function (event) {
    syncTextboxCoverRect(
      event.target
    );
  }
);

fabricCanvas.on(
  "path:created",
  function (event) {
    if (event.path) {
      event.path.set({
        annotationId:
          createAnnotationId(),
        objectRole:
          "drawing"
      });
    }
  }
);

fabricCanvas.on(
  "selection:created",
  function (event) {
    const active =
      event.selected?.[0];

    if (
      active &&
      active.type === "textbox"
    ) {
      syncEditorControlsFromObject(
        active
      );
    }
  }
);

fabricCanvas.on(
  "selection:updated",
  function (event) {
    const active =
      event.selected?.[0];

    if (
      active &&
      active.type === "textbox"
    ) {
      syncEditorControlsFromObject(
        active
      );
    }
  }
);

/* =========================================
   BOLD
   ========================================= */

document
  .getElementById(
    "boldBtn"
  )
  .addEventListener(
    "click",
    () => {

      const active =
        fabricCanvas.getActiveObject();

      if (
        active &&
        active.type === "textbox"
      ) {

        active.set(
          "fontWeight",

          active.fontWeight ===
            "bold"

            ? "normal"

            : "bold"
        );

        fabricCanvas.renderAll();
      }
    }
  );

/* =========================================
   ITALIC
   ========================================= */

document
  .getElementById(
    "italicBtn"
  )
  .addEventListener(
    "click",
    () => {

      const active =
        fabricCanvas.getActiveObject();

      if (
        active &&
        active.type === "textbox"
      ) {

        active.set(
          "fontStyle",

          active.fontStyle ===
            "italic"

            ? "normal"

            : "italic"
        );

        fabricCanvas.renderAll();
      }
    }
  );

/* =========================================
   UNDERLINE
   ========================================= */

document
  .getElementById(
    "underlineBtn"
  )
  .addEventListener(
    "click",
    () => {

      const active =
        fabricCanvas.getActiveObject();

      if (
        active &&
        active.type === "textbox"
      ) {

        active.set(
          "underline",

          !active.underline
        );

        fabricCanvas.renderAll();
      }
    }
  );

document
  .getElementById(
    "editorText"
  )
  .addEventListener(
    "input",
    (event) => {
      const active =
        fabricCanvas.getActiveObject();

      if (
        active &&
        active.type === "textbox"
      ) {
        active.set(
          "text",
          event.target.value
        );

        syncTextboxCoverRect(active);
        fabricCanvas.renderAll();
      }
    }
  );

document
  .getElementById(
    "fontSize"
  )
  .addEventListener(
    "input",
    (event) => {
      const active =
        fabricCanvas.getActiveObject();

      if (
        active &&
        active.type === "textbox"
      ) {
        active.set(
          "fontSize",
          parseInt(
            event.target.value,
            10
          )
        );

        syncTextboxCoverRect(active);
        fabricCanvas.renderAll();
      }
    }
  );

document
  .getElementById(
    "textColor"
  )
  .addEventListener(
    "input",
    (event) => {
      fabricCanvas.freeDrawingBrush.color =
        event.target.value;

      const active =
        fabricCanvas.getActiveObject();

      if (
        active &&
        active.type === "textbox"
      ) {
        active.set(
          "fill",
          event.target.value
        );

        fabricCanvas.renderAll();
      }
    }
  );

document
  .getElementById(
    "fontFamily"
  )
  .addEventListener(
    "change",
    (event) => {
      const active =
        fabricCanvas.getActiveObject();

      if (
        active &&
        active.type === "textbox"
      ) {
        active.set(
          "fontFamily",
          event.target.value
        );

        syncTextboxCoverRect(active);
        fabricCanvas.renderAll();
      }
    }
  );

/* =========================================
   RESET
   ========================================= */

document
  .getElementById(
    "resetEditorBtn"
  )
  .addEventListener(
    "click",
    () => {
      const editMode =
        document.querySelector(
          'input[name="edit_mode"]:checked'
        )?.value || "current";

      if (editMode === "all") {
        pageAnnotations = {};
      } else {
        pageAnnotations[currentPage] = {
          version: "5.3.0",
          objects: []
        };
      }

      fabricCanvas.clear();
    }
  );
