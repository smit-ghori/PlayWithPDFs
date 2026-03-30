/* =========================================
   GLOBAL
========================================= */
const dropZone = document.getElementById("dropZone");
const input = document.getElementById("imageInput");
const preview = document.getElementById("preview_section");
const form = document.getElementById("mergeForm");

let selectedFiles = [];

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
  for (let file of files) {
    if (!file.type.startsWith("image/")) continue;

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
      };

      preview.appendChild(div);
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
}

/* =========================================
   FORM SUBMIT
========================================= */
form.addEventListener("submit", (e) => {
  if (selectedFiles.length === 0) {
    e.preventDefault();
    alert("Please select images.");
    return;
  }

  // 🔥 GET ORDER FROM DOM
  const boxes = document.querySelectorAll(".img-box");
  const order = [];

  boxes.forEach(box => {
    order.push(box.getAttribute("data-index"));
  });

  console.log("FINAL ORDER:", order);

  // 🔥 SEND ORDER TO BACKEND
  let hidden = document.getElementById("orderInput");

  if (!hidden) {
    hidden = document.createElement("input");
    hidden.type = "hidden";
    hidden.name = "image_order";
    hidden.id = "orderInput";
    form.appendChild(hidden);
  }

  hidden.value = order.join(",");

  // 🔥 SEND ONLY VALID FILES
  const dataTransfer = new DataTransfer();

  selectedFiles.forEach(file => {
    if (file !== null) {
      dataTransfer.items.add(file);
    }
  });

  input.files = dataTransfer.files;
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