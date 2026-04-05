# Ministry of Failures — Setup Guide

## Project Structure
```
ministry_of_failures/
├── app.py                  ← Flask backend (all routes)
├── config.py               ← Configuration (Drive folder, credentials)
├── requirements.txt        ← Python dependencies
├── credentials/
│   └── service_account.json  ← Google API key (YOU MUST ADD THIS)
├── templates/
│   ├── base.html           ← Shared layout, header, nav, footer
│   ├── index.html          ← Home + indexed content from PDF
│   ├── gallery.html        ← Masonry gallery of all images
│   ├── images.html         ← Images tab
│   ├── videos.html         ← Videos tab
│   ├── documents.html      ← PDFs tab
│   └── upload.html         ← File upload page
└── static/
    ├── css/style.css       ← All styles (dark documentary theme)
    └── js/main.js          ← Counters, reveals, nav, search shortcuts
```

---

## Step 1 — Install dependencies
```bash
pip install -r requirements.txt
```

---

## Step 2 — Set up Google Drive API

### A. Create a Google Cloud Project
1. Go to https://console.cloud.google.com
2. Create a new project (e.g., "Ministry of Failures")
3. Enable the **Google Drive API** for your project

### B. Create a Service Account
1. Go to **IAM & Admin → Service Accounts**
2. Click **Create Service Account**
3. Name it (e.g., `ministry-drive`)
4. Grant role: **Editor** or **Drive File Creator**
5. Click **Done**

### C. Download the JSON key
1. Click your service account → **Keys** tab
2. **Add Key → Create new key → JSON**
3. Download the file
4. **Place it at:** `credentials/service_account.json`

### D. Share your Google Drive folder
1. Open Google Drive, create a folder (e.g., "Ministry of Failures Archive")
2. Copy the folder ID from the URL:
   `https://drive.google.com/drive/folders/`**`THIS_IS_THE_FOLDER_ID`**
3. Right-click the folder → **Share**
4. Add your service account email (from step B) with **Editor** access
5. Also set to **"Anyone with the link can view"** for public access

---

## Step 3 — Configure
Open `config.py` and set:
```python
DRIVE_FOLDER_ID = "YOUR_GOOGLE_DRIVE_FOLDER_ID_HERE"
```

Or use environment variables:
```bash
export DRIVE_FOLDER_ID="your_folder_id_here"
export GOOGLE_SERVICE_ACCOUNT_FILE="credentials/service_account.json"
```

---

## Step 4 — Run
```bash
python app.py
```
Open: http://localhost:5000

---

## Features
| Page | URL | Description |
|------|-----|-------------|
| Index | `/` | PDF-indexed content + statistics |
| Gallery | `/gallery` | Full masonry image gallery with lightbox |
| Images | `/images` | Image grid tab |
| Videos | `/videos` | Video grid with play previews |
| Documents | `/documents` | PDF list with view/download |
| Upload | `/upload` | Drag & drop upload to Google Drive |
| API | `/api/files` | JSON API of all files grouped by type |

## Upload Limits
- Max file size: **500 MB**
- Accepted: MP4, AVI, MOV, WEBM, PDF, JPG, PNG, GIF, WEBP
