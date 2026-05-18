pdfjsLib.GlobalWorkerOptions.workerSrc =
  "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";

const dropZone = document.getElementById("dropZone");
const input = document.getElementById("pdfInput");
const fileListUI = document.getElementById("fileList");
const uploadCard = dropZone?.closest(".merge-card");
const uploadForm = input?.closest("form");

const leftCanvas = document.getElementById("leftCanvas");
const rightCanvas = document.getElementById("rightCanvas");
const leftHighlights = document.getElementById("leftHighlights");
const rightHighlights = document.getElementById("rightHighlights");
const leftPreview = leftCanvas?.closest(".compare-preview");
const rightPreview = rightCanvas?.closest(".compare-preview");
const changeList = document.getElementById("changeList");
const changeCount = document.getElementById("changeCount");
const searchChanges = document.getElementById("searchChanges");
const zoomValue = document.getElementById("zoomValue");
const zoomOutBtn = document.getElementById("zoomOutBtn");
const zoomInBtn = document.getElementById("zoomInBtn");
const syncScrollToggle = document.getElementById("syncScrollToggle");

let selectedFiles = [];
let lastChanges = [];
let isComparing = false;
let previewScale = 1.3;
let isSyncingScroll = false;

const MIN_ZOOM = 0.75;
const MAX_ZOOM = 2.05;

