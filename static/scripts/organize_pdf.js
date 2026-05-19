pdfjsLib.GlobalWorkerOptions.workerSrc =
    'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';


/* =========================================
   STATE
========================================= */

let pages = [];
let history = [];
let dragSrcIdx = null;


/* =========================================
   DOM
========================================= */

const orgCard = document.getElementById('orgCard');

const dropZone = document.getElementById('dropZone');

const pdfInput = document.getElementById('pdfInput');

const dropLabel = document.getElementById('dropLabel');

const loadingBar = document.getElementById('loadingBar');

const progressFill = document.getElementById('progressFill');

const progressLbl = document.getElementById('progressLabel');

const gridReveal = document.getElementById('gridReveal');

const pagesGrid = document.getElementById('pagesGrid');

const toolbar = document.getElementById('toolbar');

const pageCount = document.getElementById('pageCount');

const undoBtn = document.getElementById('undoBtn');

const pageOrderInput =
    document.getElementById('pageOrderInput');


/* =========================================
   AUTO SCROLL WHILE DRAGGING
========================================= */

let autoScrollInterval = null;

function handleAutoScroll(e) {

    const container = document.getElementById('gridScroll');

    const rect = container.getBoundingClientRect();

    const topZone = rect.top + 120;

    const bottomZone = rect.bottom - 120;

    clearInterval(autoScrollInterval);

    /* Scroll UP */
    if (e.clientY < topZone) {

        autoScrollInterval = setInterval(() => {

            container.scrollTop -= 18;

        }, 16);
    }

    /* Scroll DOWN */
    else if (e.clientY > bottomZone) {

        autoScrollInterval = setInterval(() => {

            container.scrollTop += 18;

        }, 16);
    }
}

/* =========================================
   DROP ZONE
========================================= */

dropZone.addEventListener('click', () => {
    pdfInput.click();
});

dropZone.addEventListener('dragover', e => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', e => {

    e.preventDefault();

    dropZone.classList.remove('drag-over');

    const file = e.dataTransfer.files[0];

    if (file?.type === 'application/pdf') {
        startLoad(file);
    }
});

pdfInput.addEventListener('change', e => {

    if (e.target.files[0]) {
        startLoad(e.target.files[0]);
    }
});


/* =========================================
   START LOAD
========================================= */

function startLoad(file) {

    pages = [];
    history = [];

    pagesGrid.innerHTML = '';

    gridReveal.classList.remove('visible');

    toolbar.classList.remove('visible');

    orgCard.classList.add('has-pdf');

    dropLabel.innerHTML =
        `<strong>${file.name}</strong>
     <span>Click to replace</span>`;

    progressFill.style.width = '0%';

    loadingBar.classList.add('show');

    setTimeout(() => {
        loadPDF(file);
    }, 80);
}


/* =========================================
   LOAD PDF
========================================= */

async function loadPDF(file) {

    const bytes = await file.arrayBuffer();

    const pdf = await pdfjsLib.getDocument({
        data: bytes
    }).promise;

    const total = pdf.numPages;

    for (let i = 1; i <= total; i++) {

        progressFill.style.width =
            `${Math.round((i / total) * 100)}%`;

        progressLbl.textContent =
            `Rendering page ${i} of ${total}...`;

        const page = await pdf.getPage(i);

        const viewport = page.getViewport({
            scale: 0.45
        });

        const canvas = document.createElement('canvas');

        const context = canvas.getContext('2d');

        canvas.width = viewport.width;

        canvas.height = viewport.height;

        await page.render({
            canvasContext: context,
            viewport
        }).promise;

        pages.push({
            originalIndex: i - 1,
            thumb: canvas.toDataURL()
        });
    }

    loadingBar.classList.remove('show');

    buildGrid();

    requestAnimationFrame(() => {

        gridReveal.classList.add('visible');

        setTimeout(() => {
            toolbar.classList.add('visible');
        }, 300);

    });
}


/* =========================================
   BUILD GRID
========================================= */

function buildGrid() {

    pagesGrid.innerHTML = '';

    pages.forEach((page, idx) => {
        pagesGrid.appendChild(makeCard(page, idx));
    });

    syncLabels();

    updatePageOrder();
}


