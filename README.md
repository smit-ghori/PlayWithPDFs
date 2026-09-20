# PlayWithPDFs 📄✨

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.0-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/Database-SQLite%20%7C%20PostgreSQL-blue.svg)](https://www.sqlalchemy.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Responsive](https://img.shields.io/badge/Design-Responsive%20%26%20Mobile--First-success.svg)](#responsive-design)

**PlayWithPDFs** is an open-source, feature-rich web platform for processing, editing, converting, and analyzing PDF, image, and office documents. Built with Python, Flask, and modern web standards, it delivers a sleek dark glassmorphic user interface, real-time operations tracking, flexible per-tool configuration, and a comprehensive administrative control panel.

---

## 📑 Table of Contents

- [What's New & Highlights](#-whats-new--highlights)
- [Feature Suite & Tools](#-feature-suite--tools)
- [Admin Panel & Operations](#-admin-panel--operations)
- [Search Capabilities](#-search-capabilities)
- [Responsive Design & Standards Mode](#-responsive-design--standards-mode)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Configuration](#environment-configuration)
  - [Creating the Admin Account](#creating-the-admin-account)
  - [Running the Application](#running-the-application)
- [Directory Structure](#-directory-structure)
- [Configuration Reference](#-configuration-reference)
- [Contributing & License](#-contributing--license)

---

## 🚀 What's New & Highlights

- 🛡️ **Complete Operations Admin Panel**: Manage tool availability (maintenance/kill-switch), monitor live traffic metrics, review error logs, and manage user contact messages from a single secure portal (`/admin`).
- 🔐 **Admin Authentication & Password Recovery**: Secure session-based authentication with role-based access control (`admin`, `viewer`). Includes self-service password recovery via time-limited, single-use signed email tokens (`/admin/forgot-password` & `/admin/reset-password/<token>`).
- 📊 **Dynamic Upload Limits**: Admins can set maximum file count (`max_files`) and maximum file size (`max_file_size_mb`) per tool. Limits are enforced client-side with dismissable auto-expiring notification banners (10-second timeout or cross `✕` button) and validated server-side.
- 🔍 **Instant Tool Search**:
  - **Home Page Hero Search**: Real-time keystroke filtering across tool names, descriptions, and keywords with one-click shortcut filter chips.
  - **Global Navbar Search**: Quick access dropdown from any page with keyboard shortcut (`/` or `Ctrl+K` / `Cmd+K`).
- 📱 **Mobile-First Responsive Design**: Full application-wide HTML5 Standards Mode eliminating browser Quirks Mode across all 27+ templates, accompanied by a redesigned fluid Rotate PDF interface featuring dynamic 2-column mobile layout, active file banners, and paper elevation drop-shadows.

---

## 🛠️ Feature Suite & Tools

### 1. PDF Manipulation
| Tool | Route | Library / Engine | Description |
| :--- | :--- | :--- | :--- |
| **Merge PDF** | `/merge` | `pypdf` | Combine multiple PDF documents into a single organized file. |
| **Split PDF** | `/split` | `pypdf` | Split a PDF into individual pages or custom ranges. |
| **Rotate PDF** | `/rotate_pdf` | `pypdf` / `PDF.js` | Interactive page-by-page or global rotation with live preview. |
| **Remove Pages** | `/remove_pages` | `pypdf` | Select and delete unwanted pages from a document. |
| **Extract Pages** | `/extract_pages` | `pypdf` | Extract specific pages or ranges into a standalone document. |
| **Organize PDF** | `/organize_pdf` | `pypdf` | Reorder, rotate, and sort pages visually. |
| **Compress PDF** | `/compress` | `pikepdf` | Reduce PDF file size while maintaining visual fidelity. |
| **Repair PDF** | `/repair` | `pikepdf` | Fix corrupted, damaged, or unreadable PDF structures. |
| **Crop PDF** | `/crop_pdf` | `PyMuPDF` (`fitz`) | Crop margins or isolate specific sections on PDF pages. |
| **Add Watermark** | `/add_watermark` | `PyMuPDF` (`fitz`) | Overlay text or graphic stamps across document pages. |
| **Add Page Numbers**| `/add_page_number`| `PyPDF2` / `reportlab` | Add customizable headers, footers, and page numbers. |
| **Redact PDF** | `/redact_pdf` | `PyMuPDF` (`fitz`) | Permanently black out sensitive data and private information. |
| **Sign PDF** | `/sign_pdf` | `PyMuPDF` (`fitz`) | Draw or upload signatures to stamp onto PDF documents. |
| **Compare PDF** | `/compare_pdf` | `PyMuPDF` (`fitz`) | Visually highlight side-by-side differences between documents. |
| **Protect PDF** | `/protect_pdf` | `PyPDF2` | Encrypt PDFs with secure passwords and access restrictions. |
| **Unlock PDF** | `/unlock_pdf` | `PyPDF2` | Remove passwords and security permissions from unlocked files. |

### 2. Document & Image Conversions
| Tool | Route | Engine | Description |
| :--- | :--- | :--- | :--- |
| **PDF to Word** | `/pdf_to_word` | `pdf2docx` | Convert complex PDF layouts into editable `.docx` files. |
| **Word to PDF** | `/word_to_pdf` | `python-docx` | Convert `.doc` and `.docx` documents into high-quality PDFs. |
| **PDF to Excel** | `/pdf_to_excel` | `pdfplumber` / `openpyxl` | Extract tabular data into spreadsheets (`.xlsx`). |
| **Excel to PDF** | `/excel_to_pdf` | `openpyxl` / `reportlab` | Transform spreadsheets into shareable PDF tables. |
| **PDF to PPT** | `/pdf_to_ppt` | `python-pptx` / `PyMuPDF` | Convert presentation pages into editable `.pptx` slides. |
| **PPT to PDF** | `/ppt_to_pdf` | `python-pptx` | Render PowerPoint slide decks directly into PDF format. |
| **Images to PDF** | `/jpg_to_pdf` | `Pillow` | Stitch JPEG, PNG, or WebP images into a single document. |
| **PDF to Images** | `/pdf_to_jpg` | `PyMuPDF` | Export PDF pages as crisp standalone image files. |
| **HTML to PDF** | `/html_to_pdf` | `Playwright` | Capture and render live webpages or raw HTML to PDF. |
| **PDF to PDF/A** | `/pdf_to_pdfA` | `pikepdf` | Convert documents into ISO-compliant PDF/A archive files. |

### 3. OCR & Intelligence
| Tool | Route | Engine | Description |
| :--- | :--- | :--- | :--- |
| **OCR PDF** | `/ocr_to_pdf` | `ocrmypdf` / `pytesseract` / `PaddleOCR` | Recognize text in scanned documents and make them searchable. |
| **Translate PDF** | `/translate` | `deep-translator` / `PyMuPDF` | Translate text across 50+ languages while preserving layout. |

---

## 🛡️ Admin Panel & Operations

Access the control panel at `/admin` (or `/admin/login`).

```
┌────────────────────────────────────────────────────────────────┐
│ PlayWithPDFs Operations Dashboard                              │
├───────────────┬────────────────────────────────────────────────┤
│ 📈 Analytics   │ Real-time requests, unique visitors, latency   │
│ ⚙️ Tool Config │ Live toggles, upload file counts & size limits  │
│ 👥 Team Admin  │ Role management (admin, viewer), profile reset │
│ 📬 Inbox       │ Contact form submissions & read/archived state │
│ 📜 Event Logs  │ Request execution metrics and audit trails     │
└───────────────┴────────────────────────────────────────────────┘
```

### Key Administrative Features:
1. **Live Metrics & Analytics** (`/admin/dashboard`):
   - Track total requests, visitor counts, average execution times, and failure rates.
   - Interactive activity charts showing request volume by hour and day.
2. **Per-Tool Operational Controls** (`/admin/tools`):
   - **Kill Switch / Maintenance Mode**: Instantly pause or resume individual tools without restarting the application server. Paused tools display a branded 503 maintenance page.
   - **File Limits**: Configure maximum uploaded files (`max_files`) and maximum upload size (`max_file_size_mb`).
   - **Filter & Search**: Quickly filter tools by status (`Live`, `Disabled`) or search by name.
3. **Team Management** (`/admin/team`):
   - Create accounts with role-based access (`admin` with full control or `viewer` with read-only dashboard access).
   - In-place credentials updates and account removals.
4. **Account Settings & Password Recovery**:
   - **Admin Profile** (`/admin/profile`): Update administrator name, email address, and change passwords with current password verification.
   - **Forgot Password Flow** (`/admin/forgot-password`): Generate secure 1-hour signed tokens sent via email (or logged to terminal in dev mode).
   - **Reset Password** (`/admin/reset-password/<token>`): Enforces token validity, single-use invalidation upon password change, and password matching.
5. **Messages Inbox** (`/admin/messages`):
   - Review incoming inquiries from the `/contact_us` route, filter unread items, and mark messages as read or archived.
6. **Audit Logs & Event Tracking** (`/admin/events`):
   - Full audit trail of administrative modifications (tool toggles, limit changes, team updates).
   - Performance logs capturing execution times, IP hashes, and error traces.

---

## 🔍 Search Capabilities

### 1. Home Page Hero Search
- Instant, zero-latency keystroke filtering of all available tools on the home page.
- Matches tool titles, descriptions, and semantic aliases (e.g. searching *"shrink"* matches Compress, *"extract"* matches Extract Pages, *"doc"* matches Word tools).
- Quick filter chips for popular operations (*Merge, Compress, Word to PDF, JPG to PDF, Split, Watermark, Organize*).
- URL query synchronization (`/?q=...`) for shareable search links.

### 2. Global Navbar Search
- Accessible from any page across the site via the navigation bar.
- Floating instant results dropdown showing tool icons, titles, and descriptions.
- Global keyboard shortcut: Press `/` or `Ctrl+K` (`Cmd+K` on macOS) to instantly focus search.

---

## 📱 Responsive Design & Standards Mode

- **HTML5 Standards Mode Enforced**: All 27+ tool templates load stylesheets inside `{% block extra_css %}`, ensuring valid `<!doctype html>` delivery. This prevents browser Quirks Mode, guaranteeing that CSS Grid, Flexbox, and viewport units scale predictably across devices.
- **Redesigned Rotate PDF Interface**:
  - Fluid responsive grid providing **2 columns** on mobile devices (360px–480px), **3 columns** on tablets, and **4–5 columns** on desktop.
  - Replaces bulky upload drop-zones with a compact 44px **Active File Banner** displaying the document title, page count, and change action.
  - Realistic matte dark stage with elevated white paper drop-shadows and dynamic rotation badges (`90°`, `180°`, `270°`).
  - Auto-scaling canvas logic preventing portrait or landscape overflow.

---

## 💻 Tech Stack

- **Core & Backend**: Python 3.10+, Flask 3.0, Werkzeug, Gunicorn
- **Database & ORM**: SQLite (Default / Local), PostgreSQL via SQLAlchemy & `psycopg`
- **Mail Services**: Flask-Mail (SMTP / Gmail)
- **Token Security**: `itsdangerous` (URLSafeTimedSerializer)
- **PDF Engines**: `pypdf`, `PyPDF2`, `PyMuPDF` (fitz), `pikepdf`, `pdfplumber`, `reportlab`
- **Document & Office Engines**: `python-docx`, `pdf2docx`, `python-pptx`, `openpyxl`, `pandas`, `xlrd`
- **Computer Vision & OCR**: `Pillow`, `pytesseract`, `ocrmypdf`, `paddleocr`, `opencv-python-headless`
- **Browser Automation**: `Playwright`
- **Frontend**: Vanilla HTML5, Modern CSS3 (Dark Glassmorphism, CSS Grid & Flexbox), Vanilla JS, [Lucide Icons](https://lucide.dev/), [PDF.js](https://mozilla.github.io/pdf.js/)

---

## 🚦 Getting Started

### Prerequisites
- **Python**: Version 3.10 or higher.
- **Tesseract OCR** (Optional, for OCR tools):
  - Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
  - macOS: `brew install tesseract`
  - Windows: Download installer from [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki).
- **Poppler** (Optional, for PDF rendering utilities):
  - Ubuntu/Debian: `sudo apt-get install poppler-utils`
  - macOS: `brew install poppler`

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/PlayWithPDFs.git
   cd PlayWithPDFs
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # On macOS/Linux:
   python3 -m venv .venv
   source .venv/bin/activate

   # On Windows (PowerShell):
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers** (Optional, for HTML-to-PDF):
   ```bash
   playwright install chromium
   ```

---

### Environment Configuration

Create a `.env` file in the project root directory:

```ini
# Application Security
SECRET_KEY=generate-a-strong-random-secret-key-here

# Database (Default: sqlite:///playwithpdfs.db if omitted)
DATABASE_URL=sqlite:///playwithpdfs.db
# For production PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/playwithpdfs

# Mail Settings (Optional, for contact emails & password resets)
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password

# Upload Directory
UPLOAD_FOLDER=uploads
PORT=5000
```

---

### Creating the Admin Account

Provision your initial administrator credentials via the built-in CLI command:

```bash
flask create-admin
```

Follow the interactive prompts:
```text
Email: admin@example.com
Name: Super Admin
Password: [secure-password]
Created admin user: admin@example.com
```

---

### Running the Application

1. **Start the local development server**:
   ```bash
   python main.py
   ```

2. **Access the platform**:
   - **User Application**: [http://localhost:5000](http://localhost:5000)
   - **Admin Login**: [http://localhost:5000/admin/login](http://localhost:5000/admin/login)
   - **Admin Dashboard**: [http://localhost:5000/admin](http://localhost:5000/admin)

3. **Production Deployment with Gunicorn**:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 "main:app"
   ```

---

## 📁 Directory Structure

```text
PlayWithPDFs/
├── instance/               # Local SQLite database files
├── routes/                 # Modular Flask Blueprints
│   ├── admin.py            # Admin dashboard, auth & configuration routes
│   ├── home.py             # Home page & search routing
│   ├── rotate_pdf.py       # PDF rotation logic
│   ├── merge.py            # PDF merging
│   ├── compress.py         # PDF compression
│   ├── contact_us.py       # Contact form submissions
│   └── ...                 # 25+ tool blueprints
├── static/
│   ├── css/                # Component styles (navbar, footer, tools, admin)
│   │   ├── admin.css       # Admin panel styling
│   │   ├── rotate_pdf.css  # Modern responsive styles for Rotate PDF
│   │   ├── index.css       # Hero search bar styling
│   │   └── navbar.css      # Header & search dropdown styles
│   ├── scripts/            # Client scripts (card upload, previews, loader)
│   │   ├── card.js         # Upload drag/drop & limit validation
│   │   ├── rotate_pdf.js   # PDF.js preview & rotation controls
│   │   └── loader.js       # Form submit spinner & limit validation
│   └── images/             # Static logos and graphic assets
├── templates/              # Jinja HTML templates
│   ├── base.html           # Master layout with global search & notifications
│   ├── index.html          # Home landing page with hero search
│   ├── rotate_pdf.html     # Redesigned responsive Rotate PDF interface
│   ├── admin/              # Admin panel view templates
│   │   ├── _layout.html    # Admin panel layout & sidebar
│   │   ├── dashboard.html  # Live charts & telemetry
│   │   ├── tools.html      # Tool management & limits
│   │   ├── team.html       # Team member administration
│   │   ├── messages.html   # Contact message inbox
│   │   ├── events.html     # Event logs & audit stream
│   │   ├── profile.html    # Admin credentials & account settings
│   │   ├── login.html      # Admin authentication
│   │   ├── forgot_password.html # Password recovery request
│   │   └── reset_password.html  # New password submission
│   └── ...                 # Tool-specific templates
├── utils/
│   ├── file_utils.py       # Temporary file cleanup worker
│   └── tracking.py         # Request telemetry, visitor hashing & tool seeding
├── extensions.py           # SQLAlchemy & Flask-Mail instances
├── models.py               # Database schemas (AdminUser, ToolConfig, ToolEvent, etc.)
├── main.py                 # Application factory, route registration & CLI commands
├── requirements.txt        # Python package dependencies
├── render.yaml             # Render cloud deployment specification
├── Dockerfile              # Containerization definition
└── README.md               # Project documentation
```

---

## ⚙️ Configuration Reference

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `SECRET_KEY` | `string` | `"fallback-secret"` | Encryption key for sessions, CSRF, and timed password reset tokens. |
| `DATABASE_URL` | `string` | `"sqlite:///playwithpdfs.db"` | Database connection string. Automatically handles PostgreSQL dialects. |
| `MAIL_SERVER` | `string` | `"smtp.gmail.com"` | SMTP host for outbound notifications. |
| `MAIL_PORT` | `int` | `587` | Outbound SMTP port. |
| `MAIL_USE_TLS` | `bool` | `True` | Enables TLS transport security. |
| `MAIL_USERNAME` | `string` | `None` | Email username/address for sending password resets & contact receipts. |
| `MAIL_PASSWORD` | `string` | `None` | App-specific password for the email provider. |
| `UPLOAD_FOLDER` | `string` | `"uploads"` | Directory used for temporary document processing before download. |
| `PORT` | `int` | `5000` | Port on which the application server listens. |

---

## 📄 License & Contributing

- **License**: Distributed under the [MIT License](LICENSE).
- **Contributions**: Contributions, issue reports, and feature requests are welcome! Feel free to open a pull request or submit an issue on GitHub.

---

<div align="center">
  <sub>Built with ❤️ using Python &amp; Flask. Empowering seamless document management everywhere.</sub>
</div>
