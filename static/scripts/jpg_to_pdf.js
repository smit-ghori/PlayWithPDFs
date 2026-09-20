/* =========================================
   GLOBAL
========================================= */
const dropZone = document.getElementById("dropZone");
const input = document.getElementById("imageInput");
const preview = document.getElementById("preview_section");
const form = document.getElementById("mergeForm");
const uploadCard = dropZone.closest(".merge-card");

let selectedFiles = [];

function updateUploadState() {
  uploadCard.classList.toggle(
    "uploaded",
    preview.children.length > 0
  );
}

/* =========================================
   CLICK
========================================= */
dropZone.addEventListener("click", () => input.click());

/* =========================================
   INPUT SELECT
========================================= */
input.addEventListener("change", (e) => {
  handleFiles(e.target.files);
});

/* =========================================
   DRAG DROP
========================================= */
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

/* =========================================
   HANDLE FILES
========================================= */
function handleFiles(files) {
  const maxFiles = window.TOOL_CONFIG?.max_files;
  const currentCount = selectedFiles.filter(f => f !== null).length;
  let imageFiles = [];
  for (let file of files) {
    if (file.type.startsWith("image/")) {
      imageFiles.push(file);
    }
  }

  if (maxFiles && (currentCount + imageFiles.length) > maxFiles) {
    const totalAttempted = currentCount + imageFiles.length;
    const remaining = Math.max(0, maxFiles - currentCount);
    const msg = `Maximum file limit is ${maxFiles}. You selected ${totalAttempted} files. Please upload up to ${maxFiles} files only.`;
    if (typeof window.showFlashMessage === "function") {
      window.showFlashMessage(msg, "error");
    } else {
      alert(msg);
    }
    imageFiles = imageFiles.slice(0, remaining);
  }

  for (let file of imageFiles) {
    const fileIndex = selectedFiles.length; // 🔥 FIXED INDEX
    selectedFiles.push(file);

    const reader = new FileReader();
    reader.onload = function (e) {
      const div = document.createElement("div");
      div.classList.add("img-box");

      div.setAttribute("data-index", fileIndex); // 🔥 IMPORTANT

      div.innerHTML = `
        <div class="drag-handle">☰</div>
        <img src="${e.target.result}">
        <button class="remove-btn">✕</button>
      `;

      // REMOVE IMAGE
      div.querySelector(".remove-btn").onclick = () => {
        const originalIndex = parseInt(div.getAttribute("data-index"));

        selectedFiles[originalIndex] = null; // 🔥 DON'T SHIFT ARRAY
        div.remove();
        updateUploadState();
      };

      preview.appendChild(div);
      updateUploadState();
    };

    reader.readAsDataURL(file);
  }
}

/* =========================================
   SORTABLE (DRAG)
========================================= */
new Sortable(preview, {
  animation: 150,
  handle: ".drag-handle",

  scroll: true,
  scrollSensitivity: 60,
  scrollSpeed: 10,

  delay: 150,
  delayOnTouchOnly: true
});

/* =========================================
   CLEAR ALL
========================================= */
function clearAll() {
  preview.innerHTML = "";
  input.value = "";
  selectedFiles = [];
  updateUploadState();
}

/* =========================================
   FORM SUBMIT
========================================= */
form.addEventListener("submit", (e) => {
  const boxes = document.querySelectorAll(".img-box");

  if (boxes.length === 0) {
    e.preventDefault();
    alert("Please select images.");
    return;
  }

  const maxFiles = window.TOOL_CONFIG?.max_files;
  if (maxFiles && boxes.length > maxFiles) {
    e.preventDefault();
    const msg = `Maximum file limit is ${maxFiles}. You selected ${boxes.length} files. Please upload up to ${maxFiles} files only.`;
    if (typeof window.showFlashMessage === "function") {
      window.showFlashMessage(msg, "error");
    } else {
      alert(msg);
    }
    return;
  }

  // Read the ORIGINAL file indexes in the exact order the user arranged them
  const orderedIndexes = Array.from(boxes).map((box) =>
    parseInt(box.getAttribute("data-index"), 10)
  );

  console.log("FINAL ORDER:", orderedIndexes);

  // Rebuild the file input in the same visual order shown in the UI
  const dataTransfer = new DataTransfer();
  orderedIndexes.forEach((fileIndex) => {
    const file = selectedFiles[fileIndex];
    if (file) {
      dataTransfer.items.add(file);
    }
  });
  input.files = dataTransfer.files;

  // Send sequential indexes because `input.files` is already reordered above
  let hidden = document.getElementById("orderInput");

  if (!hidden) {
    hidden = document.createElement("input");
    hidden.type = "hidden";
    hidden.name = "image_order";
    hidden.id = "orderInput";
    form.appendChild(hidden);
  }

  hidden.value = Array.from({ length: input.files.length }, (_, index) => index).join(",");
});

/* =========================================
   CUSTOM DROPDOWN
========================================= */
const dropdown = document.getElementById("marginDropdown");
const selected = dropdown.querySelector(".dropdown-selected");
const options = dropdown.querySelectorAll(".dropdown-options div");
const hiddenInput = document.getElementById("marginInput");

// toggle
selected.addEventListener("click", () => {
  dropdown.classList.toggle("active");
});

// select option
options.forEach(option => {
  option.addEventListener("click", () => {
    selected.innerText = option.innerText;
    hiddenInput.value = option.dataset.value;

    options.forEach(o => o.classList.remove("active"));
    option.classList.add("active");

    dropdown.classList.remove("active");
  });
});

// close outside
document.addEventListener("click", (e) => {
  if (!dropdown.contains(e.target)) {
    dropdown.classList.remove("active");
  }
});
