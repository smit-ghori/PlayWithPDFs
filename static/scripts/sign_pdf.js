/* =========================================
   SIGN PDF
   1. Upload PDF  → card expands, renders page previews
   2. Upload signature image (any image type)
   3. Click "+ Add to page" on any page → signature placed on that page
   4. Drag signature anywhere on the page
   5. Delete badge (×) removes it
   ========================================= */

(function () {

    /* ── DOM refs ── */
    const card = document.getElementById("mergeCard");
    const dropZone = document.getElementById("dropZone");
    const pdfInput = document.getElementById("pdfInput");
    const fileListUI = document.getElementById("fileList");
    const uploadForm = document.getElementById("mergeForm");

    const sigDrop = document.getElementById("sigDrop");
    const sigInput = document.getElementById("sigInput");
    const sigThumbWrap = document.getElementById("sigThumbWrap");
    const sigThumb = document.getElementById("sigThumb");
    const sigClearBtn = document.getElementById("sigClearBtn");
    const sigDropText = document.getElementById("sigDropText");

    const pdfPagesContainer = document.getElementById("pdfPagesContainer");
    const clearAllBtn = document.getElementById("clearAllBtn");

    /* ── State ── */
    let selectedFiles = [];
    let signatureSrc = null;   // base64 of uploaded signature image
    let signatureFile = null;  // File object for signature image to send to server

    /* =========================================
       PDF DROP ZONE
    ========================================= */

    dropZone.addEventListener("click", () => pdfInput.click());

    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("drag-over");
    });

    dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));

    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("drag-over");
        handlePdfFiles(e.dataTransfer.files);
    });

    pdfInput.addEventListener("change", (e) => {
        handlePdfFiles(e.target.files);
        pdfInput.value = "";
    });

    async function handlePdfFiles(files) {
        for (const file of files) {
            if (file.type === "application/pdf") {
                selectedFiles.push(file);
                await renderPDF(file);
            } else {
                alert("Please upload PDF files only.");
            }
        }
        renderFileList();
        if (selectedFiles.length > 0) card.classList.add("uploaded");
    }

    /* =========================================
       FILE LIST UI
    ========================================= */

    function renderFileList() {
        fileListUI.innerHTML = "";
        selectedFiles.forEach((file, i) => {
            const li = document.createElement("li");
            li.innerHTML = `
        <span class="file-name">${file.name}</span>
        <button type="button" class="remove-btn" data-index="${i}">✕</button>
      `;
            fileListUI.appendChild(li);
        });
    }

    fileListUI.addEventListener("click", (e) => {
        if (!e.target.classList.contains("remove-btn")) return;
        // Prevent the click from bubbling up to the drop zone
        // (which would open the file picker via its click handler)
        e.stopPropagation();
        const i = parseInt(e.target.dataset.index);
        selectedFiles.splice(i, 1);
        renderFileList();
        pdfPagesContainer.innerHTML = "";
        if (selectedFiles.length === 0) card.classList.remove("uploaded");
        else selectedFiles.forEach(f => renderPDF(f));
    });

    /* =========================================
       RENDER PDF PAGES
    ========================================= */

    async function renderPDF(file) {
        const buffer = await file.arrayBuffer();
        const typedArr = new Uint8Array(buffer);
        const pdf = await pdfjsLib.getDocument(typedArr).promise;

        for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
            const page = await pdf.getPage(pageNum);
            const viewport = page.getViewport({ scale: 1.4 });

            /* Page wrapper */
            const pageWrap = document.createElement("div");
            pageWrap.classList.add("pdf-page");
            pageWrap.dataset.page = pageNum;

            /* Toolbar */
            const toolbar = document.createElement("div");
            toolbar.classList.add("page-toolbar");
            toolbar.innerHTML = `
        <span class="page-label">Page ${pageNum}</span>
        <button type="button" class="add-sig-btn" ${signatureSrc ? "" : "disabled"}>
          + Add Signature
        </button>
      `;
            pageWrap.appendChild(toolbar);

            /* Canvas wrapper — draggables live here */
            const canvasWrap = document.createElement("div");
            canvasWrap.classList.add("canvas-wrapper");

            /* Canvas */
            const canvas = document.createElement("canvas");
            canvas.classList.add("pdf-render");
            const ctx = canvas.getContext("2d");
            canvas.width = viewport.width;
            canvas.height = viewport.height;
            canvasWrap.appendChild(canvas);
            pageWrap.appendChild(canvasWrap);
            pdfPagesContainer.appendChild(pageWrap);

            await page.render({ canvasContext: ctx, viewport }).promise;

            /* Add Signature button */
            toolbar.querySelector(".add-sig-btn").addEventListener("click", () => {
                if (!signatureSrc) {
                    alert("Please upload a signature image first.");
                    return;
                }
                placeSig(canvasWrap, signatureSrc);
            });
        }
    }

    /* =========================================
       SIGNATURE IMAGE UPLOAD
    ========================================= */

    /* Click on the label opens file picker (input is nested in label, browser handles it) */
    /* Removed explicit sigInput.click() to avoid triggering the file picker twice */

    /* Drag over the sig drop zone */
    sigDrop.addEventListener("dragover", (e) => {
        e.preventDefault();
        sigDrop.style.borderColor = "rgba(125,211,252,0.6)";
    });
    sigDrop.addEventListener("dragleave", () => {
        sigDrop.style.borderColor = "";
    });
    sigDrop.addEventListener("drop", (e) => {
        e.preventDefault();
        sigDrop.style.borderColor = "";
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith("image/")) {
            signatureFile = file;
            loadSig(file);
        }
        else alert("Please drop an image file.");
    });

    sigInput.addEventListener("change", (e) => {
        if (e.target.files[0]) {
            signatureFile = e.target.files[0];
            loadSig(signatureFile);
        }
        // clear the file input so the same file can be re-selected later
        sigInput.value = "";
    });

    function loadSig(file) {
        const reader = new FileReader();
        reader.onload = (ev) => {
            signatureSrc = ev.target.result;

            /* Show thumbnail */
            sigThumb.src = signatureSrc;
            sigThumbWrap.style.display = "flex";
            sigDropText.textContent = "Change signature";

            /* Enable all Add Signature buttons */
            document.querySelectorAll(".add-sig-btn").forEach(btn => {
                btn.disabled = false;
            });
        };
        reader.readAsDataURL(file);
    }

    /* Remove signature */
    sigClearBtn.addEventListener("click", () => {
        signatureSrc = null;
        sigThumb.src = "";
        sigThumbWrap.style.display = "none";
        sigDropText.textContent = "Click or drag signature image here";

        /* Disable add buttons + remove all placed sigs */
        document.querySelectorAll(".add-sig-btn").forEach(btn => btn.disabled = true);
        document.querySelectorAll(".placed-sig").forEach(el => el.remove());
    });

    /* =========================================
       PLACE SIGNATURE ON A PAGE
    ========================================= */

    function placeSig(parent, src) {
        const wrap = document.createElement("div");
        wrap.classList.add("placed-sig");
        wrap.style.top = "20px";
        wrap.style.left = "20px";
        wrap.style.width = "180px";
        wrap.style.height = "80px";
        // attach page number for server-side mapping
        const pageEl = parent.closest('.pdf-page');
        if (pageEl && pageEl.dataset.page) wrap.dataset.page = pageEl.dataset.page;
        wrap.dataset.angle = '0';
        // store the canvas dimensions used to render this page so server can scale
        const canvasEl = parent.querySelector('canvas') || parent.querySelector('.pdf-render');
        if (canvasEl) {
            // canvas.width/height are the pixel dimensions used by pdf.js
            wrap.dataset.canvasWidth = String(canvasEl.width || canvasEl.offsetWidth || 0);
            wrap.dataset.canvasHeight = String(canvasEl.height || canvasEl.offsetHeight || 0);
        }

        /* Inner frame (border lives here so handles sit outside) */
        const frame = document.createElement("div");
        frame.classList.add("sig-frame");

        const img = document.createElement("img");
        img.src = src;
        img.alt = "Signature";
        img.draggable = false;
        frame.appendChild(img);
        wrap.appendChild(frame);

        /* Corner resize handles */
        ["nw", "ne", "sw", "se"].forEach(dir => {
            const h = document.createElement("div");
            h.classList.add("rh", dir);
            h.dataset.dir = dir;
            wrap.appendChild(h);
        });

        /* Rotation connector line */
        const rotLine = document.createElement("div");
        rotLine.classList.add("rot-line");
        wrap.appendChild(rotLine);

        /* Rotation handle */
        const rotHandle = document.createElement("div");
        rotHandle.classList.add("rot-handle");
        rotHandle.title = "Rotate";
        rotHandle.innerHTML = "↻";
        wrap.appendChild(rotHandle);

        /* Angle badge */
        const angleBadge = document.createElement("div");
        angleBadge.classList.add("angle-badge");
        angleBadge.textContent = "0°";
        wrap.appendChild(angleBadge);

        /* Delete badge */
        const del = document.createElement("span");
        del.classList.add("del-badge");
        del.textContent = "×";
        del.addEventListener("click", (e) => { e.stopPropagation(); wrap.remove(); });
        wrap.appendChild(del);

        parent.appendChild(wrap);
        attachInteractions(wrap, frame, rotHandle, angleBadge, parent);
    }

    /* =========================================
       DRAG + RESIZE + ROTATE
    ========================================= */

    function attachInteractions(wrap, frame, rotHandle, angleBadge, parent) {
        let angle = 0;   // degrees
        let mode = null; // "drag" | "resize-nw/ne/sw/se" | "rotate"

        /* Tracked per-interaction */
        let startX, startY;
        let origLeft, origTop, origW, origH;
        let rotStartAngle, rotCenterX, rotCenterY;

        /* ── helpers ── */
        function getXY(e) {
            return e.touches
                ? { x: e.touches[0].clientX, y: e.touches[0].clientY }
                : { x: e.clientX, y: e.clientY };
        }

        function applyTransform() {
            wrap.style.transform = `rotate(${angle}deg)`;
            angleBadge.textContent = `${Math.round(((angle % 360) + 360) % 360)}°`;
            wrap.dataset.angle = String(angle);
        }

        function setActive(on) {
            wrap.classList.toggle("active", on);
        }

        /* ── DRAG (frame) ── */
        frame.addEventListener("mousedown", startDrag);
        frame.addEventListener("touchstart", startDrag, { passive: false });

        function startDrag(e) {
            if (mode) return;
            e.preventDefault();
            mode = "drag";
            const pt = getXY(e);
            startX = pt.x;
            startY = pt.y;
            origLeft = parseInt(wrap.style.left) || 0;
            origTop = parseInt(wrap.style.top) || 0;
            wrap.classList.add("is-dragging");
            setActive(true);
        }

        /* ── RESIZE (corner handles) ── */
        wrap.querySelectorAll(".rh").forEach(h => {
            h.addEventListener("mousedown", (e) => startResize(e, h.dataset.dir));
            h.addEventListener("touchstart", (e) => startResize(e, h.dataset.dir), { passive: false });
        });

        function startResize(e, dir) {
            if (mode) return;
            e.preventDefault();
            e.stopPropagation();
            mode = "resize-" + dir;
            const pt = getXY(e);
            startX = pt.x;
            startY = pt.y;
            origW = wrap.offsetWidth;
            origH = wrap.offsetHeight;
            origLeft = parseInt(wrap.style.left) || 0;
            origTop = parseInt(wrap.style.top) || 0;
            setActive(true);
        }

        /* ── ROTATE (rotation handle) ── */
        rotHandle.addEventListener("mousedown", startRotate);
        rotHandle.addEventListener("touchstart", startRotate, { passive: false });

        function startRotate(e) {
            if (mode) return;
            e.preventDefault();
            e.stopPropagation();
            mode = "rotate";

            /* Centre of the element in page coords */
            const rect = wrap.getBoundingClientRect();
            rotCenterX = rect.left + rect.width / 2;
            rotCenterY = rect.top + rect.height / 2;

            const pt = getXY(e);
            /* Angle from centre to pointer at drag start, minus current rotation */
            rotStartAngle = Math.atan2(pt.y - rotCenterY, pt.x - rotCenterX) * (180 / Math.PI) - angle;
            rotHandle.style.cursor = "grabbing";
            setActive(true);
        }

        /* ── GLOBAL MOVE ── */
        function onMove(e) {
            if (!mode) return;
            e.preventDefault();
            const pt = getXY(e);

            if (mode === "drag") {
                const dx = pt.x - startX;
                const dy = pt.y - startY;
                const maxL = parent.offsetWidth - wrap.offsetWidth;
                const maxT = parent.offsetHeight - wrap.offsetHeight;
                wrap.style.left = `${clamp(origLeft + dx, 0, maxL)}px`;
                wrap.style.top = `${clamp(origTop + dy, 0, maxT)}px`;

            } else if (mode === "rotate") {
                const rect = wrap.getBoundingClientRect();
                const cx = rect.left + rect.width / 2;
                const cy = rect.top + rect.height / 2;
                const raw = Math.atan2(pt.y - cy, pt.x - cx) * (180 / Math.PI);
                /* Snap to 15° increments when Shift is held */
                let newAngle = raw - rotStartAngle;
                if (e.shiftKey) newAngle = Math.round(newAngle / 15) * 15;
                angle = newAngle;
                applyTransform();

            } else if (mode.startsWith("resize-")) {
                const dir = mode.slice(7);  // "nw" | "ne" | "sw" | "se"
                const dx = pt.x - startX;
                const dy = pt.y - startY;
                const MIN = 40;

                let newW = origW, newH = origH, newL = origLeft, newT = origTop;

                /* Horizontal */
                if (dir.includes("e")) { newW = Math.max(MIN, origW + dx); }
                if (dir.includes("w")) { newW = Math.max(MIN, origW - dx); newL = origLeft + (origW - newW); }

                /* Vertical */
                if (dir.includes("s")) { newH = Math.max(MIN, origH + dy); }
                if (dir.includes("n")) { newH = Math.max(MIN, origH - dy); newT = origTop + (origH - newH); }

                /* Clamp position */
                newL = clamp(newL, 0, parent.offsetWidth - newW);
                newT = clamp(newT, 0, parent.offsetHeight - newH);

                wrap.style.width = `${newW}px`;
                wrap.style.height = `${newH}px`;
                wrap.style.left = `${newL}px`;
                wrap.style.top = `${newT}px`;
            }
        }

        /* ── GLOBAL END ── */
        function onEnd() {
            if (!mode) return;
            if (mode === "drag") wrap.classList.remove("is-dragging");
            if (mode === "rotate") rotHandle.style.cursor = "";
            mode = null;
            setActive(false);
        }

        document.addEventListener("mousemove", onMove);
        document.addEventListener("mouseup", onEnd);
        document.addEventListener("touchmove", onMove, { passive: false });
        document.addEventListener("touchend", onEnd);
    }

    /* =========================================
       CLEAR ALL
    ========================================= */

    clearAllBtn.addEventListener("click", () => {
        selectedFiles = [];
        signatureSrc = null;

        renderFileList();
        pdfPagesContainer.innerHTML = "";
        sigThumb.src = "";
        sigThumbWrap.style.display = "none";
        sigDropText.textContent = "Click or drag signature image here";
        card.classList.remove("uploaded");
    });

    /* =========================================
       FORM SUBMIT — attach files to input
    ========================================= */

    uploadForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (selectedFiles.length === 0) {
            alert("Please upload a PDF first.");
            return;
        }

        // Build FormData manually
        const formData = new FormData();
        // append PDFs
        selectedFiles.forEach((f) => formData.append('pdfs', f));
        // append signature file
        if (signatureFile) formData.append('signature_image', signatureFile);

        // Collect placements including canvas dims
        const placements = [];
        document.querySelectorAll('.placed-sig').forEach(el => {
            placements.push({
                page: el.dataset.page ? parseInt(el.dataset.page, 10) : null,
                left: el.style.left ? parseFloat(el.style.left) : null,
                top: el.style.top ? parseFloat(el.style.top) : null,
                width: el.style.width ? parseFloat(el.style.width) : null,
                height: el.style.height ? parseFloat(el.style.height) : null,
                angle: el.dataset.angle ? parseFloat(el.dataset.angle) : 0,
                canvas_width_px: el.dataset.canvasWidth ? parseFloat(el.dataset.canvasWidth) : null,
                canvas_height_px: el.dataset.canvasHeight ? parseFloat(el.dataset.canvasHeight) : null
            });
        });
        formData.append('sig_placements', JSON.stringify(placements));

        // Send request via fetch to get Blob response (PDF)
        try {
            const res = await fetch(uploadForm.action || window.location.href, {
                method: 'POST',
                body: formData
            });
            if (!res.ok) {
                const txt = await res.text();
                alert('Upload failed: ' + res.status + ' ' + res.statusText + '\n' + txt);
                return;
            }

            const blob = await res.blob();
            // Trigger download
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            // Try to get filename from Content-Disposition header
            const disposition = res.headers.get('Content-Disposition') || res.headers.get('content-disposition');
            let filename = 'signed.pdf';
            if (disposition) {
                const match = /filename\*=UTF-8''(.+)$/.exec(disposition) || /filename="?([^";]+)"?/.exec(disposition);
                if (match) filename = decodeURIComponent(match[1]);
            }
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);

            // After download, reset UI to initial (collapsed) state
            selectedFiles = [];
            signatureSrc = null;
            signatureFile = null;
            renderFileList();
            pdfPagesContainer.innerHTML = '';
            sigThumb.src = '';
            sigThumbWrap.style.display = 'none';
            sigDropText.textContent = 'Click or drag signature image here';
            card.classList.remove('uploaded');

        } catch (err) {
            console.error(err);
            alert('An error occurred while signing the PDF. See console for details.');
        }
    });

    /* ── util ── */
    function clamp(v, min, max) { return Math.max(min, Math.min(v, max)); }

})();