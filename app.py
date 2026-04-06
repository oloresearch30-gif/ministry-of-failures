from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
import io
import os
import json
from config import Config

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

# ── Google Drive Service ──────────────────────────────────────────────────────
def get_drive_service():
    """Build and return an authenticated Google Drive service."""
    creds_info = Config.get_credentials_info()
    if creds_info:
        # Running on Render — load from environment variable
        creds = service_account.Credentials.from_service_account_info(
            creds_info,
            scopes=["https://www.googleapis.com/auth/drive"]
        )
    else:
        # Running locally — load from file
        creds = service_account.Credentials.from_service_account_file(
            Config.SERVICE_ACCOUNT_FILE,
            scopes=["https://www.googleapis.com/auth/drive"]
        )
    return build("drive", "v3", credentials=creds)


def list_drive_files(mime_filter=None, folder_id=None):
    """List files from Google Drive, optionally filtered by MIME type and folder."""
    try:
        service = get_drive_service()
        fid = folder_id or Config.DRIVE_FOLDER_ID
        query = f"'{fid}' in parents and trashed=false"
        if mime_filter:
            mime_parts = " or ".join([f"mimeType='{m}'" for m in mime_filter])
            query += f" and ({mime_parts})"

        results = service.files().list(
            q=query,
            pageSize=100,
            fields="files(id, name, mimeType, size, createdTime, thumbnailLink, webViewLink, webContentLink)"
        ).execute()
        return results.get("files", [])
    except Exception as e:
        print(f"Drive error: {e}")
        return []


def upload_to_drive(file_obj, filename, mime_type, folder_id=None):
    """Upload a file to Google Drive."""
    try:
        service = get_drive_service()
        fid = folder_id or Config.DRIVE_FOLDER_ID
        file_metadata = {
            "name": filename,
            "parents": [fid]
        }
        media = MediaIoBaseUpload(file_obj, mimetype=mime_type, resumable=True)
        uploaded = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, name, webViewLink"
        ).execute()
        # Make it publicly viewable
        service.permissions().create(
            fileId=uploaded["id"],
            body={"type": "anyone", "role": "reader"}
        ).execute()
        return uploaded
    except Exception as e:
        print(f"Upload error: {e}")
        return None


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Landing page — the indexed overview from the PDF."""
    return render_template("index.html")


@app.route("/videos")
def videos():
    """Videos tab — lists videos from Google Drive."""
    files = list_drive_files(mime_filter=[
        "video/mp4", "video/avi", "video/mov",
        "video/quicktime", "video/x-msvideo", "video/webm"
    ])
    return render_template("videos.html", files=files)


@app.route("/documents")
def documents():
    """Documents tab — lists PDFs from Google Drive."""
    files = list_drive_files(mime_filter=["application/pdf"])
    return render_template("documents.html", files=files)


@app.route("/images")
def images():
    """Images tab — lists images from Google Drive."""
    files = list_drive_files(mime_filter=[
        "image/jpeg", "image/png", "image/gif",
        "image/webp", "image/svg+xml"
    ])
    return render_template("images.html", files=files)


@app.route("/gallery")
def gallery():
    """Gallery view — all images in a masonry grid."""
    files = list_drive_files(mime_filter=[
        "image/jpeg", "image/png", "image/gif",
        "image/webp", "image/svg+xml"
    ])
    return render_template("gallery.html", files=files)


# ── API endpoints ─────────────────────────────────────────────────────────────

@app.route("/api/files")
def api_files():
    """Returns all files as JSON, grouped by type."""
    all_files = list_drive_files()
    grouped = {"videos": [], "documents": [], "images": [], "other": []}
    for f in all_files:
        mt = f.get("mimeType", "")
        if mt.startswith("video/"):
            grouped["videos"].append(f)
        elif mt == "application/pdf":
            grouped["documents"].append(f)
        elif mt.startswith("image/"):
            grouped["images"].append(f)
        else:
            grouped["other"].append(f)
    return jsonify(grouped)


if __name__ == "__main__":
    app.run(debug=True, port=5000)


@app.route("/pdf/page/<int:num>")
def pdf_page(num):
    try:
        import fitz
        import io
        pdf_path = os.path.join(app.static_folder, "pdf", "NPP_Failures_size_redue.pdf")
        if not os.path.exists(pdf_path):
            return "PDF not found", 404
        doc = fitz.open(pdf_path)
        if num < 1 or num > len(doc):
            return "Page out of range", 404
        page = doc[num - 1]
        mat  = fitz.Matrix(1.2, 1.2)
        pix  = page.get_pixmap(matrix=mat)
        jpg  = pix.tobytes("jpeg", jpg_quality=75)
        doc.close()
        return app.response_class(jpg, mimetype="image/jpeg")
    except Exception as e:
        print(f"PDF page error: {e}")
        return str(e), 500


@app.route("/pdf/count")
def pdf_count():
    try:
        import fitz
        pdf_path = os.path.join(app.static_folder, "pdf", "NPP_Failures_size_redue.pdf")
        if not os.path.exists(pdf_path):
            return jsonify({"count": 0})
        doc = fitz.open(pdf_path)
        count = len(doc)
        doc.close()
        return jsonify({"count": count})
    except Exception as e:
        print(f"PDF count error: {e}")
        return jsonify({"count": 0})