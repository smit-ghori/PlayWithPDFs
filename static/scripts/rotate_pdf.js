pdfjsLib.GlobalWorkerOptions.workerSrc =
    "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";

const pdfInput = document.getElementById("pdfInput");

const previewContainer = document.getElementById(
    "pdfPreviewContainer"
);

const rotationDataInput =
    document.getElementById("rotationData");

const globalControls =
    document.querySelector(".global-controls");

const rotateCard =
    document.querySelector(".rotate-card");

let uploadedPDF = null;
let pageRotations = {};
let isClearingRotatePDF = false;


/* =========================================
   SHOW / HIDE UI
========================================= */

function showControls() {

    rotateCard.classList.add("expanded");

    globalControls.style.display = "block";
    previewContainer.style.display = "grid";

    requestAnimationFrame(() => {

        globalControls.classList.add("visible");

        previewContainer.classList.add("visible");
    });
}

function hideControls() {

    globalControls.classList.remove("visible");

    previewContainer.classList.remove("visible");

    setTimeout(() => {

        globalControls.style.display = "none";

        previewContainer.style.display = "none";

        rotateCard.classList.remove("expanded");

    }, 250);
}

/* =========================================
   FILE INPUT CHANGE
========================================= */

pdfInput.addEventListener("change", async (e) => {

    const file = e.target.files[0];

    if (!file) return;

    previewContainer.innerHTML = "";

    pageRotations = {};

    const fileReader = new FileReader();

    fileReader.onload = async function () {

        try {

            const typedArray = new Uint8Array(this.result);

            uploadedPDF =
                await pdfjsLib.getDocument(typedArray).promise;

            showControls();

            await renderAllPages();

        } catch (error) {

            console.error("PDF Load Error:", error);

            alert("Failed to load PDF file.");
        }
    };

    fileReader.readAsArrayBuffer(file);
});


/* =========================================
   RENDER ALL PAGES
========================================= */

async function renderAllPages() {

    previewContainer.innerHTML = "";

    for (let i = 1; i <= uploadedPDF.numPages; i++) {

        pageRotations[i] = 0;

        const page = await uploadedPDF.getPage(i);

        const viewport = page.getViewport({
            scale: 1.2
        });

        const canvas = document.createElement("canvas");

        const context = canvas.getContext("2d");

        canvas.height = viewport.height;

        canvas.width = viewport.width;

        await page.render({
            canvasContext: context,
            viewport
        }).promise;

        /* =========================================
           PAGE CARD
        ========================================= */

        const wrapper = document.createElement("div");

        wrapper.className = "preview-page";

        /* PAGE NUMBER */

        const pageLabel = document.createElement("div");

        pageLabel.className = "page-number";

        pageLabel.textContent = `Page ${i}`;

        wrapper.appendChild(pageLabel);

        /* PDF CANVAS */

        const canvasFrame = document.createElement("div");

        canvasFrame.className = "canvas-frame";

        canvasFrame.appendChild(canvas);

        wrapper.appendChild(canvasFrame);

        /* =========================================
           PAGE CONTROLS
        ========================================= */

        const controls = document.createElement("div");

        controls.className = "page-controls";

        controls.innerHTML = `
      <button
        type="button"
        class="rotate-btn"
        onclick="rotatePage(${i}, -90)"
      >
        Left
      </button>

      <button
        type="button"
        class="rotate-btn"
        onclick="rotatePage(${i}, 90)"
      >
        Right
      </button>

      <button
        type="button"
        class="reset-btn"
        onclick="resetPage(${i})"
      >
        Reset
      </button>
    `;

        wrapper.appendChild(controls);

        previewContainer.appendChild(wrapper);
    }

    updateRotationInput();
}


/* =========================================
   ROTATE SINGLE PAGE
========================================= */

function rotatePage(pageNumber, angle) {

    pageRotations[pageNumber] += angle;

    applyRotation(pageNumber);
}


/* =========================================
   RESET SINGLE PAGE
========================================= */

function resetPage(pageNumber) {

    pageRotations[pageNumber] = 0;

    applyRotation(pageNumber);
}


/* =========================================
   ROTATE ALL PAGES
========================================= */

function rotateAll(angle) {

    Object.keys(pageRotations).forEach((page) => {

        pageRotations[page] += angle;

        applyRotation(page);
    });
}


/* =========================================
   RESET ALL PAGES
========================================= */

function resetAllPages() {

    Object.keys(pageRotations).forEach((page) => {

        pageRotations[page] = 0;

        applyRotation(page);
    });
}


/* =========================================
   APPLY ROTATION
========================================= */

function applyRotation(pageNumber) {

    const previewPages =
        document.querySelectorAll(".preview-page");

    const canvas =
        previewPages[pageNumber - 1]
            .querySelector("canvas");

    const frame =
        canvas.closest(".canvas-frame");

    const normalizedRotation =
        ((pageRotations[pageNumber] % 360) + 360) % 360;

    let scale = 1;

    if (
        normalizedRotation === 90 ||
        normalizedRotation === 270
    ) {

        const frameRect =
            frame.getBoundingClientRect();

        const canvasWidth =
            canvas.offsetWidth;

        const canvasHeight =
            canvas.offsetHeight;

        if (
            frameRect.width &&
            frameRect.height &&
            canvasWidth &&
            canvasHeight
        ) {

            scale = Math.min(
                frameRect.width / canvasHeight,
                frameRect.height / canvasWidth,
                1
            ) * 0.96;
        }
    }

    canvas.style.transition =
        "transform 0.35s ease";

    canvas.style.transform =
        `rotate(${pageRotations[pageNumber]}deg) scale(${scale})`;

    updateRotationInput();
}

window.addEventListener("resize", () => {

    Object.keys(pageRotations).forEach((page) => {

        applyRotation(page);
    });
});


/* =========================================
   UPDATE HIDDEN INPUT
========================================= */

function updateRotationInput() {

    rotationDataInput.value =
        JSON.stringify(pageRotations);
}


/* =========================================
   CLEAR ALL
========================================= */

function clearAll() {

    isClearingRotatePDF = true;

    uploadedPDF = null;

    pageRotations = {};

    previewContainer.innerHTML = "";

    rotationDataInput.value = "";

    pdfInput.value = "";

    const fileList =
        document.getElementById("fileList");

    if (fileList) {
        fileList.innerHTML = "";
    }

    hideControls();

    isClearingRotatePDF = false;
}

if (typeof window.removeFile === "function") {

    const originalRemoveFile =
        window.removeFile;

    window.removeFile = function (...args) {

        originalRemoveFile.apply(this, args);

        if (!isClearingRotatePDF) {

            clearAll();
        }
    };
}

window.resetUploadForm = clearAll;
