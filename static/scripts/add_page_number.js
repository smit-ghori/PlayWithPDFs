const previewNumber =
    document.getElementById("previewNumber");

const positionSelect =
    document.getElementById("position");

const startNumber =
    document.getElementById("startNumber");

const pageFormat =
    document.getElementById("pageFormat");

const fontFamily =
    document.getElementById("fontFamily");

const fontColor =
    document.getElementById("fontColor");

const boldBtn =
    document.getElementById("boldBtn");

const italicBtn =
    document.getElementById("italicBtn");

const underlineBtn =
    document.getElementById("underlineBtn");

const pageNumberCard =
    document.querySelector(".page-number-card");

const pageNumberFileInput =
    document.getElementById("pdfInput");

const pageNumberDropZone =
    document.getElementById("dropZone");

const pageNumberFileList =
    document.getElementById("fileList");

const pageNumberForm =
    document.getElementById("mergeForm");


/* =========================================
   HIDDEN INPUTS
========================================= */

const boldInput =
    document.getElementById("boldInput");

const italicInput =
    document.getElementById("italicInput");

const underlineInput =
    document.getElementById("underlineInput");


/* =========================================
   STATES
========================================= */

let isBold = false;
let isItalic = false;
let isUnderline = false;


/* =========================================
   SHOW / HIDE SETTINGS
========================================= */

function updatePageNumberControls() {

    const hasUploadedFile =
        pageNumberFileList.children.length > 0;

    pageNumberCard.classList.toggle(
        "uploaded",
        hasUploadedFile
    );
}

function syncPageNumberControls() {

    requestAnimationFrame(updatePageNumberControls);
}

pageNumberFileInput.addEventListener(
    "change",
    syncPageNumberControls
);

pageNumberDropZone.addEventListener(
    "drop",
    syncPageNumberControls
);

pageNumberForm.addEventListener("reset", () => {

    pageNumberFileInput.value = "";

    if (typeof window.clearAll === "function") {

        window.clearAll();
    }

    syncPageNumberControls();
});

if (typeof window.removeFile === "function") {

    const originalRemoveFile =
        window.removeFile;

    window.removeFile = function (...args) {

        originalRemoveFile.apply(this, args);

        syncPageNumberControls();
    };
}

if (typeof window.clearAll === "function") {

    const originalClearAll =
        window.clearAll;

    window.clearAll = function (...args) {

        originalClearAll.apply(this, args);

        syncPageNumberControls();
    };
}


/* =========================================
   UPDATE PREVIEW
========================================= */

function updatePreview() {

    /* -------------------------------
       PAGE NUMBER FORMAT
    -------------------------------- */

    const number =
        startNumber.value || 1;

    let text = "";

    if (pageFormat.value === "number") {

        text = number;
    }

    else if (pageFormat.value === "page-n") {

        text = `Page ${number}`;
    }

    else {

        text = `Page ${number} of 10`;
    }

    previewNumber.textContent = text;


    /* -------------------------------
       FONT
    -------------------------------- */

    previewNumber.style.fontFamily =
        fontFamily.value;

    previewNumber.style.color =
        fontColor.value;

    previewNumber.style.fontWeight =
        isBold ? "bold" : "normal";

    previewNumber.style.fontStyle =
        isItalic ? "italic" : "normal";

    previewNumber.style.textDecoration =
        isUnderline ? "underline" : "none";


    /* -------------------------------
       RESET POSITION
    -------------------------------- */

    previewNumber.style.top = "auto";

    previewNumber.style.bottom = "auto";

    previewNumber.style.left = "auto";

    previewNumber.style.right = "auto";

    previewNumber.style.transform = "none";


    /* -------------------------------
       POSITION
    -------------------------------- */

    const pos = positionSelect.value;


    if (pos === "top-left") {

        previewNumber.style.top = "18px";

        previewNumber.style.left = "18px";
    }

    else if (pos === "top-center") {

        previewNumber.style.top = "18px";

        previewNumber.style.left = "50%";

        previewNumber.style.transform =
            "translateX(-50%)";
    }

    else if (pos === "top-right") {

        previewNumber.style.top = "18px";

        previewNumber.style.right = "18px";
    }

    else if (pos === "bottom-left") {

        previewNumber.style.bottom = "18px";

        previewNumber.style.left = "18px";
    }

    else if (pos === "bottom-center") {

        previewNumber.style.bottom = "18px";

        previewNumber.style.left = "50%";

        previewNumber.style.transform =
            "translateX(-50%)";
    }

    else if (pos === "bottom-right") {

        previewNumber.style.bottom = "18px";

        previewNumber.style.right = "18px";
    }
}


/* =========================================
   STYLE TOGGLE
========================================= */

boldBtn.addEventListener("click", () => {

    isBold = !isBold;

    boldBtn.classList.toggle("active");


    /* hidden input value */

    boldInput.value =
        isBold ? "true" : "";


    updatePreview();
});


italicBtn.addEventListener("click", () => {

    isItalic = !isItalic;

    italicBtn.classList.toggle("active");


    /* hidden input value */

    italicInput.value =
        isItalic ? "true" : "";


    updatePreview();
});


underlineBtn.addEventListener("click", () => {

    isUnderline = !isUnderline;

    underlineBtn.classList.toggle("active");


    /* hidden input value */

    underlineInput.value =
        isUnderline ? "true" : "";


    updatePreview();
});


/* =========================================
   EVENTS
========================================= */

[
    positionSelect,
    startNumber,
    pageFormat,
    fontFamily,
    fontColor

].forEach((element) => {

    element.addEventListener(
        "input",
        updatePreview
    );
});


/* =========================================
   INITIAL PREVIEW
========================================= */

updatePreview();

updatePageNumberControls();
