// PPT To PDF Module JS

document.addEventListener("DOMContentLoaded", () => {

    const dropZone = document.getElementById("dropZone");

    // Set upload type dynamically
    if (dropZone) {
        dropZone.dataset.type = "ppt";
    }

});