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


@app.route("/upload", methods=["GET", "POST"])
def upload():
    """Upload page — users can upload videos, PDFs, images."""
    if request.method == "POST":
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"success": False, "error": "No file selected"}), 400

        allowed_mimes = {
            # Videos
            "video/mp4", "video/avi", "video/quicktime",
            "video/x-msvideo", "video/webm", "video/mov",
            # Documents
            "application/pdf",
            # Images
            "image/jpeg", "image/png", "image/gif",
            "image/webp", "image/svg+xml"
        }

        mime_type = file.content_type
        if mime_type not in allowed_mimes:
            return jsonify({"success": False, "error": f"File type '{mime_type}' not allowed"}), 400

        # Max 500 MB
        file_bytes = file.read()
        if len(file_bytes) > 500 * 1024 * 1024:
            return jsonify({"success": False, "error": "File too large (max 500 MB)"}), 400

        file_io = io.BytesIO(file_bytes)
        result = upload_to_drive(file_io, file.filename, mime_type)

        if result:
            return jsonify({
                "success": True,
                "name": result.get("name"),
                "link": result.get("webViewLink"),
                "id": result.get("id")
            })
        else:
            return jsonify({"success": False, "error": "Upload failed. Check server logs."}), 500

    return render_template("upload.html")


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