function makeCard(page, idx) {

    const item = document.createElement('div');

    item.className = 'page-item';

    item.draggable = true;

    item.dataset.idx = idx;

    item.innerHTML = `
    <div class="thumb-box">
      <img
        class="page-thumb"
        src="${page.thumb}"
      />
    </div>

    <div class="page-label">
      <span class="page-num">
        Page ${idx + 1}
      </span>

      <span class="drag-grip">
        ⠿
      </span>
    </div>
  `;

    item.addEventListener('dragstart', onDragStart);

    item.addEventListener('dragenter', onDragEnter);

    item.addEventListener('dragover', onDragOver);

    item.addEventListener('dragleave', onDragLeave);

    item.addEventListener('drop', onDrop);

    item.addEventListener('dragend', onDragEnd);

    return item;
}


/* =========================================
   LABELS
========================================= */

function syncLabels() {

    const items =
        pagesGrid.querySelectorAll('.page-item');

    items.forEach((el, i) => {

        el.dataset.idx = i;

        el.querySelector('.page-num').textContent =
            `Page ${i + 1}`;
    });

    pageCount.textContent =
        `${pages.length} pages`;

    undoBtn.disabled = !history.length;
}


/* =========================================
   DRAG
========================================= */

function onDragStart(e) {

    dragSrcIdx = +e.currentTarget.dataset.idx;

    e.currentTarget.classList.add('is-dragging');
}


function onDragEnter(e) {

    e.preventDefault();

    const card = e.currentTarget;

    const cardIdx = +card.dataset.idx;

    if (cardIdx === dragSrcIdx) return;

    clearDropClasses();

    card.classList.add('drop-target');
}


function onDragOver(e) {

    e.preventDefault();

    handleAutoScroll(e);
}

function onDragLeave(e) {

    e.currentTarget.classList.remove(
        'drop-target'
    );
}


function onDrop(e) {

    e.preventDefault();

    const card = e.currentTarget;

    const cardIdx = +card.dataset.idx;

    if (cardIdx === dragSrcIdx) return;

    pushHistory();

    const [moved] = pages.splice(
        dragSrcIdx,
        1
    );

    pages.splice(cardIdx, 0, moved);

    buildGrid();
}


function onDragEnd(e) {

    clearDropClasses();

    clearInterval(autoScrollInterval);

    e.currentTarget.classList.remove(
        'is-dragging'
    );

    dragSrcIdx = null;
}

function clearDropClasses() {

    pagesGrid
        .querySelectorAll('.page-item')
        .forEach(el => {

            el.classList.remove(
                'drop-target',
                'is-dragging'
            );

        });
}


/* =========================================
   HISTORY
========================================= */

function pushHistory() {

    history.push(
        pages.map(p => ({ ...p }))
    );

    undoBtn.disabled = false;
}


undoBtn.addEventListener('click', () => {

    if (!history.length) return;

    pages = history.pop();

    buildGrid();
});


/* =========================================
   RESET
========================================= */

function resetOrder() {

    pages.sort((a, b) =>
        a.originalIndex - b.originalIndex
    );

    buildGrid();
}


/* =========================================
   RESET AFTER DOWNLOAD
========================================= */

const downloadFrame =
    document.getElementById('downloadFrame');

downloadFrame.addEventListener('load', () => {

    /*
      Ignore initial empty iframe load
    */

    if (!pages.length) return;

    clearAll();
});

/* =========================================
   CLEAR
========================================= */

function clearAll() {

    pages = [];

    history = [];

    pagesGrid.innerHTML = '';

    gridReveal.classList.remove('visible');

    toolbar.classList.remove('visible');

    orgCard.classList.remove('has-pdf');

    dropLabel.innerHTML =
        `Drag & Drop a PDF here
     <span>or click to browse</span>`;

    pdfInput.value = '';
}


/* =========================================
   PAGE ORDER
========================================= */

function updatePageOrder() {

    const order = pages.map(
        p => p.originalIndex
    );

    pageOrderInput.value =
        JSON.stringify(order);
}