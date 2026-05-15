/* =========================================
   LIVE WATERMARK PREVIEW
   ========================================= */

const watermarkInput = document.querySelector(
    'input[name="watermark_text"]'
);

const boldInput = document.querySelector(
    'input[name="bold"]'
);

const italicInput = document.querySelector(
    'input[name="italic"]'
);

const underlineInput = document.querySelector(
    'input[name="underline"]'
);

const colorInput = document.querySelector(
    'input[name="watermark_color"]'
);

const fontInput = document.querySelector(
    'select[name="font_family"]'
);

const positionInput = document.querySelector(
    'select[name="position"]'
);

const transparencyInput = document.querySelector(
    'select[name="transparency"]'
);

const rotationInput = document.querySelector(
    'select[name="rotation"]'
);

const preview = document.getElementById(
    "watermarkPreview"
);

function updateWatermarkPreview() {

    /* Text */
    preview.textContent =
        watermarkInput.value || "SAMPLE WATERMARK";

    /* Font */
    preview.style.fontFamily =
        fontInput.value;

    /* Bold */
    preview.style.fontWeight =
        boldInput.checked ? "700" : "500";

    /* Italic */
    preview.style.fontStyle =
        italicInput.checked ? "italic" : "normal";

    /* Underline */
    preview.style.textDecoration =
        underlineInput.checked ? "underline" : "none";

    /* Color */
    preview.style.color =
        hexToRGBA(
            colorInput.value,
            transparencyInput.value
        );

    /* Rotation */
    const rotation =
        rotationInput.value;

    /* Position */
    setPreviewPosition(positionInput.value, rotation);
}

/* =========================================
   POSITION
   ========================================= */

function setPreviewPosition(position, rotation) {

    preview.style.top = "";
    preview.style.left = "";
    preview.style.right = "";
    preview.style.bottom = "";

    let translateX = "-50%";
    let translateY = "-50%";

    switch (position) {

        case "top-left":
            preview.style.top = "18%";
            preview.style.left = "20%";
            break;

        case "top-center":
            preview.style.top = "18%";
            preview.style.left = "50%";
            break;

        case "top-right":
            preview.style.top = "18%";
            preview.style.left = "80%";
            break;

        case "middle-left":
            preview.style.top = "50%";
            preview.style.left = "20%";
            break;

        case "middle-center":
            preview.style.top = "50%";
            preview.style.left = "50%";
            break;

        case "middle-right":
            preview.style.top = "50%";
            preview.style.left = "80%";
            break;

        case "bottom-left":
            preview.style.top = "82%";
            preview.style.left = "20%";
            break;

        case "bottom-center":
            preview.style.top = "82%";
            preview.style.left = "50%";
            break;

        case "bottom-right":
            preview.style.top = "82%";
            preview.style.left = "80%";
            break;
    }

    preview.style.transform =
        `translate(${translateX}, ${translateY}) rotate(${rotation}deg)`;
}

/* =========================================
   HEX TO RGBA
   ========================================= */

function hexToRGBA(hex, transparency) {

    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);

    let opacity = 1;

    switch (transparency) {
        case "75":
            opacity = 0.25;
            break;

        case "50":
            opacity = 0.5;
            break;

        case "20":
            opacity = 0.8;
            break;

        case "0":
            opacity = 1;
            break;
    }

    return `rgba(${r}, ${g}, ${b}, ${opacity})`;
}

/* =========================================
   EVENTS
   ========================================= */

[
    watermarkInput,
    boldInput,
    italicInput,
    underlineInput,
    colorInput,
    fontInput,
    positionInput,
    transparencyInput,
    rotationInput
].forEach(element => {

    element.addEventListener(
        "input",
        updateWatermarkPreview
    );

    element.addEventListener(
        "change",
        updateWatermarkPreview
    );
});

/* Initial Load */
updateWatermarkPreview();