if (!dropZone || !input || !fileListUI || !uploadCard || !uploadForm) {
  window.clearAll = function () {};
} else {
  function updateUploadState() {
    uploadCard.classList.toggle("uploaded", selectedFiles.length === 2);
  }

  function updateZoomUI() {
    if (zoomValue) zoomValue.innerText = `${Math.round(previewScale * 100)}%`;
    if (zoomOutBtn) zoomOutBtn.disabled = previewScale <= MIN_ZOOM;
    if (zoomInBtn) zoomInBtn.disabled = previewScale >= MAX_ZOOM;
  }

  window.zoomComparePdf = async function (delta) {
    if (isComparing || selectedFiles.length !== 2) return;

    const nextScale = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, previewScale + delta));
    if (Math.abs(nextScale - previewScale) < 0.01) return;

    previewScale = Number(nextScale.toFixed(2));
    updateZoomUI();
    await compareUploadedPDFs();
  };

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

  async function addFiles(files) {
    for (const file of files) {
      if (file.type !== "application/pdf") {
        alert("Please upload only PDF files.");
        continue;
      }

      if (selectedFiles.length === 2) selectedFiles = [];
      selectedFiles.push(file);
      if (selectedFiles.length === 2) break;
    }

    renderFileList();
    updateUploadState();

    if (selectedFiles.length === 2) {
      await compareUploadedPDFs();
    } else {
      clearPreview();
    }
  }

  function renderFileList() {
    fileListUI.innerHTML = "";

    selectedFiles.forEach((file, index) => {
      const li = document.createElement("li");
      li.innerHTML = `
        <span class="file-name">${escapeHtml(file.name)}</span>
        <button type="button" class="remove-btn" onclick="removeFile(event, ${index})">&#x2715;</button>
      `;
      fileListUI.appendChild(li);
    });
  }

  window.removeFile = function (event, index) {
    event.stopPropagation();
    selectedFiles.splice(index, 1);
    renderFileList();
    updateUploadState();
    clearPreview();
  };

  async function compareUploadedPDFs() {
    if (isComparing) return;
    isComparing = true;
    setReportLoading();

    try {
      const [leftDoc, rightDoc] = await Promise.all([
        renderPDF(selectedFiles[0], leftCanvas, leftHighlights),
        renderPDF(selectedFiles[1], rightCanvas, rightHighlights),
      ]);

      const diff = buildDiff(leftDoc.tokens, rightDoc.tokens);
      applyTokenClasses(leftDoc.tokens, diff.leftClasses);
      applyTokenClasses(rightDoc.tokens, diff.rightClasses);
      lastChanges = diff.changes;
      renderChanges(lastChanges);
    } catch (error) {
      console.error("Compare error:", error);
      changeList.innerHTML = `<div class="empty-report">Could not compare these PDFs.</div>`;
      changeCount.innerText = "(0)";
    } finally {
      isComparing = false;
    }
  }

  async function renderPDF(file, canvas, layer) {
    const bytes = await file.arrayBuffer();
    const pdf = await pdfjsLib.getDocument({ data: new Uint8Array(bytes) }).promise;
    const page = await pdf.getPage(1);
    const viewport = page.getViewport({ scale: previewScale });
    const context = canvas.getContext("2d");

    canvas.width = viewport.width;
    canvas.height = viewport.height;
    canvas.style.width = `${viewport.width}px`;
    canvas.style.height = `${viewport.height}px`;

    layer.innerHTML = "";
    layer.style.width = `${viewport.width}px`;
    layer.style.height = `${viewport.height}px`;

    await page.render({ canvasContext: context, viewport }).promise;

    const content = await page.getTextContent();
    const tokens = buildTextTokens(content.items, content.styles, viewport, layer);

    return { pdf, tokens };
  }

  function buildTextTokens(items, styles, viewport, layer) {
    const tokens = [];

    items.forEach((item, itemIndex) => {
      const text = item.str || "";
      const matches = [...text.matchAll(/\S+/g)];
      if (!matches.length || !item.width) return;

      const tx = pdfjsLib.Util.transform(viewport.transform, item.transform);
      const style = styles?.[item.fontName] || {};
      const fontHeight = Math.max(Math.hypot(tx[2], tx[3]), 6);
      const ascent = typeof style.ascent === "number" ? style.ascent : 0.8;
      const descent = typeof style.descent === "number" ? Math.abs(style.descent) : 0.2;
      const topPad = Math.max(fontHeight * 0.08, 1);
      const bottomPad = Math.max(fontHeight * 0.12, 1);
      const itemWidth = item.width * viewport.scale;
      const itemHeight = fontHeight * (ascent + descent);
      const itemX = tx[4];
      const itemY = tx[5] - fontHeight * ascent - topPad;
      const boxHeight = itemHeight + topPad + bottomPad;
      const totalUnits = Math.max(textUnits(text), 1);
      const unitWidth = itemWidth / totalUnits;

      matches.forEach((match, tokenIndex) => {
        const value = match[0];
        const before = text.slice(0, match.index);
        const x = itemX + textUnits(before) * unitWidth;
        const width = Math.max(textUnits(value) * unitWidth, 3);
        const token = {
          text: value,
          normalized: normalizeWord(value),
          el: document.createElement("span"),
          itemIndex,
          tokenIndex,
        };

        token.el.className = "pdf-word";
        Object.assign(token.el.style, {
          left: `${x}px`,
          top: `${itemY}px`,
          width: `${width}px`,
          height: `${boxHeight}px`,
        });

        layer.appendChild(token.el);
        tokens.push(token);
      });
    });

    return tokens;
  }

  function textUnits(text) {
    return Array.from(text).reduce((sum, ch) => sum + (/\s/.test(ch) ? 0.45 : 1), 0);
  }

  function normalizeWord(text) {
    return String(text).toLowerCase().replace(/[^\p{L}\p{N}]+/gu, "");
  }

  function buildDiff(leftTokens, rightTokens) {
    const leftWords = leftTokens.map((token) => token.normalized);
    const rightWords = rightTokens.map((token) => token.normalized);
    const rows = leftWords.length + 1;
    const cols = rightWords.length + 1;
    const dp = Array.from({ length: rows }, () => Array(cols).fill(0));

    for (let i = leftWords.length - 1; i >= 0; i -= 1) {
      for (let j = rightWords.length - 1; j >= 0; j -= 1) {
        dp[i][j] =
          leftWords[i] && leftWords[i] === rightWords[j]
            ? dp[i + 1][j + 1] + 1
            : Math.max(dp[i + 1][j], dp[i][j + 1]);
      }
    }

    const operations = [];
    let i = 0;
    let j = 0;

    while (i < leftWords.length || j < rightWords.length) {
      if (i < leftWords.length && j < rightWords.length && leftWords[i] === rightWords[j] && leftWords[i]) {
        operations.push({ type: "equal", left: [i], right: [j] });
        i += 1;
        j += 1;
      } else if (j < rightWords.length && (i === leftWords.length || dp[i][j + 1] >= dp[i + 1][j])) {
        operations.push({ type: "insert", right: [j] });
        j += 1;
      } else {
        operations.push({ type: "delete", left: [i] });
        i += 1;
      }
    }

    return summarizeDiff(operations, leftTokens, rightTokens);
  }

  function summarizeDiff(operations, leftTokens, rightTokens) {
    const leftClasses = Array(leftTokens.length).fill("");
    const rightClasses = Array(rightTokens.length).fill("");
    const changes = [];
    let index = 0;

    while (index < operations.length) {
      if (operations[index].type === "equal") {
        index += 1;
        continue;
      }

      const deleted = [];
      const inserted = [];

      while (index < operations.length && operations[index].type !== "equal") {
        if (operations[index].type === "delete") deleted.push(...operations[index].left);
        if (operations[index].type === "insert") inserted.push(...operations[index].right);
        index += 1;
      }

      const type = deleted.length && inserted.length ? "Edit" : deleted.length ? "Delete" : "Insert";

      deleted.forEach((idx) => {
        leftClasses[idx] = type === "Edit" ? "word-edit-old" : "word-delete";
      });
      inserted.forEach((idx) => {
        rightClasses[idx] = type === "Edit" ? "word-edit-new" : "word-insert";
      });

      changes.push({
        type,
        old: deleted.length ? deleted.map((idx) => leftTokens[idx].text).join(" ") : "-",
        newText: inserted.length ? inserted.map((idx) => rightTokens[idx].text).join(" ") : "-",
      });
    }

    return { leftClasses, rightClasses, changes };
  }

  function applyTokenClasses(tokens, classes) {
    tokens.forEach((token, index) => {
      token.el.classList.remove("word-delete", "word-insert", "word-edit-old", "word-edit-new");
      if (classes[index]) token.el.classList.add(classes[index]);
    });
  }

  function setReportLoading() {
    changeList.innerHTML = `<div class="empty-report">Comparing PDFs...</div>`;
    changeCount.innerText = "(...)";
  }

  function renderChanges(changes) {
    const query = (searchChanges?.value || "").trim().toLowerCase();
    const visible = query
      ? changes.filter((change) => `${change.type} ${change.old} ${change.newText}`.toLowerCase().includes(query))
      : changes;

    changeList.innerHTML = "";
    changeCount.innerText = `(${visible.length})`;

    if (!visible.length) {
      changeList.innerHTML = `<div class="empty-report">No text changes found.</div>`;
      return;
    }

    visible.forEach((change) => {
      const item = document.createElement("div");
      item.className = "change-item";
      item.innerHTML = `
        <div class="change-type">${escapeHtml(change.type)}</div>
        <div class="change-box">
          <div class="change-label">Old</div>
          <div class="change-old">${escapeHtml(change.old)}</div>
          <div class="change-label">New</div>
          <div class="change-new">${escapeHtml(change.newText)}</div>
        </div>
      `;
      changeList.appendChild(item);
    });
  }

  searchChanges?.addEventListener("input", () => renderChanges(lastChanges));

  function syncScroll(source, target) {
    if (!syncScrollToggle?.checked || isSyncingScroll || !source || !target) return;

    const maxSourceTop = Math.max(source.scrollHeight - source.clientHeight, 1);
    const maxTargetTop = Math.max(target.scrollHeight - target.clientHeight, 1);
    const maxSourceLeft = Math.max(source.scrollWidth - source.clientWidth, 1);
    const maxTargetLeft = Math.max(target.scrollWidth - target.clientWidth, 1);

    isSyncingScroll = true;
    target.scrollTop = (source.scrollTop / maxSourceTop) * maxTargetTop;
    target.scrollLeft = (source.scrollLeft / maxSourceLeft) * maxTargetLeft;
    requestAnimationFrame(() => {
      isSyncingScroll = false;
    });
  }

  leftPreview?.addEventListener("scroll", () => syncScroll(leftPreview, rightPreview));
  rightPreview?.addEventListener("scroll", () => syncScroll(rightPreview, leftPreview));

  function clearPreview() {
    [leftCanvas, rightCanvas].forEach((canvas) => {
      const ctx = canvas.getContext("2d");
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      canvas.width = 0;
      canvas.height = 0;
      canvas.removeAttribute("style");
    });

    leftHighlights.innerHTML = "";
    rightHighlights.innerHTML = "";
    lastChanges = [];
    changeList.innerHTML = "";
    changeCount.innerText = "(0)";
    previewScale = 1.3;
    updateZoomUI();
  }

  window.clearAll = function () {
    selectedFiles = [];
    renderFileList();
    updateUploadState();
    clearPreview();
    input.value = "";
  };

  uploadForm.addEventListener("submit", function (e) {
    e.preventDefault();

    if (selectedFiles.length < 2) {
      alert("Please upload 2 PDF files.");
      return;
    }

    compareUploadedPDFs();
  });

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
}
